"""Streams an AXIS reply as events, keeping the Socratic boundary while it streams.

Governed by SPEC-12 section 8 and ADR-0009. In Socratic mode text is held back until
a sentence or line is complete and has been checked, so no code fragment reaches the
learner first. Other modes stream as the model writes.
"""

import re
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from lms.adapters.ai import passage_safety
from lms.adapters.ai.socratic_guardrail import (
    GUIDING_INQUIRY,
    PROMPT_TAG_NAMES,
    REFLECTION_PROMPT,
    AssistanceClassifier,
    SocraticGuardrail,
    remove_prompt_tags,
)
from lms.core.interfaces import AxisMode, AxisQuery

_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n")
_FENCES = ("```", "~~~")

# The shape make_passage_id gives: source@version#cstart-end~digest.
_PASSAGE_ID = re.compile(r"^(?P<source>[^@]+)@[^#]+#c\d+-\d+~[0-9a-f]+$")

_SOURCE_NAMES = {
    "dspy-docs": "DSPy docs",
    "fastapi-docs": "FastAPI docs",
    "generative-ai-for-beginners": "Generative AI for Beginners",
    "httpx-docs": "HTTPX docs",
    "huggingface-course": "Hugging Face course",
    "llamaindex-docs": "LlamaIndex docs",
    "llms-from-scratch": "LLMs from Scratch",
    "openai-evals": "OpenAI Evals",
    "prompt-engineering-guide": "Prompt Engineering Guide",
    "pydantic-docs": "Pydantic docs",
    "pytest-docs": "pytest docs",
    "python-docs": "Python docs",
    "ruff-docs": "Ruff docs",
    "uv-docs": "uv docs",
    "zed-docs": "Zed docs",
}


def _readable(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").strip().capitalize()


def citation_title(cited: str) -> Optional[str]:
    """A readable source name for a retrieved passage id; None for anything else."""
    match = _PASSAGE_ID.match(cited)
    if not match:
        return None
    collection, *folders, file_name = match["source"].split("/")
    source = _SOURCE_NAMES.get(collection, _readable(collection))
    stem = PurePosixPath(file_name).stem
    page = stem
    if stem.lower() in ("index", "readme"):
        page = folders[-1] if folders else ""
    elif stem.isdigit() and folders:
        page = f"{folders[-1]} {stem}"
    return f"{source}: {_readable(page)}" if page else source


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


def _could_become_tag(tail: str) -> bool:
    """True when `tail` (starting at a "<") may still grow into one of our prompt tags."""
    lowered = tail.lower()
    bare = lowered.lstrip("<").lstrip("/")
    if any(name.startswith(bare) for name in PROMPT_TAG_NAMES):
        return True
    return any(
        lowered.startswith(f"<{name}") or lowered.startswith(f"</{name}")
        for name in PROMPT_TAG_NAMES
    ) and ">" not in lowered


def strip_prompt_tags(deltas: Iterable[str]) -> Iterator[str]:
    """Remove echoed prompt tags, even when a tag is split across deltas."""
    held = ""
    for delta in deltas:
        held = remove_prompt_tags(held + delta)
        # Keep back only text that could still become a tag.
        start = held.rfind("<")
        possible = start >= 0 and _could_become_tag(held[start:])
        ready, held = (held[:start], held[start:]) if possible else (held, "")
        if ready:
            yield ready
    if held:
        yield held


def stream_axis(
    axis: Any,
    query: AxisQuery,
    guardrail: SocraticGuardrail,
    classifier: AssistanceClassifier,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Yield (event, data) pairs: tokens, then citations, then done."""
    deltas, cited = axis.stream(query)
    grounding = cited if isinstance(cited, passage_safety.Grounding) else None
    gate = SocraticStreamFilter(guardrail) if query.mode == AxisMode.SOCRATIC else None
    sent: List[str] = []

    clean_deltas = strip_prompt_tags(deltas)
    if grounding is not None:
        clean_deltas = passage_safety.strip_unknown_labels_stream(clean_deltas, grounding.labels)
    for delta in clean_deltas:
        for chunk in gate.feed(delta) if gate else [delta]:
            sent.append(chunk)
            yield "token", {"text": chunk}
    if gate:
        for chunk in gate.finish():
            sent.append(chunk)
            yield "token", {"text": chunk}

    if grounding is not None:
        cited = grounding.cited_for("".join(sent))  # from the finished reply (SPEC-22 R6, R7)
    for concept in cited:
        yield "citation", {"name": concept}

    assistance = classifier.classify(query.user_prompt, "".join(sent), query.mode)
    yield "done", {"assistance_level": assistance.value, "cited_concepts": cited}
