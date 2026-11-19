# SPEC-27: rag-core adapter, model wiring, and the "not found" rule for the reranker

Status: Approved by the owner 2026-11-19 (D1 and D2 as drafted; D3 changed to a 10 second timeout).
Implements: ADR-0035 sections 2.1 (library), 2.2 (port), 2.3 (index), 2.4 (threshold), 2.7 (models optional, labelled downgrade), 2.9 (concurrency, latency), plan step 7 (section 5.1).
ADR change: a short amendment 5.4 in the same PR (decisions D1 to D3 below, plus the step 7 status row). No other ADR.
Branch: from `main`, not from the unpushed SPEC-26 branch (edb55a7). That branch changes only the keyword index text and stays `none` by default; step 7 does not need it, and mixing them would make this PR hard to review.

## 1. What we know
Confirmed (read in code and in `docs/measurements/2026-11-18-gemini-baseline.txt`):
- On the six Gemini sets (240 answerable, 60 out-of-scope), real corpus, right file in the top 3: LMS keyword 57.1%, rag-core keyword (L) 64.6%, hybrid + reranker (HR) 75.0%. Paraphrase questions: 30.0 / 31.7 / 66.7.
- The LMS keeps its own index (`data/index/*.jsonl`). rag-core uses a SQLite file with vectors. `scripts/measure_gemini.py` already builds that file from `sources.jsonl` (`ragcore_searchers`) and reads it back with `Retriever.open`.
- The rag-core public names are `Retriever`, `Result`, `IndexSetup`, `open_index`, `IndexStoreError`. The functions that build the embedder and reranker (`ragcore.stage.make_embedder`, `ragcore.stage3.make_reranker`) are internal, and they need rag-core's `configs/*.yaml`, which is not in the installed package.
- The reranker score is a model score, not a count. Median top-1 score for the 60 out-of-scope questions is -1.30 (HR) and there is no tested floor yet. The current rule (fewer than M distinct query terms in the best passage, M=3) was tuned on keyword search only.
Inferred: a reranker floor, the term rule, or both will work better for HR than the term rule alone. Unknown until measured (R9).

