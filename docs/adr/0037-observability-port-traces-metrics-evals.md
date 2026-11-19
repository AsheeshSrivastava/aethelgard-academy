# ADR 0037: AXIS observability behind a port: traces, mode-usage report, answer-level evals

- **Status:** Proposed (merged draft for the owner's go; no spec, test or code yet)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-19
- **Implements:** ADR-0035 plan step 8 (section 5.1). Owner decision of 2026-11-16 to add observability.
- **Governed by:** ADR-0001, ADR-0003 (no web, no ungrounded chat at runtime), ADR-0022 (interaction log), ADR-0025 (providers), ADR-0034, ADR-0035 (retrieval), SPEC-24 (no-source rules)
- **Extends:** the SPEC-20 gate and the SPEC-25 / SPEC-27 measurements
- **Specs to follow:** SPEC-28 (tracing), SPEC-29 (report and thumbs), SPEC-30 (answer evals)

---

## 1. Context & Problem Statement

AXIS now has a real retrieval path (keyword, hybrid rerank, labelled downgrade, `not_found`, refusal rules). Today the only view of it is log lines and offline measurement files.

1. **No timings or counts per AXIS turn.** We cannot say where time goes (search, rerank, model) or how often a turn is refused, downgraded or times out. ADR-0035 section 5.4 sets a ten second search limit and two concurrent searches and says both are "measured again in step 8".
2. **No usage report per mode.** `interaction_log` already stores `mode` (Coach, Hybrid, Socratic) in each `axis` event, but nothing counts it per mode, per unit or per week. ADR-0035 section 5.5 (revisit step 6b after real use) needs that evidence.
3. **The SPEC-24 no-source rules are only tested as prompt text,** not as whether a real model obeys them.

Two constraints shape the design:

- **Offline core.** Development and CI run with `MOCK_AI=true` and no keys (AGENTS.md). Observability must not break that.
- **Learner privacy and IP.** Learner questions and answers are personal. Hosted tracing products send them out, and auto-tracing needs LangChain-style code, which AXIS does not use.

## 2. Decision

### 2.1 One port, hexagonal, provider agnostic

Add `ITracer` (a Protocol) in `src/lms/core/` with its own types and no vendor import, same standard as `IRetriever`: `span(name, attributes)` as a context manager and `event(name, attributes)`. Spans nest. Core code only calls the port.

**A tracer never raises into the caller.** A fault is logged once and the turn carries on.

Adapters in `src/lms/adapters/observability/`:

| Adapter | Use | Default |
|---|---|---|
| `NoopTracer` | tests, CI, `MOCK_AI=true` | **yes** in tests and CI |
| `LocalTracer` | JSON lines file, size-capped with one rotated file, no network, no new table | opt in; recommended in `lms serve` (open point 4.1) |

**Vendor adapters (OpenTelemetry, Langfuse) are not built in step 8.** Each needs its own ADR because data would leave the machine. LangSmith is not planned (hosted, sends text out); it could be added behind the same port only if the owner wants it.

`LMS_TRACER=noop|local`. Any other value stops start-up with a plain message (as `LMS_RUNNER`, ADR-0036).

### 2.2 What is traced: every model call

One trace per AXIS interaction, named by kind, carrying the same `interaction_id` as the ADR-0022 log so the two join:

| Trace kind | Call kinds it covers | Child spans |
|---|---|---|
| `axis_question` | `consult`, `stream` | query cleanup, `retrieve` (keyword or hybrid, slot wait), `prompt_build`, `model_call`, `citation_check` |
| `concept_check` | `judge_explanation` (CO-6, ADR-0026) | rubric load, `model_call`, verdict rule |
| `readme_draft` | `document_draft` (`draft_readme`, Amendment A2) | `prompt_build`, `model_call` |
| `build_review` | `build_feedback` | pointer rules (no model), `model_call` if any |

All five call kinds already pass the one place in each companion adapter that does the `UsageMeter` check and record; the span wraps that place. Retrieval spans exist only on `consult` and `stream`. The judge profile, cap reached, provider refused and mock fallback are attributes, so a `not_judged` result is visible. The existing `model_usage` table (tokens and cost per call) stays the money record; traces link to it by call id and do not replace it. A test per kind: a fake companion call produces exactly one trace of that kind, so a model call that skips these entry points is caught.

**Attribute allow-list.** Allowed: ids, mode, unit id, timings, counts, `source_state`, `retrieval_mode`, `downgraded`, `index_version`, provider profile id, token counts, error class name. A new attribute is a visible code change. **Never** in any trace: learner question, answer, code, README text, concept-check explanation, passage text, keys, URLs. A debug switch that adds text would need its own owner decision.

### 2.3 Span summary

The local summary reports turns, p50 and p95 per stage, and counts of `not_found`, `no_index`, `unavailable`, `busy`, downgraded and timeouts. It is the tool that re-measures the SPEC-27 timeout and concurrency, and the result is recorded in ADR-0035 section 5.4. Cost estimates stay local; no paid call is made by tracing.

### 2.4 Mode-usage report (from the interaction log)

Read-only over `interaction_log`: rows with `event_type=axis` and `payload.mode`. **No new log field and no new table.**

- Groups: per mode; per mode and unit; per mode and week (Monday to Sunday, UTC, stated in the report header).
- A row with no `mode` is counted as `unknown`, never dropped.
- `test_mode=1` rows are excluded by default.
- Counts only: turns, and distinct learners if more than one. No text.
- Delivered as the CLI `lms report axis-modes`, a plain table plus optional JSON. No HTTP endpoint for now (there is no sign-in gate for one).

### 2.5 Answer-level evals

Extend the SPEC-20 gate from "did retrieval find the right source" to "was the answer good". Two parts.

**A. Deterministic checks on every answer (CI, no model).** Every citation points at a retrieved passage; a `not_found` search never produces a grounded-looking answer; Socratic mode returns no code; no source outside the index. CI tests the **checker** on canned good and bad replies (one breaking each rule) with `MOCK_AI=true`.

**B. Obedience eval of the SPEC-24 no-source rules.** For each question, each mode (3) and each no-source state (`not_found`, `no_index`, `unavailable`; 3 states), the harness drives the real companion with a retriever fake that returns that state. Questions come from the out-of-scope and unanswerable items in `eval/gemini-sets/`. No model judges a model. A reply passes only if:

- (a) the SPEC-24 R3 state sentence is present at the start;
- (b) there is no source label like `[1]` and no named document or page as a source (R2, R7);
- (c) there is no "Not from the course" part (R4);
- (d) in Socratic mode, there is no code block (ADR-0009).

Each check is also reported alone. The R4 rule "no facts from memory" cannot be checked by pattern, so a **fixed random sample is hand-reviewed** (as with 24 of 240 Gemini questions) and reported as a separate, smaller figure. No LLM judge in version 1. Output is counts per mode and state plus the exact failing questions (for example "412 of 450 replies passed all checks").

This is a **measurement, not a CI gate**: real models are not deterministic and may cost money. Real runs are local model first. A paid run needs a printed cost estimate and **the owner runs it**.

### 2.6 Thumbs up/down

A thumbs control under each AXIS answer. It adds a new client event type `axis_feedback` to the interaction log carrying only the AXIS turn id and up or down. No free text; `ClientPayload` keeps `extra=forbid`. It goes to the interaction log only: never the evidence ledger, and it never affects progression, assistance accounting or the soft gate. The report shows up and down counts per mode. It is a weak signal: it informs, it does not gate.

### 2.7 Dashboard (owner question, 2026-11-19)

- **No learner-facing UI** beyond the thumbs control. Learners never see traces or rates (invisible assessment, AGENTS.md).
- **SPEC-29 ships a local report command that writes a static HTML report** (latency p50 and p95, refusal and `not_found` rate, mode mix, downgrades, busy answers, thumbs ratio, recent trace ids), alongside the mode-usage table in 2.4. It works offline with no login.
- **A live dashboard page is a later, optional SPEC-29b:** read-only, owner-only, in `frontend/`, fed by one endpoint that returns aggregates and never text. It needs an owner/admin gate first, and the backend has no admin role today. Building that gate is a separate decision.

### 2.8 Failure rule

Observability never changes a learner's answer. A tracer error is caught, counted once and dropped. A slow exporter is bounded (size cap, timeout) and drops spans rather than waiting. **A test proves a failing tracer leaves the reply unchanged.**

### 2.9 Rejected

- OpenTelemetry or a hosted tracer as a core dependency.
- A new `axis_turn` table (the interaction log has everything).
- An LLM judge for R4 in version 1.
- Gating CI on a real-model result.
- Calling a vendor SDK directly in AXIS code (lock-in, sends text out, breaks the offline rule); logging only (no timings or rates to tune the limits).

## 3. Consequences

- Positive: we see where slow answers lose time; we see real mode use before step 6b or step 9; we get a measured obedience rate for the no-source rules; offline CI stays offline.
- Negative: a thin span layer in the AXIS path; a trace file to cap; R4 relies on human review; judged evals cost money and a real model, so they stay owner-run.
- Risk: a tracer bug breaking an answer. Mitigated by the never-raises rule and the failing-tracer test. Attribute values leaking text: mitigated by the allow-list and a guard test (like `tests/test_private_seed_answers.py`) that fails if a span carries a learner field or an over-long string.

## 4. Open points for the owner (recommendations from the drafts)

1. **Default tracer:** `noop` in tests and CI; `local` in `lms serve`.
2. **Obedience bar:** report-only for the first run, then set from the numbers (example: 95 percent passing checks a to d; it may block making hybrid the default).
3. **Hand-review sample:** 30 replies per mode, fixed seed.
4. **Week boundary:** UTC Monday, labelled in the report header.
5. **Dashboard:** static report first; live page (SPEC-29b) only after the owner picks it and an admin gate exists.

## 5. Sequence (each step stops for the owner's go)

1. **SPEC-28, tracing:** the port, `NoopTracer`, `LocalTracer`, the allow-list, never-raises, the guard test that fails if a span carries learner text, and spans wired into all five call kinds (one test per kind).
2. **SPEC-29, report and thumbs:** `lms report axis-modes`, the static HTML report with the latency and refusal summary from spans, the re-measure of the hybrid timeout and concurrency recorded in ADR-0035 section 5.4, and the thumbs control with `axis_feedback`.
3. **SPEC-30, answer evals:** the deterministic checker with canned replies in CI, the obedience harness, the hand-review sample, and the first local-model run and report.
4. **Later, only when the owner asks:** vendor adapters (each with its own ADR), the live dashboard page (SPEC-29b), paid judged evals.

Step 9 of ADR-0035 (query rewriting and a bounded retry) is not touched here; if built, it adds spans through the same port.

## 6. What is confirmed, inferred, unknown

- Confirmed: the ten second limit and concurrency of two are settings today (ADR-0035 section 5); the owner approved observability on 2026-11-16 as provider agnostic; `interaction_log` stores `mode` per `axis` event; all five call kinds pass one metering place per companion adapter (stated by the second draft, to be confirmed against the code in SPEC-28).
- Inferred: a local JSON-lines adapter is enough for the first review of the numbers.
- Unknown: whether the build review calls a model on every path; which vendor UI, if any, the owner later wants; whether paid judged evals are worth their cost after the deterministic ones exist.
