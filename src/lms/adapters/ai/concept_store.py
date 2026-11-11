"""Concept Store and Markdown Concept Ingestor for AXIS AI RAG Grounding.

Reads proprietary curriculum concept notes, transforms them into canonical Source
objects with licensing provenance, and deterministically chunks paragraphs into
verifiable Passage slices.
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from lms.core.rag_contracts import (
    Passage,
    Source,
    Span,
    content_sha256,
    make_passages,
    normalize_text,
)


class ConceptStore:
    """In-memory store of canonical curriculum Sources and verifiable Passages."""

    def __init__(self, chunker_version: str = "paragraph-v1") -> None:
        self.chunker_version = chunker_version
        self._sources: Dict[str, Source] = {}
        self._passages: Dict[str, List[Passage]] = {}

    def ingest_file(self, file_path: Path) -> Source:
        raw_bytes = file_path.read_bytes()
        raw_hash = content_sha256(raw_bytes.decode("utf-8", errors="replace"))

        raw_text = file_path.read_text(encoding="utf-8")
        canonical_text = normalize_text(raw_text)

        # Parse frontmatter if present
        source_id = f"concepts/{file_path.stem}"
        version = "v1.0.0"
        licence = "Proprietary-LMS"
        licence_basis = "declared"

        if canonical_text.startswith("---\n"):
            parts = canonical_text.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                for line in frontmatter.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if k == "source_id":
                            source_id = v
                        elif k == "version":
                            version = v
                        elif k == "licence":
                            licence = v

        source = Source(
            source_id=source_id,
            version=version,
            text=canonical_text,
            raw_sha256=raw_hash,
            loader_version="1.0",
            licence=licence,
            licence_basis=licence_basis,
        )

        # Chunk paragraphs into spans
        spans = self._extract_paragraph_spans(canonical_text)
        passages = make_passages(source, spans, chunker_version=self.chunker_version)

        self._sources[source_id] = source
        self._passages[source_id] = passages
        return source

    def _extract_paragraph_spans(self, text: str) -> List[Span]:
        """Extract paragraph slices as deterministic Spans."""
        spans: List[Span] = []
        # Find paragraphs separated by double newlines
        current_headings: Tuple[str, ...] = ()

        start = 0

        for para in re.split(r"\n\s*\n", text):
            cleaned = para.strip()
            if not cleaned or cleaned.startswith("---"):
                start = text.find(para, start) + len(para)
                continue

            para_start = text.find(para, start)
            para_end = para_start + len(para)

            # Check if this paragraph is a markdown header
            if cleaned.startswith("#"):
                heading_text = cleaned.lstrip("#").strip()
                current_headings = (heading_text,)

            spans.append(Span(start=para_start, end=para_end, headings=current_headings))
            start = para_end

        return spans

    def ingest_directory(self, dir_path: Path) -> int:
        """Ingest all markdown concept files from a directory."""
        count = 0
        if not dir_path.exists():
            return 0
        for md_file in dir_path.rglob("*.md"):
            self.ingest_file(md_file)
            count += 1
        return count

    def get_source(self, source_id: str) -> Optional[Source]:
        return self._sources.get(source_id)

    def get_passages(self, source_id: str) -> List[Passage]:
        return self._passages.get(source_id, [])

    def list_all_sources(self) -> List[Source]:
        return list(self._sources.values())
