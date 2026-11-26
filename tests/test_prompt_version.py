"""The prompt version and where it is written (ADR-0039 / SPEC-31 R12 to R14).

The contract these tests fix (names the spec leaves open):
  axis_rules.prompt_version(system, user_template) -> str   the one hashing function (static texts only)
  axis_rules.chat_prompt_version(mode, source_state) -> str  source_state: "course", "not_found", "no_index", "unavailable"
  results.json "prompt_versions": {"<Mode>/<state>": version}
The span attribute and the log payload key are both `prompt_version` (spec).

Real adapters behind a real ProviderRouter, with a mocked HTTP transport or a fake Gemini client: no model and
no network. All text is synthetic or the made-up test fixtures.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

import obedience_support as ob
from fake_retriever import FakeRetriever, passage
from test_ai_judgement import GOOD, write_rubric
from test_stage_build import pass_cold_checks
from test_tracing_routes import (
    LEARNER,
    consult_body,
    events_of,
    local_tracer,
    make_client,
    post_check,
    post_consult,
    post_draft,
    post_explain,
    post_stream,
    read_spans,
    trace_text,
)

from lms.adapters.ai.gemini_companion import GeminiCompanion
from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.metering import UsageMeter
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.ai.providers.router import ProviderRouter
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.model_usage import UsageStore
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.core import tracing
from lms.core.ai_judgement import Idea
from lms.core.interfaces import AxisMode, AxisQuery, ExecutionResult
from lms.core.models import ActivityType
from lms.core.retrieval import RetrievalStatus

ROOT = Path(__file__).resolve().parents[1]
MODES = [AxisMode.SOCRATIC, AxisMode.HYBRID, AxisMode.COACH]
ALL_STATES = ["course", "not_found", "no_index", "unavailable"]
HEX12 = re.compile(r"[0-9a-f]{12}")
PASSAGE_TEXT = "a synthetic passage about nothing real"
FAKE_KEY = "sk-FAKE-version-test-0001"
PROFILES = parse_profiles({"profiles": [
    {"id": "local", "label": "Local", "kind": "openai_compatible", "base_url": "http://127.0.0.1:8888/v1",
     "model": "m-local", "paid": False},
    {"id": "openai", "label": "OpenAI", "kind": "openai_compatible", "base_url": "https://api.openai.com/v1",
     "model": "m-paid", "key_env": "OPENAI_API_KEY", "paid": True, "price_per_million": {"input": 0.1, "output": 0.5}},
    {"id": "gemini", "label": "Gemini", "kind": "gemini", "model": "m-gemini", "key_env": "GEMINI_API_KEY",
     "paid": True, "price_per_million": {"input": 0.75, "output": 3.75}},
]})
USER_EVENTS = ("axis", "concept_check", "document_draft", "build_feedback")


def is_version(value) -> bool:
    return isinstance(value, str) and bool(HEX12.fullmatch(value))


# --- fakes: the real adapters over a mocked transport -------------------------------------------


class Transport:
    """Answers every OpenAI-compatible call offline. Set `status` to make the next calls fail."""

    def __init__(self):
        self.status = 200
        self.sent: list = []
        self.text = None  # set to answer every call with this

    def __call__(self, request):
        body = json.loads(request.content)
        self.sent.append(body)
        if self.status != 200:
            return httpx.Response(self.status, json={"error": {"message": "synthetic"}})
        system = body["messages"][0]["content"]
        text = GOOD if system == axis_rules.JUDGE_SYSTEM_PROMPT else "Which line fails?"
        if self.text is not None:
            text = self.text
        if body.get("stream"):
            chunk = {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "fake-model-1",
                     "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": "stop"}]}
            return httpx.Response(200, text=f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n",
                                  headers={"content-type": "text/event-stream"})
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 0, "model": "fake-model-1",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}],
        })


class FakeGeminiModels:
    def _response(self):
        return SimpleNamespace(text="Which line fails?", usage_metadata=None, model_version="fake-gemini-1")

    def generate_content(self, **kwargs):
        return self._response()

    def generate_content_stream(self, **kwargs):
        yield self._response()


def retriever(text=PASSAGE_TEXT):
    return FakeRetriever((passage("how-to/synthetic", text, score=2.5, pid="ab12cd34ef56ab12"),),
                         index_version="ab12cd34ef56")


def make_router(tmp_path, *, transport=None, found=None, cap=None, active=None, mock=False, environ=None):
    """A ProviderRouter over real adapters. `found` is the retriever (default: one passage)."""
    transport = transport or Transport()
    found = found or retriever()
    store = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc), session_id="r")
    store.initialize()
    if active:
        store.set_active(active)
    meter = None if cap is None else UsageMeter(store, cap_usd=cap)

    def factory(profile, key, used_meter):
        if profile.id == "gemini":
            return GeminiCompanion(model=profile.model, api_key="AIza-test", retriever=found, profile=profile,
                                   meter=used_meter, client=SimpleNamespace(models=FakeGeminiModels()))
        return OpenAICompatibleCompanion(
            base_url=profile.base_url, model=profile.model, api_key="local-no-key", retriever=found,
            profile=profile, meter=used_meter, fallback_to_mock=not profile.paid,
            http_client=httpx.Client(transport=httpx.MockTransport(transport)),
        )

    keys = {"OPENAI_API_KEY": FAKE_KEY, "GEMINI_API_KEY": FAKE_KEY}
    router = ProviderRouter(PROFILES, store, environ=keys if environ is None else environ, mock=mock,
                            factory=factory, meter=meter)
    router.transport = transport
    return router


def query(mode=AxisMode.COACH, **changes):
    fields = dict(unit_id="PY-0.1", mode=mode, current_activity=ActivityType.TRACE, user_prompt="synthetic question")
    return AxisQuery(**{**fields, **changes})


def stderr(text):
    return ExecutionResult(success=False, stdout="", stderr=text, exit_code=1, duration_ms=1.0)


def point(n):
    return SimpleNamespace(status="met", where=f"where {n}", found=f"found {n}", why=f"why {n}", looked_for=f"rule {n}")


@pytest.fixture
def traces(tmp_path):
    folder = tmp_path / "traces"
    tracing.set_tracer(local_tracer(folder))
    yield folder
    tracing.set_tracer(tracing.NoopTracer())


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def repo():
    r = SQLiteLearnerRepository(db_path=":memory:")
    r.initialize()
    return r


@pytest.fixture
def answers(tmp_path, monkeypatch):
    """The made-up test answers plus a made-up rubric. A bare folder would leave the build locked, and the
    cached cold-check pool of test_stage_build would stay empty for later tests."""
    shutil.copytree(os.environ["LMS_ANSWERS_DIR"], tmp_path / "answers")
    write_rubric(tmp_path / "answers", unit="py-0.4")
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))


def model_calls(folder):
    return [s for s in read_spans(folder) if s["name"] == "model_call"]


def span_versions(folder):
    """The prompt_version of each model_call span, in the order written."""
    return [s["attributes"].get("prompt_version") for s in model_calls(folder)]


def last_version(folder):
    value = span_versions(folder)[-1]
    assert is_version(value), f"model_call span has no prompt_version: {value!r}"
    return value


# --- R12: the version itself ---


def test_version_is_12_hex_and_stable():
    first = axis_rules.prompt_version("system text", "user template")

    assert is_version(first)
    assert axis_rules.prompt_version("system text", "user template") == first
    assert axis_rules.prompt_version("system text.", "user template") != first
    assert axis_rules.prompt_version("system text", "user template.") != first
    here = axis_rules.chat_prompt_version(AxisMode.COACH, "course")
    code = (
        "from lms.adapters.ai.providers import axis_rules; from lms.core.interfaces import AxisMode; "
        "print(axis_rules.chat_prompt_version(AxisMode.COACH, 'course'), end='')"
    )
    other = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60, cwd=str(ROOT),
                           env={**os.environ, "PYTHONHASHSEED": "7"}, check=True).stdout
    assert other == here


def test_each_mode_and_state_has_its_own_version():
    versions = {(m, s): axis_rules.chat_prompt_version(m, s) for m in MODES for s in ALL_STATES}

    assert all(is_version(v) for v in versions.values())
    # One version per assembled static prompt (R12). With no source, Hybrid and Coach have the same prompt
    # (R3: the same neutral header and contract; only Socratic adds the ADR-0009 line), so they share it.
    by_mode = {m.value: m for m in MODES}
    for state in ALL_STATES:
        if state != "course":
            assert versions[(by_mode["Hybrid"], state)] == versions[(by_mode["Coach"], state)]
    assert len(set(versions.values())) == 9  # 3 grounded, and (Socratic, Hybrid or Coach) for each of 3 states


def test_version_changes_when_wording_changes_not_when_learner_text_changes(tmp_path, traces, monkeypatch):
    first = make_router(tmp_path)
    first.consult(query())
    base = last_version(traces)
    first.consult(query(user_prompt="a completely different question", learner_code="x = 1",
                        execution_result=stderr("synthetic boom")))
    assert last_version(traces) == base == axis_rules.chat_prompt_version(AxisMode.COACH, "course")

    # A different passage, one that holds the placeholder text (SPEC-31 section 6).
    make_router(tmp_path, found=retriever("another passage with <passages> inside it")).consult(query())
    assert last_version(traces) == base

    # Learner text that looks like a mode header, and a very long question.
    first.consult(query(user_prompt="MODE: SOCRATIC FACILITATOR. " + "q" * 100_000))
    assert last_version(traces) == base

    # The wording changes: the version of that prompt changes, the others do not.
    untouched = axis_rules.chat_prompt_version(AxisMode.COACH, "course")
    before = axis_rules.chat_prompt_version(AxisMode.COACH, "not_found")
    monkeypatch.setitem(axis_rules.NO_SOURCE_SENTENCES, "not_found", "A different synthetic sentence.")
    assert axis_rules.chat_prompt_version(AxisMode.COACH, "not_found") != before
    assert axis_rules.chat_prompt_version(AxisMode.COACH, "course") == untouched


def test_a_reworded_judge_prompt_changes_the_judge_version(tmp_path, traces, monkeypatch):
    router = make_router(tmp_path)
    rubric = SimpleNamespace(ideas=[Idea(id="returns-text", text="synthetic one"),
                                    Idea(id="math-needs-numbers", text="synthetic two")])
    router.judge_explanation("PY-0.4", "synthetic prompt", "synthetic text", rubric)
    before = last_version(traces)

    monkeypatch.setattr(axis_rules, "JUDGE_SYSTEM_PROMPT", axis_rules.JUDGE_SYSTEM_PROMPT + " Be brief.")
    router.judge_explanation("PY-0.4", "synthetic prompt", "synthetic text", rubric)

    assert last_version(traces) != before


def test_version_ignores_unit_activity_rubric_brief_and_optional_blocks(tmp_path, traces):
    router = make_router(tmp_path)

    def versions_of(*calls):
        found = []
        for call in calls:
            call()
            found.append(last_version(traces))
        return found

    chat = versions_of(
        lambda: router.consult(query()),
        lambda: router.consult(query(unit_id="PY-1.2", current_activity=ActivityType.PREDICT)),
        lambda: router.consult(query(learner_code="x = 1")),
        lambda: router.consult(query(execution_result=stderr("synthetic boom"))),
        lambda: "".join(router.stream(query(learner_code="y = 2"))[0]),
    )
    two = SimpleNamespace(ideas=[Idea(id="returns-text", text="one"), Idea(id="math-needs-numbers", text="two")])
    other = SimpleNamespace(ideas=[Idea(id="returns-text", text="uno"), Idea(id="math-needs-numbers", text="dos")])
    judge = versions_of(
        lambda: router.judge_explanation("PY-0.4", "first question", "first explanation", two),
        lambda: router.judge_explanation("PY-1.2", "second question", "second explanation", other),
        # more ideas than the first rubric: the version covers the static text only (section 8, clarification 5)
        lambda: router.judge_explanation("PY-0.4", "q", "e", SimpleNamespace(ideas=two.ideas + [Idea(id="third-idea", text="three")])),
    )
    draft = versions_of(
        lambda: router.draft_readme("first.py", "x = 1", "first brief"),
        lambda: router.draft_readme("second.py", "y = 2", "second brief"),
    )
    feedback = versions_of(
        lambda: router.summarise_feedback([point(1)], "readme", "note", "script", "output"),
        lambda: router.summarise_feedback([point(2), point(3)], "other", "other", "", ""),
    )

    for found in (chat, judge, draft, feedback):
        assert len(set(found)) == 1, found
    assert len({chat[0], judge[0], draft[0], feedback[0]}) == 4


def test_the_catalogue_prints_the_version_a_call_records(tmp_path, traces):
    sys.path.insert(0, str(ROOT / "scripts"))
    router = make_router(tmp_path)
    ideas = SimpleNamespace(ideas=[Idea(id="returns-text", text="one"), Idea(id="math-needs-numbers", text="two")])
    router.consult(query())
    router.judge_explanation("PY-0.4", "q", "e", ideas)
    router.draft_readme("x.py", "x = 1", "brief")
    router.summarise_feedback([point(1)], "readme", "note")
    versions = span_versions(traces)
    import make_prompt_catalogue

    text = make_prompt_catalogue.render_catalogue()

    assert len(versions) == 4
    for version in versions:
        assert is_version(version) and version in text


# --- R13a: the model_call span ---


@pytest.mark.parametrize("value", [
    "ABCDEF012345", "abcdef01234", "abcdef0123456", "abcdef01234g", "abcdef012345\n", "", 123456789012, None,
    "the system prompt text",
])
def test_the_span_attribute_accepts_only_12_lowercase_hex(value):
    kept, dropped = tracing.sanitise_attributes({"prompt_version": value})

    assert kept == {} and dropped == 1
    assert tracing.sanitise_attributes({"prompt_version": "abcdef012345"}) == ({"prompt_version": "abcdef012345"}, 0)


@pytest.mark.parametrize("post, mode", [(post_consult, AxisMode.COACH), (post_stream, AxisMode.SOCRATIC)])
def test_model_call_span_carries_prompt_version_and_no_text(tmp_path, repo, catalog, traces, post, mode):
    post(make_client(repo, catalog, make_router(tmp_path)))

    (call,) = model_calls(traces)
    assert call["attributes"].get("prompt_version") == axis_rules.chat_prompt_version(mode, "course")
    written = trace_text(traces)
    for secret in (LEARNER["question"], LEARNER["code"], PASSAGE_TEXT, "You are AXIS", "COURSE REFERENCE"):
        assert secret not in written


def test_a_gemini_call_carries_the_same_version(tmp_path, traces):
    router = make_router(tmp_path, active="gemini")

    router.consult(query())
    consulted = last_version(traces)
    "".join(router.stream(query())[0])

    assert consulted == last_version(traces) == axis_rules.chat_prompt_version(AxisMode.COACH, "course")


# --- R13b: the interaction log ---


def test_interaction_log_events_carry_prompt_version(tmp_path, repo, catalog, traces, answers):
    pass_cold_checks(repo)
    client = make_client(repo, catalog, make_router(tmp_path))

    post_consult(client)
    post_stream(client)
    assert post_explain(client).status_code == 200
    assert post_draft(client).status_code == 200
    assert post_check(client).status_code == 200

    logged = {kind: [e.payload.get("prompt_version") for e in events_of(repo, kind)] for kind in USER_EVENTS}
    assert [len(logged[k]) for k in USER_EVENTS] == [2, 1, 1, 1]
    for kind, versions in logged.items():
        assert all(is_version(v) for v in versions), (kind, versions)
    # The row and the span of the same call agree.
    assert sorted(v for versions in logged.values() for v in versions) == sorted(span_versions(traces))
    assert sorted(logged["axis"]) == sorted(
        axis_rules.chat_prompt_version(m, "course") for m in (AxisMode.COACH, AxisMode.SOCRATIC)
    )


def test_the_version_of_a_grounded_and_a_no_source_turn_differ_in_the_log(tmp_path, repo, catalog):
    nothing = FakeRetriever(status=RetrievalStatus.NOT_FOUND)

    post_consult(make_client(repo, catalog, make_router(tmp_path, found=nothing)))

    (event,) = events_of(repo, "axis")
    assert event.payload.get("prompt_version") == axis_rules.chat_prompt_version(AxisMode.COACH, "not_found")


# --- R13c: results.json ---


def test_results_json_carries_prompt_versions(tmp_path):
    assert ob.run(tmp_path) == 0

    results = ob.read_results(ob.the_run_dir(tmp_path))

    assert results["prompt_versions"] == {
        f"{mode.value}/{state}": axis_rules.chat_prompt_version(mode, state)
        for mode in MODES for state in ("not_found", "no_index", "unavailable")
    }
    assert "You are AXIS" not in json.dumps(results)


def test_results_json_lists_only_the_modes_and_states_that_ran(tmp_path):
    assert ob.run(tmp_path, modes=("Coach",), states=("no_index",)) == 0

    results = ob.read_results(ob.the_run_dir(tmp_path))

    assert results["prompt_versions"] == {"Coach/no_index": axis_rules.chat_prompt_version(AxisMode.COACH, "no_index")}


# --- R14: a version only when a prompt was actually sent to a model ---


def assert_no_version(repo, folder, *kinds):
    for kind in kinds:
        events = events_of(repo, kind)
        assert events, f"no {kind} row was written"
        assert "prompt_version" not in events[0].payload, (kind, events[0].payload.get("prompt_version"))
    assert all(v is None for v in span_versions(folder))


def test_mock_records_no_version(tmp_path, repo, catalog, traces, answers):
    pass_cold_checks(repo)
    router = make_router(tmp_path, mock=True)
    client = make_client(repo, catalog, router)

    post_consult(client)
    post_stream(client)
    post_explain(client)
    post_draft(client)
    post_check(client)

    assert router.transport.sent == []
    assert len(model_calls(traces)) == 5
    assert_no_version(repo, traces, *USER_EVENTS)


@pytest.mark.parametrize("why", ["no_rubric", "ai_off", "cap_reached", "provider_refused"])
def test_unjudged_concept_check_records_no_version(tmp_path, repo, catalog, traces, monkeypatch, why):
    if why != "no_rubric":
        write_rubric(tmp_path / "answers", unit="py-0.4")
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    transport = Transport()
    options = {
        "no_rubric": {},
        "ai_off": {"active": "openai", "environ": {}},
        "cap_reached": {"active": "openai", "cap": 0.0},
        "provider_refused": {"active": "openai"},
    }[why]
    if why == "provider_refused":
        transport.status = 429

    res = post_explain(make_client(repo, catalog, make_router(tmp_path, transport=transport, **options)))

    assert res.json()["reason"] == why
    (event,) = events_of(repo, "concept_check")
    assert "prompt_version" not in event.payload
    if why != "provider_refused":  # nothing was sent, so no span may carry a version either
        assert transport.sent == []
        assert all(v is None for v in span_versions(traces))


@pytest.mark.parametrize("why", ["not_set_up", "budget"])
def test_a_draft_or_summary_that_failed_before_a_call_records_no_version(tmp_path, repo, catalog, traces, why):
    pass_cold_checks(repo)
    options = {"active": "openai", **({"environ": {}} if why == "not_set_up" else {"cap": 0.0})}
    router = make_router(tmp_path, **options)
    client = make_client(repo, catalog, router)

    assert post_draft(client).status_code == 502
    assert post_check(client).status_code == 200

    assert router.transport.sent == []
    assert_no_version(repo, traces, "document_draft", "build_feedback")


def test_a_chat_turn_refused_by_the_budget_records_no_version(tmp_path, repo, catalog, traces):
    router = make_router(tmp_path, active="openai", cap=0.0)

    post_consult(make_client(repo, catalog, router))

    assert router.transport.sent == []
    assert_no_version(repo, traces, "axis")


@pytest.mark.parametrize("path", ["/api/v1/axis/consult", "/api/v1/axis/stream"])
def test_a_mock_fallback_after_a_failed_call_records_no_version_not_even_a_stale_one(
    tmp_path, repo, catalog, traces, path
):
    transport = Transport()
    client = make_client(repo, catalog, make_router(tmp_path, transport=transport))
    assert client.post(path, json=consult_body()).status_code == 200
    transport.status = 500

    assert client.post(path, json=consult_body()).status_code == 200

    versions = [e.payload.get("prompt_version") for e in events_of(repo, "axis")]
    assert len(versions) == 2
    assert sum(v is None for v in versions) == 1 and sum(is_version(v) for v in versions) == 1, versions
    assert is_version(span_versions(traces)[0]) and span_versions(traces)[1] is None


def test_unjudged_failed_and_fallback_calls_record_no_version(tmp_path, repo, catalog, traces, monkeypatch):
    """The three cases of R14 after a successful call by the same router: none may reuse its version."""
    pass_cold_checks(repo)
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "no-answers-here"))
    transport = Transport()
    router = make_router(tmp_path, transport=transport)
    client = make_client(repo, catalog, router)
    router.consult(query())  # a real (mocked) call first, so there is a version that could be left over
    assert is_version(last_version(traces))

    post_explain(client)  # not judged: no rubric
    transport.status = 500
    post_consult(client)  # the real call fails, the mock answers

    for kind in ("concept_check", "axis"):
        (event,) = events_of(repo, kind)
        assert "prompt_version" not in event.payload
    assert span_versions(traces)[-1] is None


# --- review round 1: R14 and the SPEC-31 section 8 clarifications ---


def test_a_gemini_stream_that_fails_before_anything_arrives_records_no_version(tmp_path, traces, monkeypatch):
    """The SDK stream is lazy: nothing is sent until it is first read."""

    def refused(self, **kwargs):
        raise ConnectionError("synthetic: refused")
        yield  # makes this a generator, like the SDK's

    monkeypatch.setattr(FakeGeminiModels, "generate_content_stream", refused)
    router = make_router(tmp_path, active="gemini")

    with pytest.raises(Exception):
        "".join(router.stream(query())[0])

    assert model_calls(traces)
    assert all(v is None for v in span_versions(traces))


def test_a_check_that_was_sent_but_not_judged_logs_no_version(tmp_path, repo, catalog, traces, monkeypatch):
    write_rubric(tmp_path / "answers", unit="py-0.4")
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    transport = Transport()
    transport.text = "not the shape the judge asks for"

    res = post_explain(make_client(repo, catalog, make_router(tmp_path, transport=transport)))

    assert transport.sent and res.json()["status"] != "judged"
    (event,) = events_of(repo, "concept_check")
    assert "prompt_version" not in event.payload


def test_an_unusable_draft_or_summary_after_a_call_logs_no_version(tmp_path, repo, catalog, traces, answers):
    pass_cold_checks(repo)
    transport = Transport()
    transport.text = ""
    client = make_client(repo, catalog, make_router(tmp_path, transport=transport))

    assert post_draft(client).status_code == 502
    assert post_check(client).status_code == 200

    assert len(transport.sent) == 2
    for kind in ("document_draft", "build_feedback"):
        (event,) = events_of(repo, kind)
        assert "prompt_version" not in event.payload, kind


def test_a_replay_writes_no_prompt_versions(tmp_path):
    source = tmp_path / "in" / "replies.jsonl"
    source.parent.mkdir()
    source.write_text(json.dumps(ob.make_row("q1", "Coach", "not_found")) + "\n", encoding="utf-8")

    assert ob.run(tmp_path, replay=source, environ={"MOCK_AI": "true"}) == 0

    assert "prompt_versions" not in ob.read_results(ob.the_run_dir(tmp_path))


def test_a_run_where_every_call_failed_still_lists_what_ran(tmp_path):
    factory = ob.ScriptedFactory(lambda call: RuntimeError("down"))

    ob.run(tmp_path, factory, modes=("Coach",), states=("no_index",))

    assert ob.read_results(ob.the_run_dir(tmp_path))["prompt_versions"] == {
        "Coach/no_index": axis_rules.chat_prompt_version(AxisMode.COACH, "no_index")
    }
