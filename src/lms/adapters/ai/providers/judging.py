"""Judging a written explanation with one companion (SPEC-18 sections 3 and 4).

A companion's `judge(unit_id, prompt, explanation, ideas)` returns the model's raw reply
and the model that answered, or raises. Here the failure is named by class only, the reply
is checked, and the verdict is decided by code. There is no keyword fallback.
"""

from __future__ import annotations

import logging
from typing import Any

from lms.adapters.ai.providers.metering import BudgetExceeded
from lms.core.ai_judgement import (
    AiJudgement,
    Rubric,
    UnreadableReply,
    judged,
    not_judged,
    validate_reply,
)

logger = logging.getLogger(__name__)

REFUSED_STATUS = {401, 403, 429}
REFUSED_CLASSES = {"AuthenticationError", "PermissionDeniedError", "RateLimitError"}


def _status_of(exc: BaseException) -> Any:
    for name in ("status_code", "code"):
        value = getattr(exc, name, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def classify_failure(exc: BaseException) -> str:
    """The SPEC-18 section 4 reason for a failed call. Only the class and status are looked at."""
    if isinstance(exc, BudgetExceeded):
        return "cap_reached"
    if type(exc).__name__ in REFUSED_CLASSES or _status_of(exc) in REFUSED_STATUS:
        return "provider_refused"
    return "no_answer"


def judge_with(companion: Any, unit_id: str, prompt: str, explanation: str, rubric: Rubric) -> AiJudgement:
    """Judge with this companion. Never raises: every failure becomes a not-judged result."""
    try:
        raw, model = companion.judge(unit_id, prompt, explanation, rubric.ideas)
    except Exception as exc:
        # The provider's own text can echo a key, so only the class name is kept.
        logger.warning("Judging call failed: %s", type(exc).__name__)
        return not_judged(classify_failure(exc))
    try:
        results, feedback = validate_reply(raw, rubric.ideas)
    except UnreadableReply:
        logger.warning("Judging reply could not be read.")
        return not_judged("unreadable_reply")
    return judged(results, feedback, model)
