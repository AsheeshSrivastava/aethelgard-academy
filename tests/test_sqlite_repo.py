import pytest
from datetime import datetime, timezone
from lms.core.models import (
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
