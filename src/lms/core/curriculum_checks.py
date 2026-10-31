"""Checks that a curriculum can produce the evidence it asks for.

Governed by:
- SPEC-12 section 3.1 (Content ownership and curriculum checks)
- ADR-0016 section 2.3 (level rules)
- 04 - Proficiency & Progression System v1 (evidence categories)

Deterministic and pure: units in, findings out. Findings are reported, not
raised, because the curriculum belongs to the curator (SPEC-12 section 3.1).
"""

from enum import Enum
from typing import AbstractSet, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel

from lms.core.course_map import course_of
from lms.core.models import ActivityType, EvidenceCategory, ProficiencyLevel, Unit

# What each activity can show, from the evidence category examples in the
# Proficiency & Progression System.
ACTIVITY_EVIDENCE: Dict[ActivityType, EvidenceCategory] = {
    ActivityType.EXPLAIN: EvidenceCategory.EXPLAIN_REASON,
    ActivityType.PREDICT: EvidenceCategory.EXPLAIN_REASON,
    ActivityType.TRACE: EvidenceCategory.EXPLAIN_REASON,
    ActivityType.SPECIFY: EvidenceCategory.PERFORM_SOLVE,
    ActivityType.DECOMPOSE: EvidenceCategory.PERFORM_SOLVE,
    ActivityType.MODIFY: EvidenceCategory.PERFORM_SOLVE,
    ActivityType.BUILD: EvidenceCategory.PERFORM_SOLVE,
    ActivityType.DIRECT: EvidenceCategory.PERFORM_SOLVE,
    ActivityType.DEBUG_VALIDATE: EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER,
    ActivityType.EVALUATE: EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER,
}

# Activities a machine can grade with no AI: fixed answers or sandbox checks.
DETERMINISTIC_ACTIVITIES = {
    ActivityType.PREDICT,
    ActivityType.TRACE,
    ActivityType.MODIFY,
    ActivityType.DEBUG_VALIDATE,
    ActivityType.BUILD,
}


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class Finding(BaseModel):
    severity: Severity
    code: str
    message: str
    unit_id: Optional[str] = None
    skill_id: Optional[str] = None
    course_id: Optional[str] = None
    stage: Optional[int] = None


def check_curriculum(
    units: List[Unit],
    stages_with_build: AbstractSet[Tuple[str, int]] = frozenset(),
) -> List[Finding]:
    """Run every check. `stages_with_build` holds (course_id, stage) pairs with a curated build."""
    findings: List[Finding] = []
    for unit in units:
        findings.extend(_check_target_levels(unit, stages_with_build))
        if not DETERMINISTIC_ACTIVITIES.intersection(unit.methods):
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    code="cold-check-not-graded",
                    message=f"{unit.unit_id} has no deterministically graded activity for its Cold Check.",
                    unit_id=unit.unit_id,
                    course_id=course_of(unit.unit_id),
                    stage=unit.stage,
                )
            )
    findings.extend(_check_stage_coverage(units))
    return findings


def _check_target_levels(
    unit: Unit, stages_with_build: AbstractSet[Tuple[str, int]]
) -> List[Finding]:
    course_id = course_of(unit.unit_id)
    categories = {ACTIVITY_EVIDENCE[m] for m in unit.methods}
    findings: List[Finding] = []

    for skill in unit.target_skills:
        if skill.goal_level == ProficiencyLevel.APPLY:
            ok = EvidenceCategory.PERFORM_SOLVE in categories
            code, needs = "apply-needs-perform", "a Perform / Solve activity"
        elif skill.goal_level == ProficiencyLevel.ADAPT:
            ok = EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER in categories
            code, needs = "adapt-needs-diagnose", "a Diagnose / Judge / Transfer activity"
        elif skill.goal_level == ProficiencyLevel.OWN:
            ok = (course_id, unit.stage) in stages_with_build
            code, needs = "own-needs-stage-build", "a stage build"
        else:
            continue
        if not ok:
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    code=code,
                    message=f"{unit.unit_id} targets {skill.skill_id} at {skill.goal_level.value}, "
                    f"which needs {needs}.",
                    unit_id=unit.unit_id,
                    skill_id=skill.skill_id,
                    course_id=course_id,
                    stage=unit.stage,
                )
            )
    return findings


def _check_stage_coverage(units: List[Unit]) -> List[Finding]:
    used: Dict[Tuple[Optional[str], int], Set[ActivityType]] = {}
    for unit in units:
        used.setdefault((course_of(unit.unit_id), unit.stage), set()).update(unit.methods)

    findings: List[Finding] = []
    for (course_id, stage), activities in used.items():
        missing = [a.value for a in ActivityType if a not in activities]
        if missing:
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    code="stage-missing-activity",
                    message=f"{course_id} stage {stage} never uses: {', '.join(missing)}.",
                    course_id=course_id,
                    stage=stage,
                )
            )
    return findings
