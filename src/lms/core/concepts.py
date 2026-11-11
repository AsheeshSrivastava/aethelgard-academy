"""Concept Library rules: search ranking, wiki links and their checks.

Governed by SPEC-14. Deterministic and pure: concepts and units in, results out.
"""

import re
from typing import List, Optional, Sequence

from lms.core.course_map import course_of
from lms.core.curriculum_checks import Finding, Severity
from lms.core.models import ConceptItem, ConceptUnitRef, Unit

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

_FENCED_CODE = re.compile(r"^\s*(```|~~~).*?(^\s*\1\s*$|\Z)", re.M | re.S)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
# The label is split off by a pipe, written as \| inside a Markdown table.
_WIKI_LINK = re.compile(r"\[\[([^\]\n|\\]+)(?:\\?\|[^\]\n]*)?\]\]")
_WORD = re.compile(r"[a-z0-9_]+")

_NO_MATCH = 7


def wiki_links(markdown: str) -> List[str]:
    """Every slug linked from the text, as written, leaving code out."""
    text = _INLINE_CODE.sub("", _FENCED_CODE.sub("", markdown))
    return [match.strip() for match in _WIKI_LINK.findall(text)]


def _matcher(query: str):
    words = _WORD.findall(query)
    if words:
        return lambda field: all(word in field for word in words)
    return lambda field: query in field


def _rank(concept: ConceptItem, query: str, matches) -> int:
    title = concept.name.lower()
    if title == query:
        return 1
    if title.startswith(query):
        return 2
    if matches(title):
        return 3
    if any(matches(alias.lower()) for alias in concept.aliases):
        return 4
    if matches(concept.summary.lower()):
        return 5
    if matches((concept.content_markdown or "").lower()):
        return 6
    return _NO_MATCH


def rank_concepts(concepts: Sequence[ConceptItem], query: str) -> List[ConceptItem]:
    """SPEC-14 section 4: best field first, then title A to Z. Nothing for a blank query."""
    cleaned = query.lower().strip()
    if not cleaned:
        return []
    matches = _matcher(cleaned)
    scored = [(_rank(c, cleaned, matches), c.name.lower(), c) for c in concepts]
    return [c for rank, _, c in sorted(scored, key=lambda s: s[:2]) if rank < _NO_MATCH]


def used_in(concept: ConceptItem, units: Sequence[Unit]) -> List[ConceptUnitRef]:
    """Units that name the concept or link to it, in the order given."""
    return [
        ConceptUnitRef(unit_id=unit.unit_id, title=unit.title)
        for unit in units
        if unit.unit_id in concept.units
        or concept.concept_id in wiki_links(unit.lesson_markdown or "")
    ]


def check_concept_links(concepts: Sequence[ConceptItem], units: Sequence[Unit]) -> List[Finding]:
    """SPEC-14 section 3.1."""
    slugs = {c.concept_id for c in concepts}
    unit_ids = {u.unit_id for u in units}

    def error(code: str, message: str, unit: Optional[Unit] = None) -> Finding:
        return Finding(
            severity=Severity.ERROR,
            code=code,
            message=message,
            unit_id=unit.unit_id if unit else None,
            course_id=course_of(unit.unit_id) if unit else None,
            stage=unit.stage if unit else None,
        )

    findings: List[Finding] = []
    for unit in units:
        for slug in wiki_links(unit.lesson_markdown or ""):
            if slug not in slugs:
                findings.append(
                    error("concept-link-broken", f"{unit.unit_id} lesson links to unknown concept '{slug}'.", unit)
                )
    for concept in concepts:
        source = f"{concept.concept_id}.md"
        for slug in wiki_links(concept.content_markdown or ""):
            if slug not in slugs:
                findings.append(error("concept-link-broken", f"{source} links to unknown concept '{slug}'."))
        for slug in concept.related:
            if slug not in slugs:
                findings.append(error("concept-related-unknown", f"{source}: related names unknown concept '{slug}'."))
        for unit_id in concept.units:
            if unit_id not in unit_ids:
                findings.append(error("concept-unit-unknown", f"{source}: units names unknown unit '{unit_id}'."))
    return findings
