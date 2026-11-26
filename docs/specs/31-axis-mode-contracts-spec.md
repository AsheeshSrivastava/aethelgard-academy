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

### Clarifications (2026-11-26, taken as recommended; owner to confirm at review)
1. A `--replay` run's `results.json` carries no `prompt_versions` (no prompt was sent).
2. A concept check that is not judged records no `prompt_version` in the interaction-log event; the `model_call` span may carry it, since the call happened. The same rule holds for a draft or build-feedback summary that fails after the call.
3. An eval run where every call fails still lists the versions of the modes and states that ran.
4. The same step name in a different unit is a new step: the suggested starting mode applies again.
5. A concept check with more or fewer ideas gets the same version.
6. The catalogue does not list the retired explain-error question.

## 9. Amendment A (**Proposed** 2026-11-27; no test or code until the owner says go)
Implements ADR-0039 section 8. Amends section 3.4, SPEC-07 section 2.1 (what counts as code) and SPEC-30 checks (b) and (d).

### 9.1 No-source contract wording (replaces part of section 3.4; all three modes)
- "restate their question in their words" becomes "restate what they asked for".
- Added at the end:
> When their question, code or run output shows an error or a traceback, do not say what the error or its message means, what caused it, or what the values in it must be. Do not write "means" or "because" about it. Point at one line number or function name to look at, then ask what they expected to happen there and what they have checked. Do not copy their code or the traceback into your reply; point at it by line number or name.

With a course source nothing changes (not measured yet; plan step 5c). Every no-source `prompt_version` changes, and the catalogue is regenerated.

### 9.2 What the guard counts as code
- A1. `def` counts only as `def name(`; `class` only as `class Name:` or `class Name(`; `import x` and `from x import y` only at the start of a line.
- A2. The rule "the word return and a bracket anywhere" is replaced: `return` counts at the start of a line followed by something, or inside a sentence only when followed by a call (`name(`) or an operator.
- A3. Fenced blocks (three backticks or `~~~`), code lines and assignments count as today.
- A4. **The learner's own words.** A backtick span that occurs in the learner's text (question, code or error output; whitespace collapsed) is left out before A1 to A3 are applied, and is shown unchanged. It does not apply to fenced blocks or to code written without backticks. So the guard receives the learner's text, both for a whole reply and for the streamed one.
- A5. `AssistanceClassifier` uses the A1 to A3 detector (so English no longer counts as code) and does **not** use A4. What counts as supplied reasoning is otherwise unchanged (ADR-0039 decision 4).

The app streams replies, and there only the offending sentence is dropped before the notice; the eval scores the whole-reply path, where more can be lost. Both paths follow A1 to A4.

### 9.3 Eval: checker version C and more error questions
- C1. (b): `[n]` written directly after a name, `]` or `)` is an index, not a source label, by the same rule that already keeps it in the shown reply. A label standing alone still fails, including one the learner typed (Amendment A2 of SPEC-30 is unchanged). All 10 (b) failures of the new run were indexes in the learner's own code.
- C2. (d): uses the detector of 9.2 with the learner's text. SPEC-30 B2 (foreign inline code fails) is unchanged, and a fenced block still fails.
- C3. `results.json` says `checker_version: "C"`. Old runs are not rewritten. `--replay` of an old `replies.jsonl` rescores the raw replies under C for a like-for-like comparison (free, no model); the learner-visible text stored then was made by the old guard and cannot be recomputed.
- E1. New file `eval/obedience/error-items.yaml`: 18 made-up error-message questions (invented code and traceback; questions only, no answers). It has its own version and its own table (replies, explains flags, (b), (d)), kept **out** of the existing totals, so those stay comparable. Every one of these replies goes into `review-sample.md`. The run grows from 756 to 918 replies per temperature.

### 9.4 Tests first
`test_no_source_contract_has_the_error_rule_in_every_mode`, `test_no_source_contract_no_longer_asks_to_restate_their_question`, `test_plain_english_with_class_import_or_return_is_not_code`, `test_return_followed_by_an_expression_is_code`, `test_def_and_class_headers_are_code`, `test_a_quoted_learner_span_is_kept`, `test_a_span_the_learner_did_not_write_is_withheld`, `test_a_fenced_copy_of_learner_code_is_still_withheld`, `test_the_stream_keeps_a_quoted_learner_span`, `test_classifier_does_not_mark_plain_english_as_supplied_reasoning`, `test_b_passes_an_index_and_still_fails_a_lone_label`, `test_checker_version_is_c`, `test_error_items_are_reported_apart`. All strings are made up. Two existing SPEC-30 and SPEC-07 expectations may need to change; each change is listed in the PR.

The real replies from the run stay on the owner's machine. A scratch prototype of A1 to A4 (not repo code, run on them 2026-11-27): 16 of the 23 withheld replies pass, the 7 with a code block stay withheld, and no reply that passes today becomes withheld, in these two runs and the two earlier ones. The tests and a replay after the code must confirm this.

### 9.5 Chaos check
A learner span of one character; a span that matches only after whitespace is collapsed; an indentation change quoted inline; unbalanced backticks; a span split across stream pieces; learner text holding backticks; `return` at the end of a reply; a non-Python traceback.

### 9.6 Open choices for the owner (recommendation first)
1. **Error messages:** (a) wording only, then measure; (b) also have the server send a fixed question whenever there is no source and an error is present (certain, but robotic).
2. **Target after the re-run:** (a) the explains flag on at most 5 percent of error-message replies, else return to 1(b); (b) no pass mark. The flag is a word-based heuristic, so the replies are also read by hand.
3. **Quoting the learner's code:** (a) allowed inline (A4), blocks still withheld; (b) never allowed, fix only the English false hits.
4. **Checker C:** (a) in this amendment; (b) separately, later.
5. **Plan item 8c** (move the detector from `adapters` into `core`): it is the same code. (a) a separate move-only PR afterwards, so the behaviour change stays easy to review; (b) do both together.
