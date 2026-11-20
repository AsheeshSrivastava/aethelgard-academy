"""SPEC-28 tests, part 2: one trace per interaction kind through the real routes, the interaction_id join,
the no-learner-text guard, passage refs, and "a failing tracer leaves the reply unchanged".

Written before the code. Offline: fake companions behind a real ProviderRouter; no model, no network.
The fake companion runs the real retrieval and citation helpers (axis_rules.ground_with_trace, Grounding.cited_for)
so the `retrieve` and `citation_check` spans come from the production code paths.
"""

import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fake_retriever import FakeRetriever, passage
from test_ai_judgement import GOOD, write_rubric
from test_model_settings_api import FAKE_OPENAI_KEY, PROFILES
from test_stage_build import ME, NOTE, REVIEW, T0, good_files, pass_cold_checks

from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.metering import BudgetExceeded
from lms.adapters.ai.providers.router import ProviderRouter
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.model_usage import UsageStore
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.interfaces import AxisResponse

TRACE_FILE = "axis-trace.jsonl"
# Distinctive learner strings: if any of these reaches a span, the guard test fails.
LEARNER = {
    "question": "zebra-quartz-question-7731",
    "code": "zebra_quartz_code_7731",
    "explanation": "zebra-quartz-explanation-7731",
    "readme": "zebra-quartz-readme-7731",
    "review": "zebra-quartz-review-7731",
    "ownership": "zebra-quartz-ownership-7731",
}
PASSAGE_TEXT = "the printed value comes from the input call and is always text"
CANNED_REPLY = f"Which line fails? {PASSAGE_TEXT}"
CITED_ID = "ab12cd34ef56ab12"


def tracing():
    import lms.core.tracing as t

    return t


def local_tracer(directory, **kw):
    from lms.adapters.observability.local_tracer import LocalTracer

    return LocalTracer(directory, **kw)


def read_spans(directory):
    spans = []
    for name in (TRACE_FILE + ".1", TRACE_FILE):
        path = Path(directory) / name
        if path.exists():
            spans += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return spans


def trace_text(directory):
    return "".join(
        (Path(directory) / name).read_text(encoding="utf-8")
        for name in (TRACE_FILE, TRACE_FILE + ".1") if (Path(directory) / name).exists()
    )


def traces_of_kind(directory, kind):
    return [s for s in read_spans(directory) if s["name"] == kind and s["parent_id"] is None]


def children(directory, root, name=None):
    return [s for s in read_spans(directory)
            if s["trace_id"] == root["trace_id"] and s["parent_id"] is not None and (name is None or s["name"] == name)]


class FakeCompanion:
    """Stands in for a real adapter: real retrieval and citation helpers, scripted model."""

    def __init__(self, profile, meter, retriever=None, fail=None):
        self.profile, self.meter, self.retriever, self.fail = profile, meter, retriever, fail
        self.last_model_answered = "fake-model-1"
        self.calls = []

    def _maybe_fail(self):
        if self.fail:
            raise self.fail

    def consult(self, query):
        self._maybe_fail()
        grounding, _ = axis_rules.ground_with_trace(self.retriever, None, query.unit_id, query.user_prompt)
        axis_rules.build_prompts(query, grounding)
        cited = grounding.cited_for(CANNED_REPLY)
        self.calls.append("consult")
        return AxisResponse(reply=CANNED_REPLY, cited_concepts=cited)

    def stream(self, query):
        self._maybe_fail()
        grounding, _ = axis_rules.ground_with_trace(self.retriever, None, query.unit_id, query.user_prompt)
        axis_rules.build_prompts(query, grounding)
        self.calls.append("stream")
        return iter(["Which line ", "fails?"]), grounding

    def judge(self, unit_id, prompt, explanation, ideas):
        self._maybe_fail()
        self.calls.append("judge")
        return GOOD, "fake-model-1"

    def draft_readme(self, entry, code, brief):
        self._maybe_fail()
        self.calls.append("draft_readme")
        return "# A draft\n\nNothing about the learner.\n", "fake-model-1"

    def summarise_feedback(self, points, readme, note, script="", run_output=""):
        self._maybe_fail()
        self.calls.append("summarise_feedback")
        return "A short summary of the measured points.", "fake-model-1"


