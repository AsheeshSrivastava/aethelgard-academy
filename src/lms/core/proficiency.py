"""Whole-ledger proficiency estimator and progression decisions.

Governed by:
- ADR-0016 (Proficiency Estimation and Progression Decisions over the Whole Ledger)
- 04 - Proficiency & Progression System v1

Deterministic and pure: no LLM, no I/O (ADR-0010). Results can always be
recomputed from the append-only evidence ledger.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional

from pydantic import BaseModel, Field

from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    ProgressionDecision,
)


class Confidence(str, Enum):
    PROVISIONAL = "provisional"
    SUPPORTED = "supported"


@dataclass(frozen=True)
class EstimatorConfig:
    """Thresholds marked *tunable* in ADR-0016."""

    window_entries: int = 10
    window_days: int = 90
    supported_min_entries: int = 2
    weak_streak_to_lower: int = 2
    rebuild_weak_entries: int = 3
    rebuild_shaky_checks: int = 2
    # skill_id -> main activity, loaded from Learning Method v2 (ADR-0016 amendment A).
    main_activities: Mapping[str, ActivityType] = field(default_factory=dict)


DEFAULT_CONFIG = EstimatorConfig()

CONCEPT_CHECK_SKILL = "CO-6"


def concept_check_id(unit_id: str, prompt_no: int = 1) -> str:
    """The exercise id of a unit's concept-check prompt: `<unit>/explain/v<n>` (ADR-0016 amendment G, ADR-0032)."""
    return f"{unit_id}/explain/v{prompt_no}"

LEVEL_ORDER: List[ProficiencyLevel] = [
    ProficiencyLevel.UNDERSTAND,
    ProficiencyLevel.APPLY,
    ProficiencyLevel.ADAPT,
    ProficiencyLevel.OWN,
]

# Weakest first: a unit's decision is the weakest among its skills (ADR-0016 2.5).
DECISION_ORDER: List[ProgressionDecision] = [
    ProgressionDecision.REBUILD,
    ProgressionDecision.STRENGTHEN,
    ProgressionDecision.UNDECIDED,
    ProgressionDecision.PROGRESS,
    ProgressionDecision.ACCELERATE,
]

_GOOD = (EvidenceStrength.MODERATE, EvidenceStrength.STRONG)
_UP_TO_SMALL_HINT = (AssistanceLevel.NONE, AssistanceLevel.SYNTAX_LOOKUP, AssistanceLevel.SMALL_HINT)
_UP_TO_SYNTAX = (AssistanceLevel.NONE, AssistanceLevel.SYNTAX_LOOKUP)


class SkillEstimate(BaseModel):
    skill_id: str
    level: Optional[ProficiencyLevel] = None
    confidence: Optional[Confidence] = None
    qualifying_entry_ids: List[str] = Field(default_factory=list)  # entries backing `level`
    supported_levels: List[ProficiencyLevel] = Field(default_factory=list)  # every level with full support
    level_entry_ids: Dict[ProficiencyLevel, List[str]] = Field(default_factory=dict)  # entries qualifying per reached level
    support_gaps: Dict[ProficiencyLevel, List[str]] = Field(default_factory=dict)  # what each reached level still lacks
    no_cold_check: List[ProficiencyLevel] = Field(default_factory=list)  # reached levels with no passed Cold Check
    weak_streak: int = 0                                            # newest consecutive weak entries
    weak_count: int = 0                                             # weak entries in the window


class SkillDecision(BaseModel):
    skill_id: str
    target_level: ProficiencyLevel
    estimate: SkillEstimate
    decision: ProgressionDecision
    reason: str
    entry_ids: List[str] = Field(default_factory=list)
    needs_cold_check: bool = False  # the target level still lacks a passed Cold Check


def qualifies(
    entry: EvidenceEntry, level: ProficiencyLevel, config: EstimatorConfig = DEFAULT_CONFIG
) -> bool:
    """Level rules, ADR-0016 section 2.3 and amendment A."""
    if entry.assistance_level == AssistanceLevel.SUPPLIED_REASONING:
        return False
    is_main_activity = (
        entry.activity is not None and config.main_activities.get(entry.skill_id) == entry.activity
    )
    if level == ProficiencyLevel.UNDERSTAND:
        return entry.evidence_strength in _GOOD and entry.assistance_level in _UP_TO_SMALL_HINT
    if level == ProficiencyLevel.APPLY:
        return (
            (entry.evidence_category == EvidenceCategory.PERFORM_SOLVE or is_main_activity)
            and entry.evidence_strength in _GOOD
            and entry.assistance_level in _UP_TO_SMALL_HINT
        )
    if level == ProficiencyLevel.ADAPT:
        return (
            (entry.evidence_category == EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER or is_main_activity)
            and entry.evidence_strength == EvidenceStrength.STRONG
            and entry.assistance_level in _UP_TO_SYNTAX
        )
    return (
        entry.activity == ActivityType.BUILD
        and entry.evidence_strength == EvidenceStrength.STRONG
        and entry.assistance_level == AssistanceLevel.NONE
    )


