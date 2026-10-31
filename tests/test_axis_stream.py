"""Tests for AXIS streaming (SPEC-12 section 8) and the Cold Check block (section 4.1)."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.axis_stream import SocraticStreamFilter, stream_axis
from lms.adapters.ai.local_llm_companion import LocalLLMCompanion, LocalLLMError
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType, AssistanceLevel

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
GUARD = SocraticGuardrail()
BASE = "/api/v1/learners/me"


class ScriptedCompanion(MockAxisCompanion):
    """A model that says exactly what a test scripts, in the chunks it chooses."""

    def __init__(self, chunks, cited=("Operational Communication Cycle",)):
        super().__init__()
        self.chunks = chunks
        self.cited = list(cited)

    def stream(self, query):
        return iter(self.chunks), self.cited


class BrokenCompanion(MockAxisCompanion):
    def stream(self, query):
        raise LocalLLMError("http://127.0.0.1:8888 secret-token-abc failed")


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


def make_client(repo, catalog, axis=None):
    app = create_app(
        repo=repo,
        runner=SubprocessRunner(),
        axis=axis or MockAxisCompanion(),
        catalog=catalog,
        clock=lambda: T0,
    )
    return TestClient(app)


def body(mode="Socratic", **extra):
    return {
        "unit_id": "PY-0.1",
        "mode": mode,
        "current_activity": "Predict",
        "user_prompt": "Why does this fail?",
        "page": "predict",
        **extra,
    }


def parse_sse(text):
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def stream(client, **extra):
    res = client.post("/api/v1/axis/stream", json=body(**extra))
    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith("text/event-stream")
    return parse_sse(res.text)


def tokens(events):
    return "".join(data["text"] for name, data in events if name == "token")


# --- The route ---


def test_stream_sends_tokens_then_done(repo, catalog):
    events = stream(make_client(repo, catalog))

    assert [name for name, _ in events][0] == "token"
    assert events[-1][0] == "done"
    assert tokens(events)
    assert events[-1][1]["assistance_level"] in [a.value for a in AssistanceLevel]


def test_several_tokens_arrive(repo, catalog):
    events = stream(make_client(repo, catalog), mode="Coach")

    assert len([1 for name, _ in events if name == "token"]) > 1


def test_citations_come_before_done(repo, catalog):
    events = stream(make_client(repo, catalog))
    names = [name for name, _ in events]

    assert names.index("citation") < names.index("done")
    citation = next(data for name, data in events if name == "citation")
    assert set(citation) == {"concept_id", "title", "doc_url"}
    assert events[-1][1]["cited_concepts"]


def test_stream_logs_assistance_against_the_exercise(repo, catalog):
    client = make_client(repo, catalog)

    events = stream(client, exercise_id="PY-0.1/predict-1/v1")

    levels = repo.get_assistance_levels(LOCAL_LEARNER_ID, "PY-0.1/predict-1/v1", T0)
    assert [l.value for l in levels] == [events[-1][1]["assistance_level"]]


def test_body_learner_id_is_ignored(repo, catalog):
    stream(make_client(repo, catalog), exercise_id="PY-0.1/predict-1/v1", learner_id="someone_else")

    assert repo.get_assistance_levels("someone_else", "PY-0.1/predict-1/v1", T0) == []


def test_model_failure_is_an_error_event_with_no_details(repo, catalog):
    res = make_client(repo, catalog, BrokenCompanion()).post("/api/v1/axis/stream", json=body())

    events = parse_sse(res.text)
    assert events[-1][0] == "error"
    assert "secret-token" not in res.text
    assert "127.0.0.1" not in res.text


def test_failure_mid_stream_is_an_error_event(repo, catalog):
    class FailsLater(MockAxisCompanion):
        def stream(self, query):
            def deltas():
                yield "First sentence. "
                raise RuntimeError("boom secret")

            return deltas(), []

    res = make_client(repo, catalog, FailsLater()).post("/api/v1/axis/stream", json=body())

    events = parse_sse(res.text)
    assert events[-1][0] == "error"
    assert "secret" not in res.text


# --- Cold Check block ---


COLD = "PY-0.1/cold-predict-1/v1"


def test_stream_is_refused_on_a_cold_check_item(repo, catalog):
    res = make_client(repo, catalog).post("/api/v1/axis/stream", json=body(exercise_id=COLD))

    assert res.status_code == 403
    assert res.headers["content-type"].startswith("application/problem+json")


def test_consult_is_refused_on_a_cold_check_item(repo, catalog):
    request = body(exercise_id=COLD)
    request.pop("page")

    assert make_client(repo, catalog).post("/api/v1/axis/consult", json=request).status_code == 403


def test_normal_exercises_are_not_blocked(repo, catalog):
    client = make_client(repo, catalog)

    assert client.post("/api/v1/axis/stream", json=body(exercise_id="PY-0.1/predict-1/v1")).status_code == 200


# --- The Socratic filter ---


def filtered(chunks):
    gate = SocraticStreamFilter(GUARD)
    out = []
    for chunk in chunks:
        out.extend(gate.feed(chunk))
    out.extend(gate.finish())
    return "".join(out)


def test_clean_sentences_pass_through():
    text = filtered(["What is the type ", "of this value? ", "Look at line 2."])

    assert "What is the type of this value?" in text
    assert "Look at line 2." in text


def test_nothing_is_released_before_its_sentence_ends():
    gate = SocraticStreamFilter(GUARD)

    assert gate.feed("What is the") == []
    assert gate.feed(" type? ") == ["What is the type? "]


@pytest.mark.parametrize(
    "chunks",
    [
        ["Try this:\n```python\ndef f():\n    return 1\n```\nWhy?"],
        ["Try this:\n``", "`python\nprint(1)\n", "x = 2\n`", "``\nWhy?"],
        ["```\nname = input()\n```"],
        ["~~~\ncode_here()\n~~~\nWhy?"],
        ["You could write def solve(x): return x + 1 and be done. Why?"],
        ["First line.\n", "name = input('Name: ')\n", "Why does it work?"],
        ["import os\nprint(os.getcwd())\n```"],
        ["``", "`", "\n", "secret_answer()\n", "``", "`\n"],
    ],
)
def test_code_never_leaves_the_filter(chunks):
    text = filtered(chunks)

    assert not GUARD.contains_code(text)
    assert "def f" not in text
    assert "input(" not in text
    assert "secret_answer" not in text
    assert "code_here" not in text
    assert "print(1)" not in text


@pytest.mark.parametrize(
    "line",
    [
        "print(name.upper())",
        "clean = raw.strip().title()",
        "for line in lines:",
        "if age < 18:",
        "total += 1",
        "    return value",
    ],
)
def test_unfenced_code_lines_are_withheld(line):
    text = filtered([f"Look closely.\n{line}\nWhat do you notice?"])

    assert line.strip() not in text
    assert "What do you notice?" in text


@pytest.mark.parametrize(
    "sentence",
    [
        "What does print() do here?",
        "Think about what input() returns before you go on.",
        "If the age is 18, which desk is right?",
        "For each line, what is the value of x?",
    ],
)
def test_prose_about_code_still_passes(sentence):
    assert sentence in filtered([sentence + " "])


def test_every_released_chunk_is_clean_on_its_own():
    gate = SocraticStreamFilter(GUARD)
    released = []
    for ch in "Think first.\n```python\ndef f():\n    return 1\n```\nWhat next?":
        released.extend(gate.feed(ch))
    released.extend(gate.finish())

    assert all(not GUARD.contains_code(chunk) for chunk in released)


def test_withheld_code_leaves_the_guiding_question():
    text = filtered(["```\nx = 1\n```"])

    assert "direct code solutions are withheld" in text
    assert "?" in text


def test_a_reply_with_no_question_gets_one():
    assert "?" in filtered(["This is simply how it works."])


def test_coach_mode_is_not_filtered():
    companion = ScriptedCompanion(["Use ", "```python\nprint(1)\n```"])
    query = AxisQuery(
        unit_id="PY-0.1", mode=AxisMode.COACH, current_activity=ActivityType.PREDICT, user_prompt="How?"
    )

    events = list(stream_axis(companion, query, GUARD, AssistanceClassifier()))

    assert "print(1)" in tokens(events)


def test_socratic_stream_never_emits_a_code_block_end_to_end(repo, catalog):
    companion = ScriptedCompanion(["Here:\n``", "`python\ndef run_intake(a):\n", "    return a\n``", "`\n"])

    events = stream(make_client(repo, catalog, companion))

    assert "```" not in tokens(events)
    assert "run_intake" not in tokens(events)
    assert events[-1][0] == "done"
    assert events[-1][1]["assistance_level"] != AssistanceLevel.SUPPLIED_REASONING.value


# --- The local model ---


def sse_line(payload):
    return f"data: {json.dumps(payload)}\n\n"


def local_companion(handler, **kwargs):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return LocalLLMCompanion(
        base_url="http://local/v1", model="test-model", api_key="test-only", http_client=client, **kwargs
    )


def query():
    return AxisQuery(
        unit_id="PY-0.1", mode=AxisMode.SOCRATIC, current_activity=ActivityType.PREDICT, user_prompt="Why?"
    )


def test_local_model_streams_its_deltas():
    sent = {}

    def handler(request):
        sent.update(json.loads(request.content))
        chunks = [
            sse_line({"choices": [{"delta": {"content": "What "}}]}),
            sse_line({"choices": [{"delta": {"content": "type?"}}]}),
            "data: [DONE]\n\n",
        ]
        return httpx.Response(200, text="".join(chunks))

    deltas, cited = local_companion(handler).stream(query())

    assert "".join(deltas) == "What type?"
    assert sent["stream"] is True
    assert sent["model"] == "test-model"
    assert cited


def test_local_model_with_only_reasoning_still_answers():
    def handler(request):
        return httpx.Response(
            200,
            text=sse_line({"choices": [{"delta": {"reasoning_content": "Why this?"}}]}) + "data: [DONE]\n\n",
        )

    deltas, _ = local_companion(handler).stream(query())

    assert "".join(deltas) == "Why this?"


def test_unreachable_model_falls_back_to_mock():
    def handler(request):
        raise httpx.ConnectError("refused")

    deltas, _ = local_companion(handler, fallback_to_mock=True).stream(query())

    assert "".join(deltas)


def test_unreachable_model_without_fallback_raises():
    def handler(request):
        raise httpx.ConnectError("refused")

    deltas, _ = local_companion(handler, fallback_to_mock=False).stream(query())

    with pytest.raises(LocalLLMError):
        "".join(deltas)


def test_local_model_end_to_end_stays_socratic(repo, catalog):
    def handler(request):
        text = "".join(
            sse_line({"choices": [{"delta": {"content": c}}]})
            for c in ["Check it.\n``", "`python\nprint(1)\n```\n", "What type is it?"]
        )
        return httpx.Response(200, text=text + "data: [DONE]\n\n")

    events = stream(make_client(repo, catalog, local_companion(handler)))

    assert "print(1)" not in tokens(events)
    assert "What type is it?" in tokens(events)
