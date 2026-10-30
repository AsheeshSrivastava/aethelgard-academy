"""Unit and contract tests for the RAG chunking and hybrid reranking pipeline.

Governed by:
- ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking
- SPEC-09: RAG Indexing & Hybrid Reranked Retriever
"""

import pytest
from lms.adapters.ai.rag.chunker import HeadingSentenceSplitter
from lms.adapters.ai.rag.bm25 import InvertedBM25Index
from lms.adapters.ai.rag.fusion import reciprocal_rank_fusion
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.core.rag_contracts import Source, verify_passage, normalize_text, content_sha256


SAMPLE_DOC = """# FastApi Overview

FastAPI is a modern, fast web framework for building APIs with Python.
It is based on standard Python type hints.

## Query Parameters

When you declare other function parameters that are not part of the path,
they are automatically interpreted as query parameters.
For example, `q: str = None` defines an optional string query parameter.

## Path Parameters

You can declare path parameters or variables with the Python format string syntax.
Path parameters are required and extracted directly from the URL.
"""


def test_heading_sentence_splitter_exact_slices():
    norm_text = normalize_text(SAMPLE_DOC)
    splitter = HeadingSentenceSplitter(max_chars=300)
    spans = splitter.split(norm_text)

    source = Source(
        source_id="fastapi/sample",
        version="1.0",
        text=norm_text,
        raw_sha256=content_sha256(norm_text),
        loader_version="1.0",
        licence="MIT",
        licence_basis="declared",
    )

    assert len(spans) >= 2
    for s in spans:
        # Every slice must be exact
        slice_text = norm_text[s.start : s.end]
        assert len(slice_text.strip()) > 0
        assert s.start >= 0
        assert s.end <= len(norm_text)
        assert s.start < s.end


def test_bm25_index_exact_match_retrieval():
    index = InvertedBM25Index()
    index.add(
        passage_id="p1",
        text="FastAPI query parameters are declared as function arguments.",
        headings=["FastAPI", "Query Parameters"],
    )
    index.add(
        passage_id="p2",
        text="Path parameters are extracted directly from the URL path.",
        headings=["FastAPI", "Path Parameters"],
    )
    index.add(
        passage_id="p3",
        text="Database connection sessions are created using SQLAlchemy dependencies.",
        headings=["FastAPI", "Database Sessions"],
    )

    results = index.search("query parameters function", top_k=2)
    assert len(results) >= 1
    assert results[0][0] == "p1"  # Best match for query parameters


def test_reciprocal_rank_fusion_logic():
    # Dense ranks: p1 > p2 > p3
    dense_ranks = ["p1", "p2", "p3"]
    # BM25 ranks: p2 > p4 > p1
    lexical_ranks = ["p2", "p4", "p1"]

    fused = reciprocal_rank_fusion(dense_ranks, lexical_ranks, k=60, top_n=4)
    ranked_ids = [pid for pid, _score in fused]

    # p2 was 2nd in dense and 1st in lexical -> highest combined reciprocal score
    assert ranked_ids[0] == "p2"
    assert "p1" in ranked_ids[:2]
    assert len(ranked_ids) == 4


def test_hybrid_reranked_retriever_source_deduplication():
    norm_text = normalize_text(SAMPLE_DOC)
    splitter = HeadingSentenceSplitter(max_chars=200)
    spans = splitter.split(norm_text)

    source1 = Source(
        source_id="docs/fastapi.md",
        version="1.0",
        text=norm_text,
        raw_sha256=content_sha256(norm_text),
        loader_version="1.0",
        licence="MIT",
        licence_basis="declared",
    )
    source2 = Source(
        source_id="docs/pydantic.md",
        version="1.0",
        text="Pydantic provides data validation using Python type annotations.",
        raw_sha256=content_sha256("Pydantic provides data validation using Python type annotations."),
        loader_version="1.0",
        licence="MIT",
        licence_basis="declared",
    )

    retriever = HybridRerankedRetriever()
    retriever.index_source(source1, spans)
    retriever.index_source(source2)

    # Search for parameters
    results = retriever.retrieve("query parameters", top_k=2)

    assert len(results) <= 2
    # Verify each result is from a unique source file (deduplicated)
    source_ids = [p.source_id for p in results]
    assert len(source_ids) == len(set(source_ids))

    # All returned passages must mechanically verify
    for p in results:
        src = source1 if p.source_id == source1.source_id else source2
        assert verify_passage(src, p) is True
