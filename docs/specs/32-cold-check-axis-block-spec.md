# SPEC-32: AXIS is unavailable while a Cold Check round is open (ADR-0040)

Status: **Approved by the owner 2026-11-26** (ADR-0040 decisions: L1, least recently left item when no spare, reviews and rechecks leavable, wording as written, concept-check feedback stays available, refusals not logged). Tests first, then code, after the owner's go.
Implements: ADR-0040 option A. Builds on: ADR-0003, ADR-0019, ADR-0028, ADR-0032 (rounds), SPEC-12 sections 7 and 8, SPEC-16 (stage review and rechecks), ADR-0022.
Includes the **Leave button** (required by the owner). Does **not** implement: multi-learner identity, blocking concept-check feedback or draft/feedback features (decided: they stay available, section 4), anything about tools outside the product.

## 1. Requirements

### A. When a round is open
- R1. A **round** is a unit Cold Check, a stage review or a recheck (the items that run with AXIS off).
- R2. A round **opens** when the server first serves one of its items to the learner.
- R3. It **ends** when the first of these happens: (a) every item of the round has an attempt (the existing end of a round: outcome recorded); (b) **expiry**: 60 minutes have passed since the last item was served or attempted (treated as a leave, R17); (c) the learner **leaves** (R15); A new round for the same scope opens under R2 only after the last one has ended.
- R4. Test mode (ADR-0019 amendment) uses a **2-minute** expiry, so tests are quick and nothing is locked for an hour.
- R5. The scope is **the whole learner**: any open round, on any unit or stage, closes AXIS everywhere.
- R6. The server **stores an open-round record** (learner, round kind and scope, opened at, last item served or attempted at, items left). The existing served-item pointer is not enough: it is cleared after each answer (`api/app.py:1546`) and review pointers are keyed by unit and kind. Nothing is taken from a client flag; there is no new client field.

### B. What refuses
- R7. While a round is open, `POST /api/v1/axis/stream` and `POST /api/v1/axis/consult` refuse **whatever the request carries**, with the 403 problem today's Cold Check block uses, before any model call or retrieval.
- R8. The existing `exercise_id` check stays as a second guard (it also refuses a Cold Check item when no round is open).
- R9. Other model features (concept check, README draft, build feedback, the settings ping) are unchanged.

