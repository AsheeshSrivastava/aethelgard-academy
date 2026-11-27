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
    code_spans,
    follow_up_for,
    learner_text_of,
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


def _next_cut(buffer: str, final: bool) -> Optional[int]:
    """Where the first complete sentence or line of `buffer` ends, or None to wait for more text.

    A sentence is not cut inside a backtick span (SPEC-31 9.7 reading 2). After a backtick that nothing has closed
    yet, a sentence end waits until the line is complete: the span may still close.
    """
    newline = buffer.find("\n")
    spans, unclosed = code_spans(buffer if newline < 0 else buffer[:newline])
    for match in _BOUNDARY.finditer(buffer):
        at = match.start()
        if buffer[at] != "\n":
            if any(start < at < end for start, _inner, _inner_end, end in spans):
                continue
            if newline < 0 and not final and any(start < at for start in unclosed):
                return None
        return match.end()
    return None


class SocraticStreamFilter:
    """Releases only complete sentences that hold no code."""

    def __init__(self, guardrail: SocraticGuardrail, learner_text: str = "", reflect: bool = True):
        self.reflect = reflect
        self.guardrail = guardrail
        self.learner_text = learner_text
        self._buffer = ""
        self._in_fence = False
        self._withheld = False
        self._released = ""

    def feed(self, delta: str) -> List[str]:
        self._buffer += delta
        return self._drain(final=False)

    def finish(self) -> List[str]:
        out = self._drain(final=True)
        out.extend(self._check(self._buffer))
        self._buffer = ""
        if self._withheld:
            out.append(GUIDING_INQUIRY)
            self._released += GUIDING_INQUIRY
        if self.reflect and "?" not in self._released:
            out.append(REFLECTION_PROMPT)
            self._released += REFLECTION_PROMPT
        return out

    def _drain(self, final: bool) -> List[str]:
        out: List[str] = []
        while True:
            cut = _next_cut(self._buffer, final)
            if cut is None:
                return out
            chunk, self._buffer = self._buffer[:cut], self._buffer[cut:]
            out.extend(self._check(chunk))

    def _holds_code(self, chunk: str) -> bool:
        if self.guardrail.contains_code(chunk, learner_text=self.learner_text):
            return True
        # A chunk kept whole around a span is still read sentence by sentence, so a span the learner did not write
        # cannot carry a code line past the check by sharing its chunk with the sentence before.
        masked = self.guardrail.mask_learner_spans(chunk, self.learner_text)
        return any(self.guardrail.contains_code(piece) for piece in _BOUNDARY.split(masked) if piece)

    def _check(self, chunk: str) -> List[str]:
        fences = sum(chunk.count(fence) for fence in _FENCES)
        if fences:
            self._withheld = True
            if fences % 2:
                self._in_fence = not self._in_fence
            return []
        if self._in_fence or self._holds_code(chunk):
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
    no_source = grounding is not None and grounding.source_state != "course"
    gate = None
    if query.mode == AxisMode.SOCRATIC:
        gate = SocraticStreamFilter(guardrail, learner_text_of(query), reflect=not no_source)
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
    if no_source:  # after the classifier: a fixed question is not help (SPEC-24 R21)
        line = follow_up_for("".join(sent))
        if line:
            sent.append(line)
            yield "token", {"text": line}
    done: Dict[str, Any] = {"assistance_level": assistance.value, "cited_concepts": cited}
    if grounding is not None:
        done["source_state"] = grounding.source_state  # SPEC-24 R9: server data, never the model's words
        if grounding.downgraded:
            done["retrieval_downgraded"] = True  # SPEC-27 R6: the learner sees "Keyword search only"
    yield "done", done