## 2. Decisions needed (recommendation first)
- **D1. Who builds the models?** Approved: a small rag-core PR adds one public function, `load_models(embedder_id, reranker_id)`, returning the embedder, the reranker and the matching `IndexSetup` from pins bundled in the package, then tag v0.2.0; the LMS pins v0.2.0. Alternative: the LMS imports rag-core internals and keeps its own copy of the pins (faster, but breaks rag-core's "public surface only" rule and drifts). The rag-core PR is its own thread and goes first.
- **D2. How is the labelled downgrade shown?** Approved: the result and the answer metadata carry `downgraded=true`; the frontend shows "Keyword search only" next to the answer (ADR-0035 2.7 requires it). The frontend badge is a small change in this PR. Alternative: backend only now, badge in a later PR.
- **D3. Timeout.** Owner chose 10 seconds per search (a single call was seen taking that long) (default 10, config `LMS_RETRIEVAL_TIMEOUT_S`; the startup self-check warms the models so the first learner search is not the slow one), and a reranker concurrency limit of 2 (`LMS_RERANK_CONCURRENCY`). Both are guesses until step 8 gives latency numbers; they are settings, not constants.

## 3. Scope
In: the rag-core adapter, mode `hybrid_rerank`, startup load and self-check, the labelled downgrade, timeout and concurrency limit, the index build script, `index_version` for the new index, the optional `retrieval` extra, the re-tuned not-found rule, offline tests with fakes, and a measurement run through the adapter.
Not in: tracing and metrics (step 8), query rewriting (step 9), removing the LMS keyword copy (kept as the development and CI mode; removal waits until the adapter has run for a while), hosting (ADR 2.10), per-learner request budget (the A4 cap already exists).

## 4. Requirements
- R1. `RagcoreRetriever(IRetriever)` lives in `adapters/ai/rag/ragcore_retriever.py`. It is the only LMS file that imports `ragcore`, and it imports it inside functions, so `import lms` and CI work without torch or ragcore installed. No ragcore type appears in a signature outside it (SPEC-21 R2).
- R2. `search` maps rag-core results to `RetrievedPassage`: `passage_id`, `source_id`, readable `source_name` (same rule as the keyword adapter), original passage text, reranker score. `top_k` is capped 1 to 10. `LMS_PASSAGES_PER_SOURCE` maps to `max_per_file`. `source_prefixes` is applied after ranking (rag-core has no filter), so it can return fewer than `top_k`; this is documented and tested, not hidden.
- R3. The port never raises for expected conditions (SPEC-21 R1). Missing index file: `no_index`. rag-core refuses the setup (`IndexStoreError`): that counts as a missing ranking model (ADR 2.3 and 2.7), so the app runs keyword-only, labelled. Any other adapter fault: `unavailable`.
- R4. Mode. `LMS_RETRIEVAL_MODE=hybrid_rerank` is now accepted (SPEC-21 R6 changes: it no longer fails startup). Default stays `keyword_only`. Startup loads the rag-core index and runs one test query per model (self-check). If the index, a model or the self-check fails, the app starts in keyword-only mode and logs one loud line naming the reason. Answering-model outage handling is unchanged (fail closed).
- R5. Per-call timeout and downgrade. If a hybrid search exceeds the timeout or the models fail at run time, that search is answered by the keyword adapter and the result says `mode=keyword_only, downgraded=true`. The search thread cannot be killed; it is allowed to finish in the background and its result is dropped. At most `LMS_RERANK_CONCURRENCY` hybrid searches run at once; over the limit the search is answered `unavailable` with message "busy" at once (ADR 2.9: no queue, no quiet weaker search).
- R6. `RetrievalResult` gets one new field, `downgraded: bool = False`. The interaction log records it. `RetrievalTrace` and `as_log_fields` get the same field.
- R7. Index build. `scripts/build_ragcore_index.py` reads `data/index/sources.jsonl` (the loader output, unchanged) and syncs it into `LMS_RAGCORE_INDEX` (default `data/ragcore/index.db`, git-ignored), using the same setup as `measure_gemini.py`. Local only, offline after the models are downloaded, never touches the keyword index. The app never builds an index; it only reads (ADR 2.1).
- R8. `index_version` for the rag-core index is a sha256 over the `IndexSetup` fields (embedder and reranker ids and pinned revisions, chunker, chunk config) and the sorted pairs (`source_id`, `content_sha256`) from the index file. Same file gives the same version; a different pin or one changed source changes it. The manifest also lists the sources with licences, as today.
- R9. Not-found rule for HR. The tuning was done by measurement on the six Gemini sets (read on fastapi, httpx and pydantic, checked untouched on pytest, python and uv, as in SPEC-23). Candidates: (a) the current term rule unchanged; (b) a floor on the top-1 reranker score; (c) both. Bar: false refusal no worse than today's 6.2% and correct refusal at least today's 43.3%; among those the lowest false refusal. Settings: `LMS_HR_MIN_SCORE` (default -2.6; `off` means no floor) and `LMS_HR_MIN_TERMS` (default 2; 0 means the term rule is off). `terms_matched` and `terms_total` stay in the trace for HR (counted on the returned passage text with the existing term counter).
  **Result (2026-11-19, `docs/measurements/2026-11-19-hybrid-adapter.txt`, set_version 5d5fbd741a89, rag-core index_version 1fc9c2f9a6ff):**
  - Parity (R11): hit@1 47.1, hit@3 75.0, hit@5 85.8, MRR 0.617, identical to direct rag-core HR. Paraphrase hit@3 66.7 (keyword 30.0). 300 searches: median 150 ms, slowest 211 ms.
  - Today's term rule (M=3, no floor) with HR: 15.4% of answerable questions wrongly refused, 55.0% of out-of-scope refused. Too harsh for HR.
  - No candidate fully held the bar on both halves. The script's pick (M=2, floor -2.85) read 4.2 / 43.3 but checked 5.8 / 33.3 (false / correct, in percent).
  - **Owner decision, 2026-11-19: M=2 with floor -2.6.** Read 5.8 / 43.3, checked 6.7 / 40.0, all six 6.2 / 41.7. False refusal equals today's; correct refusal is 1 question of 60 below the 43.3% bar. This is a recorded deviation from the strict fallback ("keep the term rule"), accepted because the term rule alone refuses 15.4% of good questions with HR. The out-of-scope sets include questions that have a fair answer elsewhere in the corpus, so correct refusal is understated (SPEC-23 section 1).
  - Revisit when step 9 (query rewriting) or a new question set changes the corpus or the questions.
- R10. Packaging. New optional extra `retrieval` in `pyproject.toml`: `ragcore[embed]` pinned to the tag from D1. `uv sync` without the extra, CI and `MOCK_AI=true` run without torch. Model revisions stay pinned (ADR 2.7). `trust_remote_code` for jina was reviewed in rag-core and is pinned there.
- R11. Measurement through the port. `scripts/measure_gemini.py` gets a mode that runs the new adapter; its HR numbers must equal the direct rag-core numbers (hit@3 75.0 on the 240 answerable) within rounding, and the paraphrase hit@3 is reported again so the owner can decide on step 6b.
- R12. Offline CI never loads a model. Tests use a fake ragcore module and fake embedder/reranker. One local-only test (marker `retrieval`, skipped in CI) opens the real index and checks R11 parity on a small subset.

## 5. Tests first (names, written before code)
1. Port contract (SPEC-21 contract tests) runs against the new adapter with a fake ragcore: ok, not_found, no_index, unavailable returned, not raised (R3).
2. Mapping: fields, readable source name, original text, reranker score, order, deterministic ties (R2).
3. `top_k` bounds (0 and 1,000), `passages_per_source`, `source_prefixes` that matches nothing, and a prefix that leaves fewer than `top_k` (R2).
4. `IndexStoreError` on open gives keyword-only plus a loud log line and `downgraded=true` (R3, R4).
5. Self-check failure of the embedder, then of the reranker, each gives keyword-only at startup (R4).
6. Timeout: a fake that sleeps past the limit gives a keyword answer with `downgraded=true` within the limit plus a small margin; the late result is dropped (R5).
7. Concurrency: third simultaneous search with limit 2 returns `unavailable` "busy" at once (R5).
8. `import lms` and importing the adapter module do not import `ragcore` or `torch` (R1, R10).
9. `LMS_RETRIEVAL_MODE=hybrid_rerank` accepted; unknown value still fails startup; `LMS_RETRIEVAL_TIMEOUT_S`, `LMS_RERANK_CONCURRENCY`, `LMS_HR_MIN_SCORE` reject bad values with a clear message (R4, R5, R9).
10. `index_version`: stable on repeat; changes with a reranker pin, an embedder pin, and one source hash (R8).
11. Not-found: with floor on, a top score below the floor gives `not_found`; floor empty means no floor; the term rule still applies under (a) and (c); `terms_matched/total` appear in the trace (R9).
12. Log entry carries `downgraded` (R6).
13. Build script: syncs a tiny fake source list into a temp file, a second run reports 0 changed, and nothing is written outside the output path (R7).
14. Local-only: real-model parity subset (R12).

## 6. Edge cases for the chaos check later
Empty and whitespace query; a 10,000-character query; index file present but empty; index file built with another embedder revision; reranker returns NaN or an empty list; the timeout fires while the same retriever serves another search; two sources whose names differ only by case; model download blocked (no network) at startup.

## 7. Traceability
2.1 -> R1, R10, D1. 2.2 -> R1, R2. 2.3 -> R4, R7, R8. 2.4 -> R9. 2.7 -> R3, R4, R5, R6, D2. 2.9 -> R5, D3. Step 7 measure -> R11.

## 8. Order of work after your go
1. rag-core PR for D1 (`load_models`, v0.2.0), in the Content-Library repo, its own thread.
2. ADR-0035 amendment 5.4, then tests, then code in the LMS (needs the device for the real-model parts: GPU, model files, `data/index`).
3. Measurement run and R9 tuning on the device, printed before anything is accepted.
4. Afterwards: update the rag-core HF Space README to say it is wired into the LMS.
