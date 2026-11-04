"""Cold Check feedback, option A (ADR-0022 section 2.5).

Deterministic and pure: the unit, its seeds, the ledger and the learner's saved answers
come in; one row per item of the unit's round comes out. Nothing here grades, and AXIS
plays no part.
"""

from typing import Any, Dict, List, Mapping, Optional, Sequence

from pydantic import BaseModel

from lms.core.exercises import ExerciseSeed, cold_round
from lms.core.grading import Reveal, worked_answer
from lms.core.models import ActivityType, EvidenceEntry, EvidenceStrength, Unit


class FeedbackItem(BaseModel):
    skill_id: str
    skill_name: str
    passed: Optional[bool] = None      # None: not answered in a round yet
    your_answer: Optional[str] = None  # The learner's saved answer, in words
    hint: Optional[str] = None         # Only for a failed item, and only once approved
    practice_activity: str             # Where to practise the skill before the retry
    worked: Optional[Reveal] = None    # Only for a passed item: it will not come back


class ColdCheckFeedback(BaseModel):
    unit_id: str
    items: List[FeedbackItem]


def answer_in_words(seed: ExerciseSeed, answer: Optional[Dict[str, Any]]) -> Optional[str]:
    """What the learner chose, as they saw it; never the key or the reasoning."""
    if not answer:
        return None
    body = seed.body
    if "choice" in answer:
        options = body.get("sentences") if seed.item_type == "explain_spot_flaw" else body.get("options")
        text = next((o["text"] for o in options or [] if o["key"] == answer["choice"]), None)
        return f"{answer['choice']}. {text}" if text else str(answer["choice"])
    if "trace_answers" in answer:
        return " / ".join(answer["trace_answers"])
    if "locate" in answer:
        found = answer["locate"]
        kinds = {o["key"]: o["text"].split(":")[0] for o in body.get("error_types", [])}
        return f"Line {found.get('line')}, {kinds.get(found.get('error_type'), found.get('error_type'))}"
    return "Your code"


def practice_activity(unit: Unit, skill_id: str, main_activities: Mapping[str, ActivityType]) -> str:
    """The skill's main activity if the unit has it, else the unit's first practice activity."""
    main = main_activities.get(skill_id)
    if main is not None and main in unit.methods and main != ActivityType.EXPLAIN:
        return main.slug
    practice = [m for m in unit.methods if m != ActivityType.EXPLAIN]
    return practice[0].slug if practice else ActivityType.EXPLAIN.slug


def cold_check_feedback(
    unit: Unit,
    seeds: Sequence[ExerciseSeed],
    ledger: Sequence[EvidenceEntry],
    answers: Mapping[str, Dict[str, Any]],
    main_activities: Mapping[str, ActivityType],
) -> ColdCheckFeedback:
    """One row per item of the unit's round, from its newest unit Cold Check entry.

    `answers` maps an exercise id to the newest answer the learner submitted for it.
    """
    names = {s.skill_id: s.skill_name for s in unit.target_skills}
    newest: Dict[str, EvidenceEntry] = {}
    for entry in ledger:
        if entry.unit_id == unit.unit_id and entry.cold_check and entry.review_kind is None and entry.seed_id:
            newest[entry.seed_id] = entry  # The ledger comes oldest first.

    items: List[FeedbackItem] = []
    for seed in cold_round(unit, seeds):
        entry = newest.get(seed.seed_id)
        passed = None if entry is None else entry.evidence_strength == EvidenceStrength.STRONG
        items.append(
            FeedbackItem(
                skill_id=seed.skill_id,
                skill_name=names.get(seed.skill_id, seed.skill_id),
                passed=passed,
                your_answer=answer_in_words(seed, answers.get(entry.exercise_id)) if entry else None,
                hint=seed.hint if passed is False and seed.hint_approved else None,
                practice_activity=practice_activity(unit, seed.skill_id, main_activities),
                worked=worked_answer(seed) if passed else None,
            )
        )
    return ColdCheckFeedback(unit_id=unit.unit_id, items=items)
