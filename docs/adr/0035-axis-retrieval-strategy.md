# ADR 0035: AXIS retrieval strategy (production grade)

- **Status:** Proposed (owner confirmed scope in principle 2026-11-14; ADR text awaits owner review)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-14
- **Extends:** ADR-0011 (HR pipeline), ADR-0012 (persistent artifacts), ADR-0034
- **Governed by:** AGENTS.md (Zero-Cost Local Development, Provider Agnostic), SPEC-09, ADR-0001 (ports), ADR-0003
- **Evidence:** rag-core measured the HR pipeline: 100 vs 64 right-first and 121 vs 85 top-3 on 137 quote-level questions; +39 right-first over vector-only on 548 file-level questions; 0.15 to 0.20 s per question on a local GPU. In the LMS, the embedder and reranker are never wired (`embedder=`, `reranker=` are not passed), so retrieval today is BM25 on the raw text `"{unit_id} {question}"` plus a crude word boost.

---

## 1. Context & Problem Statement

ADR-0011 chose HR (BM25 + vector, merged by reciprocal rank fusion, then a cross-encoder) and it measured well, but the LMS runs only a simplified copy. The platform is meant for real multi-tenant use, so "wire the models" is not enough. The design must also say how the index is built and loaded, what happens when a model is down or slow, how a bad answer is traced and how a regression is caught, and how retrieved text is kept from steering the model.

## 2. Decision

### 2.1 Pipeline
Keep HR as in ADR-0011: keyword (BM25) and vector lists, merged by reciprocal rank fusion (k 60, no weights), the first 30 reranked by `BAAI/bge-reranker-v2-m3`, one hit per source, top 3 to the prompt. Embedder: `jinaai/jina-embeddings-v2-base-en`. No third model. "Encoder" means the embedder.

### 2.2 A retrieval port
Retrieval sits behind a small port in `core/` (`search(query, filters) -> RetrievalResult`), beside `IAXISCompanion`. The result carries passages, scores, source names, `index_version` and a status (`ok`, `not_found`, `no_index`, `unavailable`). Router and prompt code use only the port. Adapters: keyword+fusion (development and CI only) and full HR (service). Tests use a fake.

### 2.3 Versioned offline index, loaded at startup
- The index is built offline by the indexer (ADR-0012) and written atomically as a directory with a manifest: `index_version` (content hash), chunker version, embedder id and **pinned revision**, vector dimension, build date, source list with licences.
- The app loads the index in the app factory / startup hook, **never at import time**. A missing index gives status `no_index` and a clear message (ADR-0034), not `None`.
- **Embedder-match check at startup:** the loaded embedder id, revision and dimension must equal the manifest. A mismatch disables the vector list and logs it loudly (AXIS is unavailable per 2.7), instead of searching with incompatible vectors.
- The `index_version` is logged with every answer (interaction log, ADR-0022), so any answer can be traced to the index that produced it.

### 2.4 "Not found" threshold
A passage must pass a score threshold on the reranker score (and on the fusion score when no reranker runs) to count as found. The threshold is **tuned on the question set (2.6), not guessed**, and is stored in config with the value, date and set version. Below it the port returns `not_found` and ADR-0034's "not in the course yet" path runs.

### 2.5 Safe use of retrieved text
- **Retrieved text is untrusted data.** It goes into the prompt inside a fenced, labelled block with a standing instruction that it is reference material, not instructions. Passages are length-capped and stripped of control sequences that imitate the prompt template.
- **Citations are checked.** A chip shows only a passage id that was retrieved this turn; ids the model invents are dropped. A cited passage that the answer does not use is not shown (checked by the quote-overlap rule in SPEC-09).
- **Licence care:** quotes are short and always carry the readable source name.

### 2.6 Offline regression gate
A fixture index (a few dozen passages, made-up or licence-clear text, in `tests/fixtures/`) and **30 to 50 learner-style questions** with the expected source (and some with no answer, to test `not_found`). CI runs them with the keyword+fusion adapter, with no models and no GPU, and fails if first-hit or top-3 falls below the recorded floor. A separate, optional local run scores the full HR adapter on the same set and on a larger LMS set, using rag-core's first/top-3 measure. Answer keys are not involved, so the private-answers rule is unaffected. The question set is also what decides 2.8.

### 2.7 Models are optional for development; fail closed in service
- Embedder and reranker live in an optional extra (`uv sync --extra retrieval`). CI, `MOCK_AI=true` and a fresh clone run without torch or a GPU, using the keyword+fusion adapter. This is a development and test mode, labelled as such.
- `trust_remote_code` for the jina model is reviewed once and pinned by revision, as in rag-core. No unpinned model download at runtime.
- **In service (owner decision 2026-11-14), there is no quiet downgrade.** If the embedder, the reranker or the answering model is missing, fails its startup self-check, or times out, AXIS answers "AXIS is unavailable right now" and shows no answer. The rest of the platform keeps working. Status is `unavailable`; it is logged and shown on the health endpoint. The `degraded` status is removed.
- Each model call has a timeout, so a slow model gives a fast "unavailable" instead of a hang. A startup self-check (one test query per model) decides readiness, and the page shows AXIS status.
- Tests still cover this path: the unavailable message appears, no passage or citation is shown, nothing hangs, and the platform stays up.

### 2.8 Query transformation: measured first
Today the query is `"{unit_id} {question}"`; the unit id matches nothing in upstream docs. Step one is rule-based and cheap (drop the unit id; add the error type and identifiers from stderr and code). An LLM that rewrites the query into 1 to 3 searches, merged by RRF, is built **only if** the question set shows a gain. rag-core does not do query rewriting, so this is new and has no prior number.

### 2.9 Cost and latency control
Retrieval reuses the existing usage meter and the A4 run cap: a per-learner request budget, a concurrency limit on the reranker (it is the heavy part), and a latency budget per call. Over budget means a fast "AXIS is busy, try again" message, not a queue and not a weaker search. Retrieval time, status and `index_version` are recorded per answer.

### 2.10 Not decided here
A separate retrieval service and hosted models wait for load numbers (unknown: reranker speed on a CPU-only server; hosting cost of two local models for many tenants). The in-process adapter behind the port keeps that move cheap.

## 3. Consequences

### Positive
- Real retrieval quality (the measured HR gain) with a floor enforced in CI.
- Every answer is traceable (index version, mode, status). A model outage gives an honest "unavailable", never a weaker answer.
- Prompt-injection and invented-citation risk are handled by design, not by hope.
- CI and development stay offline and cost-free.

### Negative / trade-offs
- Optional models mean two code paths to test. The fixture gate covers the keyword+fusion path; the full-HR path and the unavailable path are tested locally and in unit tests with fakes.
- The threshold and the fixture set need upkeep as the corpus changes.
- A fixture set of 30 to 50 questions is small. It guards against regressions; it does not prove quality (the larger local run does that).

## 4. Work sequence (one small PR each, tests first)
1. Honest basics (ADR-0034 items 1 to 3): drop fake and unrelated citations; "not from the course" label; no-index message; prompt rules.
2. Wire the `ConceptStore` (A7).
3. Retrieval port, manifest with `index_version`, startup load, embedder-match check, logging.
4. Fixture index and question set with the CI gate on keyword+fusion.
5. Model wiring (embedder, reranker) as an optional extra, timeouts and fail-closed "unavailable" handling, tuned threshold, citation check and untrusted-text fence.
6. Rule-based query cleanup, measured against the set.
7. Optional LLM rewriting, only if step 6's set shows a gain.
