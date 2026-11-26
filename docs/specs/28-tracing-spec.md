# SPEC-28: AXIS tracing behind `ITracer` (ADR-0035 plan step 8, first of three specs)

Status: **Approved by the owner 2026-11-20** ("Go, all six as recommended"): spec and the six open points in section 7 as recommended. Next step is tests first; no code until the tests are written and shown failing.
Implements: ADR-0037 sections 2.1, 2.2, 2.8 and 2.9 (port, adapters, what is traced, the attribute allow-list, the failure rule); the "default tracer" part of section 4 (confirmed). Does **not** implement: the mode-usage report, the static HTML report, thumbs (SPEC-29); the obedience eval and `AXIS_TEMPERATURE` (SPEC-30); any vendor adapter (ADR-0038 later).
Governed by: AGENTS.md (zero-cost development, `MOCK_AI=true` offline), ADR-0022 (interaction log), ADR-0025 (providers, metering), ADR-0035 section 5.4 (timeout and concurrency), ADR-0036 (start-up validation pattern).

## 0. What the code shows (checked 2026-11-19; three corrections to ADR-0037)

1. **There is no single metering place.** `UsageMeter.record` is called from 11 sites: five in `gemini_companion.py` (`consult`, `stream`, `document_draft`, `build_feedback`, `concept_check`) and six in `local_llm_companion.py` (the same five, with `stream` recorded in two places). The settings ping does not record. The meter exists only when a profile and a meter are set, and `MockAxisCompanion` never meters. ADR-0037 section 2.2 said all call kinds pass "one place in each companion adapter". That is not true, so the **anchor is the `ProviderRouter` entry points** (`consult`, `stream`, `judge_explanation`, `draft_readme`, `summarise_feedback`) plus the route that starts the trace. The router is the one place every adapter, including the mock, passes through. `connection_test` (the settings ping) is **not** an interaction and gets no trace.
2. **`build_review` does not call a model on every path.** `build:feedback` (app.py, `feedback_on_my_build`) always runs `check_requirements` (which may run learner code in the runner) and `build_feedback_points` (plain rules, no model). A model is called only through `axis.summarise_feedback(...)`, and only when `axis` has that method: with `MOCK_AI=true` it is the mock (no real model); with a real profile and no key it raises `DraftFailed` ("AXIS is not set up") before any call; with a key it calls the model; on `BudgetExceeded` or any error it raises `DraftFailed`. So the `model_call` span is **conditional** for `build_review`.
3. **The interaction id is minted after the call today.** `log_event` mints `interaction_id` when none is passed, after the answer exists (`consult_axis`, `check_my_build`, `draft_my_readme`). Only the concept check mints it, and only after `judge_explanation`. For the trace and the ADR-0022 log to join, each route must mint the id **before** the call and pass it to `log_event(interaction_id=...)` (R9).

Also found, relevant to the design:

4. **`RetrievedPassage`** carries `passage_id`, `source_id`, `source_name`, `text`, `score` and **no path or heading field**. The `source_id` already is the path (for example `how-to/tmp_path`, SPEC-26). A heading in the span would need a new field on a core contract, so it is not in this spec (open point 7.2).
5. **`last_retrieval` is a per-companion attribute** written on every answer and read by the routes (`retrieval_fields(axis)`). Two overlapping requests can overwrite each other. Spans must use the `RetrievalTrace` that `ground_with_trace` returns for that turn, never `last_retrieval`. This spec does not change that existing behaviour.
6. **`Grounding.cited_for(reply)`** (passage_safety.py) already returns the cited `passage_id` list and is called from `axis_rules.finish_reply` and `axis_stream.stream_axis`. That is the `citation_check` point.
7. **Streaming runs the model lazily.** `stream_reply` (`/api/v1/axis/stream`) returns a `StreamingResponse` over a generator; the model call happens while it is iterated, after the route function has returned. The trace must be opened and closed inside that generator.
8. `data/` is git-ignored, so `data/traces/` needs no new ignore rule.
9. `lms serve` runs `uvicorn.run("lms.api.app:create_default_app", factory=True, ..., reload=True)` (`src/lms/__init__.py`); `create_default_app` builds the router with `build_default_router`.

## 1. Why

ADR-0035 section 5.4 sets a ten second search limit and two concurrent searches and says both are "measured again in step 8". There is no run-time record of where an AXIS turn spends its time or how it ended. This spec adds the recording layer and nothing else: no report, no new learner feature, no behaviour change.

## 2. Requirements

