# ADR 0037: Observability behind a port: traces, metrics and answer-level evals

- **Status:** Proposed (draft for the owner's go; no spec, test or code yet)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-19
- **Implements:** ADR-0035 plan step 8 (section 5.1). Owner decision of 2026-11-16 to add observability.
- **Governed by:** ADR-0003 (no web, no ungrounded chat at runtime), ADR-0022 (interaction log), ADR-0025 (providers), ADR-0035 (retrieval)
- **Extends:** the SPEC-20 gate and the SPEC-25 / SPEC-27 measurements

---

## 1. Context & Problem Statement

AXIS now has a real retrieval path (keyword, hybrid rerank, labelled downgrade, `not_found`, refusal rules). Today the only view of it is log lines and offline measurement files. In production we cannot answer: how long did a search take, which mode served it, how often did we refuse, did the answer cite what was retrieved, did the learner find it useful. ADR-0035 sets a ten second search limit and two concurrent searches, and says both are "measured again in step 8". There is nothing to measure them with at run time.

Two constraints shape the design:

1. **Offline core.** Development and CI run with `MOCK_AI=true` and no keys (AGENTS.md). Observability must not break that.
2. **Learner privacy and IP.** Learner questions and AXIS answers are personal. Hosted tracing products send them out. Auto-tracing needs LangChain-style code, which AXIS does not use.

## 2. Decision

### 2.1 One port, hexagonal, provider agnostic

Add `ITracer` in `src/lms/core/` (same standard as `IRetriever`). Core code only calls the port: `span(name, **attributes)` as a context manager, `event(name, **attributes)`, `metric(name, value, **labels)`. It never imports a vendor.

Adapters in `src/lms/adapters/observability/`:

| Adapter | Use | Default |
|---|---|---|
| `NoopTracer` | CI, tests, `MOCK_AI=true` | **yes**, when nothing is configured |
| `LocalTracer` | writes JSON lines to a local folder; offline; what the owner reads first | opt in |
| `OpenTelemetryTracer` | standard export (OTLP) to any collector | opt in, later step |
| Langfuse (self-hosted) | optional UI | opt in, later step, only if the owner asks |

LangSmith is not built. It is hosted and sends text out; it can be added behind the same port only if the owner wants it.

Selected by `LMS_TRACER` (`noop`, `local`, `otel`). An unknown value stops start-up with a plain message, as `LMS_SEARCH_TEXT` does.

### 2.2 What is traced (first version)

**Every model call is traced, not only chat.** One trace per AXIS interaction, named by kind, and carrying the same `interaction_id` as the ADR-0022 log so the two join:

| Trace kind | Where it starts today | Child spans |
|---|---|---|
| `axis_question` | chat (`consult`, and `stream` in `axis_stream.py`) | query cleanup, retrieval (mode, `not_found`, downgrade reason, passages returned), prompt build, model call, citation check |
| `concept_check` | `judge_explanation` (CO-6, ADR-0026) | rubric load, model call, verdict rule (ideas met, verdict, `not_judged` reason) |
| `readme_draft` | `build:draft-readme` (`draft_readme`, Amendment A2) | prompt build, model call |
| `build_review` | the build feedback call that reads the README and review note | pointer rules (no model), model call if any |

Each trace ends with a final status. The judge profile, cap reached, provider refused and mock fallback are span attributes, so a `not_judged` result is visible. The existing `model_usage` table (tokens and cost per call) stays the money record; traces link to it by call id and do not replace it. A model call that bypasses these four entry points is a bug the spec's test must catch (one test per kind: a fake companion call produces exactly one trace of that kind). Attributes are **ids, counts, timings and status**: `index_version`, `set_version`, mode, `terms_matched`, top score band, number of passages, model id, token counts, refusal reason.

**No learner text and no passage text in any trace by default** (a rule, not a setting). A debug switch that adds text would need its own owner decision and stays out of this ADR.

### 2.3 Metrics

Counters and timings only: searches by mode, `not_found` rate, downgrades, "busy" answers, search latency (p50, p95), model latency, token use, cost estimate (local, never a paid call). These are the numbers that re-check the ADR-0035 ten second limit and the concurrency of two.

### 2.4 Answer-level evals

Extend the SPEC-20 gate from "did retrieval find the right source" to "was the answer good":

- **Deterministic checks** (run in CI, no model): every citation points at a retrieved passage; a `not_found` search never produces a grounded-looking answer; Socratic mode returns no code; the answer uses no source outside the index.
- **Judged checks** (local, owner-run, not CI): groundedness and answer relevance on the six Gemini sets, with a printed cost estimate first and the owner running any paid step (AGENTS.md).
- **Learner feedback signal:** a thumbs up or down on an AXIS answer, stored with the trace id and no extra text. It goes to the interaction log (ADR-0022), not the evidence ledger, so it can never affect progression.

### 2.5 Dashboard (owner question, 2026-11-19; proposed, needs the owner's pick)

- **No learner-facing UI.** Learners never see traces or rates (invisible assessment, AGENTS.md). The only learner-visible part is the thumbs control on an AXIS answer.
- **First, a local report, not a page.** SPEC-29 ships a command that reads the `LocalTracer` files and prints or writes a static HTML report (latency p50 and p95, refusal and `not_found` rate, mode mix, downgrades, busy answers, thumbs ratio, recent trace ids). It works offline, needs no login and fits CI artifacts.
- **A live dashboard page is a later, optional step (SPEC-29b).** It would be an owner-only, read-only page in `frontend/` fed by one backend endpoint that returns the same aggregates, never text. It needs an owner/admin gate first, and the backend has no admin role today. Building the gate just for this page is a separate decision, so it is not in this ADR's first version.
- **Vendor UIs (Langfuse, Grafana) stay an adapter option**, not something we build.

### 2.6 Failure rule

Observability never changes a learner's answer. A tracer error is caught, counted once, and dropped; the request continues. A slow exporter is bounded (queue size and timeout) and drops spans rather than waiting.

## 3. Options considered

- **A. Call a vendor SDK directly in AXIS code.** Fastest. Rejected: lock-in, sends learner text out, breaks the offline rule.
- **B. Logging only.** Cheap. Rejected: no timings or rates to tune the ten second limit; hard to review.
- **C. A port with a local adapter first (chosen).** More upfront design, but offline by default, testable, and vendors stay optional.
- **D. OpenTelemetry only, no own port.** Standard, but ties core code to its API and makes the offline no-op less clean. Kept as an adapter (2.1).

## 4. Consequences

- Positive: real numbers for the ten second limit and concurrency; a reviewable trail for every AXIS answer without storing learner text; a strong production and portfolio story.
- Positive: CI is unchanged (no-op default, no key, no network).
- Negative: a small amount of span code in the AXIS path, which needs a test that it adds no learner text.
- Negative: judged evals cost money and a real model; they stay owner-run.
- Residual risk: attribute values can still leak text by mistake. The spec adds a guard test (like `tests/test_private_seed_answers.py`) that fails if a span attribute holds a string over a small length or a known learner field.

## 5. Proposed build order (each step stops for the owner's go)

1. SPEC-28: `ITracer`, `NoopTracer`, `LocalTracer`, the no-text guard test, spans on the AXIS path.
2. SPEC-29: metrics and a local report command (latency, refusal rate, static HTML); re-check the ten second limit and concurrency of two. SPEC-29b (live owner-only dashboard page) only after the owner picks it and an admin gate exists (2.5).
3. SPEC-30: deterministic answer checks in CI and the thumbs up/down signal.
4. Later, only if wanted: OpenTelemetry adapter, then Langfuse; judged evals with a printed estimate.

Step 9 of ADR-0035 (query rewriting and a bounded retry) is not touched here; if built, it adds spans through the same port.

## 6. What is confirmed, inferred, unknown

- Confirmed: the ten second limit and concurrency of two are settings today (ADR-0035 section 5); the owner approved observability on 2026-11-16 as provider agnostic.
- Inferred: a local JSON-lines adapter is enough for the first review of the numbers.
- Unknown: which vendor UI, if any, the owner wants; whether judged evals are worth their cost after the deterministic ones exist.
