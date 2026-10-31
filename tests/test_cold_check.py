"""Tests for the per-unit Cold Check timer (ADR-0016 section 2.6, SPEC-12 section 4.1)."""

from datetime import datetime, timedelta, timezone

import pytest

from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.core.cold_check import (
    ColdCheckConfig,
    ColdCheckState,
    ColdCheckTimer,
    cold_check_status,
)
from lms.core.models import (
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)
LEARNER = "learner_001"
UNIT = "PY-1.2"


def timer(**overrides) -> ColdCheckTimer:
    fields = dict(learner_id=LEARNER, unit_id=UNIT, completed_at=T0)
    fields.update(overrides)
    return ColdCheckTimer(**fields)


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


# --- Status rules ---


def test_not_ready_until_activities_are_completed():
    status = cold_check_status(None, now=T0)
    assert status.state == ColdCheckState.NOT_READY
    assert status.available_at is None
    assert status.last_attempt_at is None


def test_waiting_for_24_hours_after_completion():
    status = cold_check_status(timer(), now=T0 + timedelta(hours=23, minutes=59))
    assert status.state == ColdCheckState.WAITING
    assert status.available_at == T0 + DAY
    assert status.last_attempt_at is None


def test_available_exactly_at_24_hours():
    status = cold_check_status(timer(), now=T0 + DAY)
    assert status.state == ColdCheckState.AVAILABLE
    assert status.available_at == T0 + DAY


def test_passed_is_final_and_has_nothing_pending():
    attempted = T0 + DAY
    status = cold_check_status(
        timer(last_attempt_at=attempted, last_attempt_passed=True),
        now=attempted + timedelta(days=400),
    )
    assert status.state == ColdCheckState.PASSED
    assert status.available_at is None
    assert status.last_attempt_at == attempted


def test_fail_waits_24_hours_from_the_attempt():
    attempted = T0 + timedelta(days=3)
    status = cold_check_status(
        timer(last_attempt_at=attempted, last_attempt_passed=False),
        now=attempted + timedelta(hours=1),
    )
    assert status.state == ColdCheckState.FAILED_WAITING
    assert status.available_at == attempted + DAY
    assert status.last_attempt_at == attempted


def test_fail_becomes_available_again_after_the_new_wait():
    attempted = T0 + timedelta(days=3)
    status = cold_check_status(
        timer(last_attempt_at=attempted, last_attempt_passed=False),
        now=attempted + DAY,
    )
    assert status.state == ColdCheckState.AVAILABLE
    assert status.available_at == attempted + DAY
    assert status.last_attempt_at == attempted


def test_delay_is_tunable():
    config = ColdCheckConfig(delay_hours=48)
    assert cold_check_status(timer(), now=T0 + DAY, config=config).state == ColdCheckState.WAITING
    assert cold_check_status(timer(), now=T0 + 2 * DAY, config=config).state == ColdCheckState.AVAILABLE


# --- Repository storage ---


def test_no_timer_until_completion(repo):
    assert repo.get_cold_check_timer(LEARNER, UNIT) is None


def test_completion_is_stored(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)

    stored = repo.get_cold_check_timer(LEARNER, UNIT)
    assert stored.completed_at == T0
    assert stored.last_attempt_at is None
    assert stored.last_attempt_passed is None


def test_redoing_activities_does_not_restart_the_clock(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0 + timedelta(hours=20))

    assert repo.get_cold_check_timer(LEARNER, UNIT).completed_at == T0


def test_attempt_result_is_stored(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)
    repo.record_cold_check_attempt(LEARNER, UNIT, passed=False, attempted_at=T0 + DAY)

    stored = repo.get_cold_check_timer(LEARNER, UNIT)
    assert stored.last_attempt_at == T0 + DAY
    assert stored.last_attempt_passed is False


def test_latest_attempt_replaces_the_previous_one(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)
    repo.record_cold_check_attempt(LEARNER, UNIT, passed=False, attempted_at=T0 + DAY)
    repo.record_cold_check_attempt(LEARNER, UNIT, passed=True, attempted_at=T0 + 2 * DAY)

    stored = repo.get_cold_check_timer(LEARNER, UNIT)
    assert stored.last_attempt_at == T0 + 2 * DAY
    assert stored.last_attempt_passed is True
    assert stored.completed_at == T0


def test_attempt_without_completion_is_refused(repo):
    with pytest.raises(ValueError):
        repo.record_cold_check_attempt(LEARNER, UNIT, passed=True, attempted_at=T0)

    assert repo.get_cold_check_timer(LEARNER, UNIT) is None


def test_timers_are_separate_per_learner_and_unit(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)

    assert repo.get_cold_check_timer("someone_else", UNIT) is None
    assert repo.get_cold_check_timer(LEARNER, "PY-1.3") is None


def test_timer_survives_reopening_the_database(tmp_path):
    db_path = str(tmp_path / "timer.db")
    first = SQLiteLearnerRepository(db_path=db_path)
    first.initialize()
    first.mark_unit_activities_completed(LEARNER, UNIT, T0)

    second = SQLiteLearnerRepository(db_path=db_path)
    second.initialize()

    assert second.get_cold_check_timer(LEARNER, UNIT).completed_at == T0


# --- Reset ---


def test_reset_clears_timer_and_unit_progress(repo):
    repo.save_unit_progress(LEARNER, UNIT, "Completed")
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)

    repo.reset_unit(LEARNER, UNIT)

    assert repo.get_unit_progress(LEARNER, UNIT) is None
    assert repo.get_cold_check_timer(LEARNER, UNIT) is None


def test_reset_never_touches_the_ledger(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)
    repo.record_evidence(
        EvidenceEntry(
            learner_id=LEARNER,
            unit_id=UNIT,
            skill_id="CO-1",
            evidence_category=EvidenceCategory.PERFORM_SOLVE,
            evidence_strength=EvidenceStrength.STRONG,
            assistance_level=AssistanceLevel.NONE,
            demonstration_context="Cold Check",
            cold_check=True,
        )
    )

    repo.reset_unit(LEARNER, UNIT)

    ledger = repo.get_evidence_ledger(LEARNER)
    assert len(ledger) == 1
    assert ledger[0].cold_check is True


def test_reset_affects_only_that_learner_and_unit(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)
    repo.mark_unit_activities_completed(LEARNER, "PY-1.3", T0)
    repo.mark_unit_activities_completed("someone_else", UNIT, T0)

    repo.reset_unit(LEARNER, UNIT)

    assert repo.get_cold_check_timer(LEARNER, "PY-1.3") is not None
    assert repo.get_cold_check_timer("someone_else", UNIT) is not None


def test_completing_again_after_reset_starts_a_new_clock(repo):
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0)
    repo.reset_unit(LEARNER, UNIT)
    repo.mark_unit_activities_completed(LEARNER, UNIT, T0 + DAY)

    assert repo.get_cold_check_timer(LEARNER, UNIT).completed_at == T0 + DAY
