"""Tests for attempts, evidence and the Cold Check flow (SPEC-12 sections 4.1 and 5)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from made_up import SHOUT, SOLID, right
from lms.core.models import ActivityType, AssistanceLevel, EvidenceCategory, EvidenceStrength

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)
BASE = "/api/v1/learners/me"


class FakeClock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now

    def advance(self, delta):
        self.now += delta


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def client(repo, catalog, clock):
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock
    )
    return TestClient(app)


def exercise(client, activity="predict", unit="PY-0.1"):
    res = client.get(f"{BASE}/units/{unit}/activities/{activity}/exercise")
    assert res.status_code == 200, res.text
    return res.json()


def attempt(client, activity="predict", unit="PY-0.1", **fields):
    current = exercise(client, activity, unit)
    return client.post(
        f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": activity, **fields}
    )


def ledger(repo):
    return repo.get_evidence_ledger(LOCAL_LEARNER_ID)


def assert_problem(res, status):
    assert res.status_code == status, res.text
    assert res.headers["content-type"].startswith("application/problem+json")


def status(client, unit="PY-0.1"):
    return client.get(f"{BASE}/units/{unit}/cold-check").json()["state"]


TRACE_1 = right("PY-0.1/trace-1")  # output lines and the state table


def finish_activities(client):
    """Attempt every activity of PY-0.1, including the concept check."""
    client.post("/api/v1/explain", json={"unit_id": "PY-0.1", "explanation": SOLID})
    assert attempt(client, choice="A").status_code == 200
    assert attempt(client, "trace", **TRACE_1).status_code == 200


# --- Grading and evidence ---


def test_correct_attempt_passes_and_records_evidence(client, repo):
    body = attempt(client, choice="A").json()

    assert body["outcome"] == "passed"
    assert body["reveal"]["correct"] == "A"
    assert body["unit_decision"]
    entry = ledger(repo)[0]
    assert entry.entry_id == body["evidence_entry_id"]
    assert entry.skill_id == "CO-1"
    assert entry.activity == ActivityType.PREDICT
    assert entry.evidence_category == EvidenceCategory.EXPLAIN_REASON
    assert entry.evidence_strength == EvidenceStrength.STRONG
    assert entry.assistance_level == AssistanceLevel.NONE
    assert entry.exercise_id == "PY-0.1/predict-1/v1"
    assert entry.seed_id == "PY-0.1/predict-1"
    assert entry.cold_check is False


def test_wrong_attempt_fails_and_records_weak(client, repo):
    body = attempt(client, choice="B").json()

    assert body["outcome"] == "failed"
    assert ledger(repo)[0].evidence_strength == EvidenceStrength.WEAK


def test_a_retry_after_a_fail_is_moderate(client, repo):
    attempt(client, choice="B")
    attempt(client, choice="A")

    assert [e.evidence_strength for e in ledger(repo)] == [EvidenceStrength.WEAK, EvidenceStrength.MODERATE]


def test_name_variants_share_a_seed_for_retry_counting(client, repo):
    attempt(client, choice="B")
    client.post(f"{BASE}/units/PY-0.1/activities/predict/exercises:regenerate")
    attempt(client, choice="A")

    assert ledger(repo)[1].exercise_id == "PY-0.1/predict-1/v2"
    assert ledger(repo)[1].evidence_strength == EvidenceStrength.MODERATE


def test_trace_table_is_graded_on_practice(client):
    wrong_cells = {**TRACE_1, "trace_states": [{"line": 1, "state": {"shown": "nope"}}, *TRACE_1["trace_states"][1:]]}

    body = attempt(client, "trace", **wrong_cells).json()

    assert body["outcome"] == "failed"
    assert body["score"] == {"passed": 2, "total": 3}


def test_trace_is_moderate_when_correct(client, repo):
    attempt(client, "trace", **TRACE_1)

    assert ledger(repo)[0].evidence_strength == EvidenceStrength.MODERATE


@pytest.mark.parametrize("field", ["evidence_strength", "evidence_category", "assistance_level", "strength"])
def test_client_sent_evidence_is_refused(client, repo, field):
    current = exercise(client)

    res = client.post(
        f"{BASE}/attempts",
        json={"exercise_id": current["exercise_id"], "activity": "predict", "choice": "A", field: "Strong"},
    )

    assert res.status_code == 422
    assert ledger(repo) == []


def test_attempt_must_be_on_the_current_exercise(client):
    exercise(client)

    res = client.post(
        f"{BASE}/attempts",
        json={"exercise_id": "PY-0.1/predict-2/v1", "activity": "predict", "choice": "A"},
    )

    assert_problem(res, 409)


def test_attempt_on_an_unknown_exercise_is_not_found(client):
    res = client.post(f"{BASE}/attempts", json={"exercise_id": "PY-0.1/nope/v1", "activity": "predict"})

    assert_problem(res, 404)


def test_attempt_activity_must_fit_the_unit(client):
    res = client.post(f"{BASE}/attempts", json={"exercise_id": "PY-0.1/predict-1/v1", "activity": "direct"})

    assert_problem(res, 422)


def test_explain_attempts_use_the_concept_check_route(client):
    res = client.post(f"{BASE}/attempts", json={"exercise_id": "PY-0.1/explain/v1", "activity": "explain"})

    assert_problem(res, 409)


# --- Assistance ---


def consult(client, exercise_id, prompt="Give me the code for this exercise."):
    return client.post(
        "/api/v1/axis/consult",
        json={
            "unit_id": "PY-0.1",
            "mode": "Hybrid",
            "current_activity": "Predict",
            "user_prompt": prompt,
            "exercise_id": exercise_id,
        },
    )


def test_assistance_logged_by_axis_reaches_the_entry(client, repo, clock):
    current = exercise(client)
    repo.log_assistance(LOCAL_LEARNER_ID, current["exercise_id"], AssistanceLevel.SMALL_HINT, clock())

    attempt(client, choice="A")

    assert ledger(repo)[0].assistance_level == AssistanceLevel.SMALL_HINT


def test_highest_assistance_wins(client, repo, clock):
    current = exercise(client)
    for level in (AssistanceLevel.SMALL_HINT, AssistanceLevel.STRUCTURAL_DIRECTION, AssistanceLevel.SYNTAX_LOOKUP):
        repo.log_assistance(LOCAL_LEARNER_ID, current["exercise_id"], level, clock())

    attempt(client, choice="A")

    assert ledger(repo)[0].assistance_level == AssistanceLevel.STRUCTURAL_DIRECTION


def test_supplied_reasoning_forces_weak(client, repo, clock):
    current = exercise(client)
    repo.log_assistance(LOCAL_LEARNER_ID, current["exercise_id"], AssistanceLevel.SUPPLIED_REASONING, clock())

    attempt(client, choice="A")

    assert ledger(repo)[0].evidence_strength == EvidenceStrength.WEAK


def test_assistance_before_the_exercise_was_served_does_not_count(client, repo, clock):
    repo.log_assistance(LOCAL_LEARNER_ID, "PY-0.1/predict-1/v1", AssistanceLevel.SMALL_HINT, clock())
    clock.advance(timedelta(minutes=1))

    attempt(client, choice="A")

    assert ledger(repo)[0].assistance_level == AssistanceLevel.NONE


def test_consult_logs_assistance_against_the_exercise(client, repo, clock):
    current = exercise(client)

    assert consult(client, current["exercise_id"]).status_code == 200

    assert repo.get_assistance_levels(LOCAL_LEARNER_ID, current["exercise_id"], T0)


# --- Ungraded playground ---


SOLUTION = SHOUT  # passes the made-up practice check (tests/fixtures)


def test_ungraded_playground_writes_nothing(client, repo):
    body = attempt(client, "playground", "PY-0.4", files={"solution.py": SOLUTION}).json()

    assert body["outcome"] == "passed"
    assert body.get("evidence_entry_id") is None
    assert ledger(repo) == []


def test_ungraded_playground_reports_failure(client, repo):
    body = attempt(client, "playground", "PY-0.4", files={"solution.py": "print('no')"}).json()

    assert body["outcome"] == "failed"
    assert ledger(repo) == []


def test_verify_route_runs_checks_on_the_server(client, repo):
    res = client.post(f"{BASE}/units/PY-0.4/playground:verify", json={"code": SOLUTION})

    assert res.status_code == 200
    assert res.json()["success"] is True
    assert ledger(repo) == []


def test_verify_unknown_unit_is_not_found(client):
    assert_problem(client.post(f"{BASE}/units/PY-99.9/playground:verify", json={"code": ""}), 404)


# --- Completing a unit starts the clock ---


def test_clock_does_not_start_until_every_activity_is_attempted(client):
    attempt(client, choice="A")

    assert status(client) == "not_ready"


def test_clock_starts_when_the_last_activity_is_attempted(client):
    finish_activities(client)

    assert status(client) == "waiting"


def test_a_failed_attempt_still_completes_the_activity(client):
    client.post("/api/v1/explain", json={"unit_id": "PY-0.1", "explanation": "Because it is code."})
    attempt(client, choice="B")
    attempt(client, "trace", trace_answers=["no"])

    assert status(client) == "waiting"


def test_more_practice_does_not_restart_the_clock(client, clock):
    finish_activities(client)
    clock.advance(timedelta(hours=20))
    attempt(client, choice="A")
    clock.advance(timedelta(hours=4))

    assert status(client) == "available"


# --- Cold Check round ---


def open_cold_check(client, clock):
    finish_activities(client)
    clock.advance(DAY)


CO1 = right("PY-0.1/cold-predict-1")
CO2 = right("PY-0.1/cold-trace-1")
CO6 = right("PY-0.1/cold-explain-1")


def cold(client, **fields):
    return attempt(client, "cold_check", **fields)


def test_cold_check_attempt_is_refused_while_locked(client, repo):
    finish_activities(client)
    before = len(ledger(repo))

    res = client.post(
        f"{BASE}/attempts", json={"exercise_id": "PY-0.1/cold-predict-1/v1", "activity": "cold_check"}
    )

    assert_problem(res, 423)
    assert len(ledger(repo)) == before


def test_round_moves_through_one_item_per_skill(client, clock):
    open_cold_check(client, clock)

    served = []
    for answer in (CO1, CO2, CO6):
        served.append(exercise(client, "cold_check")["exercise_id"])
        assert cold(client, **answer).json()["outcome"] == "passed"

    assert served == ["PY-0.1/cold-predict-1/v1", "PY-0.1/cold-trace-1/v1", "PY-0.1/cold-explain-1/v1"]


def test_cold_check_stays_available_mid_round(client, clock):
    open_cold_check(client, clock)
    cold(client, **CO1)

    assert status(client) == "available"


def test_passing_every_item_passes_the_unit(client, repo, clock):
    open_cold_check(client, clock)
    for answer in (CO1, CO2, CO6):
        cold(client, **answer)

    assert status(client) == "passed"
    entries = [e for e in ledger(repo) if e.cold_check]
    assert {e.skill_id for e in entries} == {"CO-1", "CO-2", "CO-6"}
    assert {e.evidence_strength for e in entries} == {EvidenceStrength.STRONG}
    assert {e.assistance_level for e in entries} == {AssistanceLevel.NONE}


def test_each_item_has_one_try(client, clock):
    open_cold_check(client, clock)
    first = exercise(client, "cold_check")["exercise_id"]
    cold(client, **CO1)

    res = client.post(
        f"{BASE}/attempts", json={"exercise_id": first, "activity": "cold_check", "choice": "B"}
    )

    assert_problem(res, 409)


def test_a_failed_item_fails_the_round_and_waits_24_hours(client, repo, clock):
    open_cold_check(client, clock)
    assert cold(client, choice="A").json()["outcome"] == "failed"
    cold(client, **CO2)
    cold(client, **CO6)

    assert status(client) == "failed_waiting"
    assert_problem(client.get(f"{BASE}/units/PY-0.1/activities/cold_check/exercise"), 423)

    clock.advance(DAY)
    assert status(client) == "available"
    weak = [e for e in ledger(repo) if e.cold_check and e.evidence_strength == EvidenceStrength.WEAK]
    assert [e.skill_id for e in weak] == ["CO-1"]


def test_retry_covers_only_the_failed_skills(client, clock):
    open_cold_check(client, clock)
    cold(client, choice="A")
    cold(client, **CO2)
    cold(client, **CO6)
    clock.advance(DAY)

    # ADR-0032: the failed item is replaced by the next unseen item of its skill.
    assert exercise(client, "cold_check")["exercise_id"] == "PY-0.1/cold-predict-2/v1"
    cold(client, **right("PY-0.1/cold-predict-2"))

    assert status(client) == "passed"


def test_failed_cold_check_reveals_nothing(client, clock):
    open_cold_check(client, clock)

    assert "reveal" not in cold(client, choice="A").json()


def test_passed_cold_check_item_may_reveal(client, clock):
    open_cold_check(client, clock)

    assert cold(client, **CO1).json()["reveal"]["correct"] == CO1["choice"]


def test_a_passed_unit_refuses_more_attempts(client, clock):
    open_cold_check(client, clock)
    for answer in (CO1, CO2, CO6):
        cold(client, **answer)

    res = client.post(
        f"{BASE}/attempts", json={"exercise_id": "PY-0.1/cold-predict-1/v1", "activity": "cold_check"}
    )

    assert_problem(res, 409)


def test_cold_check_ignores_any_axis_assistance(client, repo, clock):
    open_cold_check(client, clock)
    current = exercise(client, "cold_check")
    repo.log_assistance(LOCAL_LEARNER_ID, current["exercise_id"], AssistanceLevel.SUPPLIED_REASONING, clock())

    cold(client, **CO1)

    assert [e for e in ledger(repo) if e.cold_check][0].evidence_strength == EvidenceStrength.STRONG


def test_full_unit_ends_supported_at_its_target(client, clock):
    open_cold_check(client, clock)
    for answer in (CO1, CO2, CO6):
        decision = cold(client, **answer).json()["unit_decision"]

    assert decision == "Progress"
    body = client.get(f"{BASE}/proficiency?course_id=python&stage=0").json()
    row = next(s for s in body["skills"] if s["skill_id"] == "CO-2")
    assert row["decision"] == "Progress"
    unit = next(u for u in body["units"] if u["unit_id"] == "PY-0.1")
    assert unit["decision"] == "Progress"


def test_reset_clears_the_cold_check_round(client, clock):
    open_cold_check(client, clock)
    cold(client, **CO1)

    client.post(f"{BASE}/units/PY-0.1/reset")
    finish_activities(client)
    clock.advance(DAY)

    # ADR-0032: an item passed before the reset comes last, so the unseen one is served first.
    assert exercise(client, "cold_check")["exercise_id"] == "PY-0.1/cold-predict-2/v1"


# --- Closing the learner_id holes and hidden fields ---


def test_explain_ignores_a_body_learner_id(client, repo):
    client.post(
        "/api/v1/explain",
        json={"unit_id": "PY-0.1", "explanation": "Because it is code.", "learner_id": "someone_else"},
    )

    assert repo.get_evidence_ledger("someone_else") == []
    assert len(ledger(repo)) == 1


def test_consult_ignores_a_body_learner_id(client, repo, clock):
    current = exercise(client)
    res = client.post(
        "/api/v1/axis/consult",
        json={
            "learner_id": "someone_else",
            "unit_id": "PY-0.1",
            "mode": "Socratic",
            "current_activity": "Predict",
            "user_prompt": "Why?",
            "exercise_id": current["exercise_id"],
        },
    )

    assert res.status_code == 200
    assert repo.get_assistance_levels("someone_else", current["exercise_id"], T0) == []


def test_the_companion_sees_the_resolved_learner(repo, catalog, clock):
    seen = []

    class Spy(MockAxisCompanion):
        def consult(self, query):
            seen.append(query.learner_id)
            return super().consult(query)

    app = create_app(repo=repo, runner=SubprocessRunner(), axis=Spy(), catalog=catalog, clock=clock)
    TestClient(app).post(
        "/api/v1/axis/consult",
        json={
            "learner_id": "someone_else",
            "unit_id": "PY-0.1",
            "mode": "Socratic",
            "current_activity": "Predict",
            "user_prompt": "Why?",
        },
    )

    assert seen == [LOCAL_LEARNER_ID]


def test_unit_route_sends_no_hidden_checks_or_rubric(client):
    body = client.get("/api/v1/units/PY-0.1").json()

    assert body["test_code"] is None
    assert "rubric" not in str(body)
    assert "solid_keywords" not in str(body)
    assert body["concept_check_config"]["prompt"]