def is_weak(entry: EvidenceEntry) -> bool:
    return (
        entry.evidence_strength == EvidenceStrength.WEAK
        or entry.assistance_level == AssistanceLevel.SUPPLIED_REASONING
    )


def _window(
    entries: Iterable[EvidenceEntry], skill_id: Optional[str], now: datetime, config: EstimatorConfig
) -> List[EvidenceEntry]:
    """Entries for the skill inside the recency window, oldest first, one per exercise (ADR-0016 2.2)."""
    cutoff = now - timedelta(days=config.window_days)
    relevant = sorted(
        (
            e
            for e in entries
            if (skill_id is None or e.skill_id == skill_id)
            and _aware(e.recorded_at) >= cutoff
            and e.evidence_strength != EvidenceStrength.INSUFFICIENT
        ),
        key=lambda e: _aware(e.recorded_at),
    )
    seen: set = set()
    unique: List[EvidenceEntry] = []
    for e in reversed(relevant):  # Newest first, so the latest result for a seed is kept
        exercise = e.seed_id or e.exercise_id
        if exercise is None and is_concept_check(e):
            exercise = concept_check_id(e.unit_id)  # Rows from before amendment G
        if exercise is not None:
            if exercise in seen:
                continue
            seen.add(exercise)
        unique.append(e)
    unique.reverse()
    return unique[-config.window_entries :]


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def evidence_counts(
    entries: Iterable[EvidenceEntry],
    skill_id: str,
    now: Optional[datetime] = None,
    config: EstimatorConfig = DEFAULT_CONFIG,
) -> Dict[EvidenceCategory, int]:
    """Entries per category inside the same window the decision uses."""
    now = now or datetime.now(timezone.utc)
    counts = {category: 0 for category in EvidenceCategory}
    for e in _window(entries, skill_id, now, config):
        counts[e.evidence_category] += 1
    return counts


def is_concept_check(entry: EvidenceEntry) -> bool:
    """A CO-6 concept check from Explain; a CO-6 entry from another activity is not one."""
    return (
        entry.skill_id == CONCEPT_CHECK_SKILL
        and entry.evidence_category == EvidenceCategory.EXPLAIN_REASON
        and entry.activity in (None, ActivityType.EXPLAIN)
    )


def consecutive_shaky_checks(entries: Iterable[EvidenceEntry], unit_id: str) -> int:
    """Newest run of Shaky concept checks for the unit (ADR-0016 2.5, Rebuild)."""
    checks = sorted(
        (e for e in entries if e.unit_id == unit_id and is_concept_check(e)),
        key=lambda e: _aware(e.recorded_at),
    )
    run = 0
    for e in reversed(checks):
        if e.evidence_strength != EvidenceStrength.WEAK:
            break
        run += 1
    return run


def estimate_skill(
    entries: Iterable[EvidenceEntry],
    skill_id: Optional[str],
    now: Optional[datetime] = None,
    config: EstimatorConfig = DEFAULT_CONFIG,
) -> SkillEstimate:
    """Current proficiency and confidence for one skill (ADR-0016 2.3, 2.4)."""
    now = now or datetime.now(timezone.utc)
    window = _window(entries, skill_id, now, config)
    sid = skill_id or (window[-1].skill_id if window else "")

    weak_streak = 0
    for e in reversed(window):
        if not is_weak(e):
            break
        weak_streak += 1
    weak_count = sum(1 for e in window if is_weak(e))

    level_index = -1
    for i, level in enumerate(LEVEL_ORDER):
        if not any(qualifies(e, level, config) for e in window):
            break
        level_index = i

    if level_index < 0:
        return SkillEstimate(skill_id=sid, weak_streak=weak_streak, weak_count=weak_count)

    # No automatic overwrite: a weak streak lowers the level by one, never more.
    lowered = weak_streak >= config.weak_streak_to_lower
    if lowered:
        level_index -= 1
        if level_index < 0:
            return SkillEstimate(skill_id=sid, weak_streak=weak_streak, weak_count=weak_count)

    level = LEVEL_ORDER[level_index]
    backing = [e for e in window if qualifies(e, level, config)]

    def gaps_at(candidate: ProficiencyLevel) -> List[str]:
        """The missing pieces of support at a level, in plain words; empty when it is supported."""
        entries = [e for e in window if qualifies(e, candidate, config)]
        gaps = []
        short = config.supported_min_entries - len(entries)
        no_cold_check = not any(e.cold_check for e in entries)
        # The Cold Check is one of the missing exercises, not an extra task (SPEC-12 section 6).
        if short > 0:
            exercises = f"{short} more exercise{'s' if short > 1 else ''} at {candidate.value}"
            if no_cold_check:
                exercises += (
                    ", and it must be a passed Cold Check" if short == 1 else "; one must be a passed Cold Check"
                )
            gaps.append(exercises)
        elif no_cold_check:
            gaps.append("a passed Cold Check")
        if weak_streak:
            gaps.append("a strong attempt after your last weak one")
        return gaps

    def supported_at(candidate: ProficiencyLevel) -> bool:
        return not gaps_at(candidate)

    return SkillEstimate(
        skill_id=sid,
        level=level,
        confidence=Confidence.SUPPORTED if supported_at(level) else Confidence.PROVISIONAL,
        qualifying_entry_ids=[e.entry_id for e in backing],
        supported_levels=[lv for lv in LEVEL_ORDER[: level_index + 1] if supported_at(lv)],
        level_entry_ids={
            lv: [e.entry_id for e in window if qualifies(e, lv, config)] for lv in LEVEL_ORDER[: level_index + 1]
        },
        support_gaps={lv: gaps_at(lv) for lv in LEVEL_ORDER[: level_index + 1] if not supported_at(lv)},
        no_cold_check=[
            lv for lv in LEVEL_ORDER[: level_index + 1]
            if not any(e.cold_check for e in window if qualifies(e, lv, config))
        ],
        weak_streak=weak_streak,
        weak_count=weak_count,
    )