def make_router(tmp_path, *, fail=None, retriever=None, mock=False):
    store = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc), session_id="r")
    store.initialize()
    built = []

    def factory(profile, key, meter):
        built.append(FakeCompanion(profile, meter, retriever or default_retriever(), fail))
        return built[-1]

    router = ProviderRouter(PROFILES, store, environ={"OPENAI_API_KEY": FAKE_OPENAI_KEY}, mock=mock, factory=factory)
    router.built = built
    return router


def default_retriever():
    return FakeRetriever((passage("how-to/tmp_path", PASSAGE_TEXT, score=2.5, pid=CITED_ID),), index_version="ab12cd34ef56")


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def repo():
    r = SQLiteLearnerRepository(db_path=":memory:")
    r.initialize()
    return r


@pytest.fixture
def traces(tmp_path):
    """A real LocalTracer set as the process tracer; its folder is returned."""
    t = tracing()
    folder = tmp_path / "traces"
    t.set_tracer(local_tracer(folder))
    yield folder
    t.set_tracer(t.NoopTracer())


@pytest.fixture
def answers(tmp_path, monkeypatch):
    write_rubric(tmp_path / "answers", unit="py-0.4")
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    return tmp_path / "answers"


def make_client(repo, catalog, axis):
    return TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=axis, catalog=catalog, clock=lambda: T0))


def consult_body(**extra):
    return {"unit_id": "PY-0.1", "mode": "Coach", "current_activity": "Predict", "user_prompt": LEARNER["question"],
            "learner_code": LEARNER["code"], "page": "predict", **extra}


def post_consult(client):
    res = client.post("/api/v1/axis/consult", json=consult_body())
    assert res.status_code == 200, res.text
    return res


def post_stream(client):
    body = {k: v for k, v in consult_body().items() if k != "learner_code"} | {"mode": "Socratic"}
    res = client.post("/api/v1/axis/stream", json=body)
    assert res.status_code == 200, res.text
    return res


def post_explain(client):
    return client.post("/api/v1/explain", json={"unit_id": "PY-0.4", "explanation": LEARNER["explanation"]})


def post_draft(client):
    return client.post(f"{ME}/build:draft-readme", json={"files": {"checkin.py": LEARNER["code"]}})


def post_check(client):
    files = {**good_files(), "README.md": good_files()["README.md"] + f"\n{LEARNER['readme']}\n"}
    return client.post(f"{ME}/build:feedback", json={
        "files": files, "ownership_note": f"{NOTE} {LEARNER['ownership']}",
        "review_note": f"{REVIEW} {LEARNER['review']}", "run_checks": False})


def events_of(repo, event_type):
    return [e for e in repo.get_interactions(LOCAL_LEARNER_ID) if e.event_type == event_type]


# --- 1. One trace per kind (R9 to R12) ---


def test_axis_consult_makes_exactly_one_axis_question_trace(tmp_path, repo, catalog, traces):
    post_consult(make_client(repo, catalog, make_router(tmp_path)))

    roots = traces_of_kind(traces, "axis_question")
    assert len(roots) == 1
    names = [c["name"] for c in children(traces, roots[0])]
    assert names.count("model_call") == 1
    for needed in ("retrieve", "prompt_build", "citation_check"):
        assert needed in names
    assert roots[0]["attributes"]["kind"] == "axis_question" and roots[0]["attributes"]["mode"] == "Coach"


def test_axis_stream_makes_one_trace_closed_at_done(tmp_path, repo, catalog, traces):
    post_stream(make_client(repo, catalog, make_router(tmp_path)))

    (root,) = traces_of_kind(traces, "axis_question")
    assert root["status"] == "ok" and root["duration_ms"] >= 0
    assert len(children(traces, root, "model_call")) == 1  # one span for the whole stream, not one per delta


def test_axis_stream_trace_closes_on_error(tmp_path, repo, catalog, traces):
    res = post_stream(make_client(repo, catalog, make_router(tmp_path, fail=RuntimeError("secret sk-1 http://x"))))

    (root,) = traces_of_kind(traces, "axis_question")
    assert "secret" not in res.text
    assert root["status"] == "error" and "secret sk-1" not in trace_text(traces)
    (call,) = children(traces, root, "model_call")
    assert call["status"] == "error" and call["attributes"]["reason"] == "provider_error"


