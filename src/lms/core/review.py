"""Stage review and spaced rechecks.

Governed by:
- SPEC-16 (Stage Review and Spaced Rechecks)
- ADR-0019 (unit check, stage review, rechecks)
- Learning Method v2 Amendment A1.5

Deterministic and pure: units, seeds, stored results and a `now` supplied by the
caller come in, rounds and states come out. Nothing here sleeps or schedules.
"""

from datetime import datetime, timedelta
from enum import Enum
from itertools import chain, zip_longest
from typing import AbstractSet, Dict, Iterable, List, Mapping, Optional, Sequence

from pydantic import BaseModel

from lms.core.cold_check import DEFAULT_CONFIG
from lms.core.timing import REAL_TIMING, ColdCheckConfig
from lms.core.exercises import ExerciseSeed, seed_variants
from lms.core.models import EvidenceEntry, EvidenceStrength, ProficiencyLevel, Unit

STAGE_REVIEW = "stage_review"
RECHECK = "recheck"
RECHECK_DAYS = (7, 30)
RECHECK_MAX_ITEMS = 4
ITEMS_PER_UNIT = 2


class ReviewState(str, Enum):
    NOT_READY = "not_ready"            # A unit has not passed its Cold Check
    UNAVAILABLE = "unavailable"        # No unseen item exists; the build opens without a review
    AVAILABLE = "available"            # Can be answered now
    FAILED_WAITING = "failed_waiting"  # Last round failed; retry delay still running
    PASSED = "passed"                  # Last finished round passed


class ReviewItem(BaseModel):
    position: int
    exercise_id: str
    unit_id: str
    skill_id: str
    passed: Optional[bool] = None      # None until answered


class ReviewResult(BaseModel):
    last_attempt_at: datetime
    passed: bool


class StageReviewStatus(BaseModel):
    state: ReviewState
    available_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    pending_units: List[str] = []
    failed_units: List[str] = []
    items_total: int = 0
    items_done: int = 0


class DueReview(BaseModel):
    skill_id: str
    skill_name: str
    days: int
    due_at: datetime
    items: int = 0


def stage_scope(course_id: str, stage: int) -> str:
    return f"{course_id}/{stage}"


def recheck_scope(skill_id: str, days: int) -> str:
    return f"{skill_id}/{days}"


def build_is_open(state: ReviewState) -> bool:
    """SPEC-16 section 3.4: missing content never locks a learner out."""
    return state in (ReviewState.PASSED, ReviewState.UNAVAILABLE)


def stage_review_status(
    pending_units: List[str],
    has_items: bool,
    result: Optional[ReviewResult],
    items: Sequence[ReviewItem],
    now: datetime,
    config: ColdCheckConfig = DEFAULT_CONFIG,
) -> StageReviewStatus:
    """Derive the learner-facing status from what is stored."""
    done = [i for i in items if i.passed is not None]
    last_attempt_at = result.last_attempt_at if result else None
    base = dict(
        last_attempt_at=last_attempt_at,
        pending_units=pending_units,
        items_total=len(items),
        items_done=len(done),
    )
    if result and result.passed:
        return StageReviewStatus(state=ReviewState.PASSED, **base)
    if pending_units:
        return StageReviewStatus(state=ReviewState.NOT_READY, **base)
    if not has_items:
        return StageReviewStatus(state=ReviewState.UNAVAILABLE, **base)
    if result:
        failed = list(dict.fromkeys(i.unit_id for i in items if i.passed is False))
        available_at = result.last_attempt_at + timedelta(hours=config.delay_hours)
        if now < available_at:
            return StageReviewStatus(
                state=ReviewState.FAILED_WAITING, available_at=available_at, failed_units=failed, **base
            )
    return StageReviewStatus(state=ReviewState.AVAILABLE, **base)


