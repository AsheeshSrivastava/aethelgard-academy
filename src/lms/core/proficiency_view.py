"""Assembles the learner-facing ProficiencyView from units and evidence.

Governed by:
- SPEC-12 section 6 (ProficiencyView)
- ADR-0016 (Proficiency Estimation and Progression Decisions)

Deterministic and pure: no LLM, no I/O (ADR-0010). Skills repeat across units at
different target levels, so a unit is decided against its own target, and a skill
row is decided against the highest target among the units in scope.
"""

from datetime import datetime
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from pydantic import BaseModel, Field

from lms.core.cold_check import ColdCheckState, ColdCheckStatus
from lms.core.models import (
    ActivityType,
    EvidenceCategory,
    EvidenceEntry,
    ProficiencyLevel,
    ProgressionDecision,
    Unit,
)
from lms.core.proficiency import (
    DECISION_ORDER,
    DEFAULT_CONFIG,
    LEVEL_ORDER,
    Confidence,
    EstimatorConfig,
    SkillDecision,
    consecutive_shaky_checks,
    decide_skill,
    decide_unit,
    evidence_counts,
    is_concept_check,
)

_DONE = (ProgressionDecision.PROGRESS, ProgressionDecision.ACCELERATE)
NO_RESETS: Mapping[str, datetime] = {}


def _after(ledger: List[EvidenceEntry], since: Optional[datetime]) -> List[EvidenceEntry]:
    """Evidence recorded after a reset; the ledger itself keeps everything (ADR-0016 amendment)."""
    return ledger if since is None else [e for e in ledger if e.recorded_at >= since]


class EvidenceCounts(BaseModel):
    explain: int = 0
    perform: int = 0
    diagnose: int = 0


class SkillView(BaseModel):
    skill_id: str
    skill_name: str
    target_level: ProficiencyLevel
    current_level: Optional[ProficiencyLevel] = None
    confidence: Optional[Confidence] = None             # of current_level only
    supported_levels: List[ProficiencyLevel] = Field(default_factory=list)  # each fully supported rung (SPEC-12 section 6)
    evidence_counts: EvidenceCounts
    decision: ProgressionDecision
    reason: str
    entry_ids: List[str]


class UnitView(BaseModel):
    unit_id: str
    decision: ProgressionDecision


class NextAction(BaseModel):
    unit_id: str
    skill_id: str
    activity: str                      # A slug: "explain", "debug-validate", "cold_check"
    decision: ProgressionDecision
    message: str
    retry_at: Optional[datetime] = None  # When a locked Cold Check retry opens (SPEC-12 section 6)


class ProficiencyView(BaseModel):
    stage: Optional[int] = None                # Stage in view; None when there are no units
    skills: List[SkillView]
    units: List[UnitView]
    next_action: Optional[NextAction] = None   # None when nothing can be done right now


def first_unfinished_unit(
    units: List[Unit],
    entries: Iterable[EvidenceEntry],
    now: datetime,
    config: EstimatorConfig = DEFAULT_CONFIG,
    resets: Mapping[str, datetime] = NO_RESETS,
) -> Optional[Unit]:
    """The learner's place in `units` (curriculum order); None when all are finished."""
    ledger = list(entries)
    for unit in units:
        decisions = _decide_unit_skills(unit, _after(ledger, resets.get(unit.unit_id)), now, config)
        if decisions and decide_unit(decisions) not in _DONE:
            return unit
    return None


def unit_decision(
    unit: Unit,
    entries: Iterable[EvidenceEntry],
    now: datetime,
    config: EstimatorConfig = DEFAULT_CONFIG,
    resets: Mapping[str, datetime] = NO_RESETS,
) -> ProgressionDecision:
    ledger = _after(list(entries), resets.get(unit.unit_id))
    return decide_unit(_decide_unit_skills(unit, ledger, now, config))


def activities_attempted(unit: Unit, entries: Iterable[EvidenceEntry], since: Optional[datetime] = None) -> bool:
    """Every activity of the unit has an entry (after its last reset), so its Cold Check clock can start."""
    tried = _tried_activities(unit, _after(list(entries), since))
    return all(activity in tried for activity in unit.methods)


def _tried_activities(unit: Unit, entries: Iterable[EvidenceEntry]) -> set:
    tried = set()
    for e in entries:
        if e.unit_id == unit.unit_id and not e.cold_check:
            tried.add(ActivityType.EXPLAIN if is_concept_check(e) else e.activity)
    return tried


def _decide_unit_skills(
    unit: Unit, ledger: List[EvidenceEntry], now: datetime, config: EstimatorConfig
) -> List[SkillDecision]:
    shaky = consecutive_shaky_checks(ledger, unit.unit_id)
    return [
        decide_skill(
            skill.goal_level,
            ledger,
            skill.skill_id,
            now=now,
            consecutive_shaky=shaky,
            config=config,
        )
        for skill in unit.target_skills
    ]