@pytest.mark.parametrize("path, stream", [("/api/v1/axis/consult", False), ("/api/v1/axis/stream", True)])
def test_a_blocked_axis_request_is_a_root_with_no_children(tmp_path, repo, catalog, traces, path, stream):
    client = make_client(repo, catalog, make_router(tmp_path))
    request = consult_body(exercise_id="PY-0.1/cold-predict-1/v1")  # a Cold Check item: AXIS is off (403)

    res = client.post(path, json=request)

    assert res.status_code == 403
    (root,) = traces_of_kind(traces, "axis_question")
    assert root["attributes"]["blocked"] is True and root["attributes"]["stream"] is stream
    assert children(traces, root) == []


def test_concept_check_makes_one_trace_with_one_model_call(tmp_path, repo, catalog, traces, answers):
    res = post_explain(make_client(repo, catalog, make_router(tmp_path)))

    assert res.status_code == 200, res.text
    (root,) = traces_of_kind(traces, "concept_check")
    assert len(children(traces, root, "model_call")) == 1
    assert "retrieve" not in [c["name"] for c in children(traces, root)]


def test_concept_check_without_rubric_has_no_model_call(tmp_path, repo, catalog, traces, monkeypatch):
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "no-answers-here"))

    post_explain(make_client(repo, catalog, make_router(tmp_path)))

    (root,) = traces_of_kind(traces, "concept_check")
    assert children(traces, root, "model_call") == []
    assert root["attributes"]["not_judged_reason"] == "no_rubric"


def test_readme_draft_makes_one_trace(tmp_path, repo, catalog, traces):
    pass_cold_checks(repo)

    res = post_draft(make_client(repo, catalog, make_router(tmp_path)))

    assert res.status_code == 200, res.text
    (root,) = traces_of_kind(traces, "readme_draft")
    assert len(children(traces, root, "model_call")) == 1


def test_build_review_has_no_model_call_without_summary_path(repo, catalog, traces):
    class NoSummary:  # an axis with no summarise_feedback: the route never asks a model
        pass

    pass_cold_checks(repo)

    res = post_check(make_client(repo, catalog, NoSummary()))

    assert res.status_code == 200, res.text
    (root,) = traces_of_kind(traces, "build_review")
    assert children(traces, root, "model_call") == []
    assert {"check_requirements", "feedback_points"} <= {c["name"] for c in children(traces, root)}


def test_build_review_with_summary_has_one_model_call(tmp_path, repo, catalog, traces):
    pass_cold_checks(repo)

    post_check(make_client(repo, catalog, make_router(tmp_path)))

    (root,) = traces_of_kind(traces, "build_review")
    assert len(children(traces, root, "model_call")) == 1


@pytest.mark.parametrize(
    "error, reason",
    [(RuntimeError("secret sk-12345 leaked"), "provider_error"), (BudgetExceeded("cap"), "budget")],
)
def test_build_review_draft_failed_sets_reason_from_fixed_set(tmp_path, repo, catalog, traces, error, reason):
    pass_cold_checks(repo)

    res = post_check(make_client(repo, catalog, make_router(tmp_path, fail=error)))

    assert res.status_code == 200, res.text
    (root,) = traces_of_kind(traces, "build_review")
    (call,) = children(traces, root, "model_call")
    assert call["status"] == "error" and call["attributes"]["reason"] == reason
    assert "secret" not in trace_text(traces)


def test_mock_path_also_gets_one_model_call_with_mock_true(tmp_path, repo, catalog, traces):
    post_consult(make_client(repo, catalog, make_router(tmp_path, mock=True)))

    (root,) = traces_of_kind(traces, "axis_question")
    (call,) = children(traces, root, "model_call")
    assert call["attributes"]["mock"] is True


def test_budget_refusal_sets_error_reason_budget(tmp_path, repo, catalog, traces):
    post_consult(make_client(repo, catalog, make_router(tmp_path, fail=BudgetExceeded("cap"))))

    (root,) = traces_of_kind(traces, "axis_question")
    (call,) = children(traces, root, "model_call")
    assert call["status"] == "error" and call["attributes"]["reason"] == "budget"


