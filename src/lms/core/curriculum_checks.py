"""Checks that a curriculum can produce the evidence it asks for.

Governed by:
- SPEC-12 section 3.1 (Content ownership and curriculum checks)
- ADR-0016 section 2.3 (level rules)
- 04 - Proficiency & Progression System v1 (evidence categories)

Deterministic and pure: units in, findings out. Findings are reported, not
raised, because the curriculum belongs to the curator (SPEC-12 section 3.1).
"""

from enum import Enum
from typing import AbstractSet, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from pydantic import BaseModel

from lms.core.course_map import course_of
from lms.core.exercises import ExerciseSeed
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
    main_activities: Optional[Mapping[str, ActivityType]] = None,
    seeds: Optional[Mapping[str, Sequence[ExerciseSeed]]] = None,
) -> List[Finding]:
    """Run every check.

    `stages_with_build` holds (course_id, stage) pairs with a curated build.
    `main_activities` maps each skill to its Learning Method main activity.
    `seeds` maps unit ids to their loaded seeds; None skips the seed checks.
    """
    main_activities = main_activities or {}
    findings: List[Finding] = []
    for unit in units:
        findings.extend(_check_target_levels(unit, stages_with_build, main_activities))
        if seeds is not None:
            findings.extend(_check_seeds(unit, seeds.get(unit.unit_id, ()), main_activities))
    findings.extend(_check_stage_coverage(units))
    return findings


def _check_seeds(
    unit: Unit, seeds: Sequence[ExerciseSeed], main_activities: Mapping[str, ActivityType]
) -> List[Finding]:
    """SPEC-13 section 8, rules 3, 8 and 11."""
    goals = {s.skill_id: s.goal_level for s in unit.target_skills}
    findings: List[Finding] = []

    def report(severity: Severity, code: str, message: str, skill_id: Optional[str]) -> None:
        findings.append(
            Finding(
                severity=severity,
                code=code,
                message=message,
                unit_id=unit.unit_id,
                skill_id=skill_id,
                course_id=course_of(unit.unit_id),
                stage=unit.stage,
            )
        )

    covered: Set[str] = set()
    for seed in seeds:
        if seed.activity not in unit.methods:
            report(Severity.ERROR, "seed-wrong-activity", f"{seed.seed_id} uses {seed.activity.value}, which is not in the unit.", seed.skill_id)
        if seed.skill_id not in goals:
            report(Severity.ERROR, "seed-wrong-skill", f"{seed.seed_id} tests {seed.skill_id}, which is not a target skill.", seed.skill_id)
        elif seed.level != goals[seed.skill_id]:
            report(Severity.ERROR, "seed-wrong-level", f"{seed.seed_id} is at {seed.level.value}; the goal is {goals[seed.skill_id].value}.", seed.skill_id)
        if seed.cold_check_eligible:
            if main_activities.get(seed.skill_id, seed.activity) != seed.activity:
                report(Severity.ERROR, "seed-not-main-activity", f"{seed.seed_id} must test {seed.skill_id} through its main activity.", seed.skill_id)
            elif seed.curator_approved:
                covered.add(seed.skill_id)

    for skill_id in goals:
        if skill_id not in covered:
            report(Severity.WARNING, "cold-check-seed-missing", f"{unit.unit_id}: {skill_id} has no approved Cold Check seed.", skill_id)
    return findings


def _check_target_levels(
    unit: Unit,
    stages_with_build: AbstractSet[Tuple[str, int]],
    main_activities: Mapping[str, ActivityType],
) -> List[Finding]:
    course_id = course_of(unit.unit_id)
    categories = {ACTIVITY_EVIDENCE[m] for m in unit.methods}
    findings: List[Finding] = []

    for skill in unit.target_skills:
        has_main_activity = main_activities.get(skill.skill_id) in unit.methods
        if skill.goal_level == ProficiencyLevel.APPLY:
            ok = has_main_activity or EvidenceCategory.PERFORM_SOLVE in categories
            code, needs = "apply-needs-perform", "a Perform / Solve activity or its main activity"
        elif skill.goal_level == ProficiencyLevel.ADAPT:
            ok = has_main_activity or EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER in categories
            code = "adapt-needs-diagnose"
            needs = "a Diagnose / Judge / Transfer activity or its main activity"
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
    used: Dict[Tuple[Optional[str], int], Set[EvidenceCategory]] = {}
    for unit in units:
        categories = used.setdefault((course_of(unit.unit_id), unit.stage), set())
        categories.update(ACTIVITY_EVIDENCE[m] for m in unit.methods)

    findings: List[Finding] = []
    for (course_id, stage), categories in used.items():
        missing = [c.value for c in EvidenceCategory if c not in categories]
        if missing:
            findings.append(
                Finding(
                    severity=Severity.WARNING,
                    code="stage-missing-evidence",
                    message=f"{course_id} stage {stage} produces no: {', '.join(missing)}.",
                    course_id=course_id,
                    stage=stage,
                )
            )
    return findings
