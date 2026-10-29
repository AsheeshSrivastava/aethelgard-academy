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

def test_progress_decision_when_apply_target_met():
    entry = EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="PY-1.2 Predict and Run task",
    )
    decision, reason = evaluate_progression(
        target_level=ProficiencyLevel.APPLY,
        evidence_entries=[entry],
    )
    assert decision == ProgressionDecision.PROGRESS
    assert "sufficient" in reason.lower()

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
