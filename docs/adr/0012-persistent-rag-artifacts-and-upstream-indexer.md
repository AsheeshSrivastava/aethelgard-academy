# ADR-0012: Persistent RAG Artifacts & Upstream Documentation Indexer

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Asheesh Ranjan Srivastava (Platform Architect & Owner), AI Systems Architect
- **Governed By:** ADR-0003, ADR-0011, SPEC-09

---

## 1. Context and Problem Statement

Our curated upstream bedrock consists of 14 official technical documentations (1,312 clean files, ~9.7 MB) located in `reference/upstream/`. 

Parsing all 1,312 Markdown, RST, and HTML documents in memory using `HeadingSentenceSplitter` and populating the BM25 inverted index takes 3 to 5 seconds per process execution. In interactive CLI commands (`uv run lms ask ...` or `uv run lms explain ...`), a 3-second startup penalty degrades learner flow.

We need a persistent indexing pipeline that:
1. Pre-slices all 1,312 sources into verified exact-slice `Passage` instances.
2. Serializes the BM25 inverted index and passage records to disk.
3. Allows the CLI and API server to warm-load the entire index in $< 50\text{ms}$.
4. Retains 100% mechanical verification (`verify_passage(source, passage) == True`).

---

## 2. Decision

We establish an offline batch indexing command and persistent artifact layout:

### 2.1 Artifact Directory Layout (`data/index/`)
- `data/index/passages.jsonl`: Line-delimited JSON containing serialised `Passage` objects (`passage_id`, `source_id`, `version`, `start`, `end`, `headings`, `text`, `chunker_version`).
- `data/index/sources.jsonl`: Line-delimited JSON of all canonical loaded `Source` metadata (`source_id`, `version`, `raw_sha256`, `licence`, `licence_basis`).
- `data/index/bm25.json`: Inverted index token map (`term -> {passage_id: freq}`), document lengths, and corpus averages.

### 2.2 Ingestion Engine (`src/lms/adapters/ai/rag/indexer.py`)
- Walks `reference/upstream/` using our registered readers (`markdown.py`, `rst.py`, `html.py`).
- Slices text strictly via `HeadingSentenceSplitter(max_chars=1500, min_chars=100)`.
- Generates deterministic passage IDs via `make_passage_id`.
- Performs an immediate self-audit during build: every single passage must pass `verify_passage(source, passage)`.
- Saves artifacts atomically using temporary files and directory rename.

### 2.3 CLI Command
```bash
uv run lms index-upstream [--corpus reference/upstream] [--output data/index]
```

### 2.4 Fast Startup Warm-Loader
- `HybridRerankedRetriever.load(index_dir="data/index")` reads pre-built JSON/JSONL artifacts into memory in $< 50\text{ms}$.
- Automatically falls back to memory indexing if artifacts are missing.

---

## 3. Consequences

### Positive
- **Instant Interactive Response:** Interactive queries (`lms ask`) avoid document re-parsing overhead.
- **Deterministic & Auditable:** All generated passages and BM25 postings are frozen on disk and can be inspected or diffed.
- **Zero Hallucination Guarantee:** Every persisted passage preserves its source repository and character offsets.

### Negative / Trade-offs
- Requires running `lms index-upstream` whenever the curated upstream documentation in `reference/upstream/` is updated.
