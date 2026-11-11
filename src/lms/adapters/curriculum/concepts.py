"""Concept Library catalog: Markdown notes from curriculum/concepts/ (SPEC-14).

A bad note is reported as a finding and skipped; it never stops the app.
"""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError
import yaml

from lms.adapters.curriculum.builds import curriculum_dir_from_env
from lms.core.concepts import SLUG, rank_concepts
from lms.core.curriculum_checks import Finding, Severity
from lms.core.models import ConceptItem


_REQUIRED = ("id", "title", "category", "summary", "status")
_LISTS = ("units", "related", "aliases")
_OPTIONAL = (*_LISTS, "doc_url")
_NOTE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*\n(.*)$", re.S)


class ConceptError(ValueError):
    """Says what is wrong with a note."""


def _frontmatter(raw: str) -> Tuple[Dict[str, Any], str]:
    match = _NOTE.match(raw)
    if not match:
        raise ConceptError("no frontmatter between --- lines")
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise ConceptError(f"frontmatter is not valid YAML: {error}") from error
    if not isinstance(meta, dict):
        raise ConceptError("frontmatter must be key: value lines")
    return meta, match.group(2).strip()


def parse_note(path: Path) -> ConceptItem:
    meta, body = _frontmatter(path.read_text(encoding="utf-8"))

    unknown = sorted(str(key) for key in set(meta) - set(_REQUIRED) - set(_OPTIONAL))
    if unknown:
        raise ConceptError(f"unknown field: {', '.join(unknown)}")
    for field in _REQUIRED:
        value = meta.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ConceptError(f"{field} is required and must be text")
    for field in _LISTS:
        value = meta.get(field, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ConceptError(f"{field} must be a list of text")

    slug = meta["id"]
    if not SLUG.match(slug):
        raise ConceptError("id must be lowercase words joined by hyphens")
    if slug != path.stem:
        raise ConceptError(f"id '{slug}' must equal the file name")
    doc_url = meta.get("doc_url", "")
    if doc_url and not re.match(r"^https?://", str(doc_url), re.I):
        raise ConceptError("doc_url must start with http:// or https://")
    if not body:
        raise ConceptError("the body is empty")

    try:
        return ConceptItem(
            concept_id=slug,
            name=meta["title"],
            category=meta["category"],
            summary=meta["summary"],
            status=meta["status"],
            units=meta.get("units", []),
            related=meta.get("related", []),
            aliases=meta.get("aliases", []),
            doc_url=doc_url,
            content_markdown=body,
        )
    except ValidationError as error:
        raise ConceptError("status must be draft or approved") from error


def load_concepts(concepts_dir: Path) -> Tuple[List[ConceptItem], List[Finding]]:
    """Load every note in the folder, A to Z by file name."""
    items: List[ConceptItem] = []
    problems: List[Finding] = []
    for path in sorted(concepts_dir.glob("*.md")):
        try:
            items.append(parse_note(path))
        except ValueError as error:  # ConceptError, and UnicodeDecodeError for a bad file
            problems.append(
                Finding(severity=Severity.ERROR, code="concept-invalid", message=f"{path.name}: {error}")
            )
    return items, problems


class ConceptCatalog:
    """In-memory searchable registry of concept notes."""

    def __init__(self, concepts_dir: Optional[Path] = None):
        items, self.findings = load_concepts(concepts_dir or curriculum_dir_from_env(Path("curriculum")) / "concepts")
        self._concepts = sorted(items, key=lambda c: c.name.lower())

    def list_all(self) -> List[ConceptItem]:
        return list(self._concepts)

    def search(self, query: str) -> List[ConceptItem]:
        return rank_concepts(self._concepts, query)

    def get(self, concept_id: str) -> Optional[ConceptItem]:
        return next((c for c in self._concepts if c.concept_id == concept_id), None)
