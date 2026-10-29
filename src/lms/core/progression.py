"""Progression and evidence evaluation engine.

Governed by:
- 04 - Proficiency & Progression System v1
"""

from typing import List, Tuple
from lms.core.models import (
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    ProgressionDecision,
)


def evaluate_progression(
    target_level: ProficiencyLevel,
    evidence_entries: List[EvidenceEntry],
) -> Tuple[ProgressionDecision, str]:
    """Evaluate observable evidence against a target proficiency level.

    Returns:
        (ProgressionDecision, reason_str)
    """
    if not evidence_entries:
        return (
            ProgressionDecision.UNDECIDED,
            "Insufficient evidence: No observable performance entries found.",
        )

    # Inspect the most relevant / recent evidence
    latest_entry = evidence_entries[-1]

    # Check for heavy assistance dependency -> Strengthen
    if latest_entry.assistance_level == AssistanceLevel.SUPPLIED_REASONING:
        return (
            ProgressionDecision.STRENGTHEN,
            "Capability is fragile: Reasoning was supplied by an external source. Target targeted unassisted practice.",
        )

    # Check for Insufficient strength
    if latest_entry.evidence_strength == EvidenceStrength.INSUFFICIENT:
        return (
            ProgressionDecision.UNDECIDED,
            "Current observation is too ambiguous to justify a progression decision.",
        )

    # Evaluate target depths
    if target_level == ProficiencyLevel.UNDERSTAND:
        if latest_entry.evidence_strength in (EvidenceStrength.MODERATE, EvidenceStrength.STRONG):
            return (
                ProgressionDecision.PROGRESS,
                "Sufficient evidence for Understand: Mental model clearly reconstructed.",
            )
        return (
            ProgressionDecision.STRENGTHEN,
            "Mental model needs strengthening: Explanation was weak or incomplete.",
        )

    if target_level == ProficiencyLevel.APPLY:
        if latest_entry.evidence_strength in (EvidenceStrength.MODERATE, EvidenceStrength.STRONG):
            if latest_entry.assistance_level in (
                AssistanceLevel.NONE,
                AssistanceLevel.SYNTAX_LOOKUP,
                AssistanceLevel.SMALL_HINT,
            ):
                return (
                    ProgressionDecision.PROGRESS,
                    "Sufficient evidence for Apply: Correct application with learner owning the reasoning path.",
                )
        return (
            ProgressionDecision.STRENGTHEN,
            "Apply capability requires strengthening with bounded hints.",
        )

    if target_level == ProficiencyLevel.ADAPT:
        if (
            latest_entry.evidence_strength == EvidenceStrength.STRONG
            and latest_entry.evidence_category == EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER
        ):
            return (
                ProgressionDecision.PROGRESS,
                "Sufficient evidence for Adapt: Successfully handled meaningful variation/imperfect condition.",
            )
        return (
            ProgressionDecision.STRENGTHEN,
            "Adapt capability requires demonstrating handling of variations without full scaffolding.",
        )

    if target_level == ProficiencyLevel.OWN:
        if (
            latest_entry.evidence_strength == EvidenceStrength.STRONG
            and latest_entry.assistance_level == AssistanceLevel.NONE
        ):
            return (
                ProgressionDecision.PROGRESS,
                "Sufficient evidence for Own: Self-directed problem framing and validation in realistic context.",
            )
        return (
            ProgressionDecision.STRENGTHEN,
            "Own capability requires greater autonomy and complete problem framing.",
        )

    return (ProgressionDecision.UNDECIDED, "Unable to evaluate evidence against target.")
