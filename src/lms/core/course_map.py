"""Courses and course maps for the learner frontend.

Governed by:
- SPEC-12 section 3 (Catalog)
- ADR-0016 section 2.6 (a stage build unlocks when every unit has a passed Cold Check)

Deterministic and pure: units and Cold Check states come in, views come out.
"""

from typing import Callable, Dict, List, Mapping, NamedTuple, Optional

from pydantic import BaseModel

from lms.core.cold_check import ColdCheckState
from lms.core.models import ProficiencyLevel, ProgressionDecision, Unit


class CourseInfo(BaseModel):
    title: str
    summary: str
    unit_prefix: str


COURSES: Dict[str, CourseInfo] = {
    "python": CourseInfo(
        title="Python",
        summary="Read, reason about and build reliable Python programs.",
        unit_prefix="PY-",
    ),
    "backend": CourseInfo(
        title="Python for Backend/AI",
        summary="Design, build and operate backend services with FastAPI.",
        unit_prefix="BE-",
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


class AuthoredBuild(NamedTuple):
    """The parts of a curated build that the course map shows."""

    title: str
    kind: str
    status: str


class StageView(BaseModel):
    stage: int
    title: str
    units: List[UnitSummary]
    build: Optional[BuildSummary] = None


class CourseMap(BaseModel):
    course: Course
    stages: List[StageView]


def course_of(unit_id: str) -> Optional[str]:
    """The course a unit belongs to, from its id prefix."""
    for course_id, info in COURSES.items():
        if unit_id.startswith(info.unit_prefix):
            return course_id
    return None


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
) -> CourseMap:
    """Group a course's units by stage number; units keep their teaching order."""
    by_stage: Dict[int, List[Unit]] = {}
    for unit in units:
        by_stage.setdefault(unit.stage, []).append(unit)

    return CourseMap(
        course=build_course(course_id, units),
        stages=[
            _stage_view(stage, by_stage[stage], stage_titles, cold_check_state_of, decision_of, builds.get(stage))
            for stage in sorted(by_stage)
        ],
    )


def _stage_view(
    stage: int,
    units: List[Unit],
    stage_titles: Dict[int, str],
    cold_check_state_of: Callable[[str], ColdCheckState],
    decision_of: Callable[[Unit], ProgressionDecision],
    authored: Optional[AuthoredBuild] = None,
) -> StageView:
    states = {u.unit_id: cold_check_state_of(u.unit_id) for u in units}
    pending = [unit_id for unit_id, state in states.items() if state != ColdCheckState.PASSED]
    return StageView(
        stage=stage,
        title=stage_titles.get(stage, f"Stage {stage}"),
        units=[_unit_summary(u, decision_of(u), states[u.unit_id]) for u in units],
        # Every stage has one build (owner decision); curator data replaces these defaults.
        build=BuildSummary(
            title=authored.title if authored else f"Stage {stage} build",
            kind=authored.kind if authored else "script",
            locked=bool(pending),
            pending_units=pending,
            authored=authored is not None,
            status=authored.status if authored else None,
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
