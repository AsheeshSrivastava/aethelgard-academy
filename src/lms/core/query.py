"""Search-text cleanup (SPEC-23 R1, ADR-0035 section 2.8). Pure standard library.

The learner's question goes to the index as typed, minus function words. Nothing else is
removed or added: error-type extraction and path stripping were measured and did not help.
"""

from __future__ import annotations

import re
from typing import List

# The same split the BM25 index uses (adapters/ai/rag/bm25.py TOKEN_RE); a test keeps them equal.
TOKEN_PATTERN = r"[A-Za-z0-9_\-\.:]+"
_TOKEN = re.compile(TOKEN_PATTERN)

# Negations ("not", "no") stay: "did not raise" is not "did raise".
FUNCTION_WORDS = frozenset(
    "a an and are as at be but by can do does did for from how i if in into is it its me my of on or so "
    "than that the then there this to up was what when where which who why will with would you your "
    "should could am we they them our just also any some very".split()
)


def clean_query_words(text: str) -> List[str]:
    """Words of `text` without function words and repeats (case-insensitive), in first-seen order."""
    seen = set()
    words: List[str] = []
    for token in _TOKEN.findall(text or ""):
        key = token.lower()
        if key in FUNCTION_WORDS or key in seen:
            continue
        seen.add(key)
        words.append(token)
    return words


def clean_query(text: str) -> str:
    """The search text: `clean_query_words` joined by single spaces. Empty when nothing is left."""
    return " ".join(clean_query_words(text))
