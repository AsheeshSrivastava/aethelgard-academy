# AXIS and Cold Checks: known gaps to close later

Recorded 2026-11-26 (owner: "we need to work to resolve this issue in future, so record it"). Governing: ADR-0040, SPEC-32 (draft), ADR-0003 and ADR-0019 ("AXIS off during a Cold Check").

## The gap that started this
AXIS was refused only when the request carried a Cold Check `exercise_id`. Tested 2026-11-26 on `main` with a temporary test: with a Cold Check item served (`PY-0.1/cold-predict-1/v1`), `/api/v1/axis/consult` and `/api/v1/axis/stream` **without** an id both returned 200 (as a second browser tab would); with the id, 403. The Cold Check stayed available and is graded as unassisted. The legacy `explain-error` route had no block and was retired (PR #73).

## What ADR-0040 option A fixes (not yet built)
The server refuses every AXIS chat route while a learner has an open Cold Check, stage review or recheck round, whatever the request says, and tells the learner when AXIS is back.

## What still remains after it
| # | Gap | Why it matters | Likely fix | Revisit when |
|---|-----|----------------|-----------|--------------|
| 1 | A learner who walks away from a Cold Check has no AXIS until the round expires. There is no "leave the Cold Check" button. | Frustrating; feels like a lock-out | An explicit leave action that says what it does to the attempt | After first real use |
| 2 | The 60-minute expiry is a guess. | Too long annoys; too short reopens the gap | Tune from real use (count expiries and returns) | After first real use |
| 3 | It protects only this product's AXIS, not other tools or people. | An open-book risk remains | None in the product; state it honestly | n/a |
| 4 | Other model features (concept-check feedback, README draft, build feedback) are not refused. | A learner could get hints about a skill from them | Decide per feature (SPEC-32 open question) | Before a pilot |
| 5 | Edge cases of "round open": an item served but never answered, a new round starting, two tabs finishing at once, clock changes. | Wrong block or wrong release | Tests in SPEC-32, then watch real use | With the build |
| 6 | One learner per install (ADR-0015): the block is keyed on the server's current learner. | Multi-learner or public hosting needs a real identity first | Authentication and per-learner sessions | **Before any pilot or public hosting** (same gate as sandbox gap 1, `a6-sandbox-known-gaps.md`) |

**Revisit when:** before any pilot or public hosting, and after the first real use of Cold Checks with AXIS on.
