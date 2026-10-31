import sqlite3

import pytest
from datetime import datetime, timezone
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository

@pytest.fixture
def repo():
    # Use an in-memory SQLite database for deterministic tests
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository

def test_save_and_get_unit_progress(repo):
    repo.save_unit_progress(learner_id="learner_001", unit_id="PY-1.1", status="Completed")
    progress = repo.get_unit_progress(learner_id="learner_001", unit_id="PY-1.1")
    assert progress is not None
    assert progress["status"] == "Completed"

def test_record_and_get_evidence_ledger(repo):
    entry = EvidenceEntry(
        entry_id="entry-123",
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="PY-1.2 Predict task",
        observed_reasoning="Explained type coercion error without hints",
    )
    repo.record_evidence(entry)

    ledger = repo.get_evidence_ledger(learner_id="learner_001")
    assert len(ledger) == 1
    retrieved = ledger[0]
    assert retrieved.entry_id == "entry-123"
    assert retrieved.skill_id == "CO-1"
    assert retrieved.evidence_strength == EvidenceStrength.STRONG
    assert retrieved.assistance_level == AssistanceLevel.NONE

def test_get_evidence_ledger_filtered_by_skill(repo):
    entry1 = EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="Task 1",
    )
    entry2 = EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="VE-6",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.MODERATE,
        assistance_level=AssistanceLevel.SMALL_HINT,
        demonstration_context="Task 2",
    )
    repo.record_evidence(entry1)
    repo.record_evidence(entry2)

    co1_ledger = repo.get_evidence_ledger(learner_id="learner_001", skill_id="CO-1")
    assert len(co1_ledger) == 1
    assert co1_ledger[0].skill_id == "CO-1"


def _entry(entry_id: str = "entry-1", **overrides) -> EvidenceEntry:
    fields = dict(
        entry_id=entry_id,
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="Task",
    )
    fields.update(overrides)
    return EvidenceEntry(**fields)


# The evidence_ledger table as it shipped before ADR-0016 added the new columns.
OLD_LEDGER_SCHEMA = """
    CREATE TABLE evidence_ledger (
        entry_id TEXT PRIMARY KEY,
        learner_id TEXT NOT NULL,
        unit_id TEXT NOT NULL,
        skill_id TEXT NOT NULL,
        evidence_category TEXT NOT NULL,
        evidence_strength TEXT NOT NULL,
        assistance_level TEXT NOT NULL,
        demonstration_context TEXT NOT NULL,
        observed_reasoning TEXT,
        recorded_at TEXT NOT NULL
    );
"""


@pytest.fixture
def old_db(tmp_path):
    """A database file holding one row, created by the pre-ADR-0016 code."""
    db_path = str(tmp_path / "old.db")
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(OLD_LEDGER_SCHEMA)
        conn.execute(
            "INSERT INTO evidence_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "old-entry",
                "learner_001",
                "PY-1.2",
                "CO-1",
                EvidenceCategory.PERFORM_SOLVE.value,
                EvidenceStrength.STRONG.value,
                AssistanceLevel.NONE.value,
                "Old task",
                None,
                "2026-01-01T00:00:00+00:00",
            ),
        )
    conn.close()
    return db_path


def test_new_evidence_fields_round_trip(repo):
    repo.record_evidence(
        _entry(exercise_id="ex-7", activity=ActivityType.DEBUG_VALIDATE, cold_check=True)
    )

    entry = repo.get_evidence_ledger(learner_id="learner_001")[0]
    assert entry.exercise_id == "ex-7"
    assert entry.activity == ActivityType.DEBUG_VALIDATE
    assert entry.cold_check is True


def test_seed_id_round_trips(repo):
    repo.record_evidence(_entry(seed_id="PY-0.1/predict-1"))

    assert repo.get_evidence_ledger("learner_001")[0].seed_id == "PY-0.1/predict-1"


def test_new_evidence_fields_default_when_absent(repo):
    repo.record_evidence(_entry())

    entry = repo.get_evidence_ledger(learner_id="learner_001")[0]
    assert entry.exercise_id is None
    assert entry.activity is None
    assert entry.cold_check is False


def test_initialize_migrates_old_database_and_old_rows_read_as_defaults(old_db):
    repository = SQLiteLearnerRepository(db_path=old_db)
    repository.initialize()

    entry = repository.get_evidence_ledger(learner_id="learner_001")[0]
    assert entry.entry_id == "old-entry"
    assert entry.demonstration_context == "Old task"
    assert entry.exercise_id is None
    assert entry.activity is None
    assert entry.cold_check is False


def test_migrated_database_accepts_new_entries(old_db):
    repository = SQLiteLearnerRepository(db_path=old_db)
    repository.initialize()
    repository.record_evidence(_entry(entry_id="new-entry", cold_check=True))

    ledger = repository.get_evidence_ledger(learner_id="learner_001")
    assert {e.entry_id: e.cold_check for e in ledger} == {"old-entry": False, "new-entry": True}


def test_initialize_is_idempotent(old_db):
    repository = SQLiteLearnerRepository(db_path=old_db)
    repository.initialize()
    repository.record_evidence(_entry(entry_id="new-entry", exercise_id="ex-1"))
    repository.initialize()
    repository.initialize()

    ledger = repository.get_evidence_ledger(learner_id="learner_001")
    assert [e.entry_id for e in ledger] == ["old-entry", "new-entry"]
    assert ledger[1].exercise_id == "ex-1"


def test_ledger_stays_append_only(repo):
    repo.record_evidence(_entry())

    with pytest.raises(sqlite3.IntegrityError):
        repo.record_evidence(_entry(evidence_strength=EvidenceStrength.WEAK))

    assert repo.get_evidence_ledger("learner_001")[0].evidence_strength == EvidenceStrength.STRONG
