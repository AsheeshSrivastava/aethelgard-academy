"""What AXIS says with no course source, and the "course reference" status (SPEC-24).

Implements: SPEC-24 sections 2, 4 and 5; ADR-0034 section 2.3 as amended 2026-11-18.
Test numbers in the comments are SPEC-24 section 5.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import retrieval_quality as rq
from fake_retriever import FakeRetriever, passage
from lms.adapters.ai import passage_safety as ps
from lms.adapters.ai.axis_stream import stream_axis
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.ai.providers.router import ProviderRouter
from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.adapters.db.model_usage import UsageStore
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import create_app
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType
from lms.core.retrieval import RetrievalStatus

GUARD = SocraticGuardrail()
MODES = [AxisMode.COACH, AxisMode.HYBRID, AxisMode.SOCRATIC]
STATES = ["not_found", "no_index", "unavailable"]
STATE_SENTENCE = {
    "not_found": "This is not in the course yet.",
    "no_index": "The course reference is not loaded, so I could not check this against the course.",
    "unavailable": "The course search is not working right now, so I could not check this against the course.",
}


def query(mode=AxisMode.COACH):
    return AxisQuery(unit_id="PY-0.1", mode=mode, current_activity=ActivityType.PREDICT, user_prompt="Why?")


# --- 1. The notice, per state and mode (R1 to R4) ---------------------------------------------


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("mode", MODES)
def test_every_no_source_notice_carries_the_state_sentence_and_the_rules(mode, state):
    notice = axis_rules.no_source_notice(mode, state)
    assert STATE_SENTENCE[state] in notice
    lowered = notice.lower()
    assert "do not pretend a course source was used" in lowered
    assert "[1]" in notice  # it names the label form it forbids
    assert "do not write source labels" in lowered
    assert "do not name a document" in lowered


# --- 2. One memory rule for all modes (R4) ----------------------------------------------------


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("mode", MODES)
def test_no_mode_may_answer_from_memory_or_use_the_old_label(mode, state):
    notice = axis_rules.no_source_notice(mode, state)
    assert "Not from the course" not in notice
    lowered = notice.lower()
    assert "own memory" in lowered
    assert "ask" in lowered and "question" in lowered  # guiding questions are the way forward
    # The rule beats the mode stance, so Coach's "explain error messages" cannot win.
    assert "overrides any mode instruction" in lowered


def test_coach_no_longer_gets_a_general_knowledge_path():
    prompt = axis_rules.build_system_prompt(AxisMode.COACH, "", "not_found")
    assert "Not from the course" not in prompt
    assert "You may still explain syntax" not in prompt


# --- 3. Socratic invariant stays (ADR-0009) ---------------------------------------------------


@pytest.mark.parametrize("state", STATES)
def test_socratic_prompt_keeps_the_no_code_invariant_with_no_source(state):
    prompt = axis_rules.build_system_prompt(AxisMode.SOCRATIC, "", state)
    assert "STRICT INVARIANT" in prompt
    assert "Python code blocks" in prompt


# --- 4. Grounded prompt: answer only from passages, no notice (R4a, R5) -----------------------


@pytest.mark.parametrize("mode", MODES)
def test_a_grounded_prompt_says_answer_only_from_the_passages(mode):
    prompt = axis_rules.build_system_prompt(mode, "<reference_passages>x</reference_passages>")
    assert "only from the numbered passages" in prompt
    assert "not in the course yet" in prompt.lower()
    for sentence in STATE_SENTENCE.values():
        assert sentence not in prompt
    assert "do not pretend a course source was used" not in prompt.lower()


def test_a_concept_store_rescue_counts_as_grounded():
    g = ps.build_grounding([("concepts/a", "A concept", "alpha beta gamma delta")], trace=None)
    assert g.source_state == "course"


# --- 5. Retrieval status becomes the prompt notice and the source state (R1, R9) --------------


@pytest.mark.parametrize(
    "status, expected",
    [
        (RetrievalStatus.NOT_FOUND, "not_found"),
        (RetrievalStatus.NO_INDEX, "no_index"),
        (RetrievalStatus.UNAVAILABLE, "unavailable"),
    ],
)
def test_the_retrieval_status_becomes_the_source_state(status, expected):
    grounding, trace = axis_rules.ground_with_trace(FakeRetriever(status=status), None, "PY-0.1", "why does it fail")
    assert grounding.source_state == expected
    assert trace is not None and trace.status == status.value


def test_passages_found_give_course_state_and_no_notice():
    retriever = FakeRetriever(passages=(passage("python-docs/a.md", "alpha beta gamma delta"),))
    grounding, _ = axis_rules.ground_with_trace(retriever, None, "PY-0.1", "alpha")
    assert grounding.source_state == "course"
    prompt = axis_rules.build_system_prompt(AxisMode.COACH, grounding.block, grounding.source_state)
    assert "NO COURSE SOURCE" not in prompt


def test_no_retriever_at_all_counts_as_no_index():
    grounding, trace = axis_rules.ground_with_trace(None, None, "PY-0.1", "anything")
    assert trace is None
    assert grounding.source_state == "no_index"


@pytest.mark.parametrize("state", STATES)
def test_the_system_prompt_uses_the_matching_notice(state):
    prompt = axis_rules.build_system_prompt(AxisMode.HYBRID, "", state)
    assert STATE_SENTENCE[state] in prompt
    for other, sentence in STATE_SENTENCE.items():
        if other != state:
            assert sentence not in prompt


# --- 6. Invented labels under no source are removed (R7) --------------------------------------


def test_an_invented_label_is_removed_when_no_passage_was_given():
    g = ps.build_grounding([])
    reply = axis_rules.finish_reply("Try it again [1] and look [2].", query(), g, GUARD, AssistanceClassifier())
    assert "[1]" not in reply.reply and "[2]" not in reply.reply


# --- 7. source_state on consult and on the stream done event (R9) -----------------------------


class FakeAxis:
    def __init__(self, deltas, grounding):
        self._deltas, self._grounding = deltas, grounding

    def stream(self, _query):
        return iter(self._deltas), self._grounding


@pytest.mark.parametrize("state", STATES + ["course"])
def test_consult_and_stream_report_the_same_source_state(state):
    if state == "course":
        g = ps.build_grounding([("a#1", "A", "alpha beta gamma delta epsilon")])
    else:
        g = _grounding_with_state(state)
    consult = axis_rules.finish_reply("What does it hold?", query(), g, GUARD, AssistanceClassifier())
    events = list(stream_axis(FakeAxis(["What does it hold?"], g), query(), GUARD, AssistanceClassifier()))
    done = [d for e, d in events if e == "done"][0]
    assert consult.source_state == state == done["source_state"]


def _grounding_with_state(state):
    retriever = FakeRetriever(status=RetrievalStatus(state))
    grounding, _ = axis_rules.ground_with_trace(retriever, None, "PY-0.1", "why")
    return grounding


def test_a_plain_citation_list_from_the_mock_has_no_source_state():
    events = list(stream_axis(FakeAxis(["Hello."], ["Some Concept"]), query(), GUARD, AssistanceClassifier()))
    done = [d for e, d in events if e == "done"][0]
    assert "source_state" not in done
    consult_like = MockAxisCompanion().consult(query())
    assert consult_like.source_state is None


# --- 8. index_status on the port (R8) ---------------------------------------------------------


def test_the_keyword_adapter_reports_its_index_status(tmp_path):
    assert KeywordRetriever.from_index_dir(tmp_path / "missing").index_status() is RetrievalStatus.NO_INDEX
    loaded = KeywordRetriever.from_hybrid(rq.build_keyword_retriever(), min_matched_terms=2)
    assert loaded.index_status() is RetrievalStatus.OK


def test_the_fake_retriever_reports_the_status_it_was_given():
    assert FakeRetriever().index_status() is RetrievalStatus.OK
    assert FakeRetriever(status=RetrievalStatus.NO_INDEX).index_status() is RetrievalStatus.NO_INDEX
    assert FakeRetriever(status=RetrievalStatus.UNAVAILABLE).index_status() is RetrievalStatus.UNAVAILABLE
    # A search-time "nothing found" is not an index problem.
    assert FakeRetriever(status=RetrievalStatus.NOT_FOUND).index_status() is RetrievalStatus.OK


# --- 9. The status endpoint (R10) -------------------------------------------------------------

PROFILES = parse_profiles(
    {
        "profiles": [
            {"id": "local", "label": "Local", "kind": "openai_compatible",
             "base_url": "http://127.0.0.1:8888/v1", "model": "auto", "paid": False},
        ]
    }
)


class BrokenIndexRetriever(FakeRetriever):
    def index_status(self):
        raise RuntimeError("secret-path C:\\private\\index exploded")


def _client(tmp_path, retriever, mock=False):
    store = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc), session_id="r")
    store.initialize()
    router = ProviderRouter(PROFILES, store, environ={}, mock=mock, retriever=retriever)
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(repo=repo, runner=SubprocessRunner(), providers=router, clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc))
    return TestClient(app)


@pytest.mark.parametrize(
    "retriever, mock, expected",
    [
        (FakeRetriever(), False, "ready"),
        (FakeRetriever(status=RetrievalStatus.NO_INDEX), False, "not_loaded"),
        (FakeRetriever(status=RetrievalStatus.UNAVAILABLE), False, "unavailable"),
        (None, False, "not_loaded"),
        (FakeRetriever(), True, "mock"),
        (BrokenIndexRetriever(), False, "unavailable"),
    ],
)
def test_the_status_endpoint(tmp_path, retriever, mock, expected):
    res = _client(tmp_path, retriever, mock).get("/api/v1/axis/status")
    assert res.status_code == 200
    assert res.json() == {"course_reference": expected}
    text = res.text.lower()
    assert "secret" not in text and "index_version" not in text and "fake-index" not in text


def test_an_injected_companion_without_a_router_reports_mock(tmp_path):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion())
    assert TestClient(app).get("/api/v1/axis/status").json() == {"course_reference": "mock"}


# --- R4b. Concept Check and README prompts are untouched --------------------------------------


def test_the_judge_and_feedback_prompts_are_unchanged():
    """R4b: byte-for-byte what main had (hashes taken from main at 90c7f66)."""
    import hashlib

    system, _ = axis_rules.feedback_summary_prompts([], "", "")
    assert hashlib.sha256(axis_rules.JUDGE_SYSTEM_PROMPT.encode()).hexdigest() == (
        "10d5442a47f213dfdd8765e35aa169a06060e2d5a2b105e112256f2afd86797d"
    )
    assert hashlib.sha256(system.encode()).hexdigest() == (
        "a4056f22ceb12eb329571d512caa591172447955e9d83c664b90c0349c557c89"
    )


# --- Round 1 review additions ---------------------------------------------------------------


def test_a_stream_removes_an_invented_label_when_no_passage_was_given():
    g = ps.build_grounding([])
    reply = "Try it again [1] and look [2]."
    pieces = [reply[i:i + 4] for i in range(0, len(reply), 4)]
    events = list(stream_axis(FakeAxis(pieces, g), query(), GUARD, AssistanceClassifier()))
    text = "".join(d["text"] for e, d in events if e == "token")
    assert "[1]" not in text and "[2]" not in text


def test_a_concept_store_rescue_with_a_not_found_trace_is_course_state():
    from lms.adapters.ai.concept_store import ConceptStore
    from pathlib import Path

    store = ConceptStore()
    for f in sorted((Path(__file__).parent / "fixtures" / "concepts").glob("*.md")):
        store.ingest_file(f)
    retriever = FakeRetriever(status=RetrievalStatus.NOT_FOUND)
    grounding, trace = axis_rules.ground_with_trace(retriever, store, "PY-0.4", "communication cycle")
    assert trace is not None and trace.status == "not_found"
    assert grounding.ids and grounding.source_state == "course"
    prompt = axis_rules.build_system_prompt(AxisMode.COACH, grounding.block, grounding.source_state)
    assert "NO COURSE SOURCE IS AVAILABLE" not in prompt


class RaisingSearchRetriever(FakeRetriever):
    def search(self, *args, **kwargs):
        raise RuntimeError("boom C:\private\index")


def test_a_search_that_raises_gives_unavailable_not_a_crash():
    grounding, trace = axis_rules.ground_with_trace(RaisingSearchRetriever(), None, "PY-0.1", "why")
    assert grounding.source_state == "unavailable"
    assert trace is not None and trace.status == "unavailable"
    assert "private" not in str(trace.as_log_fields())


def test_a_directly_injected_real_companion_is_not_reported_as_mock():
    class RealLike:
        retriever = FakeRetriever(status=RetrievalStatus.NO_INDEX)

    from lms.adapters.ai.providers.router import course_reference_of

    assert course_reference_of(RealLike()) == "not_loaded"
    assert course_reference_of(MockAxisCompanion()) == "mock"