def build_proficiency_view(
    units: List[Unit],
    entries: Iterable[EvidenceEntry],
    cold_check_status_of: Callable[[str], ColdCheckStatus],
    now: datetime,
    stage: Optional[int] = None,
    config: EstimatorConfig = DEFAULT_CONFIG,
    unseen_activities: Callable[[Unit], List[str]] = lambda unit: [],
    resets: Mapping[str, datetime] = NO_RESETS,
) -> ProficiencyView:
    """Decide every unit and skill in scope; `units` must be in curriculum order.

    Each unit counts only evidence after its last reset; a skill row counts evidence after the
    latest reset among the units in view that target it (ADR-0016 amendment 2026-11-04).
    """
    ledger = list(entries)
    unit_rows: List[Tuple[Unit, List[SkillDecision]]] = []
    # skill_id -> (highest target, most shaky checks) across the units in scope
    scope: Dict[str, Tuple[ProficiencyLevel, int]] = {}
    names: Dict[str, str] = {}
    skill_since: Dict[str, Optional[datetime]] = {}

    for unit in units:
        since = resets.get(unit.unit_id)
        unit_ledger = _after(ledger, since)
        shaky = consecutive_shaky_checks(unit_ledger, unit.unit_id)
        for skill in unit.target_skills:
            names[skill.skill_id] = skill.skill_name
            target, most_shaky = scope.get(skill.skill_id, (skill.goal_level, 0))
            scope[skill.skill_id] = (
                max(target, skill.goal_level, key=LEVEL_ORDER.index),
                max(most_shaky, shaky),
            )
            known = skill_since.get(skill.skill_id)
            skill_since[skill.skill_id] = max(filter(None, (known, since)), default=None)
        unit_rows.append((unit, _decide_unit_skills(unit, unit_ledger, now, config)))

    return ProficiencyView(
        stage=stage,
        skills=[
            _skill_view(skill_id, names[skill_id], target, shaky, _after(ledger, skill_since[skill_id]), now, config)
            for skill_id, (target, shaky) in scope.items()
        ],
        units=[
            UnitView(unit_id=unit.unit_id, decision=decide_unit(decisions))
            for unit, decisions in unit_rows
        ],
        next_action=_next_action(unit_rows, ledger, cold_check_status_of, unseen_activities, config, resets),
    )


def _skill_view(
    skill_id: str,
    skill_name: str,
    target: ProficiencyLevel,
    shaky: int,
    ledger: List[EvidenceEntry],
    now: datetime,
    config: EstimatorConfig,
) -> SkillView:
    decided = decide_skill(target, ledger, skill_id, now=now, consecutive_shaky=shaky, config=config)
    counts = evidence_counts(ledger, skill_id, now=now, config=config)
    return SkillView(
        skill_id=skill_id,
        skill_name=skill_name,
        target_level=target,
        current_level=decided.estimate.level,
        confidence=decided.estimate.confidence,
        supported_levels=decided.estimate.supported_levels,
        evidence_counts=EvidenceCounts(
            explain=counts[EvidenceCategory.EXPLAIN_REASON],
            perform=counts[EvidenceCategory.PERFORM_SOLVE],
            diagnose=counts[EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER],
        ),
        decision=decided.decision,
        reason=decided.reason,
        entry_ids=decided.entry_ids,
    )


def _next_action(
    unit_rows: List[Tuple[Unit, List[SkillDecision]]],
    ledger: List[EvidenceEntry],
    cold_check_status_of: Callable[[str], ColdCheckStatus],
    unseen_activities: Callable[[Unit], List[str]] = lambda unit: [],
    config: EstimatorConfig = DEFAULT_CONFIG,
    resets: Mapping[str, datetime] = NO_RESETS,
) -> Optional[NextAction]:
    """First unit in curriculum order with something to do now."""
    for unit, decisions in unit_rows:
        if not decisions or decide_unit(decisions) in _DONE:
            continue
        status = cold_check_status_of(unit.unit_id)
        if status.state == ColdCheckState.WAITING:
            continue  # A Cold Check wait never blocks learning (ADR-0016 2.6).
        weakest = min(decisions, key=lambda d: DECISION_ORDER.index(d.decision))
        locked = status.state == ColdCheckState.FAILED_WAITING
        unit_ledger = _after(ledger, resets.get(unit.unit_id))
        activity = (
            _fresh_activity(unit, weakest.skill_id, unseen_activities(unit), config)
            if locked
            else _next_activity(unit, weakest.decision, status.state, unit_ledger)
        )
        message = weakest.reason
        if weakest.needs_cold_check and status.state == ColdCheckState.NOT_READY:
            message += _opens_cold_check(unit, unit_ledger)
        return NextAction(
            unit_id=unit.unit_id,
            skill_id=weakest.skill_id,
            activity=activity,
            decision=weakest.decision,
            message=message,
            retry_at=status.available_at if locked else None,
        )
    return None


def _opens_cold_check(unit: Unit, unit_ledger: List[EvidenceEntry]) -> str:
    """What opens a closed Cold Check: the activities with no entry since the last reset (SPEC-12 section 6)."""
    tried = _tried_activities(unit, unit_ledger)
    left = sum(1 for activity in unit.methods if activity not in tried)
    if not left:
        return ""
    return f" Do this unit's {left} remaining activit{'y' if left == 1 else 'ies'} to open its Cold Check."


def _fresh_activity(unit: Unit, skill_id: str, unseen: List[str], config: EstimatorConfig) -> str:
    """While the retry is locked: never a done item (SPEC-12 section 6).

    The weakest skill's main activity if it has an unseen item, else any activity that does,
    else the Cold Check step, which shows the countdown.
    """
    main = config.main_activities.get(skill_id)
    if main is not None and main.slug in unseen:
        return main.slug
    return unseen[0] if unseen else "cold_check"


def _next_activity(
    unit: Unit,
    decision: ProgressionDecision,
    state: ColdCheckState,
    ledger: List[EvidenceEntry],
) -> str:
    """The smallest next probe: an activity of the unit (ADR-0016 2.5)."""
    if decision == ProgressionDecision.REBUILD:
        return ActivityType.EXPLAIN.slug
    if state == ColdCheckState.AVAILABLE:
        return "cold_check"

    tried = _tried_activities(unit, ledger)
    untried = [activity for activity in unit.methods if activity not in tried]
    # Everything tried: practise again on the unit's last activity.
    return (untried[0] if untried else unit.methods[-1]).slug
