# SPEC-34: A fixed reply for error questions with no course source (local model)

Status: **Draft 2026-11-27, waiting for the owner's go** on this spec and the choices of section 8. No test or code.
Implements: ADR-0041 section 5 (the fallback kept for this case). Decided by the owner 2026-11-27: use it with the local model; OpenAI stays a Settings choice and needs no change.
Needs first: SPEC-24 section 10 (PR #84) and SPEC-33 stage 1 (PR #83, which sends the run error to AXIS).

## 1. Why
With no course source, the local model states the cause of a pasted error in about half of its replies (stricter count) although told not to. Wording did not fix it. Figures: `docs/plan/axis-learning-limits.md`.

## 2. When it applies (all of these)
- R1. The turn has **no course source** (`source_state` is `not_found`, `no_index` or `unavailable`).
- R2. The active model profile has `fixed_error_reply: true` in `config/providers.yaml`. Set on `local` only.
- R3. It is an **error turn**:
  - the question holds a traceback: `Traceback (most recent call last)`, a line `File "…", line N`, or a name ending in `Error` or `Exception` followed by a colon; **or**
  - a run error came with the turn **and** the question is about it: it holds one of the frozen words `why, error, fail, wrong, work, crash, stuck, help, fix, broke, traceback, exception` (choice 1).
  - Measured on the eval sets: the first rule matches all 24 error questions and none of the 78 others.

## 3. The reply (learner-facing; owner approval needed)
The usual state sentence (SPEC-24 R3), then, when a line number and error name can be read from the error:
> Look at line 3, where the KeyError is reported. What did you expect that line to do, and what have you checked so far?

otherwise:
> Look at the line your error points to. What did you expect that line to do, and what have you checked so far?

- R4. "3" is the line of the last `File` frame that is not the app's run harness. "KeyError" is the name on the error's last line; **its message is never used**. If either is missing or odd, the second form is used.
- R5. One question; no cause, no fix, no code, nothing from memory; the same in every mode.

## 4. Behaviour
- R6. **The model is not called.** The search still runs, to know there is no source. No cost, no wait.
- R7. Consult returns it; stream sends it as the whole reply. `source_state` is as usual, so the panel's note shows.
- R8. Assistance level: `none`.
- R9. Interaction log: the answer as shown, plus `fixed_reply: true`; no `prompt_version` (nothing was sent). Traces: no model call span; no new attribute.
- R10. Not for: the mock companion, a Cold Check (refused earlier), concept check, drafts, build feedback, or any profile without the flag.

## 5. Eval
The obedience eval reports fixed replies apart. With the local profile every error item (pasted, and as run output) must be a fixed reply, with no explains flag and no causal statement; no model call is made for them. Other questions are unaffected, compared on the same cases.

## 6. Tests first (names, written and failing before code, after the go)
`test_a_pasted_traceback_gets_the_fixed_reply`, `test_a_run_error_with_a_question_about_it_gets_it`, `test_a_run_error_with_an_unrelated_question_does_not`, `test_the_line_and_error_name_are_read_from_the_last_learner_frame`, `test_the_error_message_is_never_repeated`, `test_no_model_call_is_made`, `test_only_a_profile_with_the_flag`, `test_not_with_a_course_source`, `test_mock_is_unaffected`, `test_consult_and_stream_agree`, `test_the_log_says_fixed_reply_and_no_prompt_version`, `test_assistance_is_none`, `test_all_error_items_are_detected_and_no_other_question`.

## 7. Limits, known in advance
It teaches nothing: it is the same question every time. A conceptual question that names an error ("what is a `KeyError:`?") gets it too, though without a source AXIS could not have answered from memory anyway. An error message in an unusual shape falls back to the model. With a course source, errors are answered by the model as today, which is unmeasured.

## 8. Choices for the owner (recommendation first)
1. **A held run error:** (a) fixed reply only when the question is about it (the word list); (b) for every question while an error is held; (c) only for pasted tracebacks.
2. **The reply:** (a) name the line and error when readable; (b) always the general form.
3. **Add a small action** to the reply, such as "Then write what you expected next to what happened": (a) not now; (b) add it.
4. **Gemini profile:** (a) leave the flag off, untested; (b) on.
