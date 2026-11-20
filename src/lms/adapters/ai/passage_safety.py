"""Safe use of retrieved text (SPEC-22, ADR-0035 section 2.5).

Retrieved passages are untrusted data. This module cleans them, caps them, fences them in one
labelled block, removes labels the model invented, and decides which passages a reply really used.
It has no model and no network call, so every rule here is tested offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, List, Optional, Set, Tuple

from lms.adapters.ai.socratic_guardrail import PROMPT_TAG_PATTERN
from lms.core import tracing

MAX_PASSAGE_CHARS = 1200
MAX_PASSAGES_TOTAL_CHARS = 3600
MAX_SOURCE_NAME_CHARS = 120
MIN_USEFUL_CHARS = 40  # a passage squeezed below this by the total cap is dropped
CITATION_MIN_RUN = 4

_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
_WORD = re.compile(r"\w+")
_LABEL = re.compile(r"(?P<ws>[ \t]?)(?P<br>\[(?P<n>\d+)\])")
_LABEL_ANY = re.compile(r"\[\d+\]")
_PARTIAL_LABEL = re.compile(r"[ \t]?(?:\[\d*)?$")


def clean_text(text: str) -> str:
    """Remove our prompt tags (any case, with or without attributes) and control characters.

    Tags are removed until none is left, so text such as `<pas<passage>sage>` cannot rebuild one.
    """
    text = _CONTROL.sub("", text)
    while True:
        stripped = PROMPT_TAG_PATTERN.sub("", text)
        if stripped == text:
            return text
        text = stripped


def _clean_name(name: str) -> str:
    one_line = " ".join(clean_text(name).split())
    safe = one_line.replace('"', "").replace("<", "").replace(">", "")
    return safe[:MAX_SOURCE_NAME_CHARS]


def _cut(text: str, limit: int) -> str:
    """At most `limit` characters, cut at a word boundary, with an ellipsis when cut."""
    if len(text) <= limit:
        return text
    head = text[:limit]
    if not text[limit].isspace() and not head[-1].isspace() and " " in head.strip():
        head = head.rsplit(None, 1)[0]
    return head.rstrip() + "…"


@dataclass(frozen=True)
class Entry:
    label: str
    passage_id: str
    source_name: str
    text: str


@dataclass
class Grounding:
    """The passages shown to the model this turn, and what the reply later used."""

    entries: List[Entry] = field(default_factory=list)
    trace: Optional[Any] = None  # RetrievalTrace; passages_cited is written when a reply is checked

    @property
    def block(self) -> str:
        if not self.entries:
            return ""
        rows = [f'<passage label="{e.label}" source="{e.source_name}">{e.text}</passage>' for e in self.entries]
        return "<reference_passages>\n" + "\n".join(rows) + "\n</reference_passages>"

    @property
    def source_state(self) -> str:
        """What the learner should know about this turn's source (SPEC-24 R9).

        "course" when at least one passage reached the model, else why none did.
        """
        if self.entries:
            return "course"
        status = getattr(self.trace, "status", None)
        if status in ("no_index", "unavailable"):
            return status
        if self.trace is None:
            return "no_index"  # nothing was searched, so there was no reference to check against
        return "not_found"

    @property
    def downgraded(self) -> bool:
        """True when the ranking models were not used for this turn: shown as "Keyword search only" (SPEC-27 R6)."""
        return bool(getattr(self.trace, "downgraded", False))

    @property
    def ids(self) -> List[str]:
        return [e.passage_id for e in self.entries]

    @property
    def labels(self) -> Set[str]:
        return {e.label for e in self.entries}

    def cited_for(self, reply: str) -> List[str]:
        """Ids of the passages the reply shares a run of CITATION_MIN_RUN words with (SPEC-22 R6)."""
        with tracing.span("citation_check") as sp:
            reply_runs = _runs(_LABEL_ANY.sub(" ", reply))
            cited = [e.passage_id for e in self.entries if reply_runs & _runs(e.text)]
            if self.trace is not None:
                self.trace.passages_cited = len(cited)
            sp.set(passages_cited=len(cited), cited_passage_ids=cited[: tracing.MAX_REFS])
        return cited


def _runs(text: str) -> Set[Tuple[str, ...]]:
    words = _WORD.findall(text.lower())
    n = CITATION_MIN_RUN
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def build_grounding(items: Iterable[Tuple[str, str, str]], trace: Optional[Any] = None) -> Grounding:
    """items are (passage_id, readable source name, text), best first. Cleaned, capped, numbered."""
    entries: List[Entry] = []
    remaining = MAX_PASSAGES_TOTAL_CHARS
    for passage_id, name, raw_text in items:
        text = clean_text(raw_text).strip()
        if not text or remaining < MIN_USEFUL_CHARS:
            continue
        text = _cut(text, min(MAX_PASSAGE_CHARS, remaining))
        remaining -= len(text)
        entries.append(Entry(str(len(entries) + 1), passage_id, _clean_name(name), text))
    return Grounding(entries, trace)


def _label_sub(text: str, valid: Set[str]):
    def sub(m: "re.Match[str]") -> str:
        n = m.group("n")
        if n == "0" or n in valid:
            return m.group(0)
        if not m.group("ws"):
            start = m.start("br")
            if start > 0 and (text[start - 1].isalnum() or text[start - 1] in "_)]"):
                return m.group(0)  # indexing such as items[3] or m[1][2], not a label
        return ""

    return sub


def strip_unknown_labels(text: str, valid: Set[str]) -> str:
    """Remove [n] labels that do not belong to a passage shown this turn (SPEC-22 R5)."""
    return _LABEL.sub(_label_sub(text, valid), text)


def strip_unknown_labels_stream(deltas: Iterable[str], valid: Set[str]) -> Iterator[str]:
    """The same removal for text that arrives in pieces; a possible label start is held back."""
    held, prev = "", ""
    for delta in deltas:
        buf = held + delta
        tail = _PARTIAL_LABEL.search(buf)
        cut = tail.start() if tail else len(buf)
        ready, held = buf[:cut], buf[cut:]
        out = _emit(prev, ready, valid)
        if ready:
            prev = ready[-1]  # the original character, so the indexing rule matches the whole-text version
        if out:
            yield out
    out = _emit(prev, held, valid)
    if out:
        yield out


def _emit(prev: str, ready: str, valid: Set[str]) -> str:
    if not ready:
        return ""
    joined = prev + ready
    return strip_unknown_labels(joined, valid)[len(prev):]
