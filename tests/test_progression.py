import pytest
from lms.core.models import (
    ProficiencyLevel,
    EvidenceCategory,
    EvidenceStrength,
    AssistanceLevel,
    ProgressionDecision,
    EvidenceEntry,
)
from lms.core.progression import evaluate_progression

def _apply_entry(**kw):
    return EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="PY-1.2 Predict and Run task",
        **kw,
    )

def test_progress_decision_when_apply_target_met():
    # ADR-0016: two qualifying entries from different exercises, one a passed Cold Check.
    entries = [_apply_entry(exercise_id="ex-1"), _apply_entry(exercise_id="ex-2", cold_check=True)]
    decision, reason = evaluate_progression(
        target_level=ProficiencyLevel.APPLY,
        evidence_entries=entries,
    )
    assert decision == ProgressionDecision.PROGRESS
    assert "sufficient" in reason.lower()

def test_single_entry_is_provisional_so_strengthen():
    # ADR-0016: one lucky answer must not justify progression.
    decision, reason = evaluate_progression(
        target_level=ProficiencyLevel.APPLY,
        evidence_entries=[_apply_entry(exercise_id="ex-1")],
    )
    assert decision == ProgressionDecision.STRENGTHEN
    assert "provisional" in reason.lower()

def test_strengthen_decision_when_assistance_was_supplied():
    entry = EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.WEAK,
        assistance_level=AssistanceLevel.SUPPLIED_REASONING,
        demonstration_context="PY-1.2 Predict task",
    )
    decision, reason = evaluate_progression(
        target_level=ProficiencyLevel.APPLY,
        evidence_entries=[entry],
    )
    assert decision == ProgressionDecision.STRENGTHEN
    assert "assisted" in reason.lower() or "fragile" in reason.lower()

def test_undecided_when_no_evidence():
    decision, reason = evaluate_progression(
        target_level=ProficiencyLevel.APPLY,
        evidence_entries=[],
    )
    assert decision == ProgressionDecision.UNDECIDED
