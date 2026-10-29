"""The shared data contract for curriculum knowledge ingestion and passage verification.

Adopted directly from rag-core (ADR 0003) to ensure zero impedance mismatch:
- A Source is one loaded document: its canonical text plus provenance and license metadata.
- A Span specifies where a slice sits inside a Source's text.
- A Passage is an exact slice of a Source's text with verifiable IDs.

Enforces:
1. Canonical text: normalize_text(text) == text.
2. Passage text is exactly source.text[start:end] and non-blank.
3. passage_id is derived from all definition inputs including chunker_version.
4. Objects are immutable and self-validating on construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import List, Tuple
import unicodedata

SCHEMA_VERSION = 1
NORMALIZER_VERSION = 1

LICENCE_BASES = ("detected", "declared", "unknown")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """Raised when data breaks the RAG contract."""


def normalize_text(text: str) -> str:
    """Canonical text: no leading BOM, Unicode NFC, '\\n' line endings. Idempotent."""
    text = text.removeprefix("\ufeff")
    text = unicodedata.normalize("NFC", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def content_sha256(text: str) -> str:
    """SHA-256 (hex) of the UTF-8 bytes of canonical text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_passage_id(
    source_id: str,
    version: str,
    start: int,
    end: int,
    text_hash: str,
    chunker_version: str,
) -> str:
    """Deterministic, positional ID: a readable prefix plus a digest of everything defining the passage."""
    digest = hashlib.sha256(
        "\0".join([source_id, version, str(start), str(end), text_hash, chunker_version]).encode(
            "utf-8"
        )
    ).hexdigest()[:12]
    return f"{source_id}@{version[:8]}#c{start}-{end}~{digest}"


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must not be empty")


@dataclass(frozen=True)
class Source:
    source_id: str
    version: str  # Commit or content hash
    text: str  # Canonical text
    raw_sha256: str  # Hash of the input file as read
    loader_version: str
    licence: str  # SPDX identifier, or "Proprietary-LMS", or "unknown"
    licence_basis: str  # detected / declared / unknown
    normalizer_version: int = NORMALIZER_VERSION
    schema_version: int = SCHEMA_VERSION
    text_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for name in ("source_id", "version", "loader_version", "licence"):
            _require_text(getattr(self, name), name)
        if not _HEX64.match(self.raw_sha256):
            raise ContractError("raw_sha256 must be 64 lowercase hex characters")
        if self.licence_basis not in LICENCE_BASES:
            raise ContractError(
                f"licence_basis must be one of {LICENCE_BASES}, got {self.licence_basis!r}"
            )
        if normalize_text(self.text) != self.text:
            raise ContractError(
                "text is not normalized: pass the loader output through normalize_text"
            )
        object.__setattr__(self, "text_sha256", content_sha256(self.text))


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    headings: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ContractError(f"span must satisfy 0 <= start < end, got {self.start}..{self.end}")


@dataclass(frozen=True)
class Passage:
    source_id: str
    version: str
    start: int
    end: int
    text: str
    headings: Tuple[str, ...]
    chunker_version: str
    passage_id: str
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        _require_text(self.chunker_version, "chunker_version")
        if not self.text.strip():
            raise ContractError("passage text is blank")
        content = content_sha256(self.text)
        expected = make_passage_id(
            self.source_id, self.version, self.start, self.end, content, self.chunker_version
        )
        if self.passage_id != expected:
            raise ContractError(
                f"passage_id {self.passage_id!r} does not match the passage (expected {expected!r})"
            )
        object.__setattr__(self, "content_id", content)


def make_passages(source: Source, spans: List[Span], *, chunker_version: str) -> List[Passage]:
    """Passages that are exact slices of source.text, with IDs filled in."""
    _require_text(chunker_version, "chunker_version")
    passages: List[Passage] = []
    for span in spans:
        if span.end > len(source.text):
            raise ContractError(
                f"span {span.start}..{span.end} is outside the source text (length {len(source.text)})"
            )
        text = source.text[span.start : span.end]
        if not text.strip():
            raise ContractError(f"span {span.start}..{span.end} is blank")
        passage_id = make_passage_id(
            source.source_id,
            source.version,
            span.start,
            span.end,
            content_sha256(text),
            chunker_version,
        )
        passages.append(
            Passage(
                source.source_id,
                source.version,
                span.start,
                span.end,
                text,
                span.headings,
                chunker_version,
                passage_id,
            )
        )
    return passages


def verify_passage(source: Source, passage: Passage) -> bool:
    """Read-back check: the passage belongs to this source version and its text is exactly the slice."""
    return (
        passage.source_id == source.source_id
        and passage.version == source.version
        and passage.end <= len(source.text)
        and source.text[passage.start : passage.end] == passage.text
    )