### The port and its rules
- R1. `ITracer` is a `Protocol` in `src/lms/core/tracing.py` with its own types and **no vendor import**: `span(name, **attributes)` returns a context manager that yields a span handle with `set(**attributes)`; `event(name, **attributes)`. Spans nest through an ambient context (`contextvars`), so a child opened inside a parent is linked without passing a handle.
- R2. **A tracer never raises into the caller.** Every public tracer method and the span context manager catch their own exceptions, log the failure class **once per process** (not per call), and carry on. A failure to open a span yields a no-op handle. An exception raised by the *caller's* code inside a span still propagates unchanged and marks the span `status="error"` with the exception **class name only**.
- R3. `lms.core.tracing` exports `span(...)`, `event(...)` and `set_tracer(tracer)` that act on the process tracer (default `NoopTracer`). Core and adapter code call these, never an adapter class.
- R4. A span records: `trace_id`, `span_id`, `parent_id`, `name`, `started_at_ms`, `duration_ms`, `status` (`ok` or `error`), and its attributes. Times come from the clock; **no wall-clock value is stored in an attribute**.

### Adapters and selection
- R5. `NoopTracer` does nothing, allocates nothing per span beyond the shared no-op handle, and is the default when `LMS_TRACER` is unset in tests and CI.
- R6. `LocalTracer` writes one JSON object per finished span to `data/traces/axis-trace.jsonl` (folder from `LMS_TRACE_DIR`). One line per span, `sort_keys`, UTF-8, `\n` line ends. **Size cap:** `LMS_TRACE_MAX_BYTES` (default 10,000,000; a whole number from 100,000 to 1,000,000,000). When the file would pass the cap it is renamed to `axis-trace.jsonl.1` (replacing any older one) and a new file starts. **One rotated file only.** No network, no new table, no thread that can outlive the process: writes are synchronous, short, under a lock.
- R7. `LMS_TRACER=noop|local` (case-insensitive, trimmed). **Unset means `noop`**, except that `lms serve` sets the default to `local` before it starts the server (`os.environ.setdefault`), so a developer running the app records without setting anything (ADR-0037 open point 4.1, confirmed). Any other value stops start-up with a plain message that lists the choices, like `LMS_RUNNER` (ADR-0036), **even when `MOCK_AI=true`**. A folder that cannot be created or written is a start-up message for `local` and never a crash while serving (R2 applies once running).
- R8. The tracer is built once in `create_default_app` / `build_default_router`, logged at start-up as `Tracing: local dir=... max_bytes=...` or `Tracing: off (noop)`, and set with `set_tracer`. `create_app(...)` keeps working with no tracer argument (tests unchanged, `NoopTracer`).

### What is traced
- R9. **One trace per interaction, named by kind, root span name = kind.** Kinds: `axis_question`, `concept_check`, `readme_draft`, `build_review`. Each route **mints the `interaction_id` first** (`new_ulid`) and passes it both to the root span (attribute `interaction_id`) and to the `log_event(interaction_id=...)` call that logs the same interaction, so the trace and the ADR-0022 log join on it. Where the route already mints one (concept check) it is moved ahead of the model call.
- R10. Routes and roots:
  - `axis_question`: `consult_axis` (`/api/v1/axis/consult`) and `stream_reply` (`/api/v1/axis/stream`). For the stream, the root is opened and closed **inside the generator** (finishing on `done`, `error`, client disconnect or exception), never in the route function (finding 7). A blocked request (cold check, `axis_blocked`) produces a root with `status="ok"` and attribute `blocked=true`, and no children.
  - `concept_check`: `evaluate_explanation` (`.../explain`), including the `no_rubric` and `ai_off` outcomes (root only, attribute `not_judged_reason`).
  - `readme_draft`: `draft_my_readme` (`build:draft-readme`).
  - `build_review`: `feedback_on_my_build` (`build:feedback`). The sibling `build:check` (`check_my_build`, event `verify`) never calls a model and is not an AXIS interaction, so it gets no trace.
- R11. Child spans (names fixed): `retrieve` (in `axis_rules.ground_with_trace`, only on `axis_question`), `prompt_build` (where `build_system_prompt` and `build_user_message` are called), `model_call`, `citation_check` (around `Grounding.cited_for`, only on `axis_question`), `check_requirements` and `feedback_points` (on `build_review`, no model). `model_call` is emitted **by `ProviderRouter` around each entry point's call into the companion** (`consult`, `stream`, `judge_explanation`, `draft_readme`, `summarise_feedback`) and also around the mock companion, with `mock=true`. Adapters add no `model_call` span; they may add attributes to the current span through `tracing.span`'s handle (`input_tokens`, `output_tokens`, `model_answered`) at their existing `_record` call.
  - `build_review`: `model_call` appears **only when** `summarise_feedback` is called (finding 2). A `DraftFailed` sets `status="error"` with `reason` from a fixed set (`not_set_up`, `budget`, `provider_error`, `empty`), never the provider's text.
  - `concept_check`: `model_call` is absent for `no_rubric`, `ai_off` and `not_judged("ai_off")` from a missing key.