def _unseen_items(
    unit_id: str, seeds: Iterable[ExerciseSeed], seen: AbstractSet[str]
) -> List[ReviewItem]:
    """The first unseen variant of each approved Cold Check seed."""
    items: List[ReviewItem] = []
    for seed in seeds:
        if not (seed.cold_check_eligible and seed.curator_approved):
            continue
        unseen = (f"{seed.seed_id}/v{n}" for n, _ in seed_variants(seed))
        exercise_id = next((e for e in unseen if e not in seen), None)
        if exercise_id:
            items.append(
                ReviewItem(position=0, exercise_id=exercise_id, unit_id=unit_id, skill_id=seed.skill_id)
            )
    return items


def plan_stage_review(
    units: Sequence[Unit], seeds: Mapping[str, Sequence[ExerciseSeed]], seen: AbstractSet[str]
) -> List[ReviewItem]:
    """SPEC-16 section 3.1: cover Apply and above, fill to 2 per unit, then mix the units."""
    covered = set()
    chosen: Dict[str, List[ReviewItem]] = {}
    spare: Dict[str, List[ReviewItem]] = {}
    for unit in units:
        goals = {s.skill_id for s in unit.target_skills}
        candidates = [i for i in _unseen_items(unit.unit_id, seeds.get(unit.unit_id, ()), seen) if i.skill_id in goals]
        picked: List[ReviewItem] = []
        for skill in unit.target_skills:
            if skill.goal_level == ProficiencyLevel.UNDERSTAND or skill.skill_id in covered:
                continue
            match = next((i for i in candidates if i.skill_id == skill.skill_id), None)
            if match:
                candidates.remove(match)
                picked.append(match)
                covered.add(skill.skill_id)
        chosen[unit.unit_id] = picked
        spare[unit.unit_id] = candidates

    for unit_id, picked in chosen.items():
        missing = max(0, ITEMS_PER_UNIT - len(picked))
        picked.extend(spare[unit_id][:missing])

    mixed = [i for i in chain.from_iterable(zip_longest(*chosen.values())) if i is not None]
    return [item.model_copy(update={"position": n}) for n, item in enumerate(mixed)]


def plan_recheck(
    skill_id: str, seeds: Mapping[str, Sequence[ExerciseSeed]], seen: AbstractSet[str]
) -> List[ReviewItem]:
    """SPEC-16 section 4: up to 4 unseen items for one skill, from any unit."""
    found = [
        item
        for unit_id, unit_seeds in seeds.items()
        for item in _unseen_items(unit_id, unit_seeds, seen)
        if item.skill_id == skill_id
    ]
    return [i.model_copy(update={"position": n}) for n, i in enumerate(found[:RECHECK_MAX_ITEMS])]


def due_reviews(
    ledger: Sequence[EvidenceEntry],
    finished: AbstractSet[str],
    now: datetime,
    wait_days: Sequence[int] = REAL_TIMING.recheck_days,
) -> List[DueReview]:
    """Rechecks due now, oldest first; one per skill, so the queue stays short.

    Rechecks keep their names (7, 30); `wait_days` is how long each waits (zero in test mode).
    """
    waits = dict(zip(RECHECK_DAYS, wait_days))
    first_pass: Dict[str, datetime] = {}
    for entry in ledger:
        if entry.review_kind == STAGE_REVIEW and entry.evidence_strength == EvidenceStrength.STRONG:
            known = first_pass.get(entry.skill_id)
            first_pass[entry.skill_id] = min(known, entry.recorded_at) if known else entry.recorded_at

    due: List[DueReview] = []
    for skill_id, passed_at in first_pass.items():
        days = next((d for d in RECHECK_DAYS if recheck_scope(skill_id, d) not in finished), None)
        if days is None:
            continue
        due_at = passed_at + timedelta(days=waits[days])
        if due_at <= now:
            due.append(DueReview(skill_id=skill_id, skill_name=skill_id, days=days, due_at=due_at))
    return sorted(due, key=lambda d: d.due_at)
