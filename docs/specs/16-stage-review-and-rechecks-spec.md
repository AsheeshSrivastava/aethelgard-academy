# SPEC-16: Stage Review and Spaced Rechecks

- **Status:** Draft (2026-10-31)
- **Governed by:** ADR-0019, Learning Method v2 Amendment A1 (A1.5), ADR-0016 (Cold Check), SPEC-12 sections 4.1 and 5, SPEC-13 section 5, SPEC-15

---

## 1. Purpose

A unit Cold Check finds a gap within a day. A stage review mixes the units of a stage. Rechecks bring a skill back after 7 and 30 days. All three use curator-approved Cold Check seeds, AXIS off, deterministic grading, one try per item.

## 2. Unit Cold Check

A round is 3 to 5 items. It takes one approved item per target skill in unit order, then goes round the skills again until it holds 3 items, and stops at 5. A unit with fewer approved seeds runs what it has. Everything else stays as in SPEC-12 section 5, except that round progress is tracked per item, not per skill.

## 3. Stage review

### 3.1 The round

Made once, when the review first opens, and stored for the learner. It takes only items the learner has not seen, at most one variant of a seed:

1. One item for each target skill at Apply or above, wherever an unseen item exists.
2. Then items from each unit until the unit has 2.
3. Items are mixed: one from each unit in turn.

### 3.2 State

```text
StageReviewStatus { state, available_at: datetime | null, last_attempt_at: datetime | null,
                    pending_units: [unit_id], failed_units: [unit_id],
                    items_total: int, items_done: int }
```

| State | Meaning |
| --- | --- |
| `passed` | The last finished round passed. Stays passed if a unit is later reset. |
| `not_ready` | Some unit has not passed its Cold Check. |
| `unavailable` | Every unit passed, and no unseen item exists. |
| `failed_waiting` | The last round failed; `available_at` is 24 hours after it. |
| `available` | The learner can answer now. |

### 3.3 Passing and failing

The round passes if every item passes. On a fail, `failed_units` names the units of the failed items. After 24 hours those items return: passed items stay passed, and each failed item is replaced by the next unseen item for that unit and skill, or by another seen one when none is left, so a retry can repeat an item when a stage is short of seeds.

`reveal` is never sent on a failed item.

### 3.4 The build gate

A stage build is open when the review is `passed` or `unavailable`. This replaces ADR-0016 section 2.6: a passed stage review opens the build by itself.

`unavailable` opens the build because missing content must never lock a learner out. The curriculum check `stage-review-short` warns when a stage's approved items, after its unit rounds, leave a unit with no spare item. Stages where the warning stands have no stage review, by design, until seeds are written.

`BuildSummary` gains `review_state`. `locked` is true unless the build is open.

## 4. Rechecks

- **Schedule.** Computed from the ledger when asked; no worker. A skill's clock starts at its first Strong entry with `review_kind` `stage_review`. Its rechecks fall due at +7 and +30 days. The 30-day recheck is listed only after the 7-day one is finished, so the queue stays short, and an overdue recheck stays due.
- **A round** is up to 4 unseen items for that skill, from any unit. A due recheck with no unseen item is left out of the list until seeds exist.
- **Result.** Each item writes evidence like a Cold Check. A round ends when every item is answered, pass or fail. There is no retry: a failed recheck lowers the estimate through the whole-ledger estimator and resets nothing.

## 5. API

| Method | Path | Response |
| --- | --- | --- |
| GET | `/learners/me/courses/{course_id}/stages/{stage}/review` | `StageReviewStatus` |
| GET | `/learners/me/courses/{course_id}/stages/{stage}/review/exercise` | `Exercise` |
| GET | `/learners/me/reviews/due` | `[DueReview]` |
| GET | `/learners/me/reviews/{skill_id}/{days}/exercise` | `Exercise` |

```text
DueReview { skill_id, skill_name, days: 7 | 30, due_at: datetime, items: int }
```

- Stage review exercise: `423` when `not_ready` or `failed_waiting`, `404` when `unavailable`, `409` when `passed`.
- Recheck exercise: `404` unless that recheck is in the due list or already started.
- Attempts use `POST /learners/me/attempts` with `activity` `stage_review` or `recheck`. The attempt must be on the round's next unanswered item: `409` otherwise.
- AXIS requests on these exercises return `403`, as for any Cold Check seed.

## 6. Evidence

Entries set `cold_check` true and `review_kind` to `stage_review` or `recheck`, with `seed_id`, `unit_id` and `skill_id` from the item. Strong if passed, Weak if not. `reset_unit` touches none of the review tables or the ledger.

## 7. Not in this spec

- Frontend tiles and the review page (next step). Until then only the build tile's locked message changes.
- The volume warning in ADR-0019 section 2.6.
