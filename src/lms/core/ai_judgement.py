"""The shared AI-judgement verdict (SPEC-18, ADR-0026).

Pure rules, no I/O. A model reports, for each required idea, whether the learner's
explanation shows it. The code decides the verdict: Solid only when every idea is met.
The model's own overall opinion is never read.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

# Owner option A (ADR-0026 section 2.4): a judged verdict writes CO-6 evidence.
# Set to False for option C: a verdict is feedback only and writes nothing.
CONCEPT_CHECK_WRITES_EVIDENCE = True

MAX_FEEDBACK_CHARS = 400
MIN_IDEAS, MAX_IDEAS = 2, 3

NotJudgedReason = Literal[
    "ai_off", "no_rubric", "cap_reached", "provider_refused", "no_answer", "unreadable_reply"
]

NOT_JUDGED_MESSAGES: Dict[str, str] = {
    "ai_off": "AI is off, so this was not judged. Your answer is saved; try again when AI is on.",
    "no_rubric": "This concept check has no marking guide yet, so it was not judged.",
    "cap_reached": "The monthly AI budget is used up, so this was not judged.",
    "provider_refused": "The AI provider refused the request (quota, rate limit or key). This was not judged.",
    "no_answer": "The AI provider did not answer. This was not judged; try again in a moment.",
    "unreadable_reply": "The AI's reply could not be read, so this was not judged.",
}


class Idea(BaseModel):
    id: str
    text: str


class Rubric(BaseModel):
    """The private required ideas of one concept check (SPEC-18 section 1)."""

    unit_id: str
    ideas: List[Idea]


class IdeaResult(BaseModel):
    id: str
    text: str
    met: bool


class AiJudgement(BaseModel):
    status: Literal["judged", "not_judged"]
    verdict: Optional[Literal["Solid", "Shaky"]] = None
    ideas: List[IdeaResult] = Field(default_factory=list)
    feedback: Optional[str] = None
    model: Optional[str] = None
    reason: Optional[NotJudgedReason] = None
    message: str = ""
    interaction_id: Optional[str] = None


class RubricError(ValueError):
    pass


class UnreadableReply(ValueError):
    pass


def parse_rubric(raw: Any, unit_id: str) -> Rubric:
    """A rubric file's content, checked: 2 or 3 ideas, each with a unique id and some text."""
    if not isinstance(raw, dict) or not isinstance(raw.get("ideas"), list):
        raise RubricError("The rubric needs an 'ideas' list.")
    ideas: List[Idea] = []
    for item in raw["ideas"]:
        if not isinstance(item, dict):
            raise RubricError("Each idea must be an object.")
        idea_id, text = item.get("id"), item.get("text")
        if not isinstance(idea_id, str) or not idea_id.strip() or not isinstance(text, str) or not text.strip():
            raise RubricError("Each idea needs an id and some text.")
        ideas.append(Idea(id=idea_id.strip(), text=text.strip()))
    if not MIN_IDEAS <= len(ideas) <= MAX_IDEAS:
        raise RubricError(f"A concept check needs {MIN_IDEAS} or {MAX_IDEAS} ideas.")
    if len({i.id for i in ideas}) != len(ideas):
        raise RubricError("Idea ids must be unique.")
    return Rubric(unit_id=unit_id, ideas=ideas)


def not_judged(reason: str, interaction_id: Optional[str] = None) -> AiJudgement:
    return AiJudgement(
        status="not_judged", reason=reason, message=NOT_JUDGED_MESSAGES[reason], interaction_id=interaction_id
    )


def verdict_for(ideas: Sequence[IdeaResult]) -> str:
    """Solid when every idea is met; otherwise Shaky."""
    return "Solid" if ideas and all(i.met for i in ideas) else "Shaky"


def validate_reply(raw_reply: str, rubric_ideas: Sequence[Idea]) -> Tuple[List[IdeaResult], str]:
    """Check a model's reply (SPEC-18 section 3). Returns the idea results and the feedback.

    Valid JSON, every rubric id exactly once, `met` a boolean, `feedback` a non-empty
    string of at most 400 characters. Anything else raises UnreadableReply.
    """
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(raw_reply).strip(), flags=re.DOTALL).strip()
    try:
        parsed = json.loads(cleaned)
    except (ValueError, TypeError):
        raise UnreadableReply("not JSON") from None
    if not isinstance(parsed, dict):
        raise UnreadableReply("not an object")
    items, feedback = parsed.get("ideas"), parsed.get("feedback")
    if not isinstance(items, list):
        raise UnreadableReply("no ideas list")
    if not isinstance(feedback, str) or not feedback.strip() or len(feedback.strip()) > MAX_FEEDBACK_CHARS:
        raise UnreadableReply("bad feedback")
    met_by_id: Dict[str, bool] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("met"), bool):
            raise UnreadableReply("bad idea entry")
        if item["id"] in met_by_id:
            raise UnreadableReply("repeated idea")
        met_by_id[item["id"]] = item["met"]
    if set(met_by_id) != {i.id for i in rubric_ideas}:
        raise UnreadableReply("ideas do not match the rubric")
    results = [IdeaResult(id=i.id, text=i.text, met=met_by_id[i.id]) for i in rubric_ideas]
    return results, feedback.strip()


def judged(results: List[IdeaResult], feedback: str, model: Optional[str]) -> AiJudgement:
    return AiJudgement(
        status="judged", verdict=verdict_for(results), ideas=results, feedback=feedback, model=model or "unknown"
    )


__all__ = [
    "AiJudgement",
    "CONCEPT_CHECK_WRITES_EVIDENCE",
    "Idea",
    "IdeaResult",
    "NOT_JUDGED_MESSAGES",
    "Rubric",
    "RubricError",
    "UnreadableReply",
    "judged",
    "not_judged",
    "parse_rubric",
    "validate_reply",
    "verdict_for",
]