def test_local_llm_mock_fallback_sets_fallback_attribute(traces):
    import httpx

    from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion
    from lms.core.interfaces import AxisMode, AxisQuery
    from lms.core.models import ActivityType

    def handler(request):
        return httpx.Response(500, json={"error": "down"})

    companion = OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:1/v1", model="m", fallback_to_mock=True,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    query = AxisQuery(unit_id="PY-0.1", mode=AxisMode.COACH, current_activity=ActivityType.PREDICT, user_prompt="Why?")

    with tracing().span("axis_question", interaction_id="01JCXYZABCDEFGHJKMNPQRSTVW"):
        companion.consult(query)

    assert any(s["attributes"].get("fallback") == "mock" for s in read_spans(traces))


def test_connection_test_makes_no_trace(tmp_path, traces):
    router = make_router(tmp_path)
    router.built.clear()

    try:
        router.test_connection()
    except Exception:
        pass

    assert read_spans(traces) == []


# --- 2. The interaction_id join (R9) ---


def test_trace_interaction_id_equals_logged_interaction_id_for_each_kind(tmp_path, repo, catalog, traces, answers):
    pass_cold_checks(repo)
    client = make_client(repo, catalog, make_router(tmp_path))

    post_consult(client)
    post_explain(client)
    post_draft(client)
    post_check(client)

    for kind, logged in (("axis_question", "axis"), ("concept_check", "concept_check"),
                         ("readme_draft", "document_draft"), ("build_review", "build_feedback")):
        (root,) = traces_of_kind(traces, kind)
        (event,) = events_of(repo, logged)
        assert root["attributes"]["interaction_id"] == event.interaction_id, kind


# --- 3. Passage refs (R16) ---


def test_retrieve_span_lists_passage_refs_from_the_turns_own_trace(tmp_path, repo, catalog, traces):
    post_consult(make_client(repo, catalog, make_router(tmp_path)))

    (root,) = traces_of_kind(traces, "axis_question")
    (retrieve,) = children(traces, root, "retrieve")
    attrs = retrieve["attributes"]
    assert attrs["passage_refs"] == [{"passage_id": CITED_ID, "source_id": "how-to/tmp_path", "score": 2.5}]
    assert attrs["index_version"] == "ab12cd34ef56" and attrs["retrieval_mode"] == "keyword_only"
    assert attrs["retrieval_status"] == "ok" and attrs["passages_retrieved"] == 1
    assert PASSAGE_TEXT not in trace_text(traces)  # ids and scores, never the text


def test_two_overlapping_requests_do_not_mix_retrieval_attributes(tmp_path, repo, catalog, traces):
    first = FakeRetriever((passage("how-to/first", PASSAGE_TEXT, 1.0, pid="aaaaaaaaaaaaaaaa"),), index_version="aaaaaaaaaaaa")
    second = FakeRetriever((passage("how-to/second", PASSAGE_TEXT, 2.0, pid="bbbbbbbbbbbbbbbb"),), index_version="bbbbbbbbbbbb")
    for n in ("a", "b"):
        (tmp_path / n).mkdir()
    clients = [make_client(repo, catalog, make_router(tmp_path / n, retriever=r))
               for n, r in (("a", first), ("b", second))]

    workers = [threading.Thread(target=post_consult, args=(c,)) for c in clients for _ in range(10)]
    [w.start() for w in workers]
    [w.join() for w in workers]

    for retrieve in (s for s in read_spans(traces) if s["name"] == "retrieve"):
        ref = retrieve["attributes"]["passage_refs"][0]
        assert (ref["source_id"], retrieve["attributes"]["index_version"]) in (
            ("how-to/first", "aaaaaaaaaaaa"), ("how-to/second", "bbbbbbbbbbbb"))


def test_citation_check_span_lists_cited_ids(tmp_path, repo, catalog, traces):
    post_consult(make_client(repo, catalog, make_router(tmp_path)))

    (root,) = traces_of_kind(traces, "axis_question")
    (check,) = children(traces, root, "citation_check")
    assert check["attributes"]["cited_passage_ids"] == [CITED_ID] and check["attributes"]["passages_cited"] == 1


# --- 4. test_mode (R17) ---


def test_test_mode_requests_are_recorded_with_flag(tmp_path, repo, catalog, traces):
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=make_router(tmp_path),
                                   catalog=catalog, clock=lambda: T0, test_mode=True))

    post_consult(client)

    (root,) = traces_of_kind(traces, "axis_question")
    assert root["attributes"]["test_mode"] is True


