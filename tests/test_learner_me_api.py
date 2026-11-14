"""Tests for the /learners/me proficiency and Cold Check routes (SPEC-12 sections 4.1 and 6)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog, load_roadmap_from_file
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    TargetSkill,
    Unit,
)

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)


class FakeClock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


def make_unit(unit_id: str, stage: int, skill_id: str = "CO-1") -> Unit:
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=stage,
        concept_line="Concept",
        target_skills=[
            TargetSkill(skill_id=skill_id, skill_name=skill_id, goal_level=ProficiencyLevel.APPLY)
        ],
        methods=[ActivityType.EXPLAIN, ActivityType.PREDICT],
    )


def make_entry(learner_id: str = LOCAL_LEARNER_ID, days_ago: int = 1, **overrides) -> EvidenceEntry:
    fields = dict(
        learner_id=learner_id,
        unit_id="PY-1.1",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="Task",
        recorded_at=T0 - timedelta(days=days_ago),
    )
    fields.update(overrides)
    return EvidenceEntry(**fields)


@pytest.fixture
def clock():
    return FakeClock(T0)


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def client(repo, clock):
    catalog = CurriculumCatalog()
    catalog.add_unit(make_unit("PY-1.1", 1, "CO-1"))
    catalog.add_unit(make_unit("PY-1.2", 1, "CO-2"))
    catalog.add_unit(make_unit("PY-2.1", 2, "CO-3"))
    catalog.add_unit(make_unit("BE-1.1", 1, "BU-1"))
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock
    )
    return TestClient(app)


def proficiency(client, query: Optional[str] = None):
    url = "/api/v1/learners/me/proficiency"
    res = client.get(f"{url}?{query}" if query else url)
    assert res.status_code == 200
    return res.json()


def assert_problem(res, status: int) -> None:
    assert res.status_code == status
    assert res.headers["content-type"].startswith("application/problem+json")
    body = res.json()
    assert body["status"] == status
    assert {"type", "title", "status", "detail"} <= set(body)


# --- Proficiency ---


def test_proficiency_matches_the_spec_shape(client):
    body = proficiency(client, "course_id=python&stage=1")

    assert set(body) == {"stage", "skills", "units", "next_action"}
    assert set(body["skills"][0]) == {
        "skill_id",
        "skill_name",
        "target_level",
        "current_level",
        "confidence",
        "supported_levels",
        "evidence_counts",
        "decision",
        "reason",
        "entry_ids",
    }
    assert set(body["skills"][0]["evidence_counts"]) == {"explain", "perform", "diagnose"}
    assert set(body["units"][0]) == {"unit_id", "decision"}
    assert set(body["next_action"]) == {"unit_id", "skill_id", "activity", "decision", "message", "retry_at"}


def supported(skill_id: str, unit_id: str):
    return [
        make_entry(skill_id=skill_id, unit_id=unit_id, days_ago=3),
        make_entry(skill_id=skill_id, unit_id=unit_id, days_ago=2, cold_check=True),
    ]


def test_stage_defaults_to_the_stage_of_the_first_unfinished_unit(client):
    body = proficiency(client, "course_id=python")

    assert body["stage"] == 1
    assert [u["unit_id"] for u in body["units"]] == ["PY-1.1", "PY-1.2"]


def test_default_stage_moves_on_when_a_stage_is_finished(client, repo):
    for entry in supported("CO-1", "PY-1.1") + supported("CO-2", "PY-1.2"):
        repo.record_evidence(entry)

    body = proficiency(client, "course_id=python")

    assert body["stage"] == 2
    assert [u["unit_id"] for u in body["units"]] == ["PY-2.1"]


def test_default_stage_stays_put_while_a_cold_check_is_waiting(client, repo):
    repo.record_evidence(make_entry())
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.1", T0)

    assert proficiency(client, "course_id=python")["stage"] == 1


def test_finished_course_opens_on_its_last_stage(client, repo):
    for entry in (
        supported("CO-1", "PY-1.1") + supported("CO-2", "PY-1.2") + supported("CO-3", "PY-2.1")
    ):
        repo.record_evidence(entry)

    body = proficiency(client, "course_id=python")

    assert body["stage"] == 2
    assert body["next_action"] is None


def test_default_stage_without_a_course_stays_inside_one_course(client):
    body = proficiency(client)

    assert body["stage"] == 1
    assert [u["unit_id"] for u in body["units"]] == ["PY-1.1", "PY-1.2"]


def test_default_stage_is_per_course(client, repo):
    for entry in supported("CO-1", "PY-1.1") + supported("CO-2", "PY-1.2"):
        repo.record_evidence(entry)

    assert proficiency(client, "course_id=backend")["stage"] == 1
    assert proficiency(client, "course_id=python")["stage"] == 2


def test_explicit_stage_wins_and_is_echoed(client, repo):
    for entry in supported("CO-1", "PY-1.1") + supported("CO-2", "PY-1.2"):
        repo.record_evidence(entry)

    assert proficiency(client, "course_id=python&stage=1")["stage"] == 1


def test_proficiency_filters_by_course(client):
    assert [u["unit_id"] for u in proficiency(client, "course_id=backend")["units"]] == ["BE-1.1"]


def test_proficiency_filters_by_stage(client):
    body = proficiency(client, "stage=2")

    assert [u["unit_id"] for u in body["units"]] == ["PY-2.1"]
    assert [s["skill_id"] for s in body["skills"]] == ["CO-3"]


def test_proficiency_filters_by_course_and_stage(client):
    body = proficiency(client, "course_id=python&stage=1")

    assert [u["unit_id"] for u in body["units"]] == ["PY-1.1", "PY-1.2"]


def test_known_course_without_units_is_an_empty_view(client):
    body = proficiency(client, "course_id=ai-engineering")

    assert body == {"stage": None, "skills": [], "units": [], "next_action": None}


def test_stage_without_units_is_an_empty_view(client):
    assert proficiency(client, "stage=99") == {
        "stage": 99,
        "skills": [],
        "units": [],
        "next_action": None,
    }


def test_unknown_course_is_a_problem_response(client):
    assert_problem(client.get("/api/v1/learners/me/proficiency?course_id=cooking"), 404)


def test_proficiency_uses_the_injected_clock_for_the_recency_window(client, repo, clock):
    repo.record_evidence(make_entry())
    assert proficiency(client, "stage=1")["skills"][0]["evidence_counts"]["perform"] == 1

    clock.advance(timedelta(days=100))

    assert proficiency(client, "stage=1")["skills"][0]["evidence_counts"]["perform"] == 0


def test_supported_evidence_gives_progress(client, repo):
    repo.record_evidence(make_entry(days_ago=3))
    repo.record_evidence(make_entry(days_ago=2, cold_check=True))

    body = proficiency(client, "course_id=python&stage=1")
    row = next(s for s in body["skills"] if s["skill_id"] == "CO-1")

    assert row["current_level"] == "Apply"
    assert row["confidence"] == "supported"
    assert row["decision"] == "Progress"
    assert len(row["entry_ids"]) == 2
    assert body["units"][0] == {"unit_id": "PY-1.1", "decision": "Progress"}
    assert body["next_action"]["unit_id"] == "PY-1.2"


def test_main_activity_evidence_reaches_the_target(repo, clock):
    catalog = CurriculumCatalog()
    catalog.add_unit(make_unit("PY-1.1", 1, "CO-1"))
    catalog.main_activities = {"CO-1": ActivityType.PREDICT}
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock
    )
    predict = dict(
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=EvidenceStrength.MODERATE,
        activity=ActivityType.PREDICT,
    )
    repo.record_evidence(make_entry(days_ago=3, **predict))
    repo.record_evidence(make_entry(days_ago=2, cold_check=True, **predict))

    body = proficiency(TestClient(app), "course_id=python&stage=1")

    assert body["skills"][0]["current_level"] == "Apply"
    assert body["units"][0]["decision"] == "Progress"
    assert body["next_action"] is None


def test_two_entries_without_a_cold_check_stay_provisional(client, repo):
    repo.record_evidence(make_entry(days_ago=3))
    repo.record_evidence(make_entry(days_ago=2))

    row = proficiency(client, "stage=1&course_id=python")["skills"][0]

    assert row["confidence"] == "provisional"
    assert row["decision"] == "Strengthen"


def test_shaky_explain_route_feeds_the_rebuild_decision(client, repo):
    payload = {"unit_id": "PY-1.2", "explanation": "Because it is code."}
    assert client.post("/api/v1/explain", json=payload).json()["verdict"] == "Shaky"
    assert client.post("/api/v1/explain", json=payload).json()["verdict"] == "Shaky"

    body = proficiency(client, "course_id=python&stage=1")

    assert {"unit_id": "PY-1.2", "decision": "Rebuild"} in body["units"]
    assert body["next_action"]["activity"] == "explain"


def test_available_cold_check_becomes_the_next_action(client, repo, clock):
    repo.record_evidence(make_entry())
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.1", T0)

    assert proficiency(client, "course_id=python&stage=1")["next_action"]["unit_id"] == "PY-1.2"

    clock.advance(DAY)
    action = proficiency(client, "course_id=python&stage=1")["next_action"]

    assert action["unit_id"] == "PY-1.1"
    assert action["activity"] == "cold_check"


def test_me_resolves_to_the_local_learner(client, repo):
    repo.record_evidence(make_entry())

    row = proficiency(client, "stage=1&course_id=python")["skills"][0]

    assert row["evidence_counts"]["perform"] == 1


def test_me_never_reads_another_learners_evidence(client, repo):
    repo.record_evidence(make_entry(learner_id="someone_else"))

    row = proficiency(client, "stage=1&course_id=python&learner_id=someone_else")["skills"][0]

    assert row["evidence_counts"]["perform"] == 0


def test_proficiency_is_read_only(client, repo):
    repo.record_evidence(make_entry())

    proficiency(client)

    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 1


def test_real_roadmap_view(repo, clock):
    catalog = load_roadmap_from_file(Path("reference/Python Subject Roadmap v4.md"))
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock
    )
    client = TestClient(app)

    body = proficiency(client, "course_id=python")
    assert body["stage"] == 0
    assert [u["unit_id"] for u in body["units"]] == ["PY-0.4", "PY-0.1", "PY-0.3"]
    assert body["next_action"]["activity"] == "explain"
    assert len(proficiency(client, "course_id=python&stage=6")["units"]) == 9


# --- Cold Check ---


def cold_check(client, unit_id: str = "PY-1.1"):
    res = client.get(f"/api/v1/learners/me/units/{unit_id}/cold-check")
    assert res.status_code == 200
    return res.json()


def test_cold_check_not_ready(client):
    assert cold_check(client) == {"state": "not_ready", "available_at": None, "last_attempt_at": None}


def test_cold_check_waits_24_hours_then_opens(client, repo, clock):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.1", T0)

    waiting = cold_check(client)
    assert waiting["state"] == "waiting"
    assert datetime.fromisoformat(waiting["available_at"].replace("Z", "+00:00")) == T0 + DAY

    clock.advance(DAY - timedelta(seconds=1))
    assert cold_check(client)["state"] == "waiting"

    clock.advance(timedelta(seconds=1))
    assert cold_check(client)["state"] == "available"


def test_cold_check_fail_then_retry_then_pass(client, repo, clock):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.1", T0)
    clock.advance(DAY)

    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-1.1", passed=False, attempted_at=clock())
    failed = cold_check(client)
    assert failed["state"] == "failed_waiting"
    assert datetime.fromisoformat(failed["available_at"].replace("Z", "+00:00")) == T0 + 2 * DAY

    clock.advance(DAY)
    assert cold_check(client)["state"] == "available"

    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-1.1", passed=True, attempted_at=clock())
    passed = cold_check(client)
    assert passed["state"] == "passed"
    assert passed["available_at"] is None


def test_cold_check_is_per_learner(client, repo):
    repo.mark_unit_activities_completed("someone_else", "PY-1.1", T0)

    assert cold_check(client)["state"] == "not_ready"


def test_cold_check_unknown_unit_is_a_problem_response(client):
    assert_problem(client.get("/api/v1/learners/me/units/PY-99.9/cold-check"), 404)


# --- Chaos: hostile input fails safely ---


def test_injection_in_course_id_is_rejected_and_harmless(client, repo):
    repo.record_evidence(make_entry())

    res = client.get(
        "/api/v1/learners/me/proficiency", params={"course_id": "python'; DROP TABLE evidence_ledger;--"}
    )

    assert_problem(res, 404)
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 1


def test_injection_in_unit_id_is_rejected_and_harmless(client, repo):
    repo.record_evidence(make_entry())

    res = client.get("/api/v1/learners/me/units/PY-1.1'%20OR%20'1'='1/cold-check")

    assert_problem(res, 404)
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 1


def test_non_numeric_stage_is_rejected(client):
    assert client.get("/api/v1/learners/me/proficiency?stage=abc").status_code == 422


# --- Ledger security (SPEC-12 criterion 6) ---


def test_my_ledger_is_newest_first(client, repo):
    older = make_entry(days_ago=3)
    newer = make_entry(days_ago=1)
    repo.record_evidence(older)
    repo.record_evidence(newer)

    body = client.get("/api/v1/learners/me/ledger").json()

    assert [e["entry_id"] for e in body] == [newer.entry_id, older.entry_id]


def test_my_ledger_filters_by_skill_and_unit(client, repo):
    repo.record_evidence(make_entry(skill_id="CO-1", unit_id="PY-1.1"))
    repo.record_evidence(make_entry(skill_id="CO-2", unit_id="PY-1.1"))
    repo.record_evidence(make_entry(skill_id="CO-1", unit_id="PY-1.2"))

    assert len(client.get("/api/v1/learners/me/ledger?skill_id=CO-1").json()) == 2
    assert len(client.get("/api/v1/learners/me/ledger?unit_id=PY-1.1").json()) == 2
    assert len(client.get("/api/v1/learners/me/ledger?skill_id=CO-1&unit_id=PY-1.2").json()) == 1


def test_my_ledger_never_returns_another_learners_entries(client, repo):
    repo.record_evidence(make_entry(learner_id="someone_else"))

    res = client.get("/api/v1/learners/me/ledger?learner_id=someone_else")

    assert res.status_code == 200
    assert res.json() == []


def test_old_ledger_route_answers_only_for_the_local_learner(client, repo):
    repo.record_evidence(make_entry())
    repo.record_evidence(make_entry(learner_id="someone_else"))

    assert len(client.get(f"/api/v1/learners/{LOCAL_LEARNER_ID}/ledger").json()) == 1
    assert_problem(client.get("/api/v1/learners/someone_else/ledger"), 404)


def test_old_progress_route_answers_only_for_the_local_learner(client, repo):
    payload = {"unit_id": "PY-1.1", "status": "Completed"}

    assert client.post(f"/api/v1/learners/{LOCAL_LEARNER_ID}/progress", json=payload).status_code == 200
    assert_problem(client.post("/api/v1/learners/someone_else/progress", json=payload), 404)
    assert repo.get_unit_progress("someone_else", "PY-1.1") is None


def test_me_is_not_treated_as_a_learner_id_on_the_old_routes(client):
    payload = {"unit_id": "PY-1.1", "status": "Completed"}

    assert_problem(client.post("/api/v1/learners/me/progress", json=payload), 404)
