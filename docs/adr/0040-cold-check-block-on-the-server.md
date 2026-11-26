# ADR-0040: The server, not the request, decides that AXIS is off during a Cold Check

- **Status:** Proposed (draft 2026-11-26, waiting for the owner's go). No test or code.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Number:** 0038 is reserved (LangSmith, ADR-0037), 0039 is in PR #72 (not yet merged).
- **Builds on:** ADR-0003 ("Cold Checks stay free of AXIS"), ADR-0019 (unit Cold Check: AXIS off), ADR-0028, ADR-0032 (Cold Check rounds), SPEC-12 sections 7 and 8, SPEC-16 (stage review and rechecks also run AXIS off), ADR-0022 (interaction log).

## 1. Context: how the block works today
- AXIS is refused only when the **request carries** a Cold Check `exercise_id`: `is_cold_check_exercise` (`api/app.py:1184-1188`), used by the stream (`:1216-1219`) and consult (`:1273-1275`) routes.
- The panel is hidden on the Cold Check page (`frontend/src/pages/Lesson.tsx:615`).
- Evidence from a Cold Check is always recorded with assistance `none` (`api/app.py:1826`).

**The gap, tested** with a temporary test (not kept) on `main` after PR #71: a learner who has a Cold Check item served (`PY-0.1/cold-predict-1/v1`) sends AXIS a question **without** an `exercise_id`, as a second browser tab on a lesson step would. `consult` returned **200** and `stream` returned **200**; the same request with the Cold Check id returned 403; the Cold Check state stayed `available`. So the block depends on the client saying which exercise it is. The Cold Check is then graded as unassisted.
Read in code, not tested: stage reviews and rechecks use the same Cold Check seeds with AXIS off (SPEC-16), so the same gap applies to them. The legacy `explain-error` route had no block at all and is retired separately (PR #73).

## 2. What this does and does not protect
A server rule keeps **this product's** AXIS out of a Cold Check. It cannot stop a learner using another tool or another person. The aim is honest product behaviour and honest evidence labels, not exam security.

## 3. Options
**A. Server-side "Cold Check open" state (recommended).** A Cold Check round is *open* from the first time one of its items is served until the round finishes (or expires). While a learner has an open round, every AXIS route refuses with the same 403 and plain message, whatever the request carries.
- *What the server already has:* the `exercise_pointer` table (`learner_id, unit_id, activity, exercise_id, served_at`, `adapters/db/sqlite_repo.py:384-408`), the check that an item was attempted since it was served (`attempted_since_served`, `api/app.py:1589`), round selection (`learner_cold_round`, `:1538`) and the end of a round (`finish_cold_item`, `:1560`). The round state needs no new table, but "round finished" must be defined precisely in the spec.
- *Scope:* the whole learner, not only the unit (a second tab on another unit can answer the same question).
- *Abandoned rounds:* the round expires after a fixed time from the last served item (proposal: 60 minutes, configurable, shorter under test mode), so a learner is never locked out for long. An explicit "leave the Cold Check" action could end it early (optional).
- *Reviews and rechecks:* the same rule applies to a served stage review or recheck item.
- *Cost:* a learner who walks away is without AXIS until expiry; one more state to reason about and test.

**B. Block only the unit that has an open round.** Less intrusive, but AXIS still answers on other units, which share the skills a Cold Check tests.

**C. Block while any Cold Check is *available* (not yet started).** Too broad: it would cut AXIS for learners who have not begun and may never begin that day.

**D. Do not block; record it.** Keep answering but mark the Cold Check result as assisted or void. Honest, but it contradicts ADR-0003 and ADR-0019 ("AXIS off") and changes grading.

## 4. Consequences (option A)
- **Evidence ledger:** unchanged. Cold Check entries stay `none`; with the block that label is now true for product AXIS. Nothing is rewritten.
- **Soft gate (concept check):** unaffected; it never blocks, and AXIS is not part of grading it.
- **Builds:** builds stay Socratic as today; they are not Cold Checks and are not blocked.
- **Interaction log (ADR-0022):** a refused request is logged like today's 403s (no change in what is stored); the spec should say whether a refused attempt writes a row (recommend: no).
- **Test mode:** delays are zero (ADR-0019 amendment); the expiry also shortens, so tests are quick and learners' test runs are not locked.
- **Single learner today (ADR-0015):** the learner id is the server's current learner, so no new identity is needed.
- **UI:** the AXIS panel on other tabs should show "AXIS is off while your Cold Check is open" and offer to go back to it.

## 5. Decision (proposed)
Option **A**: the server decides, for every AXIS route, from its own state; the request's `exercise_id` check stays as a second guard.

## 6. Open points for the owner
1. Option A, B, C or D (recommended A).
2. Expiry of an abandoned round: 60 minutes (recommended), or another value; and whether to add a "leave the Cold Check" button.
3. Does a served stage review or recheck also close AXIS (recommended yes)?
4. Scope: the whole learner (recommended) or the unit only.

## 7. After the go
A spec (round-open definition, expiry, messages, which routes, tests first), then tests, then code. The index row in `docs/adr/README.md` is added after PR #72 merges, to avoid a conflicting edit.
