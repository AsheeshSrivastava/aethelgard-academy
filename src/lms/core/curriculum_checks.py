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
from lms.core.exercises import ExerciseSeed, spare_cold_items
from lms.core.models import ActivityType, EvidenceCategory, ProficiencyLevel, Unit, stage_label

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
        findings.extend(_check_make_step(unit))
        if seeds is not None:
            findings.extend(_check_seeds(unit, seeds.get(unit.unit_id, ()), main_activities))
            findings.extend(_check_make_items(unit, seeds.get(unit.unit_id, ())))
    findings.extend(_check_stage_coverage(units))
    findings.extend(_check_level_steps(units))
    if seeds is not None:
        findings.extend(_check_stage_review_items(units, seeds))
        for unit in units:
            findings.extend(_check_practice_volume(unit, seeds.get(unit.unit_id, ())))
            findings.extend(_check_topics(unit, seeds.get(unit.unit_id, ())))
    return findings


RUNGS = [ProficiencyLevel.UNDERSTAND, ProficiencyLevel.APPLY, ProficiencyLevel.ADAPT, ProficiencyLevel.OWN]
EARLY_PYTHON_STAGES = range(0, 6)  # Python Stages 0 to 5 (Amendment A1.6)


def _finding(severity: Severity, code: str, message: str, unit: Unit, skill_id: Optional[str] = None) -> Finding:
    return Finding(severity=severity, code=code, message=message, unit_id=unit.unit_id, skill_id=skill_id,
                   course_id=course_of(unit.unit_id), stage=unit.stage)


def _check_level_steps(units: List[Unit]) -> List[Finding]:
    """Amendment A1.1 and A1.2, over the units in path order: enter at Apply or below, rise one rung at a time."""
    findings: List[Finding] = []
    last: Dict[str, Tuple[str, ProficiencyLevel]] = {}
    for unit in units:
        for skill in unit.target_skills:
            level = skill.goal_level
            if skill.skill_id not in last:
                if RUNGS.index(level) > RUNGS.index(ProficiencyLevel.APPLY):
                    findings.append(_finding(Severity.ERROR, "skill-enters-above-apply",
                                             f"{unit.unit_id}: {skill.skill_id} enters the path at {level.value}; "
                                             "the first unit must set it to Understand or Apply.", unit, skill.skill_id))
            else:
                before_unit, before = last[skill.skill_id]
                if RUNGS.index(level) - RUNGS.index(before) > 1:
                    findings.append(_finding(Severity.ERROR, "skill-skips-a-rung",
                                             f"{unit.unit_id}: {skill.skill_id} rises from {before.value} in {before_unit} "
                                             f"to {level.value}, more than one level.", unit, skill.skill_id))
            last[skill.skill_id] = (unit.unit_id, level)
    return findings


def _check_practice_volume(unit: Unit, seeds: Sequence[ExerciseSeed]) -> List[Finding]:
    """Amendment A1.6, as a warning: only for a unit whose content has started."""
    approved = [s for s in seeds if s.curator_approved]
    if not seeds:
        return []
    early = course_of(unit.unit_id) == "python" and unit.stage in EARLY_PYTHON_STAGES
    target = 15 if early else 8
    findings: List[Finding] = []
    if len(approved) < target:
        findings.append(_finding(Severity.WARNING, "practice-volume-low",
                                 f"{unit.unit_id} has {len(approved)} approved items; it needs at least {target}.", unit))
    makes = [s for s in approved if s.item_type == "playground" and s.body.get("make")]
    if early and unit.make is not None and len(makes) < 3:
        findings.append(_finding(Severity.WARNING, "make-volume-low",
                                 f"{unit.unit_id} has {len(makes)} approved Make items; it needs at least 3.",
                                 unit, unit.make.skill_id))
    return findings