### C. What the learner sees
- R10. The refusal carries `title` "AXIS is off", `available_again_at` (ISO 8601, UTC) in the problem body, and in `detail` the R11 message **without its last sentence** (the server does not know the learner's clock format); the panel shows the full R11 message built from `available_again_at`. With several rounds open, the time is the latest expiry and the link goes to the most recently active round.
- R11. Message: "AXIS is unavailable while your Cold Check is open. Finish it, or leave it from the Cold Check page, to get AXIS back. Otherwise it returns at {time} ({minutes} minutes from now)." `{time}` is the learner's local clock time shown by the panel; `{minutes}` is rounded up.
- R12. The AXIS panel, on any tab, shows that message in place of the input (and when a send is refused), with a link back to the open round. It learns this on page load from `GET /api/v1/axis/status`, which adds `round_open_until` and the round's path (amends SPEC-24 R10), and on a refused send. It does not poll.

### D. Records
- R13. A refused request writes **no** interaction-log row (as today's 403) and no assistance row. Tracing records the existing `blocked` attribute.
- R14. Unchanged: evidence is recorded `none` for Cold Checks; builds stay Socratic and are not blocked; the concept-check soft gate; the ledger is never rewritten.

### E. Leaving a round (semantics L1 of ADR-0040 5.2, accepted)
- R15. `POST` a leave action for an open round (path set at build time, learner-scoped). The round ends, AXIS is available at once, and the response says when the round opens again. Leaving a round that is not open is refused.
- R16. A left item is **not an attempt**: no evidence entry, no assistance row, no effect on the concept check. Answers already given in the round stay.
- R17. The served, unanswered item is recorded as **left**. The next round takes another eligible item of that skill first; when a skill has none, the least recently left item is used after the wait. An expired round is treated the same way.
- R18. The round reopens after the same wait as a retry (24 hours; test timing in test mode).
- R19. The leave is written to the interaction log (new event type; unit, item id, reason `button` or `expired`). Expiry has no background worker (ADR-0019): it is detected, and logged once, the next time the round or AXIS is asked for.
- R20. Stage reviews and rechecks may be left under the same rules.
- R21. **The button** is on the page of the open round (Cold Check, stage review and recheck pages), secondary, labelled "Leave the Cold Check". It opens an in-page dialog (never a browser `alert` or `confirm`): title "Leave this Cold Check?"; text "AXIS will be available again straight away. This question will not be used again for now, and the Cold Check opens again tomorrow, with other questions where we have them. Nothing counts against you."; buttons "Leave" and "Keep going"; focus starts on "Keep going"; Escape keeps going.

### F. What this amends
- SPEC-16 sections 3 and 4: today stage reviews and rechecks use only **unseen** items and a recheck has **no retry**. A leave is **not a result**: a left stage-review item is replaced after the retry wait by an unseen item; a left recheck stays due and is served again after the wait; where no unseen item exists the least recently left item may be used. Pass and fail rules are unchanged.
- SPEC-24 R10: the AXIS status response adds `round_open_until` and the round's path.
- ADR-0022: one new interaction-log event type for a leave.

## 2. Tests first (written and failing before any code), `tests/test_cold_check_axis_block.py` unless said
- R1 to R6: `test_round_opens_when_an_item_is_served`, `test_round_ends_when_every_item_is_attempted`, `test_round_expires_after_60_minutes_without_activity`, `test_serving_or_attempting_restarts_the_expiry`, `test_test_mode_expiry_is_two_minutes`, `test_a_new_round_reopens`, `test_stage_review_and_recheck_rounds_also_close_axis`, `test_a_round_on_one_unit_closes_axis_on_another`.
- R7, R8: `test_second_tab_without_an_exercise_id_is_refused` (**the regression test for the gap**, consult and stream), `test_refused_before_retrieval_or_model_call`, `test_cold_check_item_id_still_refused_with_no_open_round`, `test_normal_use_is_unaffected_when_no_round_is_open`.
- R9: `test_concept_check_drafts_build_feedback_and_ping_are_unaffected`, `test_axis_is_refused_on_build_pages_while_a_round_is_open`.
- R10 to R12: `test_refusal_body_has_message_and_available_again_at`, `test_status_reports_round_open_until_and_path`, `test_minutes_are_rounded_up`, `test_several_open_rounds_use_the_latest_expiry`; frontend `AxisPanel.test.tsx`: shows the message with the time and minutes, link back, input disabled.
- R13, R14: `test_refused_requests_write_no_log_or_assistance_row`, `test_ledger_and_grading_are_unchanged`.
- R15 to R20: `test_leaving_ends_the_round_and_axis_returns`, `test_leaving_a_closed_round_is_refused`, `test_leaving_records_no_evidence_and_keeps_given_answers`, `test_left_item_is_not_served_next_when_a_spare_exists`, `test_no_spare_serves_the_least_recently_left_item_after_the_wait`, `test_expiry_is_treated_as_leaving`, `test_the_loophole_is_closed_with_spares` (serve, leave, ask AXIS, come back: a different item), `test_round_reopens_after_the_retry_wait`, `test_leave_is_logged`, `test_expiry_is_logged_once_as_expired`, `test_review_and_recheck_can_be_left`, `test_a_left_recheck_stays_due`.
- R21: frontend: button shown only on an open round, dialog wording, focus on "Keep going", Escape, no `window.confirm`.

## 3. Chaos check
An item served and never answered (the round expires and counts as left); the server restarts mid-round (the stored record keeps it open); the clock moves back (the round does not reopen or last longer than the expiry); two tabs finishing at once; a round reopened after expiry; an attempt arriving after expiry or after leaving; two tabs leaving at once; leaving with no spare item; a very old pointer from before this change (must not close AXIS for ever); `progress reset` mid-round; unknown unit or stage in a stored pointer.

## 4. Decisions (owner, 2026-11-26)
0. Leaving: **L1**; with no spare, serve the least recently left item after the wait; reviews and rechecks can be left; the R11 and R21 wording **as written**.
1. Concept-check feedback **stays available** during a round (gap 4).
2. Test-mode expiry of 2 minutes.
3. Refusals are **not** logged; tracing already marks them blocked.
4. **Content note:** the supply of spare items per skill is content, not code; adding curator-approved items (answers kept outside this repository) widens it.
