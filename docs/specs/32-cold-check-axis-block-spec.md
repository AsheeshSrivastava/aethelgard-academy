# SPEC-32: AXIS is unavailable while a Cold Check round is open (ADR-0040)

Status: **Draft 2026-11-26, waiting for the owner's go.** No test or code.
Implements: ADR-0040 option A. Builds on: ADR-0003, ADR-0019, ADR-0028, ADR-0032 (rounds), SPEC-12 sections 7 and 8, SPEC-16 (stage review and rechecks), ADR-0022.
Does **not** implement: a "leave the Cold Check" button, multi-learner identity, blocking concept-check feedback or draft/feedback features (open point 1), anything about tools outside the product.

## 1. Requirements

### A. When a round is open
- R1. A **round** is a unit Cold Check, a stage review or a recheck (the items that run with AXIS off).
- R2. A round **opens** when the server first serves one of its items to the learner.
- R3. It **ends** when the first of these happens: (a) every item of the round has an attempt (the existing end of a round: outcome recorded); (b) **expiry**: 60 minutes have passed since the last item was served or attempted; (c) the round is replaced by a new one for the same unit, which re-opens under R2.
- R4. Test mode (ADR-0019 amendment) uses a **2-minute** expiry, so tests are quick and nothing is locked for an hour.
- R5. The scope is **the whole learner**: any open round, on any unit or stage, closes AXIS everywhere.
- R6. "Open" is derived from stored facts (the served-item pointer and the attempts), not from a flag the client sends. No new client field.

### B. What refuses
- R7. While a round is open, `POST /api/v1/axis/stream` and `POST /api/v1/axis/consult` refuse **whatever the request carries**, with the 403 problem today's Cold Check block uses, before any model call or retrieval.
- R8. The existing `exercise_id` check stays as a second guard (it also refuses a Cold Check item when no round is open).
- R9. Other model features (concept check, README draft, build feedback, the settings ping) are unchanged.

### C. What the learner sees
- R10. The refusal carries `title` "AXIS is off", the message below in `detail`, and `available_again_at` (ISO 8601, UTC) in the problem body.
- R11. Message: "AXIS is unavailable while your Cold Check is open. Finish the Cold Check to get AXIS back sooner. Otherwise it returns at {time} ({minutes} minutes from now)." `{time}` is the learner's local clock time shown by the panel; `{minutes}` is rounded up.
- R12. The AXIS panel, on any tab, shows that message in place of the input (and when a send is refused), with a link back to the Cold Check. It does not poll; it updates on the next send or page load.

### D. Records
- R13. A refused request writes **no** interaction-log row (as today's 403) and no assistance row. Tracing records the existing `blocked` attribute.
- R14. Unchanged: evidence is recorded `none` for Cold Checks; builds stay Socratic and are not blocked; the concept-check soft gate; the ledger is never rewritten.

## 2. Tests first (written and failing before any code), `tests/test_cold_check_axis_block.py` unless said
- R1 to R6: `test_round_opens_when_an_item_is_served`, `test_round_ends_when_every_item_is_attempted`, `test_round_expires_after_60_minutes_without_activity`, `test_serving_or_attempting_restarts_the_expiry`, `test_test_mode_expiry_is_two_minutes`, `test_a_new_round_reopens`, `test_stage_review_and_recheck_rounds_also_close_axis`, `test_a_round_on_one_unit_closes_axis_on_another`.
- R7, R8: `test_second_tab_without_an_exercise_id_is_refused` (**the regression test for the gap**, consult and stream), `test_refused_before_retrieval_or_model_call`, `test_cold_check_item_id_still_refused_with_no_open_round`, `test_normal_use_is_unaffected_when_no_round_is_open`.
- R9: `test_concept_check_and_drafts_are_unaffected`.
- R10 to R12: `test_refusal_body_has_message_and_available_again_at`; frontend `AxisPanel.test.tsx`: shows the message with the time and minutes, link back, input disabled.
- R13, R14: `test_refused_requests_write_no_log_or_assistance_row`, `test_ledger_and_grading_are_unchanged`.

## 3. Chaos check
An item served and never answered; the server restarts mid-round; the clock moves back; two tabs finishing at once; a round reopened after expiry; an attempt arriving after expiry; a very old pointer from before this change (must not close AXIS for ever); `progress reset` mid-round; unknown unit or stage in a stored pointer.

## 4. Open points for the owner (recommendations)
1. Also refuse concept-check feedback while a round is open? **No for the first version** (recorded as gap 4).
2. Test-mode expiry of 2 minutes (**yes**).
3. Count refusals anywhere? **No** (no new log row); tracing already marks them blocked.
