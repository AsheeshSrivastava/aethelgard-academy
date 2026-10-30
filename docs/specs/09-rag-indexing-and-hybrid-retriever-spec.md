# Specification 09: RAG Indexing & Hybrid Reranked Retriever

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed By:**
  - `ADR-0003: Two-Stage RAG: Upstream Research vs. Downstream AXIS AI Grounding`
  - `ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking`
- **Domain:** Upstream Documentation Indexing, Sentence-Split Passage Extraction, Hybrid BM25+Dense RRF, Cross-Encoder Reranker
- **Date:** 2026-10-30

---

## 1. Scope & Core Invariants

1. **Exact-Slice Invariant:** Chunks are defined strictly by character offsets `(start, end)` into the canonical normalized text of `Source`. Every passage satisfies `verify_passage(source, passage) == True`.
2. **Chunking Sizing:** Headings split first; long sections split at sentence boundaries targeting ~375 tokens (median ~640 characters).
3. **Hybrid Search Contract:**
   - Dense retrieval: `jinaai/jina-embeddings-v2-base-en` (top-200).
   - Lexical retrieval: BM25 on `heading_path + " " + passage_text` (top-200).
   - Reciprocal Rank Fusion ($k=60$) yields top-30 merged candidates.
   - Cross-Encoder: `BAAI/bge-reranker-v2-m3` scores top-30 against the query.
   - File Deduplication: Returns top-3 unique source files.

---

## 2. Component Design (`src/lms/adapters/ai/rag/`)

```python
class ChunkCoordinate(BaseModel):
    start: int
    end: int
    headings: tuple[str, ...]

class HeadingSentenceSplitter:
    """Extracts sentence-aligned chunk coordinates respecting markdown headings."""
    def split(self, text: str, target_chars: int = 1500) -> list[ChunkCoordinate]: ...

class InvertedBM25Index:
    """Lightweight in-memory BM25 index over passage text and heading paths."""
    def add(self, passage_id: str, text: str, headings: list[str]) -> None: ...
    def search(self, query: str, top_k: int = 200) -> list[tuple[str, float]]: ...

def reciprocal_rank_fusion(
    dense_ranks: list[str],
    lexical_ranks: list[str],
    k: int = 60,
    top_n: int = 30,
) -> list[tuple[str, float]]: ...

class HybridRerankedRetriever:
    """Coordinates Dense + BM25 + RRF + BGE Reranker + Source Deduplication."""
    def retrieve(self, query: str, top_k: int = 3) -> list[Passage]: ...
```

---

## 3. Acceptance Criteria

1. **Exact Slice Verification:** 100% of generated passages pass `verify_passage(source, passage)`.
2. **Deterministic RRF Fusion:** Given two ranked candidate lists, RRF produces consistent, mathematically exact score ordering.
3. **Source Deduplication:** If multiple chunks from `fastapi-docs/tutorial.md` rank highly, only the single highest-scoring chunk from that file is returned in the final top-3.
4. **Offline Testability:** Operates with fast mock vector/reranker embeddings during `pytest` without requiring live HuggingFace weight downloads in CI.
