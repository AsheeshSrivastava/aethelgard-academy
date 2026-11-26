# ADR-0040: The server, not the request, decides that AXIS is off during a Cold Check

- **Status:** Accepted by the owner 2026-11-26: option A, with a message that AXIS is unavailable until the round ends or expires, and **a Leave button, which the owner requires**, with the leave semantics L1 and the decisions of section 6 (all accepted 2026-11-26). The follow-up in section 8 is recorded for later. No test or code yet.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Number:** 0038 is reserved (LangSmith, ADR-0037).
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
- **UI (decided 2026-11-26):** wherever AXIS is refused, the learner sees that **AXIS is unavailable until the Cold Check round ends or expires**, with the time it expires, that **finishing the Cold Check brings AXIS back sooner**, and a way back to it. Other tabs show the same message. Exact wording is set in SPEC-32. The refusal carries the expiry time so the panel can show it.

## 5. Decision
### 5.1 The block (accepted)
Option **A**: the server decides, for every AXIS chat route, from its own state; the request's `exercise_id` check stays as a second guard. Scope: the whole learner; stage reviews and rechecks too. An abandoned round expires after 60 minutes. The learner is told AXIS is unavailable, when it returns, and how to get it back sooner.

### 5.2 Leaving a round (accepted: L1)
**The problem.** A learner could leave, ask AXIS about the question they just saw, return to the same question, and be recorded as unaided.

**What the code shows (checked 2026-11-26).** Each unit that has a Cold Check holds 6 eligible items; a round uses 3 (TW-0.2: 7 items, 3 used), so there are 3 or 4 spares, at least one per target skill. Unanswered items are not recorded, so today a left item would be served again. The round choice already prefers never-answered items (`cold_round`, `core/exercises.py:410-441`). Stage reviews and rechecks use the same seed pools (SPEC-16); their spare counts were not checked.

| Option | What happens to a left item | Gain | Cost |
|---|---|---|---|
| L1 | **Set aside and delayed:** the served, unanswered item is marked left; the next round takes another item of that skill first; the round reopens after the normal retry wait (24 hours) | Closes the loophole while spares last; no penalty | One new stored fact; spares run out after about one leave per skill |
| L2 | Same item stays; its later result is marked assisted or void | Simple; no spares needed | Punishes honest leavers; changes grading; against Invisible Assessment |
| L3 | AXIS stays off for a cool-down after leaving | No new data | The button then gives nothing, which is not what the owner asked |
| L4 | Nothing: leave and return to the same item | Simplest | The loophole stays open |

**Decision: L1.** Leaving is **not an attempt**: no evidence entry, no penalty, the concept-check soft gate unaffected; answers already given in the round stay as recorded. AXIS returns at once. The round reopens after the same wait as a retry. When a skill has no unused item left, the least recently left item is served after the wait and graded normally (a recorded limit, not a penalty). The leave is written to the interaction log (a new event type, ADR-0022) so a progress decision stays traceable.
**Expiry must follow the same rule:** an expired round is treated as left. Otherwise waiting 60 minutes would be the same loophole.
**Reviews and rechecks:** leaving is allowed with the same rule (a recheck moves to a later day).
**Test mode:** the retry wait and expiry follow test timing, so tests stay quick.

## 6. Decisions and open points
1. Option A: **decided**.
2. A message that says AXIS is unavailable until it ends or expires: **decided**.
3. Expiry 60 minutes (shorter in test mode), reviews and rechecks included, whole-learner scope, `exercise_id` check kept: **confirmed**.
4. A **Leave button is required**: **decided** (2026-11-26).
5. What leaving does to the item: **decided, L1**.
6. When a skill has no unused item: **decided**, serve the least recently left one after the wait.
7. Stage reviews and rechecks can be left: **decided, yes**.
8. The refusal and confirm wording of SPEC-32: **decided, as written**. Concept-check feedback stays available during a round. Refusals are not logged.
9. Spare items per skill are **content, not code**: adding Cold Check items (curator-approved, answers kept outside this repository) widens the spares; a learner who leaves repeatedly still reaches the oldest item eventually.

## 7. After the go
SPEC-32 (round-open definition, expiry, messages, which routes, tests first), then tests, then code.

## 8. Recorded follow-up (owner, 2026-11-26: "we need to work to resolve this issue in future")
The Leave button (decided) removes the lock-out for a learner who wants AXIS back. Still to watch later:
- what leaving should do once real learners use it (spares run out; is the 24-hour wait right?);
- whether 60 minutes is the right expiry.
It does not and cannot stop help from outside the product (section 2).
The full list, with when to revisit each item, is in `docs/plan/axis-cold-check-known-gaps.md`.