- R12. **Exactly one `model_call` span per model call** (or none where the call is skipped) on every route and every path, including streaming, the mock, the budget refusal (`status="error"`, `reason="budget"`) and the labelled mock fallback inside `OpenAICompatibleCompanion` (attribute `fallback=mock`).
- R13. **Link to `model_usage`:** v1 links by the shared fields. The `model_call` span carries `call` (the `CALLS` name), `profile_id`, `model_answered`, `input_tokens`, `output_tokens`; with `started_at_ms` and `duration_ms` a reader can match the `model_usage` row written in that window. The `model_usage` table stays the only money record; traces carry **no cost**. A `usage_id` column link is open point 7.4.

### Attributes
- R14. **Allow-list.** A span attribute is accepted only if its key is in `ALLOWED_ATTRIBUTES` (a frozen set in `lms.core.tracing`) and its value passes the type rule below; otherwise the attribute is **dropped and counted** (`dropped_attributes` on the span, an integer). The initial set:

  | Key | Type |
  |---|---|
  | `interaction_id`, `trace_id`-related ids | string matching `^[A-Za-z0-9_-]{8,64}$` |
  | `kind`, `call`, `mode`, `source_state`, `retrieval_mode`, `retrieval_status`, `status`, `reason`, `not_judged_reason`, `error_class`, `profile_id`, `model_answered` | short string (at most 80 characters), no whitespace run longer than one space |
  | `unit_id` | string matching the unit id pattern |
  | `index_version` | hex string (12 or 64 characters) |
  | `downgraded`, `mock`, `fallback`, `blocked`, `test_mode`, `stream` | bool (`fallback` is a short string `mock` or absent) |
  | `terms_matched`, `terms_total`, `passages_retrieved`, `passages_cited`, `input_tokens`, `output_tokens`, `dropped_attributes` | non-negative integer |
  | `latency_ms`, `duration_ms` | non-negative integer |
  | `passage_refs` | list of at most 10 objects `{passage_id, source_id, score}`; `passage_id` of 8 to 200 characters from `A-Za-z0-9._/@#~-` (the real shape is `source@version#c0-120~digest`), `source_id` a course or upstream path (at most 200 characters, no spaces), `score` a finite number rounded to 4 places |
  | `cited_passage_ids` | list of at most 10 passage ids (same rule as `passage_id`) |
  | `prompt_version` | exactly 12 lowercase hex characters (added 2026-11-26, SPEC-31 R13) |

- R15. **Never in any span:** the learner's question, answer, explanation, code, README or review note; passage text; model reply text; keys, tokens, URLs, file paths on the learner's machine. This holds even with `test_mode` and even if a caller passes such a key (R14 drops it). A `unit_id` or `source_id` value is a course reference, not learner text.
- R16. **Passage refs.** The `retrieve` span lists, per returned passage, `passage_id` (the `make_passage_id` hash), `source_id` and `score`, plus the turn's `index_version`, `retrieval_mode`, `retrieval_status`, `terms_matched`, `terms_total`, `downgraded` and `latency_ms`, **taken from the `RetrievalTrace` returned for that turn** (finding 5). The `citation_check` span lists `cited_passage_ids` from `Grounding.cited_for` and `passages_cited`. `passage_id` changes when the index is rebuilt and is for tracing only; nothing in the eval anchors reads it (ADR-0037 2.2).
- R17. `test_mode=true` (ADR-0019 amendment) traces are **recorded** with `test_mode=true` so the later report can exclude them (SPEC-29); this spec does not drop them.

### Failure and safety
- R18. A failing tracer (raises on open, set, write or close; full disk; unwritable file; slow disk) leaves the learner's reply, status code, streamed events and interaction-log row **byte-for-byte the same** as with `NoopTracer`. A write that takes longer than 200 ms is not interrupted (it is synchronous) but is counted once; a second consecutive failure disables the writer for the rest of the process with one log line (so a dead disk costs one write attempt, not one per span).
- R19. `NoopTracer` and `LocalTracer` are safe under the app's thread pool: concurrent spans from different requests never share a parent (the ambient context is per request or per generator iteration) and the file lock is held only for the write.
- R20. No span, attribute or log line made by tracing contains an API key or a URL (profile ids and model ids only).

