"""Tests for test mode: every wait zero, flagged, and tagged in the ledger (ADR-0019 amendment 2026-11-04)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app, env_test_mode
from lms.core.cold_check import ColdCheckState, ColdCheckTimer, cold_check_status
from lms.core.models import AssistanceLevel, EvidenceCategory, EvidenceEntry, EvidenceStrength
from lms.core.review import STAGE_REVIEW, due_reviews
from lms.core.timing import REAL_TIMING, TEST_TIMING, timing_for

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
BASE = "/api/v1/learners/me"


# --- The settings ---


def test_real_waits_live_in_one_place():
    assert REAL_TIMING.cold_check_hours == 24
    assert REAL_TIMING.recheck_days == (7, 30)


def test_test_timing_is_all_zero():
    assert TEST_TIMING.cold_check_hours == 0
    assert TEST_TIMING.recheck_days == (0, 0)


def test_timing_for_picks_by_mode():
    assert timing_for(False) is REAL_TIMING
    assert timing_for(True) is TEST_TIMING


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
def test_env_turns_test_mode_on(monkeypatch, value):
    monkeypatch.setenv("LMS_TEST_MODE", value)

    assert env_test_mode() is True


@pytest.mark.parametrize("value", [None, "", "false", "0", "no", "off", "maybe"])
def test_test_mode_is_off_unless_clearly_on(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("LMS_TEST_MODE", raising=False)
    else:
        monkeypatch.setenv("LMS_TEST_MODE", value)

    assert env_test_mode() is False


# --- The rules with each timing ---


def timer(**fields):
    return ColdCheckTimer(learner_id="l", unit_id="u", completed_at=T0, **fields)


def test_real_timing_waits_a_day_for_the_cold_check():
    assert cold_check_status(timer(), T0 + timedelta(hours=23), timing_for(False).cold_check).state == ColdCheckState.WAITING


def test_test_timing_opens_the_cold_check_at_once():
    assert cold_check_status(timer(), T0, timing_for(True).cold_check).state == ColdCheckState.AVAILABLE


def test_test_timing_allows_a_retry_at_once():
    failed = timer(last_attempt_at=T0, last_attempt_passed=False)

    assert cold_check_status(failed, T0, TEST_TIMING.cold_check).state == ColdCheckState.AVAILABLE
    assert cold_check_status(failed, T0, REAL_TIMING.cold_check).state == ColdCheckState.FAILED_WAITING


def review_entry():
    return EvidenceEntry(
        learner_id="l",
        unit_id="PY-0.1",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="x",
        recorded_at=T0,
        cold_check=True,
        review_kind=STAGE_REVIEW,
    )


def test_rechecks_fall_due_at_once_in_test_mode_and_keep_their_names():
    first = due_reviews([review_entry()], set(), T0, TEST_TIMING.recheck_days)
    second = due_reviews([review_entry()], {"CO-1/7"}, T0, TEST_TIMING.recheck_days)

    assert [(d.days, d.due_at) for d in first] == [(7, T0)]
    assert [(d.days, d.due_at) for d in second] == [(30, T0)]


def test_rechecks_keep_their_real_waits_by_default():
    assert due_reviews([review_entry()], set(), T0 + timedelta(days=6)) == []


# --- The app ---


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


def make(catalog, test_mode):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo,
        runner=SubprocessRunner(),
        axis=MockAxisCompanion(),
        catalog=catalog,
        clock=lambda: T0,
        test_mode=test_mode,
    )
    return TestClient(app), repo


@pytest.mark.parametrize("mode", [True, False])
def test_features_report_the_mode(catalog, mode):
    client, _ = make(catalog, mode)

    assert client.get("/api/v1/features").json()["test_mode"] is mode


def test_the_app_reads_the_environment_when_not_told(catalog, monkeypatch):
    monkeypatch.setenv("LMS_TEST_MODE", "true")
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog))

    assert client.get("/api/v1/features").json()["test_mode"] is True


def finish_activities(client):
    client.post("/api/v1/explain", json={"unit_id": "PY-0.1", "explanation": "statement order sequential return"})
    for activity, answer in (("predict", {"choice": "A"}), ("trace", {"trace_answers": ["waiting", "checked in"]})):
        current = client.get(f"{BASE}/units/PY-0.1/activities/{activity}/exercise").json()
        client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": activity, **answer})


def test_test_mode_opens_the_cold_check_straight_after_the_activities(catalog):
    client, _ = make(catalog, True)
    finish_activities(client)

    assert client.get(f"{BASE}/units/PY-0.1/cold-check").json()["state"] == "available"


def test_real_mode_still_waits(catalog):
    client, _ = make(catalog, False)
    finish_activities(client)

    assert client.get(f"{BASE}/units/PY-0.1/cold-check").json()["state"] == "waiting"


@pytest.mark.parametrize("mode", [True, False])
def test_every_entry_carries_the_mode(catalog, mode):
    client, repo = make(catalog, mode)
    finish_activities(client)

    ledger = repo.get_evidence_ledger(LOCAL_LEARNER_ID)
    assert ledger
    assert {e.test_mode for e in ledger} == {mode}


def test_a_dot_env_line_turns_test_mode_on(catalog, monkeypatch, tmp_path):
    monkeypatch.delenv("LMS_TEST_MODE", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("LMS_TEST_MODE=true\n", encoding="utf-8")
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()

    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog))

    assert client.get("/api/v1/features").json()["test_mode"] is True


# --- Storage ---


def test_the_tag_survives_storage():
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    repo.record_evidence(review_entry().model_copy(update={"test_mode": True}))

    assert repo.get_evidence_ledger("l")[0].test_mode is True


def test_old_rows_read_as_not_test_mode(tmp_path):
    import sqlite3

    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE evidence_ledger (entry_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL, unit_id TEXT NOT NULL,"
            " skill_id TEXT NOT NULL, evidence_category TEXT NOT NULL, evidence_strength TEXT NOT NULL,"
            " assistance_level TEXT NOT NULL, demonstration_context TEXT NOT NULL, observed_reasoning TEXT,"
            " recorded_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO evidence_ledger VALUES ('e1', 'l', 'PY-0.1', 'CO-1', 'Explain / Reason', 'Strong', 'none', 'old', NULL, ?)",
            (T0.isoformat(),),
        )
    repo = SQLiteLearnerRepository(db_path=str(path))
    repo.initialize()

    assert repo.get_evidence_ledger("l")[0].test_mode is False
