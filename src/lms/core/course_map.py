"""Courses and course maps for the learner frontend.

Governed by:
- SPEC-12 section 3 (Catalog)
- ADR-0019 and SPEC-16 section 3.4 (a passed stage review opens the stage build)

Deterministic and pure: units and Cold Check states come in, views come out.
"""

from typing import Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

from pydantic import BaseModel

from lms.core.cold_check import ColdCheckState
from lms.core.models import (
    ProficiencyLevel,
    ProgressionDecision,
    Unit,
    is_slotted_stage,
    stage_label,
)
from lms.core.review import ReviewState, build_is_open


class CourseInfo(BaseModel):
    title: str
    summary: str
    unit_prefix: str
    slotted_prefixes: Tuple[str, ...] = ()  # Supporting roadmaps taught inside this course (ADR-0020)


COURSES: Dict[str, CourseInfo] = {
    "python": CourseInfo(
        title="Python",
        summary="Read, reason about and build reliable Python programs.",
        unit_prefix="PY-",
        slotted_prefixes=("DSA-", "GIT-", "SD-", "AAE-"),
    ),
    "backend": CourseInfo(
        title="Python for Backend/AI",
        summary="Design, build and operate backend services with FastAPI.",
        unit_prefix="BE-",
        slotted_prefixes=("NET-", "DB-"),
    ),
    "ai-engineering": CourseInfo(
        title="AI Engineering",
        summary="Build, evaluate and operate applications around language models.",
        unit_prefix="AI-",
    ),
}


class Course(BaseModel):
    course_id: str
    title: str
    summary: str
    stage_count: int
    unit_count: int


class UnitSkill(BaseModel):
    skill_id: str
    skill_name: str
    goal_level: ProficiencyLevel


class UnitSummary(BaseModel):
    unit_id: str
    title: str
    concept_line: str
    target_skills: List[UnitSkill]
    authored: bool                     # Has a curator lesson package
    decision: ProgressionDecision      # For the signed-in learner
    cold_check_state: ColdCheckState


class BuildSummary(BaseModel):
    title: str
    kind: str                          # "script" | "mini_project"
    locked: bool
    pending_units: List[str]
    authored: bool = False             # False: a placeholder until the curator writes it
    status: Optional[str] = None       # "draft" | "approved"
    review_state: Optional[ReviewState] = None  # None when the caller gives no review (SPEC-16)


class AuthoredBuild(NamedTuple):
    """The parts of a curated build that the course map shows."""

    title: str
    kind: str
    status: str


class StageView(BaseModel):
    stage: int
    label: str                         # What the learner sees: "Stage 4", "DSA 0"
    title: str
    units: List[UnitSummary]
    build: Optional[BuildSummary] = None


class CourseMap(BaseModel):
    course: Course
    stages: List[StageView]


def course_of(unit_id: str) -> Optional[str]:
    """The course a unit belongs to, from its id prefix."""
    for course_id, info in COURSES.items():
        if unit_id.startswith((info.unit_prefix, *info.slotted_prefixes)):
            return course_id
    return None


def stages_in_path_order(units: List[Unit]) -> List[int]:
    """Numbered stages by number; a slotted stage just before the next numbered unit's stage.

    `units` must be in path order (ADR-0020 section 2.5).
    """
    before: Dict[int, List[int]] = {}
    pending: List[int] = []
    for unit in units:
        if not is_slotted_stage(unit.stage):
            before.setdefault(unit.stage, []).extend(pending)
            pending = []
        elif unit.stage not in pending:
            pending.append(unit.stage)
    return [stage for number in sorted(before) for stage in (*before[number], number)] + pending


def build_course(course_id: str, units: List[Unit]) -> Course:
    info = COURSES[course_id]
    return Course(
        course_id=course_id,
        title=info.title,
        summary=info.summary,
        stage_count=len({u.stage for u in units}),
        unit_count=len(units),
    )


def build_course_map(
    course_id: str,
    units: List[Unit],
    stage_titles: Dict[int, str],
    cold_check_state_of: Callable[[str], ColdCheckState],
    decision_of: Callable[[Unit], ProgressionDecision],
    builds: Mapping[int, AuthoredBuild] = {},
    reviews: Mapping[int, ReviewState] = {},
) -> CourseMap:
    """Group a course's units by stage, in path order; units keep their teaching order."""
    by_stage: Dict[int, List[Unit]] = {}
    for unit in units:
        by_stage.setdefault(unit.stage, []).append(unit)

    return CourseMap(
        course=build_course(course_id, units),
        stages=[
            _stage_view(
                stage,
                by_stage[stage],
                stage_titles,
                cold_check_state_of,
                decision_of,
                builds.get(stage),
                reviews.get(stage),
            )
            for stage in stages_in_path_order(units)
        ],
    )


def _stage_view(
    stage: int,
    units: List[Unit],
    stage_titles: Dict[int, str],
    cold_check_state_of: Callable[[str], ColdCheckState],
    decision_of: Callable[[Unit], ProgressionDecision],
    authored: Optional[AuthoredBuild] = None,
    review: Optional[ReviewState] = None,
) -> StageView:
    states = {u.unit_id: cold_check_state_of(u.unit_id) for u in units}
    pending = [unit_id for unit_id, state in states.items() if state != ColdCheckState.PASSED]
    label = stage_label(stage)
    return StageView(
        stage=stage,
        label=label,
        title=stage_titles.get(stage, label),
        units=[_unit_summary(u, decision_of(u), states[u.unit_id]) for u in units],
        # Every stage has one build (owner decision); curator data replaces these defaults.
        build=BuildSummary(
            title=authored.title if authored else f"{label} build",
            kind=authored.kind if authored else "script",
            locked=not build_is_open(review) if review else bool(pending),
            pending_units=pending,
            authored=authored is not None,
            status=authored.status if authored else None,
            review_state=review,
        ),
    )


def _unit_summary(
    unit: Unit, decision: ProgressionDecision, cold_check_state: ColdCheckState
) -> UnitSummary:
    return UnitSummary(
        unit_id=unit.unit_id,
        title=unit.title,
        concept_line=unit.concept_line,
        target_skills=[
            UnitSkill(skill_id=s.skill_id, skill_name=s.skill_name, goal_level=s.goal_level)
            for s in unit.target_skills
        ],
        authored=unit.lesson_markdown is not None,
        decision=decision,
        cold_check_state=cold_check_state,
    )
