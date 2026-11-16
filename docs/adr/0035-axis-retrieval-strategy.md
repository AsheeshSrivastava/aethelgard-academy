# ADR 0035: AXIS retrieval strategy (production grade)

- **Status:** Proposed; in progress. Work steps 1 to 3 are done (SPEC-20, SPEC-21); steps 4 to 7 remain. Amended 2026-11-15 after the owner's read of the independent review (section 7): decisions (a) and (b) accepted, (c) rejected, rag-core adopted as the retrieval library.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-14
- **Extends:** ADR-0011 (HR pipeline), ADR-0012 (persistent artifacts), ADR-0034
- **Governed by:** AGENTS.md (Zero-Cost Local Development, Provider Agnostic), SPEC-09, ADR-0001 (ports), ADR-0003
- **Evidence:** rag-core measured the HR pipeline: 100 vs 64 right-first and 121 vs 85 top-3 on 137 quote-level questions; +39 right-first over vector-only on 548 file-level questions; 0.15 to 0.20 s per question on a local GPU. In the LMS, the embedder and reranker are never wired (`embedder=`, `reranker=` are not passed), so retrieval today is BM25 on the raw text `"{unit_id} {question}"` plus a crude word boost.

---

## 1. Context & Problem Statement

ADR-0011 chose HR (BM25 + vector, merged by reciprocal rank fusion, then a cross-encoder) and it measured well, but the LMS runs only a simplified copy. The platform is meant for real multi-tenant use, so "wire the models" is not enough. The design must also say how the index is built and loaded, what happens when a model is down or slow, how a bad answer is traced and how a regression is caught, and how retrieved text is kept from steering the model.

## 2. Decision

### 2.1 Pipeline and library
Keep HR as in ADR-0011: keyword (BM25) and vector lists, merged by reciprocal rank fusion (k 60, no weights), the first 30 reranked by `BAAI/bge-reranker-v2-m3`, one hit per source, top 3 to the prompt. Embedder: `jinaai/jina-embeddings-v2-base-en`. No third model. "Encoder" means the embedder.

**The pipeline comes from rag-core, not from a copy (owner, 2026-11-15).** The LMS depends on the `ragcore` package, pinned to a tag (`ragcore @ git+https://github.com/AsheeshSrivastava/Content-Library-Aethelgard-Academy@v0.1.0`; Apache-2.0). Its public names are `Retriever`, `Result`, `IndexSetup`, `open_index` and `IndexStoreError`. rag-core builds and syncs the index; the LMS only reads it. The simplified `HybridRerankedRetriever` copy in the LMS is kept only as the keyword-only development and CI mode and is removed once the rag-core adapter covers that mode.

**Upstream docs stay the primary source** (ADR-0034; the owner rejected "give AXIS the current lesson instead of searching"). AXIS needs data, so retrieval stays. Answer quality is improved through the system prompt and, if needed, an agentic evaluation, not by shrinking the data.

### 2.2 A retrieval port
Retrieval sits behind a small port in `core/` (`search(query, filters) -> RetrievalResult`), beside `IAXISCompanion`. The result type is **ours**: passages, scores, source names, `index_version`, `mode` (`hybrid_rerank` or `keyword_only`) and a status (`ok`, `not_found`, `no_index`, `unavailable`). No `ragcore` type or SQLite detail leaks past the adapter. Router and prompt code use only the port. Adapters: a rag-core adapter (HR, or L when chosen), the LMS keyword-only copy (development and CI), and later, if measured to be needed, an HTTP adapter for a hosted service (2.10). Tests use a fake.

