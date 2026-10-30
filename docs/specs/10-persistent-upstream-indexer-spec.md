# Specification 10: Persistent Upstream Indexer & Warm Retriever Loader

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed By:**
  - `ADR-0003: Two-Stage RAG: Upstream Research vs. Downstream AXIS AI Grounding`
  - `ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking`
  - `ADR-0012: Persistent RAG Artifacts & Upstream Documentation Indexer`
- **Domain:** Corpus Ingestion, Persistent Serialization, Fast BM25 Postings Loader
- **Date:** 2026-10-30

---

## 1. Functional Requirements

1. **Batch Indexing CLI (`lms index-upstream`):**
   - Ingests all Markdown, RST, and HTML files from a corpus root (default: `reference/upstream/`).
   - Slices documents using `HeadingSentenceSplitter` (~375 tokens, ~1500 chars max, ~640 median).
   - Verifies 100% of passages via `verify_passage(source, passage)`.
   - Serializes passages and sources to JSONL format.
   - Serializes the BM25 inverted index to JSON format.
   - Provides stdout progress reporting (number of sources, passages extracted, time elapsed).

2. **Persistence Schema:**
   - `passages.jsonl`: One JSON object per line containing:
     `passage_id`, `source_id`, `version`, `start`, `end`, `headings`, `text`, `chunker_version`.
   - `sources.jsonl`: One JSON object per line containing:
     `source_id`, `version`, `raw_sha256`, `licence`, `licence_basis`, `text`.
   - `bm25.json`: JSON object containing:
     `k1`, `b`, `doc_count`, `avg_doc_length`, `doc_lengths`, `doc_headings`, `inverted_index`.

3. **Fast Loader Contract:**
   - `HybridRerankedRetriever.load(index_dir: Path) -> HybridRerankedRetriever`
   - Reconstitutes the entire retriever state in $< 50\text{ms}$ without parsing source text.

---

## 2. Acceptance Criteria

1. **Passage Verification:** 100% of reloaded passages must pass `verify_passage(source, passage)`.
2. **Deterministic Retrieval:** Results from a persisted and warm-loaded retriever must match an in-memory indexed retriever identically.
3. **Atomic Writes:** Indexing must write to temporary files before replacing target index directory to prevent partial corruption.
4. **Offline Testability:** All tests run fast without network or model weights.
