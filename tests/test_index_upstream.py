"""Unit and integration tests for persistent upstream indexing and warm retriever loader.

Governed by:
- ADR-0012: Persistent RAG Artifacts & Upstream Documentation Indexer
- SPEC-10: Persistent Upstream Indexer & Warm Retriever Loader
"""

import json
from pathlib import Path
import pytest

from lms.adapters.ai.rag.indexer import CorpusIndexer
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.core.rag_contracts import Source, content_sha256, normalize_text, verify_passage


SAMPLE_MD = """# FastAPI Guide

FastAPI is a modern web framework for Python.
It provides automatic OpenAPI documentation.

## Dependency Injection

Dependencies in FastAPI are declared using `Depends()`.
This allows sharing database sessions across routes.
"""

SAMPLE_MD_2 = """# Pydantic Schemas

Pydantic models define schema boundaries, data transformation pipelines,
and runtime data validation for Python applications and APIs.
"""



def test_corpus_indexer_builds_and_saves_index(tmp_path: Path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    doc1 = corpus_dir / "fastapi.md"
    doc1.write_text(SAMPLE_MD, encoding="utf-8")
    doc2 = corpus_dir / "pydantic.md"
    doc2.write_text(SAMPLE_MD_2, encoding="utf-8")

    index_dir = tmp_path / "index"

    indexer = CorpusIndexer(corpus_dir=corpus_dir, output_dir=index_dir)
    stats = indexer.build_and_save()

    assert stats["source_count"] == 2
    assert stats["passage_count"] >= 2

    # Verify generated files
    assert (index_dir / "passages.jsonl").exists()
    assert (index_dir / "sources.jsonl").exists()
    assert (index_dir / "bm25.json").exists()

    # Load into HybridRerankedRetriever
    retriever = HybridRerankedRetriever.load(index_dir)
    assert len(retriever.passages) == stats["passage_count"]
    assert len(retriever.sources) == 2

    # Verify all passages mechanically verify
    for p in retriever.passages.values():
        source = retriever.sources[p.source_id]
        assert verify_passage(source, p) is True

    # Search query
    results = retriever.retrieve("Dependency Injection Depends", top_k=2)
    assert len(results) >= 1
    assert "fastapi.md" in results[0].source_id
    assert "Depends()" in results[0].text


def test_cli_index_upstream_handler(tmp_path: Path):
    from lms.cli import handle_index_upstream_command

    corpus_dir = tmp_path / "upstream"
    corpus_dir.mkdir()
    (corpus_dir / "test.md").write_text(
        "# Test Documentation\n\nThis is a sufficiently long document to pass the minimum character inspection gate for testing indexing.",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out_idx"

    res = handle_index_upstream_command(corpus_dir=corpus_dir, output_dir=out_dir)
    assert res["success"] is True
    assert res["source_count"] == 1
    assert (out_dir / "passages.jsonl").exists()