### 2.3 Versioned offline index, loaded at startup
- The index is a rag-core SQLite file. It records the embedder, chunker and reranker it was built with and refuses to open with a different setup (rag-core ADR-0011). The LMS adds a manifest check: `index_version` (content hash of the file's meta and source list), embedder id and **pinned revision**, vector dimension, build date, source list with licences.
- The app loads the index in the app factory / startup hook, **never at import time**. A missing index gives status `no_index` and a clear message (ADR-0034), not `None`.
- **Embedder-match check at startup** uses rag-core's own refusal plus the manifest. A mismatch makes the ranked modes unavailable (see 2.7) and logs it loudly. It never searches with incompatible vectors.
- The `index_version` and the `mode` are logged with every answer (interaction log, ADR-0022).
- **The mode is chosen explicitly at startup and logged**: `Retriever.open(path, setup, variant="L")` for keyword-only (no torch) or the default HR (needs embedder and reranker). rag-core has no automatic fallback; the LMS makes the choice from configuration and from the self-check in 2.7.

### 2.4 "Not found" threshold
A passage must pass a score threshold on the reranker score (and on the fusion score when no reranker runs) to count as found. The threshold is **tuned on the question set (2.6), not guessed**, and is stored in config with the value, date and set version. Below it the port returns `not_found` and ADR-0034's "not in the course yet" path runs.

### 2.5 Safe use of retrieved text
- **Retrieved text is untrusted data.** It goes into the prompt inside a fenced, labelled block with a standing instruction that it is reference material, not instructions. Passages are length-capped and stripped of control sequences that imitate the prompt template.
- **Citations are checked.** A chip shows only a passage id that was retrieved this turn; ids the model invents are dropped. A cited passage that the answer does not use is not shown (checked by the quote-overlap rule in SPEC-09).
- **Licence care:** quotes are short and always carry the readable source name.

### 2.6 Offline regression gate and the first decision
A fixture index (a few dozen passages, made-up or licence-clear text, in `tests/fixtures/`) and **30 to 50 learner-style questions** with the expected source (and some with no answer, to test `not_found`). CI runs them with keyword-only mode, with no models and no GPU, and fails if first-hit or top-3 falls below the recorded floor. A separate, optional local run scores keyword-only (L) and HR on the same set and on a larger LMS set, using rag-core's first/top-3 measure.

**The first piece of work is the measurement (decision (a), owner 2026-11-15):** build the set, then score keyword search with stop words dropped and a score floor. The embedder and reranker are adopted only if HR beats it by a clear margin on this corpus. The rag-core numbers (100 vs 64 right-first) come from another corpus and are not enough on their own. Answer keys are not involved, so the private-answers rule is unaffected.

### 2.7 Models are optional for development; failure behaviour in service
- Embedder and reranker live in an optional extra (`uv sync --extra retrieval`). CI, `MOCK_AI=true` and a fresh clone run without torch or a GPU, using keyword-only mode. This is a development and test mode, labelled as such.
- `trust_remote_code` for the jina model is reviewed once and pinned by revision, as in rag-core. No unpinned model download at runtime.
- **Answering model down: fail closed (owner decision 2026-11-14).** If the answering model is missing, fails its startup self-check, or times out, AXIS answers "AXIS is unavailable right now" and shows no answer. The rest of the platform keeps working. Status `unavailable`, logged, shown on the health endpoint.
- **Only a ranking model down: labelled downgrade (owner decision 2026-11-15, decision (b)).** If the embedder or reranker is missing, fails its self-check or times out, AXIS answers from keyword-only mode and says so on the answer ("Keyword search only") with `mode = keyword_only` in the log. This is a visible downgrade, never a quiet one. An unmatched embedder (2.3) counts as a missing ranking model. The tutor's uptime does not depend on a component that only improves ranking.
- Each model call has a timeout. A startup self-check (one test query per model) decides readiness, and the page shows AXIS status and mode.
- Tests cover both paths: answering model down gives the unavailable message with no answer or citation and no hang; ranking model down gives a labelled keyword-only answer.

### 2.8 Query transformation: measured first
Today the query is `"{unit_id} {question}"`; the unit id matches nothing in upstream docs. Step one is rule-based and cheap (drop the unit id; add the error type and identifiers from stderr and code). An LLM that rewrites the query into 1 to 3 searches, merged by RRF, is built **only if** the question set shows a gain. rag-core does not do query rewriting, so this is new and has no prior number.

### 2.9 Cost and latency control
Retrieval reuses the existing usage meter and the A4 run cap: a per-learner request budget, a concurrency limit on the reranker (it is the heavy part), and a latency budget per call. Over budget means a fast "AXIS is busy, try again" message, not a queue and not a weaker search. Retrieval time, status and `index_version` are recorded per answer.

### 2.10 Hosting: not decided here
During the test period the owner's computer is the server, so rag-core runs in-process there. Hosting rag-core on Hugging Face (a Space or an Inference Endpoint, behind an HTTP adapter for the port) is a later, measured experiment, not a plan. Open points: reranker latency on a CPU Space (unmeasured), sleeping free tiers (a pilot needs an always-on tier), the network hop, access control (private Space and token), and cost. Because the LMS only sees the port and our own result type, the move is one adapter and a config change. A separate retrieval service otherwise waits for load numbers.

## 3. Consequences

### Positive
- Retrieval quality chosen by measurement on our own questions, with a floor enforced in CI.
- Every answer is traceable (index version, mode, status). An answering-model outage gives an honest "unavailable"; a ranking-model outage gives a visibly labelled keyword-only answer. Neither is silent.
- Prompt-injection and invented-citation risk are handled by design, not by hope.
- CI and development stay offline and cost-free.

### Negative / trade-offs
- One more dependency (`ragcore`, pinned by tag) and its release process to follow.
- Optional models mean two code paths to test. The fixture gate covers the keyword-only path; the full-HR path and the unavailable path are tested locally and in unit tests with fakes.
- The threshold and the fixture set need upkeep as the corpus changes.
- A fixture set of 30 to 50 questions is small. It guards against regressions; it does not prove quality (the larger local run does that).

## 4. Work sequence (one small PR each, tests first)
Done: ADR-0034 and this ADR (#37); honest basics (#42); rag-core packaged as `ragcore` v0.1.0 (separate repo); step 1, fixture set and CI gate (SPEC-20, #47); step 2, local measurement (#48); step 3, retrieval port, manifest, startup load and logging (SPEC-21; the mode `hybrid_rerank` is accepted in the type but fails startup until step 6).
1. Fixture index and question set, with the CI gate on keyword-only mode (2.6).
2. Local measurement: keyword-only with stop words dropped and a floor, against HR, on the set. Decide whether the models are worth adopting.
3. Retrieval port with our own result type, manifest with `index_version`, startup load, explicit mode choice, logging (2.2, 2.3).
4. Fenced untrusted passages and the checked citation rule; drop the "first 30 passages" fallback; stop words and unit id dropped from the query; minimum score so "not found" can fire (F7, F8).
5. Prompt rules and the learner-facing "no index" message (ADR-0034).
6. rag-core adapter and, if step 2 says yes, model wiring as an optional extra, with timeouts, self-checks, the labelled downgrade and the tuned threshold (2.4, 2.7).
7. Optional, only if measured: more query cleanup, then LLM rewriting (2.8).
A7 (ConceptStore wiring) is paused until there are enough concept notes. The self-hosted pilot ADR is on hold.
