# ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Asheesh Ranjan Srivastava (Platform Architect & Owner), AI Systems Architect
- **Governed By:** Retrieval Comparison Report (Stage 1 to Stage 4, 2026-10-30)

---

## 1. Context and Problem Statement

To ground the AXIS AI Companion with verifiable facts from our 14 curated upstream technical documentations (1,312 clean sources, ~9.7 MB), we need a proven, empirical retrieval pipeline. 

An empirical benchmark across 598 primary/secondary questions and 137 quote-anchored passage-level questions evaluated:
1. **7 Chunking Strategies:** `rules`, `fixed`, `merge-small`, `parent-child`, `semantic-bge-m3`, `semantic-jina`, `llamaindex` sentence-splitter.
2. **2 Embedding Modes:** Normal vs. Late Chunking.
3. **2 Local Embedders:** `BAAI/bge-m3` (1,024 dims) vs. `jinaai/jina-embeddings-v2-base-en` (768 dims).
4. **4 Retrieval Pipelines:** Vector-only (`V`), Keyword-only (`L` via BM25), Hybrid RRF (`H`), and Hybrid + Reranker (`HR` via `BAAI/bge-reranker-v2-m3`).

Key empirical findings from the report:
- **Late Chunking lost everywhere:** Mean-pooled late vectors suffered direction collapse and degraded right-first accuracy significantly.
- **Parent-Child & Semantic underperformed:** Did not beat structural heading-aware cutting.
- **The Reranker is the dominant lever:** Moving from Vector-only (`V`) to Hybrid+Reranker (`HR`) boosted Right-First accuracy from 64 to 100 on passage-level evaluation and raised MRR to 0.818.
- **`jina-v2-base-en` + `llamaindex` heading-sentence chunking won the pre-registered decision:** Zero pairs cut at the 1,024-token reranker limit, faster execution, highest right-first passage-level score (100 vs 96), and optimal for our English technical corpus.

---

## 2. Decision

We formally adopt the **Hybrid Reranked Retrieval Architecture (HR)** for the LMS Stage 3 Curriculum & Documentation RAG:

### 2.1 Chunking Strategy (`llamaindex` Heading-Sentence Slicer)
- Documents are split by headings, then subdivided at sentence boundaries into passages of approximately **375 tokens** (median ~640 characters).
- **Exact-Slice Invariant:** LlamaIndex algorithms determine *only the cut coordinates `(start, end)`*. Every passage is mechanically sliced from our canonical, normalized source text.
- **Provenance Contract:** Every chunk is represented as a deterministic `Passage` object passing `verify_passage(source, passage) == True`.

### 2.2 Dense Embedding
- **Model:** `jinaai/jina-embeddings-v2-base-en` (768 dimensions, mean pooling).
- **Execution:** Local zero-cost inference running on workstation GPU/CPU.

### 2.3 Sparse Lexical Search (BM25)
- Tokenizes heading path (`heading_1 > heading_2`) concatenated with the passage text.
- Captures exact symbols, method signatures, CLI flags, and exception names (e.g. `TypeError`, `APIRouter`, `--filter=blob:none`).

### 2.4 Hybrid Fusion (Reciprocal Rank Fusion - RRF)
- Retrieves `k=200` candidates from Dense search and `k=200` candidates from BM25 lexical search.
- Merges candidates using parameter-free RRF scoring ($k=60$):
  $$RRF\_Score(d) = \sum_{m \in \{dense, bm25\}} \frac{1}{60 + \text{rank}_m(d)}$$
- Yields the top 30 merged candidate passages.

### 2.5 Cross-Encoder Reranking & File Deduplication
- **Model:** `BAAI/bge-reranker-v2-m3`.
- Re-scores the top 30 candidates against the user query.
- **Source Deduplication:** Retains at most one highest-scoring passage per source file to ensure broad, non-redundant architectural context.
- Top-3 deduplicated passages are passed to AXIS AI prompts with mechanical quotation citations.

---

## 3. Consequences

### Positive
- **Proven Empirical Performance:** Backed by 598 file-level and 137 passage-level evaluation questions (MRR ~0.818).
- **Zero Token Truncation in Reranking:** With median ~640 chars / 375 tokens, 0% of query-passage pairs exceed the 1,024-token reranker window.
- **Fast Interactive Latency:** Total retrieval time is ~130–150ms on local GPU hardware.
- **Preserves Exact Provenance:** Zero synthetic paraphrasing; citations are exact slices of official upstream documentation.

### Negative / Trade-offs
- Requires maintaining both a BM25 inverted index and vector store in the local adapter layer.