def _check_topics(unit: Unit, seeds: Sequence[ExerciseSeed]) -> List[Finding]:
    """Amendment A1.4: each seed names a topic of its unit, and no Cold Check item tests an awareness topic."""
    known = {t.name.casefold(): t for t in unit.topics}
    findings: List[Finding] = []
    for seed in seeds:
        if not seed.topic:
            findings.append(_finding(Severity.ERROR, "seed-topic-missing", f"{seed.seed_id} names no topic.", unit, seed.skill_id))
            continue
        topic = known.get(seed.topic.casefold())
        if topic is None:
            if known:
                findings.append(_finding(Severity.ERROR, "seed-topic-unknown",
                                         f"{seed.seed_id}: '{seed.topic}' is not a topic of {unit.unit_id}.", unit, seed.skill_id))
            continue
        if topic.awareness and seed.cold_check_eligible:
            findings.append(_finding(Severity.ERROR, "cold-check-awareness-topic",
                                     f"{seed.seed_id} is a Cold Check item on '{topic.name}', an awareness topic.", unit, seed.skill_id))
        elif topic.awareness:
            findings.append(_finding(Severity.WARNING, "exercise-awareness-topic",
                                     f"{seed.seed_id} tests '{topic.name}', an awareness topic; it must not be needed to pass.",
                                     unit, seed.skill_id))
    return findings


def _check_stage_review_items(
    units: List[Unit], seeds: Mapping[str, Sequence[ExerciseSeed]]
) -> List[Finding]:
    """SPEC-16 section 3.4: a stage with no spare items runs no review, so the curator is told."""
    short: Dict[Tuple[Optional[str], int], List[str]] = {}
    for unit in units:
        key = (course_of(unit.unit_id), unit.stage)
        short.setdefault(key, [])
        if spare_cold_items(unit, seeds.get(unit.unit_id, ())) < 1:
            short[key].append(unit.unit_id)
    return [
        Finding(
            severity=Severity.WARNING,
            code="stage-review-short",
            message=f"{course_id} {stage_label(stage)}: no spare Cold Check item in {', '.join(lacking)}.",
            course_id=course_id,
            stage=stage,
        )
        for (course_id, stage), lacking in short.items()
        if lacking
    ]


def _check_make_step(unit: Unit) -> List[Finding]:
    """Learning Method v2 Amendment A1.3: Make is a Build that credits one of the unit's targets."""
    if unit.make is None:
        return []
    if (
        ActivityType.BUILD in unit.methods
        and unit.make.skill_id in {s.skill_id for s in unit.target_skills}
    ):
        return []
    return [
        Finding(
            severity=Severity.ERROR,
            code="make-credit-invalid",
            message=f"{unit.unit_id}: Make credits {unit.make.skill_id}, which needs a Build method "
            "and to be a target skill.",
            unit_id=unit.unit_id,
            skill_id=unit.make.skill_id,
            course_id=course_of(unit.unit_id),
            stage=unit.stage,
        )
    ]


def _check_make_items(unit: Unit, seeds: Sequence[ExerciseSeed]) -> List[Finding]:
    """SPEC-13 playground, Make items: on a Make unit only, from a blank file, and present."""
    findings: List[Finding] = []

    def report(severity: Severity, code: str, message: str) -> None:
        findings.append(
            Finding(severity=severity, code=code, message=message, unit_id=unit.unit_id,
                    skill_id=unit.make.skill_id if unit.make else None,
                    course_id=course_of(unit.unit_id), stage=unit.stage)
        )

    make_items = [s for s in seeds if s.item_type == "playground" and s.body.get("make")]
    for seed in make_items:
        if unit.make is None:
            report(Severity.ERROR, "make-seed-unexpected", f"{seed.seed_id} is a Make item, but {unit.unit_id} has no Make step.")
        code = [line for line in seed.body.get("starter", []) if line.strip() and not line.strip().startswith("#")]
        if code:
            report(Severity.ERROR, "make-starter-not-blank", f"{seed.seed_id} must start from a blank file; its starter has code.")
    if unit.make is not None and not any(s.curator_approved for s in make_items):
        report(Severity.WARNING, "make-seed-missing", f"{unit.unit_id} has a Make step but no approved Make item.")
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
        if unit.make and seed.activity == ActivityType.BUILD and seed.skill_id != unit.make.skill_id:
            report(Severity.ERROR, "make-seed-wrong-skill", f"{seed.seed_id} is a Build seed; the Make step credits {unit.make.skill_id}.", seed.skill_id)
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
                    message=f"{course_id} {stage_label(stage)} produces no: {', '.join(missing)}.",
                    course_id=course_id,
                    stage=stage,
                )
            )
    return findings