def test_a_normal_request_is_recorded_with_test_mode_false(tmp_path, repo, catalog, traces):
    post_consult(TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=make_router(tmp_path),
                                       catalog=catalog, clock=lambda: T0, test_mode=False)))

    (root,) = traces_of_kind(traces, "axis_question")
    assert root["attributes"]["test_mode"] is False


# --- 5. Guards (R14, R15, R20) ---


def run_every_route(tmp_path, repo, catalog):
    pass_cold_checks(repo)
    client = make_client(repo, catalog, make_router(tmp_path))
    return [post_consult(client), post_stream(client), post_explain(client), post_draft(client), post_check(client)]


def test_guard_no_span_carries_learner_text(tmp_path, repo, catalog, traces, answers):
    run_every_route(tmp_path, repo, catalog)

    written = trace_text(traces)
    assert written  # the guard must be looking at something
    for label, marker in LEARNER.items():
        assert marker not in written, f"learner {label} reached a span"
    assert "zebra-quartz" not in written
    assert PASSAGE_TEXT not in written and CANNED_REPLY not in written


def test_guard_every_recorded_key_is_allow_listed(tmp_path, repo, catalog, traces, answers):
    run_every_route(tmp_path, repo, catalog)

    allowed = tracing().ALLOWED_ATTRIBUTES
    spans = read_spans(traces)
    assert spans
    for span in spans:
        assert set(span["attributes"]) <= allowed, span["name"]
        assert span["attributes"].get("dropped_attributes", 0) == 0, f"{span['name']} passed a non-allow-listed key"


def test_guard_no_url_or_key_in_any_span(tmp_path, repo, catalog, traces, answers):
    run_every_route(tmp_path, repo, catalog)

    written = trace_text(traces)
    for forbidden in ("http://", "https://", FAKE_OPENAI_KEY, "sk-", "OPENAI_API_KEY", "127.0.0.1"):
        assert forbidden not in written, forbidden


# --- 6. A failing tracer leaves the reply unchanged (R18) ---


class ExplodingTracer:
    def span(self, name, **attributes):
        raise RuntimeError("tracer is broken")

    def event(self, name, **attributes):
        raise RuntimeError("tracer is broken")


def outputs(tmp_path, catalog, answers_dir, monkeypatch):
    """Every route's visible result and logged payload, with whatever tracer is currently set."""
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(answers_dir))
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    pass_cold_checks(repo)
    client = make_client(repo, catalog, make_router(tmp_path))
    got = {
        "consult": post_consult(client).json(),
        "stream": post_stream(client).text,
        "explain": post_explain(client).json(),
        "draft": post_draft(client).json(),
        "check": post_check(client).json(),
    }
    got["explain"].pop("interaction_id", None)  # a fresh id per run by design
    logged = sorted((e.event_type, json.dumps(e.payload, sort_keys=True)) for e in repo.get_interactions(LOCAL_LEARNER_ID))
    return got, logged


def test_replies_identical_with_noop_local_and_failing_tracer(tmp_path, catalog, monkeypatch):
    t = tracing()
    write_rubric(tmp_path / "answers", unit="py-0.4")
    results = {}
    try:
        for name, tracer in (("noop", t.NoopTracer()), ("local", local_tracer(tmp_path / "traces")),
                             ("exploding", ExplodingTracer())):
            t.set_tracer(tracer)
            run_dir = tmp_path / name
            run_dir.mkdir()
            results[name] = outputs(run_dir, catalog, tmp_path / "answers", monkeypatch)
    finally:
        t.set_tracer(t.NoopTracer())

    assert results["local"] == results["noop"]
    assert results["exploding"] == results["noop"]


def test_an_unwritable_trace_folder_changes_nothing_a_learner_sees(tmp_path, catalog, monkeypatch):
    t = tracing()
    write_rubric(tmp_path / "answers", unit="py-0.4")
    folder = tmp_path / "traces"
    broken = local_tracer(folder)
    shutil.rmtree(folder)
    folder.write_text("i am a file", encoding="utf-8")
    try:
        t.set_tracer(t.NoopTracer())
        (tmp_path / "ok").mkdir()
        expected = outputs(tmp_path / "ok", catalog, tmp_path / "answers", monkeypatch)
        t.set_tracer(broken)
        (tmp_path / "bad").mkdir()
        actual = outputs(tmp_path / "bad", catalog, tmp_path / "answers", monkeypatch)
    finally:
        t.set_tracer(t.NoopTracer())

    assert actual == expected

