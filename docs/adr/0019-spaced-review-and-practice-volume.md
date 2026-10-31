# ADR 0019: Unit Cold Check, Stage Review, Spaced Rechecks and Practice Volume

- **Status:** Proposed (2026-10-31)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-31
- **Governed by:** Learning Method v2 Amendment A1 (A1.5, A1.6), ADR-0016 (Cold Check and progression), ADR-0017 (variant pools)

---

## 1. Context & Problem Statement

Cold Check runs once, 24 hours after a unit is completed, and tests only that unit (ADR-0016). Nothing mixes the units of a stage or brings a skill back later, so a learner can pass Stage 1 and have forgotten it by Stage 4. The review also found that most units in Stages 0 to 5 have too few graded items to build fluency. Amendment A1 sets the rules; this ADR decides how the app applies them.

---

## 2. Decision

Decided by the owner on 2026-10-31: Cold Check at both unit end and stage end.

1. **Unit Cold Check (kept, shortened).** 3 to 5 items, unlocked 24 hours after the unit is completed, AXIS off, deterministic grading, covering only the unit's target skills. Fail → Strengthen and retry in 24 hours, as today.
2. **Stage review (new).** Opens when every unit of the stage has passed its unit Cold Check. A mixed set of items drawn from all the stage's units, roughly 2 per unit, at least one per target skill at Apply or above, AXIS off, deterministic grading, unseen curator-approved variants. **Passing it unlocks the stage build**, replacing ADR-0016's rule that the build unlocks when every unit has passed Cold Check. Fail → the result names the units whose items failed; the learner strengthens those and retries after 24 hours.
3. **Rechecks.** Passing a skill in a stage review schedules a recheck at **+7 days** and **+30 days**: 2 to 4 items for that skill alone, shown on My progress as "Due for review". Results go to the evidence ledger like any Cold Check, and the whole-ledger estimator (ADR-0016) uses them. A failed recheck lowers the estimate; it does not reset the unit or lock later work.
4. **Scheduling** is computed from the ledger when the learner opens the app. No background worker and no Temporal. A recheck that is overdue simply stays due.
5. **No items, no gate.** A stage with no unseen approved item cannot run a review, so its build opens once every unit has passed, as under ADR-0016. A curriculum warning names the stage. Missing content must never lock a learner out. Details in SPEC-16.
6. **Volume targets** (15 to 20 graded items per unit in Python Stages 0 to 5, at least 3 Make; 8 to 12 later) become a curriculum check: a warning when a unit's seed pool and approved variants fall short. They set the pool size that `lms variants generate` aims for.

---

## 3. Consequences

### Positive
- A gap is found within a day of the unit (unit check), mixing across the stage builds retention (stage review), and the estimator sees decay (rechecks).
- Curators get a clear target for how many items each unit needs.

### Negative / Trade-offs
- Each skill needs more curator-approved Cold Check variants, because the stage review and rechecks must not repeat earlier items.
- ADR-0016's build-unlock rule changes; ADR-0016 needs an amendment note when this ADR is accepted.
- My progress gains a review queue that must stay short to avoid nagging.

### Open
- Whether rechecks continue after 30 days (for example 90 days) is left until there is data from the first learner.
