> **Superseded 2026-11-27 by the freeze tracker; kept as a record.** See [freeze-2026-12-05.md](freeze-2026-12-05.md).

> **Snapshot copied from the project folder on 2026-11-20.** Source: lms-backlog/after-stage0-round2.md. History only: S0-1 to S0-4 are done (see master-plan-2026-11-15.md section 1).

# Changes waiting for the end of Stage 0 round 2

Status 2026-11-13: items 1+2 DONE (PR #12, 2c0e76c), item 3 DONE (PRs #13-#15). Only item 4 (My progress redesign) left, on hold until owner says.

Recorded 2026-11-11 (thread "Improve PY-0.4 exercises and progress page"). Apply these only after the owner finishes the second Stage 0 run. Each one needs the owner's go before starting.

## 1. Evidence rule: a repeated concept check counts once (ADR-0016 amendment)
- Problem: concept-check ledger entries have no exercise or seed id, so the same answer submitted twice counts as 2 qualifying exercises. That proves memory, not understanding.
- Change: give each concept check an exercise id (for example `PY-0.1/explain/v1`) so repeats collapse to one, like other items. The second piece of support must come from a different exercise (another activity or the Cold Check).
- Order: ADR-0016 amendment, then tests first, then code. Local commit only.

## 2. Next-step wording
- Problem: `src/lms/core/proficiency.py` joins two support gaps with "and" ("needs 1 more exercise at Understand and a passed Cold Check"), which reads as 3 tasks when 2 suffice (one strong result plus one passed Cold Check item).
- Change: "needs 1 more exercise at Understand; it must be a passed Cold Check" (or similar).
- After a unit reset, say what actually unlocks the Cold Check: "Redo the unit's N activities to unlock its Cold Check."

## 3. More question variety (MOVED 2026-11-12 to thread "Fix Stage 0 content, build and Cold Checks") (content, all units, PY-0.4 pilot)
- Each unit has exactly 1 concept-check prompt, with no variants. A retry or reset serves the same prompt.
- PY-0.1 has 1 Cold Check item for CO-6 (cold-explain-1). A reset serves the item already passed. PY-0.4 has none for CO-6. Neither unit has CO-6 practice items.
- Practice pool is about 2 items per activity. Target is 6 to 10.
- Change: 2 to 3 concept-check prompts per unit, more than one Cold Check item per skill, and 6 to 10 practice items per activity. Never serve an item the learner already passed after a reset or retry.
- Owner direction: varied exercises aiming at the same skill; PantryFlow story only for Build; practice uses varied everyday scenarios.
- Answers and keys go only in the private answers repo, never in the lms repo.

## 4. My progress redesign (mock awaiting approval)
- Mock: https://claude.ai/artifact/8sn7XSzCao3bhkDfYEpCMs
- Fold in these bugs: (a) bars colour every rung with the top rung's confidence (send `supported_levels` in SkillView); (b) the reason counts the top level's entries and wrongly says "including a Cold Check" for a Build entry.
- Open question for the owner: should a skill that is proven above its goal, with an unproven top rung, show Accelerate instead of Progress? (amendment F)

## Done already
- Selection highlight fix: local commit 8745fba in D:\01-Project\lms (not pushed).

## Open follow-ups from the Stage 0 fixes thread (recorded 2026-11-12, not yet scheduled)
- (a) Recommended: TW-0.1 and TW-0.2 choice items where the key is the longest option (same flaw fixed for PY-0.3 in round 2 fix 8).
- SPEC-16 note about Module review spare items (follow-up from PR #13).
- PY-0.3 practice volume: 12 items vs target 15 (single activity), 3 short.
- Owner wants to discuss Stage 0 Explain page content (raised 2026-11-12).
