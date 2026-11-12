"""SPEC-18: AI judgement of written explanations (ADR-0026).

Offline: every model here is a fake; no SDK is called and no key is used.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.judging import classify_failure, judge_with
from lms.adapters.ai.providers.metering import BudgetExceeded
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.ai.providers.router import PaidNotConfirmed, ProviderRouter, UnknownProfile
from lms.adapters.curriculum.rubric import check_concept_checks, load_rubric
from lms.adapters.db.model_usage import UsageStore
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core import ai_judgement
from lms.core.ai_judgement import (
    NOT_JUDGED_MESSAGES,
    AiJudgement,
    Idea,
    IdeaResult,
    Rubric,
    RubricError,
    UnreadableReply,
    parse_rubric,
    validate_reply,
    verdict_for,
)
from lms.core.curriculum_checks import Severity
from lms.core.interaction_log import InteractionEvent, new_ulid

REPO_ROOT = Path(__file__).resolve().parents[1]
IDEAS = [
    Idea(id="returns-text", text="input() always gives back text (a string), whatever is typed."),
    Idea(id="math-needs-numbers", text="Arithmetic on that text fails until it is converted to a number."),
]
RUBRIC = Rubric(unit_id="PY-0.4", ideas=IDEAS)
GOOD = json.dumps(
    {"ideas": [{"id": "returns-text", "met": True}, {"id": "math-needs-numbers", "met": True}], "feedback": "Clear."}
)


def reply(ideas=(("returns-text", True), ("math-needs-numbers", True)), feedback="Nice work.", **extra):
    return json.dumps({"ideas": [{"id": i, "met": m} for i, m in ideas], "feedback": feedback, **extra})


def write_rubric(answers: Path, unit="py-0.4", ideas=None):
    folder = answers / "python" / unit
    folder.mkdir(parents=True, exist_ok=True)
    data = {"unit_id": unit.upper(), "ideas": [i.model_dump() for i in (ideas or IDEAS)]}
    (folder / "concept_check.json").write_text(json.dumps(data), encoding="utf-8")


# --- 1. Rubric loading ---


def test_the_private_rubric_is_joined_by_unit(tmp_path):
    write_rubric(tmp_path)

    rubric = load_rubric(tmp_path, "PY-0.4")

    assert rubric is not None and [i.id for i in rubric.ideas] == ["returns-text", "math-needs-numbers"]


def test_no_rubric_when_there_is_no_file_or_no_folder(tmp_path):
    assert load_rubric(tmp_path, "PY-0.4") is None
    assert load_rubric(None, "PY-0.4") is None


def test_a_unit_id_cannot_reach_outside_the_answers_folder(tmp_path):
    assert load_rubric(tmp_path, "../../etc") is None


@pytest.mark.parametrize(
    "ideas",
    [
        [{"id": "a", "text": "only one"}],
        [{"id": "a", "text": "x"}, {"id": "a", "text": "y"}],
        [{"id": "a", "text": "x"}, {"id": "b", "text": ""}],
        [{"id": str(n), "text": "t"} for n in range(4)],
    ],
)
def test_a_bad_rubric_is_refused(ideas):
    with pytest.raises(RubricError):
        parse_rubric({"ideas": ideas}, "PY-0.4")


def test_a_broken_rubric_file_counts_as_missing(tmp_path):
    folder = tmp_path / "python" / "py-0.4"
    folder.mkdir(parents=True)
    (folder / "concept_check.json").write_text("{not json", encoding="utf-8")

    assert load_rubric(tmp_path, "PY-0.4") is None


def write_meta(curriculum: Path, unit: str, concept_check):
    folder = curriculum / "python" / unit
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meta.json").write_text(json.dumps({"unit_id": unit.upper(), "concept_check": concept_check}), encoding="utf-8")


@pytest.mark.parametrize("field", ["rubric", "solid_keywords", "ideas"])
def test_a_public_rubric_is_an_error(tmp_path, field):
    write_meta(tmp_path / "c", "py-0.4", {"prompt": "Explain.", field: ["x"]})
    write_rubric(tmp_path / "a")

    findings = check_concept_checks(tmp_path / "c", tmp_path / "a")

    [found] = [f for f in findings if f.code == "concept-check-answers-public"]
    assert found.severity == Severity.ERROR and found.unit_id == "PY-0.4"


def test_a_prompt_without_a_private_rubric_is_a_warning(tmp_path):
    write_meta(tmp_path / "c", "py-0.4", {"prompt": "Explain."})
    (tmp_path / "a").mkdir()

    [found] = check_concept_checks(tmp_path / "c", tmp_path / "a")

    assert found.code == "concept-check-rubric-missing" and found.severity == Severity.WARNING


def test_a_clean_unit_has_no_findings(tmp_path):
    write_meta(tmp_path / "c", "py-0.4", {"prompt": "Explain."})
    write_rubric(tmp_path / "a")

    assert check_concept_checks(tmp_path / "c", tmp_path / "a") == []


# --- 10. Guard ---


def test_no_public_meta_json_holds_a_rubric():
    leaks = []
    for meta in sorted((REPO_ROOT / "curriculum").glob("*/*/meta.json")):
        check = json.loads(meta.read_text(encoding="utf-8")).get("concept_check") or {}
        leaks += [f"{meta.parent.name}: {field}" for field in ("rubric", "solid_keywords", "ideas") if field in check]
    assert leaks == []


# --- 2. Verdict rule ---


def results(*flags):
    return [IdeaResult(id=f"i{n}", text="t", met=flag) for n, flag in enumerate(flags)]


def test_solid_only_when_every_idea_is_met():
    assert verdict_for(results(True, True)) == "Solid"
    assert verdict_for(results(True, False)) == "Shaky"
    assert verdict_for(results(False, False, False)) == "Shaky"


def test_the_models_own_overall_verdict_is_ignored():
    good = reply(ideas=(("returns-text", True), ("math-needs-numbers", False)), status="Solid", verdict="Solid")

    judgement = judge_with(FakeCompanion(good), "PY-0.4", "Explain.", "an answer", RUBRIC)

    assert judgement.verdict == "Shaky"


# --- 3. Reply checks ---


class FakeCompanion:
    def __init__(self, raw=GOOD, model="fake-model-1", error=None):
        self.raw, self.model, self.error, self.calls = raw, model, error, 0

    def judge(self, unit_id, prompt, explanation, ideas):
        self.calls += 1
        if self.error:
            raise self.error
        return self.raw, self.model


def test_a_good_reply_is_judged_with_the_model_that_answered():
    judgement = judge_with(FakeCompanion(), "PY-0.4", "Explain.", "an answer", RUBRIC)

    assert judgement.status == "judged" and judgement.verdict == "Solid"
    assert judgement.model == "fake-model-1" and judgement.feedback == "Clear."
    assert [(i.id, i.met, i.text) for i in judgement.ideas][0] == ("returns-text", True, IDEAS[0].text)


@pytest.mark.parametrize(
    "bad",
    [
        "not json at all",
        "[]",
        json.dumps({"feedback": "ok"}),
        reply(ideas=(("returns-text", True),)),                                       # an id missing
        reply(ideas=(("returns-text", True), ("returns-text", True))),                # a repeat
        reply(ideas=(("returns-text", True), ("made-up", True))),                     # an unknown id
        reply(ideas=(("returns-text", True), ("math-needs-numbers", "yes"))),         # met not a boolean
        reply(feedback=""),
        reply(feedback="x" * 401),
        json.dumps({"ideas": [{"id": "returns-text", "met": True}, {"id": "math-needs-numbers", "met": True}]}),
    ],
)
def test_each_malformed_reply_is_unreadable(bad):
    with pytest.raises(UnreadableReply):
        validate_reply(bad, IDEAS)
    judgement = judge_with(FakeCompanion(bad), "PY-0.4", "Explain.", "an answer", RUBRIC)
    assert judgement.status == "not_judged" and judgement.reason == "unreadable_reply"


def test_a_fenced_reply_is_accepted():
    ok = judge_with(FakeCompanion("```json\n" + GOOD + "\n```"), "PY-0.4", "Explain.", "a", RUBRIC)

    assert ok.status == "judged"


# --- 4. Failure classes ---


class RateLimitError(Exception):
    pass


class HttpError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class ConnectionError_(Exception):
    pass


@pytest.mark.parametrize(
    "error, reason",
    [
        (BudgetExceeded("cap"), "cap_reached"),
        (HttpError(401), "provider_refused"),
        (HttpError(403), "provider_refused"),
        (HttpError(429), "provider_refused"),
        (RateLimitError("slow down"), "provider_refused"),
        (HttpError(500), "no_answer"),
        (HttpError(503), "no_answer"),
        (TimeoutError("slow"), "no_answer"),
        (ConnectionError_("refused"), "no_answer"),
    ],
)
def test_each_failure_class_maps_to_its_reason(error, reason):
    assert classify_failure(error) == reason
    judgement = judge_with(FakeCompanion(error=error), "PY-0.4", "Explain.", "an answer", RUBRIC)
    assert judgement.status == "not_judged" and judgement.reason == reason
    assert judgement.message == NOT_JUDGED_MESSAGES[reason]
    assert judgement.verdict is None and judgement.ideas == []


def test_there_is_no_keyword_grader_left():
    assert not hasattr(axis_rules, "keyword_concept_check")
    assert not hasattr(axis_rules, "parse_concept_check")


def test_the_provider_error_text_is_never_in_the_message():
    judgement = judge_with(FakeCompanion(error=HttpError(401)), "PY-0.4", "Explain.", "a", RUBRIC)

    assert "401" not in judgement.model_dump_json()


# --- 6. The mock judges deterministically ---


def test_the_mock_judges_by_whole_words_of_five_letters_or_more():
    mock = MockAxisCompanion()
    ideas = [Idea(id="a", text="A variable keeps the value."), Idea(id="b", text="Print shows a blank line.")]
    rubric = Rubric(unit_id="PY-0.1", ideas=ideas)

    full = mock.judge_explanation("PY-0.1", "Explain.", "The variable holds a value; print gives a line", rubric)
    part = mock.judge_explanation("PY-0.1", "Explain.", "the variables are neat", rubric)  # "variables" is not a whole word

    assert full.model == "offline-mock" and full.verdict == "Solid"
    assert part.verdict == "Shaky" and [i.met for i in part.ideas] == [False, False]
    assert mock.judge_explanation("PY-0.1", "Explain.", "The variable holds a value; print gives a line", rubric) == full


# --- App: evidence, logging, disputes ---


class Judge:
    """An axis that returns a prepared AiJudgement (or none), for the route tests."""

    def __init__(self, judgement):
        self.judgement, self.calls = judgement, []

    def judge_explanation(self, unit_id, prompt, explanation, rubric):
        self.calls.append((unit_id, explanation, rubric))
        return self.judgement

    def consult(self, query):  # pragma: no cover - not used
        raise AssertionError


def judged_solid():
    return AiJudgement(
        status="judged", verdict="Solid", model="fake-model-1", feedback="Clear.",
        ideas=[IdeaResult(id=i.id, text=i.text, met=True) for i in IDEAS],
    )


def judged_shaky():
    ideas = [IdeaResult(id=IDEAS[0].id, text=IDEAS[0].text, met=True), IdeaResult(id=IDEAS[1].id, text=IDEAS[1].text, met=False)]
    return AiJudgement(status="judged", verdict="Shaky", model="fake-model-1", feedback="Add the number step.", ideas=ideas)


@pytest.fixture
def answers(tmp_path, monkeypatch):
    write_rubric(tmp_path / "answers", unit="py-0.4")
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    return tmp_path / "answers"


@pytest.fixture
def repo():
    r = SQLiteLearnerRepository(db_path=":memory:")
    r.initialize()
    return r


def make_client(repo, axis):
    return TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=axis))


def explain(client, unit="PY-0.4", text="Because input gives text, convert it."):
    return client.post("/api/v1/explain", json={"unit_id": unit, "explanation": text})


def ledger(repo):
    return repo.get_evidence_ledger(LOCAL_LEARNER_ID)


def concept_events(repo):
    return [e for e in repo.get_interactions(LOCAL_LEARNER_ID) if e.event_type == "concept_check"]


def test_a_judged_verdict_writes_one_tagged_co6_entry(answers, repo):
    axis = Judge(judged_shaky())
    body = explain(make_client(repo, axis)).json()

    assert body["status"] == "judged" and body["verdict"] == "Shaky" and body["evidence_logged"] is True
    assert [i["met"] for i in body["ideas"]] == [True, False]
    [entry] = ledger(repo)
    assert entry.skill_id == "CO-6" and entry.evidence_strength.value == "Weak"
    assert "fake-model-1" in entry.demonstration_context
    assert IDEAS[0].id in entry.observed_reasoning and IDEAS[1].id in entry.observed_reasoning
    assert axis.calls[0][2].ideas == IDEAS  # the private rubric reached the judge


def test_a_solid_verdict_is_strong_evidence(answers, repo):
    explain(make_client(repo, Judge(judged_solid())))

    assert ledger(repo)[0].evidence_strength.value == "Strong"


def test_a_concept_check_entry_carries_its_exercise_id(answers, repo):
    """ADR-0016 amendment G: the id lets a repeated concept check count once."""
    explain(make_client(repo, Judge(judged_solid())))

    assert ledger(repo)[0].exercise_id == "PY-0.4/explain/v1"


def test_with_the_switch_off_a_verdict_writes_nothing(answers, repo, monkeypatch):
    monkeypatch.setattr(ai_judgement, "CONCEPT_CHECK_WRITES_EVIDENCE", False)

    body = explain(make_client(repo, Judge(judged_solid()))).json()

    assert body["verdict"] == "Solid" and body["evidence_logged"] is False
    assert ledger(repo) == []


@pytest.mark.parametrize("reason", ["cap_reached", "provider_refused", "no_answer", "unreadable_reply", "ai_off"])
def test_not_judged_writes_no_evidence_but_is_logged(answers, repo, reason):
    body = explain(make_client(repo, Judge(ai_judgement.not_judged(reason)))).json()

    assert body["status"] == "not_judged" and body["reason"] == reason and body["verdict"] is None
    assert body["evidence_logged"] is False and body["message"] == NOT_JUDGED_MESSAGES[reason]
    assert ledger(repo) == []
    [event] = concept_events(repo)
    assert event.payload["reason"] == reason and event.interaction_id == body["interaction_id"]


def test_no_rubric_is_not_judged_and_the_model_is_not_called(tmp_path, repo, monkeypatch):
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "empty"))
    axis = Judge(judged_solid())

    body = explain(make_client(repo, axis)).json()

    assert body["reason"] == "no_rubric" and axis.calls == [] and ledger(repo) == []


def test_an_axis_that_cannot_judge_is_ai_off(answers, repo):
    class Plain:
        def consult(self, query):  # pragma: no cover
            raise AssertionError

    body = explain(make_client(repo, Plain())).json()

    assert body["reason"] == "ai_off" and ledger(repo) == []


def test_the_offline_mock_judges_through_the_route(answers, repo):
    ok = explain(make_client(repo, MockAxisCompanion()), text="Input returns text so arithmetic needs a converted number").json()

    assert ok["model"] == "offline-mock" and ok["verdict"] == "Solid"


# --- 7. Disputes ---


def dispute(client, interaction_id):
    return client.post(f"/api/v1/learners/me/judgements/{interaction_id}:dispute")


def test_a_dispute_is_logged_and_changes_nothing(answers, repo):
    client = make_client(repo, Judge(judged_shaky()))
    body = explain(client).json()
    before = ledger(repo)

    res = dispute(client, body["interaction_id"])

    assert res.status_code == 204
    [event] = [e for e in repo.get_interactions(LOCAL_LEARNER_ID) if e.event_type == "judgement_disputed"]
    assert event.payload["interaction_id"] == body["interaction_id"]
    assert ledger(repo) == before
    assert concept_events(repo)[0].payload["status"] == "Shaky"


def test_an_unknown_interaction_cannot_be_disputed(answers, repo):
    assert dispute(make_client(repo, Judge(judged_shaky())), new_ulid(1_000)).status_code == 404


def test_another_learners_judgement_cannot_be_disputed(answers, repo):
    repo.append_interaction(
        InteractionEvent(
            interaction_id="01J9ZK3Y4D8Q2W6X0OTHER0001", learner_id="someone-else", recorded_at_ms=1,
            event_type="concept_check", payload={"status": "Shaky"},
        )
    )

    assert dispute(make_client(repo, Judge(judged_shaky())), "01J9ZK3Y4D8Q2W6X0OTHER0001").status_code == 404


# --- 8. The judging model ---


PROFILES = parse_profiles(
    {
        "profiles": [
            {"id": "local", "label": "Local", "kind": "openai_compatible",
             "base_url": "http://127.0.0.1:8888/v1", "model": "auto", "paid": False},
            {"id": "gemini", "label": "Gemini", "kind": "gemini", "model": "gemini-3.8-flash",
             "key_env": "GEMINI_API_KEY", "paid": True, "price_per_million": {"input": 0.75, "output": 3.75}},
        ]
    }
)


class ProfileJudge:
    def __init__(self, profile):
        self.profile = profile

    def judge(self, unit_id, prompt, explanation, ideas):
        return GOOD, f"{self.profile.id}-model"

    def consult(self, query):  # pragma: no cover
        raise AssertionError


@pytest.fixture
def store(tmp_path):
    s = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 8, tzinfo=timezone.utc), session_id="run-1")
    s.initialize()
    return s


def make_router(store, environ=None, mock=False):
    return ProviderRouter(
        PROFILES, store, environ={"GEMINI_API_KEY": "AIza-FAKE-0001"} if environ is None else environ,
        mock=mock, factory=lambda profile, key, meter: ProfileJudge(profile),
    )


def test_unset_the_judge_is_the_chat_profile(store):
    router = make_router(store)

    assert router.judge_profile().id == "local"
    assert router.judge_explanation("PY-0.4", "Explain.", "a", RUBRIC).model == "local-model"
    router.switch("gemini", confirm_paid=True)
    assert router.judge_explanation("PY-0.4", "Explain.", "a", RUBRIC).model == "gemini-model"


def test_set_the_judge_uses_that_profile_whatever_chat_uses(store):
    router = make_router(store)

    router.set_judge("gemini", confirm_paid=True)

    assert router.active_profile().id == "local"
    assert router.judge_explanation("PY-0.4", "Explain.", "a", RUBRIC).model == "gemini-model"


def test_a_paid_judge_needs_confirmation_and_a_key(store):
    router = make_router(store)
    with pytest.raises(PaidNotConfirmed):
        router.set_judge("gemini", confirm_paid=False)
    with pytest.raises(UnknownProfile):
        router.set_judge("nope", confirm_paid=True)
    from lms.adapters.ai.providers.router import KeyMissing

    with pytest.raises(KeyMissing):
        make_router(store, environ={}).set_judge("gemini", confirm_paid=True)
    assert router.judge_profile().id == "local"


def test_the_judge_choice_survives_a_restart_and_can_be_cleared(store):
    make_router(store).set_judge("gemini", confirm_paid=True)

    again = make_router(store)
    assert again.judge_profile().id == "gemini"
    again.set_judge(None, confirm_paid=False)
    assert make_router(store).judge_profile().id == "local"


def test_no_key_for_the_judging_profile_is_ai_off(store):
    router = make_router(store, environ={})
    router.store.set_judge("gemini")
    router = make_router(store, environ={})

    judgement = router.judge_explanation("PY-0.4", "Explain.", "a", RUBRIC)

    assert judgement.reason == "ai_off"


def test_the_mock_router_judges_offline(store):
    judgement = make_router(store, mock=True).judge_explanation("PY-0.4", "Explain.", "text converted number", RUBRIC)

    assert judgement.model == "offline-mock"


def test_settings_api_carries_the_judging_model(store):
    router = make_router(store)
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), providers=router))

    assert client.get("/api/v1/settings/models").json()["judge_profile_id"] is None
    assert client.put("/api/v1/settings/models/judge", json={"profile_id": "gemini", "confirm_paid": False}).status_code == 409
    assert client.put("/api/v1/settings/models/judge", json={"profile_id": "nope", "confirm_paid": True}).status_code == 404
    ok = client.put("/api/v1/settings/models/judge", json={"profile_id": "gemini", "confirm_paid": True})
    assert ok.status_code == 200 and ok.json()["judge_profile_id"] == "gemini"
    cleared = client.put("/api/v1/settings/models/judge", json={"profile_id": None, "confirm_paid": False})
    assert cleared.json()["judge_profile_id"] is None