## 3. Settings
`LMS_TRACER` (`noop` | `local`), `LMS_TRACE_DIR` (default `data/traces`), `LMS_TRACE_MAX_BYTES` (default 10,000,000). Read once at start-up beside the other retrieval and runner settings; invalid values stop start-up with a plain message.

## 4. Traceability (spec to ADR-0037)
| Requirement | ADR-0037 |
|---|---|
| R1 to R4 | 2.1 (port, never raises) |
| R5 to R8 | 2.1 adapters and `LMS_TRACER`, 4.1 default tracer |
| R9 to R13 | 2.2 trace kinds, shared `interaction_id`, `model_usage` link, per-kind test |
| R14 to R17 | 2.2 allow-list and passage refs, no learner text |
| R18 to R20 | 2.8 failure rule |
| Correction of the "one metering place" sentence | 2.2 (amended in this change, see section 8) |

## 5. Tests first (names; written and failing before any code, after the owner's go)
`tests/test_tracing.py` unless noted.
- Port and rules: `test_noop_tracer_does_nothing`, `test_spans_nest_through_ambient_context`, `test_a_failing_tracer_never_raises_into_the_caller`, `test_tracer_fault_is_logged_once_per_process`, `test_exception_in_caller_code_propagates_and_marks_span_error_with_class_name_only`.
- Local adapter: `test_local_tracer_writes_one_sorted_json_line_per_span`, `test_local_tracer_rotates_to_one_file_at_the_cap`, `test_local_tracer_second_rotation_replaces_the_old_one`, `test_local_tracer_survives_unwritable_dir_after_startup`, `test_local_tracer_disables_after_second_consecutive_write_failure`.
- Settings: `test_tracer_setting_default_is_noop`, `test_tracer_setting_rejects_unknown_value_even_with_mock_ai`, `test_lms_serve_defaults_tracer_to_local`, `test_trace_max_bytes_bounds`.
- Allow-list and guard: `test_non_allow_listed_key_is_dropped_and_counted`, `test_value_type_rules_are_enforced`, `test_guard_no_span_carries_learner_text` (a recording tracer plus real routes with distinctive learner strings in question, answer, code, README and review note; **fails if any of those strings appears anywhere in any recorded span**), `test_guard_every_recorded_key_is_allow_listed`, `test_guard_no_url_or_key_in_any_span`.
- One trace per kind with a fake companion injected through the router factory: `test_axis_consult_makes_exactly_one_axis_question_trace`, `test_axis_stream_makes_one_trace_closed_at_done`, `test_axis_stream_trace_closes_on_error_and_on_disconnect`, `test_concept_check_makes_one_trace_with_one_model_call`, `test_concept_check_without_rubric_has_no_model_call`, `test_readme_draft_makes_one_trace`, `test_build_review_has_no_model_call_without_summary_path`, `test_build_review_with_summary_has_one_model_call`, `test_build_review_draft_failed_sets_reason_from_fixed_set`, `test_mock_path_also_gets_one_model_call_with_mock_true`, `test_budget_refusal_sets_error_reason_budget`, `test_local_llm_mock_fallback_sets_fallback_attribute`, `test_connection_test_makes_no_trace`.
- Join and refs: `test_trace_interaction_id_equals_logged_interaction_id_for_each_kind`, `test_retrieve_span_lists_passage_refs_from_the_turns_own_trace`, `test_two_overlapping_requests_do_not_mix_retrieval_attributes`, `test_citation_check_span_lists_cited_ids`, `test_test_mode_requests_are_recorded_with_flag`.
- Unchanged behaviour: `test_replies_identical_with_noop_local_and_failing_tracer` (consult, stream, concept check, README, build review), and the full existing suites unchanged.

