# SPEC-31: AXIS mode contracts and a record of every prompt (ADR-0035 plan step 8b)

Status: **Approved by the owner 2026-11-26**, with the four open points of section 8 decided as recommended. Next step: tests first (section 5), then code. No test or code is part of the docs change that adds this file.
Implements: ADR-0039 sections 2.1 to 2.6 and its decisions 1 to 6.
Builds on: ADR-0009 (Socratic boundary), ADR-0022 (interaction log), SPEC-24 (no-source rules), SPEC-28 (tracing), SPEC-30 (eval).
Does **not** implement: the with-source quality eval (plan step 5c, its own spec), any change to grading (ADR-0039 decision 4), turn history or the offer to switch mode after stalls, retrieval, guardrails, the live temperature.

## 1. What changes
Today the system prompt is base + mode sentence + (course reference or no-source notice). Coach is told to explain and the notice then takes it back, and no place records which wording produced a reply.

## 2. Requirements

### A. Composition
- R1. `build_system_prompt(mode, grounded_context, source_state)` returns, in order: **base rules** (unchanged), then the **mode block**, then the **source block**.
- R2. With a course passage: the mode block is the mode's contract (section 3) and the source block is today's COURSE REFERENCE text plus the passages (unchanged).
- R3. With no passage (`not_found`, `no_index`, `unavailable`): the mode block is the one-line neutral header of section 3.4 (**never** the mode contract, so no instruction to explain is present), and the source block is the no-source contract of section 3.4.
- R4. Socratic keeps the ADR-0009 invariant sentence in **both** cases (section 3.1).
- R5. The user message is unchanged. The concept-check, README, build-feedback and ping prompts are unchanged (SPEC-24 R4b stays).

### B. Starting mode by activity
- R6. The panel preselects a mode from the step's activity: Explain **Coach**; Specify, Decompose, Modify (also the playground), Evaluate, Direct **Hybrid**; Predict, Trace, Debug & Validate **Socratic**. The suggestion keys on the activity name. An unknown **step** is already mapped to `Explain` by `activityFor` (`frontend/src/lesson/steps.ts:17`), so it gets Coach; only an activity name outside the list above falls back to Socratic.
- R7. The learner can change it; their choice holds while they stay on that step; a new step applies that step's suggestion.
- R8. Builds stay Socratic and cannot be changed (as today, panel and server).
- R9. No server behaviour depends on the suggestion: the request still carries the mode the learner sent.

### C. Prompt catalogue
- R10. `scripts/make_prompt_catalogue.py` renders every model prompt (AXIS chat for the three modes, grounded and each no-source state; the user message template; concept-check judge; README draft; build feedback summary; ping; and the fixed runtime-error question of `POST /api/v1/explain-error` while that route exists, which a separate change retires) into `docs/prompts/prompt-catalogue.md`, with placeholders for passages and learner text and no learner data, answer keys or rubric content.
- R11. A test renders it again and fails if the file differs (drift). The output has no date or timestamp, so it only changes when the wording changes.

### D. Prompt version
- R12. `prompt_version` = the first 12 hex characters of SHA-256 over the **static** text of one call: the system prompt and the user-message template with **every variable value** replaced by a fixed placeholder: passages (`<passages>`), learner question, code and stderr, unit and activity, the concept-check question and idea list, the README brief and entry file name, and the build-feedback points and texts. The optional `<learner_code>` and `<execution_stderr>` blocks are always present in the template, so a version does not depend on whether a learner sent code. One version per assembled static prompt (so Socratic no-source `not_found` and `no_index` differ). It is computed by one function that both the catalogue and the callers use; the catalogue prints it beside each prompt.
- R13. It is written to: (a) a new allow-listed attribute `prompt_version` (exactly 12 lowercase hex) on the `model_call` span (amends SPEC-28 R14); (b) a `prompt_version` field in the payload of the interaction-log events that follow a model call: `axis`, `concept_check`, `document_draft`, `build_feedback` (amends ADR-0022 section 2.3); (c) a `prompt_versions` map (mode/state to version) in the eval `results.json` (amends SPEC-30 R14).
- R14. Never the prompt text, never learner text, in any of these places (SPEC-28 R15 unchanged). A version is recorded **only when a prompt was actually sent to a model**: no field for a mock reply, for a concept check that was not judged, for a draft that failed before a call, or for a mock fallback after a failed real call (that reply came from no prompt).

## 3. Contract wording (learner-facing behaviour: owner approval needed)

### 3.1 Socratic, with a source
> MODE: SOCRATIC FACILITATOR.
> STRICT INVARIANT: Under NO circumstances may you output Python code blocks, function definitions, or direct code solutions.
> Draw out what the learner already thinks. Reply with one sentence that restates their question, then one question about their own code, data or reasoning. Never ask more than two questions. Write no code, not even inside a sentence.

### 3.2 Hybrid, with a source
> MODE: HYBRID (PLAN BEFORE CODE).
> State the learner's goal in one line. Then give two or three sub-steps phrased as gaps for them to fill: the inputs, the outputs and how they will know it works. End with one next action. Do not write implementation code. Do not write the plan or the contract for them.

### 3.3 Coach, with a source
> MODE: COACH (EXPLAIN, THEN THEY DO IT).
> Explain briefly and encouragingly, using only the numbered passages, and mark each claim with its label such as [1]. Give one example from the passages. Then set one small task for the learner to try. Keep it to about 150 words. Never write the solution to their exercise.

