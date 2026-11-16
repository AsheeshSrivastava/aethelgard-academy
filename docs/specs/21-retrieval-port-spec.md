# SPEC-21: Retrieval port, result type, manifest and startup load

Status: Approved by the owner on 2026-11-16 ("proceed", as drafted, source_prefixes kept, hybrid_rerank fails loudly until its adapter exists).
Implements: ADR-0035 sections 2.2 (port), 2.3 (index and startup), 2.7 (explicit mode, logging) and section 4 step 3.
No new ADR is needed. The same PR updates the ADR-0035 section 4 "Done" list (steps 1 and 2 done, step 3 done) and sets its Status line.

## 1. Scope
In this step:
- A retrieval port in `core/` and our own result type.
- A manifest with `index_version`, computed from the existing index.
- Loading at app startup, never at import time, with the mode chosen from configuration.
- The existing LMS keyword search wrapped as the first adapter (mode `keyword_only`).
- A fake adapter for tests.
- AXIS companions call the port, not `HybridRerankedRetriever` directly.
- Per-answer logging of `index_version`, `mode`, `status`, `latency_ms`.

Not in this step (each has its own later step):
- The rag-core adapter and the full search mode `hybrid_rerank` (ADR step 6). The mode exists in the type so nothing changes later.
- Fenced untrusted text and checked citations (safe text, ADR step 4 / F7).
- Stop-word and unit-id query cleanup and the "not found" rule (F8).
- Prompt rules and the "no index" learner message wording (ADR-0034, step 5).

## 2. Types (`src/lms/core/`, no third-party imports)
- `RetrievalStatus`: `ok`, `not_found`, `no_index`, `unavailable`.
- `RetrievalMode`: `hybrid_rerank`, `keyword_only`.
- `RetrievedPassage`: `passage_id`, `source_id`, `source_name` (readable), `text`, `score`.
- `RetrievalResult`: `status`, `mode`, `index_version` (empty string when there is no index), `passages` (tuple, empty unless `ok`), `message` (short, for logs).
- `IRetriever` (port): `search(query: str, *, top_k: int = 3, source_prefixes: tuple[str, ...] = ()) -> RetrievalResult`.
- `IndexManifest`: `index_version`, `built_at`, `loader_version`, `sources` (source_id, licence, licence_basis, raw_sha256).

## 3. Requirements
- R1. `search` never raises for expected conditions. A missing or unreadable index returns `no_index`; an adapter fault returns `unavailable`; an empty result returns `not_found`. Only programming errors raise.
- R2. No adapter-specific type (SQLite, ragcore, BM25 internals) appears in a signature outside its adapter.
- R3. Results are ordered by score, ties broken by passage position, so the order is deterministic.
- R4. `index_version` is a sha256 over the sorted pairs (`source_id`, `raw_sha256`) plus `loader_version`, all read from `data/index/sources.jsonl`. The same index gives the same version; changing one source changes it.
- R5. The index is loaded in the app factory or startup hook. Importing `lms` or `lms.api.app` loads nothing and opens no file.
- R6. Mode comes from `LMS_RETRIEVAL_MODE` (default `keyword_only`). An unknown value fails startup with a clear message. `hybrid_rerank` is accepted only once its adapter exists; until then it fails startup with "not available in this build", never silently falls back.
- R7. The index folder comes from `LMS_INDEX_DIR` (default `data/index`). A missing folder gives `no_index` plus one log line at startup, not a crash.
- R8. Mode, `index_version` and startup outcome are logged once at startup. Each answer's interaction-log entry records `index_version`, `mode`, `status` and `latency_ms` (ADR-0022).
- R9. `top_k` is capped (1 to 10); `source_prefixes`, when given, restricts results to sources whose id starts with one of them.
- R10. The companions (`gemini_companion`, `local_llm_companion`, `router`, `axis_rules`) receive an `IRetriever`, not a concrete retriever. Behaviour for a loaded keyword index is unchanged (same passages, same order).

## 4. Tests first (names, to be written before code)
1. Port contract, run against both the fake and the keyword adapter: ok, not_found, no_index, unavailable are returned, not raised (R1).
2. Deterministic order and tie-break (R3).
3. `index_version`: stable on repeat, changes when one source's `raw_sha256` changes, changes with `loader_version` (R4).
4. Importing the app module does not touch the filesystem index (R5), checked by pointing `LMS_INDEX_DIR` at a missing folder and importing.
5. Startup: missing folder gives `no_index` and a logged line; unknown mode value fails startup; `hybrid_rerank` fails with the "not available" message (R6, R7).
6. Interaction log entry carries index_version, mode, status, latency_ms (R8).
7. `top_k` bounds and `source_prefixes` filter (R9).
8. Regression: the SPEC-20 fixture question set gives the same first-hit and top-3 numbers through the port as it does today through the old class, so the CI gate floor is unchanged (R10).
9. Companion tests use the fake; none imports `HybridRerankedRetriever`.

## 5. Edge cases to test (chaos check later)
Empty query, whitespace query, a query of 10,000 characters, a corrupt `sources.jsonl` line, an index folder with `sources.jsonl` but no `passages.jsonl`, `top_k` of 0 or 1,000, a prefix that matches nothing.

## 6. Traceability
ADR-0035 2.2 -> R1, R2, section 2 types. 2.3 -> R4, R5, R7. 2.7 (explicit mode, logged) -> R6, R8. SPEC-20 gate -> test 8.

## 7. Open points
1. Resolved by the owner: `source_prefixes` (R9) stays.
2. Resolved by the owner: R6 makes `hybrid_rerank` fail loudly until its adapter exists.
3. To confirm before writing tests: when `load_default_retriever()` in `local_llm_companion.py` is called today (at import or at startup). R5 depends on it.
