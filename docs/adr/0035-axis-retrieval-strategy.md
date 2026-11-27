# ADR 0035: AXIS retrieval strategy (production grade)

- **Status:** Proposed; in progress. Plan steps 1 to 5 and 7 are done (SPEC-21 to SPEC-25, SPEC-27); step 6a is measured (SPEC-26, default off, branch not merged); 6b and 5b are skipped by the owner for later; steps 8 and 9 remain. See section 5 (amendments 2026-11-16 and 2026-11-19). Amended 2026-11-15 after the owner's read of the independent review (section 7): decisions (a) and (b) accepted, (c) rejected, rag-core adopted as the retrieval library.
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
- **Citations are checked.** A chip shows only a passage id that was retrieved this turn; ids the model invents are dropped. A cited passage that the answer does not use is not shown (checked by the quote-overlap rule in SPEC-22 R6).
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
Done: ADR-0034 and this ADR (#37); honest basics (#42); rag-core packaged as `ragcore` v0.1.0 (separate repo); step 1, fixture set and CI gate (SPEC-20, #47); step 2, local measurement (#48); step 3, retrieval port, manifest, startup load and logging (SPEC-21; the mode `hybrid_rerank` is accepted in the type but fails startup until step 6); step 4a, fenced untrusted passages, checked citations and no "first 30" fallback (SPEC-22, which also defines the quote-overlap rule that 2.5 needs; SPEC-09 never had one); step 4b, query cleanup (function words out, unit id out), `keyword_only` ranked by BM25 alone, and "not found" on the number of query terms found, minimum 3 on the real corpus and 2 on the CI fixture (SPEC-23; measured, see `docs/measurements/2026-11-16-not-found-rules.txt`). Weighted fusion, error-type extraction and path stripping were measured and not adopted; step 4c, prompt rules and a visible "no index" status (SPEC-24): one rule for every mode (no answers from the model's memory; ADR-0034 amended), a distinct notice per state (`not_found`, `no_index`, `unavailable`), `source_state` on every reply, a yes/no `index_status()` on the retrieval port, `GET /api/v1/axis/status`, and a status line and per-answer note on the AXIS panel.
1. Fixture index and question set, with the CI gate on keyword-only mode (2.6).
2. Local measurement: keyword-only with stop words dropped and a floor, against HR, on the set. Decide whether the models are worth adopting.
3. Retrieval port with our own result type, manifest with `index_version`, startup load, explicit mode choice, logging (2.2, 2.3).
4. Fenced untrusted passages and the checked citation rule; drop the "first 30 passages" fallback; stop words and unit id dropped from the query; minimum score so "not found" can fire (F7, F8).
5. Prompt rules and the learner-facing "no index" message (ADR-0034).
6. rag-core adapter and, if step 2 says yes, model wiring as an optional extra, with timeouts, self-checks, the labelled downgrade and the tuned threshold (2.4, 2.7).
7. Optional, only if measured: more query cleanup, then LLM rewriting (2.8).
A7 (ConceptStore wiring) is paused until there are enough concept notes. The self-hosted pilot ADR is on hold.

## 5. Amendment 2026-11-16 (owner-approved plan)

### 5.1 New plan order

> **2026-11-27:** status tracking for the table below moved to [the freeze tracker](../plan/freeze-2026-12-05.md). The decisions stand; the table is no longer updated.
Step 4 above was split, and the owner's plan of 2026-11-16 reordered what follows. **The nine-step list below is the plan order. The "Work sequence" numbers in section 4 are the older numbering** (corrected 2026-11-16; an earlier version of this section wrongly said the later steps were unchanged in order and put contextual retrieval after the rag-core adapter).

| Plan step | What | Status | Old section 4 number |
| :--- | :--- | :--- | :--- |
| 1 | Retrieval port | done (SPEC-21, #50) | 3 |
| 2 | Safe retrieved text: fenced and capped passages, checked citations, no "first 30" fallback | done (SPEC-22, #51) | 4 (4a) |
| 3 | Query cleanup and `not_found` | done (SPEC-23, #53) | 4 (4b) |
| 4 | Prompt rules and the "no index" message | done (SPEC-24, #54) | 5 |
| 5 | Measurement: the six Gemini sets, P@K, MRR and nDCG at K=1, 3 and 5, and the per-file passage limit test | done (SPEC-25, #55); the mode stress test (5b) was skipped by the owner 2026-11-19, to be re-run later | 2 (extended) |
| 5c | With-source reply quality eval (240 answerable questions, three modes, structural checks and hand review, no LLM judge; ADR-0039 2.7) | ADR accepted 2026-11-26; spec not yet written | |
| 6 | Contextual retrieval: heading path first, then an LLM-written context in a search-only field (5.2); local against cheap paid on a small trial. A paid run needs a printed estimate and the owner runs it | 6a measured, small gain, default stays off (SPEC-26, on a separate unmerged branch); **6b skipped by the owner 2026-11-19, to be revisited after real use** (5.5) | not numbered before |
| 7 | rag-core adapter and model wiring, with `not_found` re-tuned for the reranker (2.4, 2.7) | done (SPEC-27, #56, merged 2026-11-19) | 6 |
| 8 | Tracing, metrics and answer-level evals behind a hexagonal port (local adapter, no-op in CI, vendors optional); its ADR comes first | after 7 | not numbered before |
| 8b | AXIS mode contracts and a record of every prompt (catalogue, `prompt_version`; ADR-0039) | ADR accepted 2026-11-26; SPEC-31 drafted | |
| 8c | Follow-up from SPEC-30: move the code detector from `adapters` into `core` | **Proposed** 2026-11-26 | |
| 8d | Owner console (GUI) for evals, traces and observability ([backlog](../plan/owner-console-evals-traces.md); builds on ADR-0037 section 2.7) | **Proposed** 2026-11-26, after the 5 Dec 2026 freeze | |
| 8e | AXIS facilitation: what a good turn is, conversation memory, how it is judged ([decision paper](../plan/axis-facilitation-decision-paper.md); touches 8b, and 5c would use the same rubric) | ADR-0041 accepted 2026-11-27; SPEC-33 drafted; stage 2 after the freeze | |
| 8f | AXIS learning limits ([record](../plan/axis-learning-limits.md)) and a fixed reply for error questions with no source (SPEC-34) | Limits recorded; SPEC-34 **draft** 2026-11-27 | |
| 9 | Learner-style questions: query rewriting and at most one bounded agentic retry, only if measured to help (2.8) | last, optional | 7 |

Later, not in the nine: A7 (ConceptStore wiring), then A8 (split `app.py`). The old section 4 items 1 and 2 (fixture set, first local measurement) were done before this list began (SPEC-20, #47 and #48). GraphRAG stays rejected (5.3).

### 5.2 Contextual retrieval: design only, nothing built yet (6b skipped for now, see 5.5)
- Each passage may get a short, model-written context sentence ("where this passage sits in its page"). It is stored in a **separate, search-only field**. It is indexed for search but is **never put in the prompt, never shown to the learner and never cited**; the passage text the learner sees and the quote-overlap check use stays the original source text.
- Adding or changing this field **changes `index_version`**, because the index changes what it finds. An index built without it keeps its old version.
- It is adopted only if the question set (2.6) shows a clear gain, the same rule as the embedder and reranker. Building it needs a model call per passage at index time, so a printed cost estimate comes first (AGENTS.md).

### 5.2a Split of step 6 (owner, 2026-11-19)
Step 6 is split. **6a** (free, offline) adds search-only words from fields the index already holds (path words and page title) to the keyword index; it is SPEC-26 and is adopted only by its measured rule. **6b** (the model-written context sentence in 5.2) is decided after the 6a numbers and gets its own spec and printed cost estimate. The 5.2 rules apply to both: search-only text never reaches the prompt, the learner or a citation, and a changed recipe changes `index_version`.

**6a result (SPEC-26, 2026-11-19):** measured on the six Gemini sets; V4 (path and page-title words, counted twice) gained 5 questions of 240 (Hit@3 57.1 to 59.2), exactly on the 2-point bar; V1 to V3 missed it. The owner kept the default `none`; V4 stays behind `LMS_SEARCH_TEXT=path_title_x2`. 6b is decided next.

### 5.3 GraphRAG: considered and rejected
GraphRAG (a knowledge graph built over the text) was considered for questions that need links between topics. Rejected for now: the course map's prerequisite graph already holds the links we need (what comes before what), it is authored by us, and a model-built graph would add cost, a second index to version and a new place for wrong facts. Revisit only if the question set shows a class of cross-topic questions that keyword and hybrid search cannot answer.

### 5.4 Amendment 2026-11-19: decisions for step 7 (SPEC-27)
- **Models come from a public rag-core function.** rag-core v0.2.0 adds `load_models(embedder_id, reranker_id)` returning the embedder, the reranker and the matching `IndexSetup` from pins bundled in the package. The LMS does not import rag-core's internal model builders and does not keep its own copy of the pins. The LMS pins the tag in the optional `retrieval` extra.
- **A labelled downgrade is a field, not a mode.** `RetrievalResult.downgraded` is true when the ranking models were not used; the mode then reads `keyword_only`, the log records `downgraded`, and the learner sees "Keyword search only" (2.7). It covers a missing index file, an index built with a different setup, a failed startup self-check, a model fault and a timeout.
- **Timeout and concurrency are settings.** Ten seconds per hybrid search (owner, 2026-11-19: a single call was seen taking that long) and two searches at once on the reranker, both measured again in step 8. A search over the limit gets "busy" at once, never a queue and never a quiet weaker search (2.9).
- **Not found for the reranker is measured, not assumed (owner decision, 2026-11-19).** SPEC-27 R9 tuned a floor on the top reranker score and the term rule on the six Gemini sets. The default for hybrid search is at least 2 distinct query terms in the best passage and a top reranker score of at least -2.6 (`LMS_HR_MIN_TERMS=2`, `LMS_HR_MIN_SCORE=-2.6`; `off` removes the floor). On all six sets this wrongly refuses 6.2% of answerable questions (today's rate) and refuses 41.7% of out-of-scope questions, 1 question of 60 under the bar of 43.3%. The old rule (3 terms) refuses 15.4% of good questions with hybrid search. Recorded as a deviation from the spec's strict fallback; the numbers are in SPEC-27 R9 and `docs/measurements/2026-11-19-hybrid-adapter.txt`. Hybrid search found the right file in the top 3 for 75.0% of questions through the adapter (same as direct rag-core) and for 66.7% of paraphrase questions (keyword: 30.0%).

### 5.5 Amendment 2026-11-19: step 6b skipped, revisit after real use
The owner skipped the model-written context sentence (6b). Evidence: the keyword-only variant (6a) raised the right file in the top 3 from 57.1% to 59.2% on the six Gemini sets (paraphrase 30.0% to 31.7%), and hybrid search alone then reached 75.0% overall and 66.7% on paraphrase questions. **Revisit once real learners have used AXIS in hybrid mode, and only if the questions it still misses justify a per-passage model cost.** Nothing in 5.2 changes; it stays a design with no code. A paid run still needs a printed cost estimate and the owner runs it. The same note is in rag-core's `PROGRESS.md`.