## 6. Chaos check (step 5 of the loop; each becomes a test or a recorded finding)
- Learner text hidden in a place a caller might pass it: a `unit_id` of 10 KB; a `mode` containing a newline; a `reason` that is the provider's error text; a passage text smuggled in `passage_refs`; `score` of `NaN` or `inf`; a 10 MB attribute list.
- File problems: trace folder is a file; file is read-only; disk full mid-line (a torn last line must not break the next write); two processes (the reloader) writing the same file; cap smaller than one line; clock going backwards.
- Streaming: client disconnects at the first token; the generator is closed early; the model raises after the first delta; thousands of deltas must not create thousands of spans (one `model_call` span, not one per delta).
- Concurrency: 50 threaded requests with a `LocalTracer`; ambient context leaking from a finished request into the next in the same worker thread.
- `LMS_TRACER=LOCAL`, ` local `, `""`, `0`; `LMS_TRACE_MAX_BYTES` of `abc`, `-1`, `1e9`, `10**12`.
- A tracer that blocks forever or raises `BaseException` subclasses such as `KeyboardInterrupt` (must not be swallowed; only `Exception` is).

## 7. Open points (decided by the owner 2026-11-20: all six as recommended)
1. **Where `model_call` lives.** This spec puts it in `ProviderRouter` (one place for all adapters and the mock) and gets tokens from the existing `_record` site. The alternative, a span inside each of the 11 adapter sites, gives sharper timing around the SDK call but is 11 edits and misses the mock. Recommended: the router.
2. **Heading or title in `passage_refs`.** `RetrievedPassage` has no heading field today; `source_id` already carries the path. Adding a heading needs a new field on a core contract and re-measuring. Recommended: not in SPEC-28.
3. **Trace file location and size.** Default `data/traces/` (git-ignored), 10 MB, one rotation. Recommended as is.
4. **Joining to `model_usage`.** Time-window match (this spec) or return the new row id from `UsageStore.add` and put `usage_id` on the span (touches the meter and 11 `_record` sites). Recommended: window in v1, `usage_id` only if the report needs an exact join.
5. **`test_mode` traces.** Recorded with a flag (R17). Alternative: not recorded at all. Recommended: recorded with the flag.
6. **A tracer write that is slow.** v1 is synchronous with a disable-after-two-failures rule (R18). A background writer thread would be faster but adds a thread and a shutdown story. Recommended: synchronous.

## 8. Change made alongside this spec
ADR-0037 section 2.2, the sentence "All five call kinds already pass the one place in each companion adapter ..." is replaced by the router-anchor wording, and the section 6 "Confirmed" note is corrected (findings 1 and 2).

## 9. Out of scope
The mode-usage report, the static HTML report and thumbs (SPEC-29); the obedience eval and `AXIS_TEMPERATURE` (SPEC-30); OpenTelemetry, Langfuse and the LangSmith eval-only adapter (ADR-0038); any HTTP endpoint or dashboard; changing `last_retrieval`; retention beyond one rotated file; sampling.

## 10. Deviations and additions made at the code step (2026-11-20)
Found while writing the code; each is small and recorded here so the spec matches what was built.
1. **Build review route.** The build review is `build:feedback` (`feedback_on_my_build`), not `build:check`. `build:check` calls no model and is not traced (section 0, finding 2, and R10 are corrected above). The tests post to `build:feedback`.
2. **Passage id shape.** Real ids look like `source@version#c0-120~digest`, not hex. R14 now allows that character set (8 to 200 characters). The first draft said hex, which would have dropped every real passage id.
3. **Port details the spec left open** (all in `lms.core.tracing`): `ISpan` has `set(**attributes)` and `fail(reason)`; a tracer's `span` and `event` also receive the ambient `parent` span as a keyword; `annotate(**attributes)` adds attributes to the span open now (used for token counts and `fallback`); `token_attributes` and `passage_refs` build attribute values; `pinned_context(generator)` runs every step of a stream in one captured context.
4. **Stream context (R10).** The server may run each step of a stream in a copy of the context, which would lose the parent span between yields. The stream route wraps `events()` in `pinned_context`. A reader who leaves a stream (`GeneratorExit`) closes the spans with status `ok`, not `error`.
5. **Prompt spans.** `axis_rules.build_prompts(query, grounding)` builds the system prompt and the user message inside one `prompt_build` span; the four adapter call sites use it. The `retrieve` span is inside `ground_with_trace` and the `citation_check` span is inside `Grounding.cited_for`, so every caller is covered.
6. **Module names fixed by the tests:** `lms.core.tracing`, `lms.adapters.observability.local_tracer` (`LocalTracer`), `lms.adapters.observability.startup` (`build_tracer`, `TracerConfigError`, `describe`). `create_default_app` builds and sets the tracer and logs `Tracing: ...` once.
7. **Tests added beyond the list:** the stream-disconnect tests (three, in `tests/test_tracing.py`, section 5), a blocked-request test for both consult and stream, and a threads-never-share-a-parent test. The disconnect test is at the generator level because `TestClient` cannot disconnect mid-stream.
