"""My skills: each framework skill once, grouped by area, from the whole ledger.

Governed by:
- SPEC-12 section 6.1 (My skills)
- ADR-0016 amendment 2026-11-04, points 3 and 5 (lifetime level; unit resets do not apply)
- AI-Era Programming Skills Framework v1 (the five areas and 27 skills)

Deterministic and pure: no I/O, no LLM.
"""

from datetime import datetime
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from pydantic import BaseModel

from lms.core.course_map import course_of
from lms.core.models import EvidenceEntry, ProficiencyLevel, Unit
from lms.core.proficiency import DEFAULT_CONFIG, Confidence, EstimatorConfig, estimate_skill

# The framework's areas, in its own order, with what each area owns.
AREAS: Dict[str, tuple] = {
    "CO": ("Comprehend", "owns the mental model"),
    "SP": ("Specify", "owns the intent"),
    "BU": ("Build & Adapt", "owns the consequences"),
    "VE": ("Verify", "owns the verification"),
    "DE": ("Decide & Direct", "owns the decisions"),
}


class SkillSummary(BaseModel):
    skill_id: str
    skill_name: str
    level: Optional[ProficiencyLevel] = None      # None: not started
    confidence: Optional[Confidence] = None
    evidence: int = 0
    last_seen: Optional[datetime] = None
    practised_in: List[str]                      # Units with the learner's evidence, first seen first
    targeted_in: Dict[str, int]                  # course_id -> units of that course targeting the skill


class SkillArea(BaseModel):
    area_id: str
    name: str
    owns: str
    skills: List[SkillSummary]


class SkillsOverview(BaseModel):
    areas: List[SkillArea]


def _order(skill_id: str) -> tuple:
    area, _, number = skill_id.partition("-")
    return (list(AREAS).index(area) if area in AREAS else len(AREAS), int(number) if number.isdigit() else 0)


def build_skills_overview(
    skill_names: Mapping[str, str],
    units: Sequence[Unit],
    entries: Iterable[EvidenceEntry],
    now: datetime,
    config: EstimatorConfig = DEFAULT_CONFIG,
) -> SkillsOverview:
    ledger = sorted(entries, key=lambda e: e.recorded_at)
    targeted: Dict[str, Dict[str, int]] = {}
    for unit in units:
        for skill in unit.target_skills:
            course = course_of(unit.unit_id) or "other"
            per_course = targeted.setdefault(skill.skill_id, {})
            per_course[course] = per_course.get(course, 0) + 1

    areas: Dict[str, List[SkillSummary]] = {}
    for skill_id in sorted(skill_names, key=_order):
        mine = [e for e in ledger if e.skill_id == skill_id]
        estimate = estimate_skill(ledger, skill_id, now=now, config=config)
        summary = SkillSummary(
            skill_id=skill_id,
            skill_name=skill_names[skill_id],
            level=estimate.level,
            confidence=estimate.confidence,
            evidence=len(mine),
            last_seen=mine[-1].recorded_at if mine else None,
            practised_in=list(dict.fromkeys(e.unit_id for e in mine)),
            targeted_in=targeted.get(skill_id, {}),
        )
        areas.setdefault(skill_id.partition("-")[0], []).append(summary)

    return SkillsOverview(
        areas=[
            SkillArea(area_id=area_id, name=AREAS[area_id][0], owns=AREAS[area_id][1], skills=areas[area_id])
            for area_id in AREAS
            if area_id in areas
        ]
    )