def decide_skill(
    target_level: ProficiencyLevel,
    entries: Iterable[EvidenceEntry],
    skill_id: Optional[str],
    now: Optional[datetime] = None,
    consecutive_shaky: int = 0,
    config: EstimatorConfig = DEFAULT_CONFIG,
) -> SkillDecision:
    """Progression decision for one skill against the unit's target level (ADR-0016 2.5)."""
    est = estimate_skill(entries, skill_id, now=now, config=config)

    def result(decision: ProgressionDecision, reason: str, needs_cold_check: bool = False) -> SkillDecision:
        return SkillDecision(
            skill_id=est.skill_id,
            target_level=target_level,
            estimate=est,
            decision=decision,
            reason=reason,
            entry_ids=est.qualifying_entry_ids,
            needs_cold_check=needs_cold_check,
        )

    if consecutive_shaky >= config.rebuild_shaky_checks:
        return result(
            ProgressionDecision.REBUILD,
            f"Mental model is unreliable: {consecutive_shaky} concept checks in a row were Shaky.",
        )

    if est.level is None:
        if est.weak_count >= config.rebuild_weak_entries:
            return result(
                ProgressionDecision.REBUILD,
                f"Mental model is unreliable: {est.weak_count} weak attempts and no qualifying evidence yet.",
            )
        if est.weak_count:
            return result(
                ProgressionDecision.STRENGTHEN,
                "Capability is fragile: recent attempts were weak or assisted, with no qualifying evidence yet.",
            )
        return result(
            ProgressionDecision.UNDECIDED,
            "Insufficient evidence: no qualifying or contradicting entries yet. Collect the smallest next probe.",
        )

    current = LEVEL_ORDER.index(est.level)
    target = LEVEL_ORDER.index(target_level)

    if current < target:
        return result(
            ProgressionDecision.STRENGTHEN,
            f"Evidence shows {est.level.value}; the target is {target_level.value}.",
        )
    if target_level not in est.supported_levels:
        return result(
            ProgressionDecision.STRENGTHEN,
            f"{target_level.value} is provisional: it needs {', and '.join(est.support_gaps.get(target_level, []))}.",
            needs_cold_check=target_level in est.no_cold_check,
        )
    proven_above = [lv for lv in est.supported_levels if LEVEL_ORDER.index(lv) > target]
    if proven_above:  # ADR-0016 amendment H: any proven rung above the goal; the top rung may be unproven
        return result(
            ProgressionDecision.ACCELERATE,
            f"Supported {proven_above[-1].value} is above the {target_level.value} target.",
        )
    # Count the target level's own entries: a supported target always includes a passed Cold Check,
    # while the top rung's entries may not (SPEC-12 section 6, 2026-11-14).
    return result(
        ProgressionDecision.PROGRESS,
        f"Sufficient evidence for {target_level.value}: supported by "
        f"{len(est.level_entry_ids.get(target_level, []))} entries including a Cold Check.",
    )


def decide_unit(skill_decisions: Iterable[SkillDecision]) -> ProgressionDecision:
    """A unit's decision is the weakest among its target skills."""
    decisions = [d.decision for d in skill_decisions]
    if not decisions:
        return ProgressionDecision.UNDECIDED
    return min(decisions, key=DECISION_ORDER.index)
