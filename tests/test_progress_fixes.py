"""Tests for the five My progress fixes of 2026-11-04 (SPEC-12 sections 4, 5 and 6)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.exercises import pool_for
from lms.core.models import EvidenceCategory, EvidenceEntry, EvidenceStrength, AssistanceLevel, ProficiencyLevel
from lms.core.proficiency import decide_skill

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
BASE = "/api/v1/learners/me"
UNIT = "PY-0.4"


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def client(repo, catalog, clock):
    return TestClient(
        create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock, test_mode=False)
    )


def exercise(client, activity="predict"):
    res = client.get(f"{BASE}/units/{UNIT}/activities/{activity}/exercise")
    assert res.status_code == 200, res.text
    return res.json()


def attempt(client, current, activity="predict", **extra):
    body = {"exercise_id": current["exercise_id"], "activity": activity, "choice": "A", **extra}
    return client.post(f"{BASE}/attempts", json=body)


# --- 1. An attempted item is not served again by default ---


def test_the_current_item_stays_until_it_is_attempted(client):
    assert exercise(client)["exercise_id"] == exercise(client)["exercise_id"]


def test_after_an_attempt_the_next_fetch_serves_another_item(client):
    first = exercise(client)
    assert attempt(client, first).status_code == 200

    assert exercise(client)["exercise_id"] != first["exercise_id"]


def test_with_every_item_done_it_still_moves_on(client, catalog):
    pool = pool_for(catalog.seeds[UNIT], "predict")
    served = []
    for _ in range(len(pool) + 1):
        current = exercise(client)
        served.append(current["exercise_id"])
        attempt(client, current)

    assert all(a != b for a, b in zip(served, served[1:]))


# --- 2. A locked Cold Check retry never sends the learner back to a done item ---


def fail_cold_check(repo, at):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, UNIT, at - timedelta(days=2))
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, UNIT, False, at)


def next_action(client):
    return client.get(f"{BASE}/proficiency?course_id=python&stage=0").json()["next_action"]


def test_next_action_names_the_retry_time_and_an_unseen_item(client, repo, clock):
    fail_cold_check(repo, T0)
    clock.now = T0 + timedelta(hours=2)

    action = next_action(client)

    assert action["unit_id"] == UNIT
    assert action["retry_at"].startswith("2026-06-02T09:00")
    assert action["activity"] in {"predict", "debug-validate"}
    served = exercise(client, action["activity"])["exercise_id"]
    seen = repo.get_seen_exercises(LOCAL_LEARNER_ID, UNIT, action["activity"])
    assert seen == [served]


def test_with_no_unseen_item_the_next_action_is_the_cold_check_countdown(client, repo, clock, catalog):
    fail_cold_check(repo, T0)
    clock.now = T0 + timedelta(hours=2)
    for activity in ("predict", "debug-validate"):
        for exercise_id in pool_for(catalog.seeds[UNIT], activity):
            repo.set_current_exercise(LOCAL_LEARNER_ID, UNIT, activity, exercise_id, T0)

    action = next_action(client)

    assert action["activity"] == "cold_check"
    assert action["retry_at"] is not None


def test_no_retry_time_when_nothing_is_locked(client):
    assert next_action(client)["retry_at"] is None


# --- 3. A repeated submit is recorded once ---


def test_the_same_interaction_id_is_recorded_once(client, repo):
    current = exercise(client)

    first = attempt(client, current, interaction_id="01J9ZK3Y4D8Q2W6X0ABCDEFGH1")
    again = attempt(client, current, interaction_id="01J9ZK3Y4D8Q2W6X0ABCDEFGH1")

    assert first.status_code == again.status_code == 200
    assert again.json() == first.json()
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 1


def test_different_interaction_ids_are_different_attempts(client, repo):
    current = exercise(client)
    attempt(client, current, interaction_id="id-one-12345")
    attempt(client, current, interaction_id="id-two-12345")

    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 2


def test_a_repeat_while_the_first_is_being_graded_is_refused(client, repo):
    current = exercise(client)
    assert repo.claim_interaction(LOCAL_LEARNER_ID, "in-flight-1234", T0)

    res = attempt(client, current, interaction_id="in-flight-1234")

    assert res.status_code == 409
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_a_refused_attempt_releases_its_id(client, repo):
    current = exercise(client)
    wrong = attempt(client, {"exercise_id": "PY-0.4/predict-9/v1"}, interaction_id="retry-me-1234")
    assert wrong.status_code in (404, 409)

    assert attempt(client, current, interaction_id="retry-me-1234").status_code == 200


def test_ids_are_per_learner(repo):
    assert repo.claim_interaction("a", "shared-id-1234", T0)
    assert repo.claim_interaction("b", "shared-id-1234", T0)
    assert not repo.claim_interaction("a", "shared-id-1234", T0)


@pytest.mark.parametrize("bad", ["short", "has space in it", "x" * 65, "semi;colon-1234"])
def test_a_malformed_interaction_id_is_refused(client, bad):
    assert attempt(client, exercise(client), interaction_id=bad).status_code == 422


def test_without_an_id_attempts_work_as_before(client, repo):
    current = exercise(client)
    attempt(client, current)
    attempt(client, current)

    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 2


# --- 4. The reason names only what is missing ---


NOW = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
_n = 0


def entry(strength=EvidenceStrength.STRONG, cold_check=False, hours_ago=10.0):
    global _n
    _n += 1
    return EvidenceEntry(
        learner_id="l",
        unit_id="PY-0.4",
        skill_id="VE-4",
        evidence_category=EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER,
        evidence_strength=strength,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="t",
        recorded_at=NOW - timedelta(hours=hours_ago, seconds=-_n),
        exercise_id=f"ex-{_n}",
        seed_id=f"seed-{_n}",
        cold_check=cold_check,
    )


def reason(*entries):
    return decide_skill(ProficiencyLevel.UNDERSTAND, list(entries), "VE-4", now=NOW).reason


def test_one_exercise_and_no_cold_check_names_both():
    text = reason(entry())

    assert "1 more exercise" in text
    assert "a passed Cold Check" in text
    assert "weak" not in text


def test_two_exercises_without_a_cold_check_names_only_the_cold_check():
    text = reason(entry(hours_ago=20), entry(hours_ago=10))

    assert "a passed Cold Check" in text
    assert "exercise" not in text


def test_a_passed_cold_check_alone_names_only_the_exercise():
    text = reason(entry(cold_check=True))

    assert "1 more exercise" in text
    assert "Cold Check" not in text


def test_a_newer_weak_attempt_is_named():
    text = reason(entry(hours_ago=30), entry(cold_check=True, hours_ago=20), entry(EvidenceStrength.WEAK, hours_ago=1))

    assert "a strong attempt after your last weak one" in text
    assert "exercise" not in text
    assert "Cold Check" not in text
