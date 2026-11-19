"""Search-only text for keyword search (SPEC-26, ADR-0035 5.2a).

Extra words that go into the BM25 bag of words of a passage, taken only from fields the index already
holds: the source id (path words) and the page title. They are never stored on the passage, never shown
to the learner, never put in the prompt and never cited (R4). Pure functions, no vendor import (R1).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from lms.core.rag_contracts import Passage

# Changing how the words are made changes what the index finds, so it changes index_version (R6).
SEARCH_TEXT_VERSION = "1"
DEFAULT_RECIPE = "none"

_WORD_RE = re.compile(r"[A-Za-z0-9_\-\.:]+")  # the same shape of word the BM25 index reads
_SPLIT_RE = re.compile(r"[-_.]+")
_DOC_SUFFIXES = (".md", ".mdx", ".rst", ".txt", ".ipynb", ".html", ".htm")


@dataclass(frozen=True)
class Recipe:
    path: bool
    title: bool
    times: int  # how often the block of extra words is repeated (term frequency)


# R5: V0 .. V4
SEARCH_TEXT_RECIPES: Dict[str, Recipe] = {
    "none": Recipe(False, False, 0),
    "path": Recipe(True, False, 1),
    "title": Recipe(False, True, 1),
    "path_title": Recipe(True, True, 1),
    "path_title_x2": Recipe(True, True, 2),
}


def _dedupe(words: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for w in words:
        if w and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def path_words(source_id: str) -> List[str]:
    """R2: each path segment whole and split on - _ . ; lower case; no repeats; set prefix and extension dropped."""
    parts = [p for p in (source_id or "").lower().split("/") if p]
    if len(parts) > 1:
        parts = parts[1:]  # the first segment is the set (for example pytest-docs); a bare file name has none
    if parts:
        last = parts[-1]
        for suffix in _DOC_SUFFIXES:
            if last.endswith(suffix) and len(last) > len(suffix):
                parts[-1] = last[: -len(suffix)]
                break
    words: List[str] = []
    for segment in parts:
        words.append(segment)
        pieces = [x for x in _SPLIT_RE.split(segment) if x]
        if pieces != [segment]:
            words.extend(pieces)
    return _dedupe(words)


def _file_stem(source_id: str) -> str:
    last = (source_id or "").rsplit("/", 1)[-1]
    for suffix in _DOC_SUFFIXES:
        if last.lower().endswith(suffix) and len(last) > len(suffix):
            return last[: -len(suffix)]
    return last


def title_words(passage: Passage) -> List[str]:
    """The page title: the outermost heading of the passage's heading path, else the file name (SPEC-26 note 1)."""
    title = passage.headings[0] if passage.headings else _file_stem(passage.source_id)
    return _dedupe([w.lower() for w in _WORD_RE.findall(title)])


def search_text(passage: Passage, recipe: str = DEFAULT_RECIPE) -> str:
    """The extra words for this passage under `recipe`, space-joined ('' for recipe none). Raises ValueError on an unknown recipe."""
    try:
        spec = SEARCH_TEXT_RECIPES[recipe]
    except KeyError:
        raise ValueError(f"unknown search-text recipe '{recipe}'") from None
    words: List[str] = []
    if spec.path:
        words += path_words(passage.source_id)
    if spec.title:
        words += title_words(passage)
    block = " ".join(words)
    return " ".join([block] * spec.times) if block else ""