### 3.4 No course source (all modes)
Mode block (one line, plus the Socratic invariant of 3.1 in Socratic):
> MODE: NO COURSE SOURCE.

Source block:
> NO COURSE SOURCE IS AVAILABLE FOR THIS ANSWER. Do not pretend a course source was used. Do not write source labels such as [1]. Do not name a document, page or book as your source. Begin your reply with this sentence, in your own plain words: "<state sentence>" Then do not give facts, syntax, error explanations or advice from your own memory. Do not explain an error, even in the learner's own code. Do not say what a name you do not recognise is or does, and do not guess. Write no code, not even inside a sentence. Work only from what the learner wrote (the question, the code and the run output): restate their question in their words, ask what they already know or have tried, with at most two questions, or suggest they rephrase or reread this step's lesson text. A question may point at a line of their code; it never states the cause or the fix.

State sentences are unchanged (SPEC-24 R3).

### 3.5 What these contracts leave for later (not in this spec)
ADR-0039 2.2 also asks Socratic to follow up and close with a short check of what the learner concluded, and Hybrid to compare the learner's plan with their stated inputs, outputs and criteria. Both need **turn history** (AXIS answers one turn at a time today), so the wording above does not ask for them and no test in section 5 checks them. They belong with the later step that adds history.

## 4. Existing text this changes (amendments, made in the same PR as the code)
| Place | Today | Becomes |
|---|---|---|
| SPEC-24 R4, last sentence | "The tone differences between modes stay in the mode stance text; only the memory rule is shared." | With no source the mode stance is replaced by the neutral header; the tone differences apply with a source (SPEC-31 R3). |
| SPEC-24 test list item 2 and `tests/test_no_source_rules.py` | asserts "overrides any mode instruction" | asserts that no mode instruction is present with no source |
| SPEC-28 R14 | attribute allow-list | adds `prompt_version` (12 lowercase hex) |
| ADR-0022 section 2.3 table | rows for `axis` and `concept_check`; the code also logs `document_draft` and `build_feedback`, which the table does not list | the `axis` and `concept_check` rows add `prompt_version`; two rows are **added** for `document_draft` and `build_feedback`, each with `prompt_version` |
| SPEC-30 R14 | `results.json` keys | adds `prompt_versions` |

## 5. Tests first (written and failing before any code)
- R1 to R5, `tests/test_mode_contracts.py`: `test_grounded_prompt_has_base_mode_contract_and_reference_in_order` (3 modes); `test_no_source_prompt_has_no_mode_contract` (9); `test_no_source_prompt_has_no_instruction_to_explain` (9); `test_socratic_keeps_the_no_code_invariant_with_and_without_a_source`; `test_no_source_contract_forbids_error_explanations_guessing_names_and_inline_code` (9); `test_coach_with_a_source_asks_for_a_task_and_citations`; `test_hybrid_forbids_implementation_code`; `test_socratic_limits_to_two_questions`; `test_other_prompts_are_byte_for_byte_unchanged`.
- R6 to R9, frontend `AxisPanel.test.tsx`: suggested mode per activity (all ten, plus unknown), override holds on the step, a new step re-suggests, builds locked to Socratic, the request carries the chosen mode.
- R10, R11, `tests/test_prompt_catalogue.py`: `test_catalogue_matches_the_code`, `test_catalogue_has_every_model_prompt`, `test_catalogue_holds_no_learner_or_answer_text`, `test_catalogue_has_no_date`.
- R12 to R14, `tests/test_prompt_version.py`: `test_version_is_12_hex_and_stable`, `test_version_changes_when_wording_changes_not_when_learner_text_changes`, `test_each_mode_and_state_has_its_own_version`, `test_model_call_span_carries_prompt_version_and_no_text`, `test_interaction_log_events_carry_prompt_version`, `test_results_json_carries_prompt_versions`, `test_mock_records_no_version`, `test_unjudged_failed_and_fallback_calls_record_no_version`, `test_version_ignores_unit_activity_rubric_brief_and_optional_blocks`.
- Existing suites: SPEC-24 prompt tests updated only where section 4 says; the SPEC-30 checker is unchanged.

## 6. Chaos check (each a test or a recorded finding)
Unknown activity or mode; the activity changes mid-reply; the learner switches mode during streaming; an unknown `source_state`; a passage containing the placeholder text `<passages>`; learner text containing a mode header; a very long question; the catalogue file edited by hand; two processes rendering the catalogue.

## 7. Measuring the effect
Before and after, the SPEC-30 eval on the local model at the live temperature 0.2 (free, about 25 minutes a pass). No pass mark unless the owner sets one. The prompts change, so the old and new runs are told apart by `prompt_versions`.

## 8. Open points (decided by the owner 2026-11-26: all as recommended)
1. The wording of section 3 is used **as drafted**.
2. The Socratic invariant sentence **stays** in the no-source case (a refinement of ADR-0039 2.4, which says the mode contract is replaced: this keeps that one ADR-0009 sentence).
3. The 150 words for Coach is **guidance**, not a hard limit; the with-source quality eval (plan step 5c) measures it.
4. The concept-check judge, README draft and build-feedback prompts **get a `prompt_version` too** (one function covers all).
