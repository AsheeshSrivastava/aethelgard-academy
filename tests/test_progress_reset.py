"""Reset starts a unit's progress fresh; the ledger keeps everything (ADR-0016 amendment 2026-11-04)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.models import ProficiencyLevel, ProgressionDecision
from lms.core.proficiency_view import activities_attempted, build_proficiency_view, unit_decision
from lms.core.review import ReviewItem

from test_proficiency_view import NOW, make, statuses, supported_apply, unit

U = ProficiencyLevel.UNDERSTAND


# --- The decision rules ---


def test_a_reset_unit_counts_only_evidence_after_its_reset():
    entries = supported_apply()
    reset_at = NOW - timedelta(hours=1)

    assert unit_decision(unit(), entries, NOW) == ProgressionDecision.PROGRESS
    assert unit_decision(unit(), entries, NOW, resets={"PY-1.1": reset_at}) == ProgressionDecision.UNDECIDED


def test_evidence_after_the_reset_counts_again():
    entries = supported_apply() + [make(days_ago=0.02), make(days_ago=0.01, cold_check=True)]

    assert unit_decision(unit(), entries, NOW, resets={"PY-1.1": NOW - timedelta(hours=1)}) == ProgressionDecision.PROGRESS


def test_another_unit_sharing_the_skill_keeps_its_progress():
    entries = supported_apply("CO-1", "PY-1.1")
    other = unit("PY-1.2")

    assert unit_decision(other, entries, NOW, resets={"PY-1.1": NOW}) == ProgressionDecision.PROGRESS


def test_my_progress_shows_the_reset_unit_and_its_skill_fresh():
    entries = supported_apply()

    view = build_proficiency_view([unit()], entries, statuses(), now=NOW, resets={"PY-1.1": NOW})

    assert view.units[0].decision == ProgressionDecision.UNDECIDED
    assert view.skills[0].current_level is None and view.skills[0].entry_ids == []


def test_a_reset_unit_must_try_its_activities_again():
    entries = [make(activity=a) for a in unit().methods]

    assert activities_attempted(unit(), entries) is True
    assert activities_attempted(unit(), entries, since=NOW) is False


# --- Storage ---


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


def test_a_unit_reset_writes_a_marker_and_keeps_the_ledger(repo):
    repo.record_evidence(make(learner_id="L"))
    at = datetime(2026, 6, 1, 10, tzinfo=timezone.utc)

    repo.reset_unit("L", "PY-1.1", at=at)

    assert repo.progress_resets("L") == {"PY-1.1": at}
    assert len(repo.get_evidence_ledger("L")) == 1


def test_the_latest_marker_wins(repo):
    first, second = (datetime(2026, 6, d, tzinfo=timezone.utc) for d in (1, 2))

    repo.reset_unit("L", "PY-1.1", at=first)
    repo.reset_unit("L", "PY-1.1", at=second)

    assert repo.progress_resets("L") == {"PY-1.1": second}
    assert repo.progress_resets("someone else") == {}


def test_restarting_a_stage_review_clears_its_rounds_and_result(repo):
    at = datetime(2026, 6, 1, 10, tzinfo=timezone.utc)
    repo.save_review_items("L", "stage_review", "python/0", [ReviewItem(position=0, exercise_id="e", unit_id="PY-0.1", skill_id="CO-1")])
    repo.record_review_result("L", "stage_review", "python/0", True, at)
    repo.save_review_items("L", "stage_review", "python/1", [ReviewItem(position=0, exercise_id="f", unit_id="PY-1.2", skill_id="CO-1")])

    repo.reset_stage_review("L", "python/0", at=at)

    assert repo.get_review_items("L", "stage_review", "python/0") == []
    assert repo.get_review_result("L", "stage_review", "python/0") is None
    assert len(repo.get_review_items("L", "stage_review", "python/1")) == 1
    assert repo.progress_resets("L") == {"stage-review:python/0": at}


# --- The API ---


@pytest.fixture
def client(repo):
    clock = lambda: datetime(2026, 6, 1, 9, tzinfo=timezone.utc)  # noqa: E731
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=load_all_roadmaps(Path("reference")), clock=clock)
    return TestClient(app)


def test_reset_route_starts_the_unit_fresh_on_my_progress(client, repo):
    for entry in supported_apply("CO-1", "PY-0.1") + supported_apply("CO-2", "PY-0.1") + supported_apply("CO-6", "PY-0.1"):
        repo.record_evidence(entry.model_copy(update={"learner_id": LOCAL_LEARNER_ID}))

    def decision():
        units = client.get("/api/v1/learners/me/proficiency?course_id=python&stage=0").json()["units"]
        return next(u["decision"] for u in units if u["unit_id"] == "PY-0.1")

    before = decision()
    assert client.post("/api/v1/learners/me/units/PY-0.1/reset").status_code == 204

    assert before != "Undecided" and decision() == "Undecided"
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 6


def test_restart_stage_review_route(client, repo):
    at = datetime(2026, 5, 1, tzinfo=timezone.utc)
    repo.record_review_result(LOCAL_LEARNER_ID, "stage_review", "python/0", True, at)

    res = client.post("/api/v1/learners/me/courses/python/stages/0/review:reset")

    assert res.status_code == 204
    assert repo.get_review_result(LOCAL_LEARNER_ID, "stage_review", "python/0") is None
    assert "stage-review:python/0" in repo.progress_resets(LOCAL_LEARNER_ID)


def test_restart_unknown_stage_is_not_found(client):
    assert client.post("/api/v1/learners/me/courses/python/stages/99/review:reset").status_code == 404
