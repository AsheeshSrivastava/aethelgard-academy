"""Streams an AXIS reply as events, keeping the Socratic boundary while it streams.

Governed by SPEC-12 section 8 and ADR-0009. In Socratic mode text is held back until
a sentence or line is complete and has been checked, so no code fragment reaches the
learner first. Other modes stream as the model writes.
"""

import re
from typing import Any, Dict, Iterator, List, Tuple

from lms.adapters.ai.socratic_guardrail import (
    GUIDING_INQUIRY,
    REFLECTION_PROMPT,
    AssistanceClassifier,
    SocraticGuardrail,
)
from lms.core.interfaces import AxisMode, AxisQuery

_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n")
_FENCES = ("```", "~~~")


class SocraticStreamFilter:
    """Releases only complete sentences that hold no code."""

    def __init__(self, guardrail: SocraticGuardrail):
        self.guardrail = guardrail
        self._buffer = ""
        self._in_fence = False
        self._withheld = False
        self._released = ""

    def feed(self, delta: str) -> List[str]:
        self._buffer += delta
        out: List[str] = []
        while True:
            match = _BOUNDARY.search(self._buffer)
            if match is None:
                return out
            chunk, self._buffer = self._buffer[: match.end()], self._buffer[match.end() :]
            out.extend(self._check(chunk))

    def finish(self) -> List[str]:
        out = self._check(self._buffer)
        self._buffer = ""
        if self._withheld:
            out.append(GUIDING_INQUIRY)
            self._released += GUIDING_INQUIRY
        if "?" not in self._released:
            out.append(REFLECTION_PROMPT)
            self._released += REFLECTION_PROMPT
        return out

    def _check(self, chunk: str) -> List[str]:
        fences = sum(chunk.count(fence) for fence in _FENCES)
        if fences:
            self._withheld = True
            if fences % 2:
                self._in_fence = not self._in_fence
            return []
        if self._in_fence or self.guardrail.contains_code(chunk):
            self._withheld = True
            return []
        if not chunk:
            return []
        self._released += chunk
        return [chunk]


def stream_axis(
    axis: Any,
    query: AxisQuery,
    guardrail: SocraticGuardrail,
    classifier: AssistanceClassifier,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Yield (event, data) pairs: tokens, then citations, then done."""
    deltas, cited = axis.stream(query)
    gate = SocraticStreamFilter(guardrail) if query.mode == AxisMode.SOCRATIC else None
    sent: List[str] = []

    for delta in deltas:
        for chunk in gate.feed(delta) if gate else [delta]:
            sent.append(chunk)
            yield "token", {"text": chunk}
    if gate:
        for chunk in gate.finish():
            sent.append(chunk)
            yield "token", {"text": chunk}

    for concept in cited:
        yield "citation", {"name": concept}

    assistance = classifier.classify(query.user_prompt, "".join(sent), query.mode)
    yield "done", {"assistance_level": assistance.value, "cited_concepts": cited}
