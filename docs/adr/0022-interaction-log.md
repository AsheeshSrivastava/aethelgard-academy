# ADR 0022: Interaction Log and Cold Check Feedback

- **Status:** Accepted (2026-11-09, by the owner, as built). Proposed 2026-11-04.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-04
- **Governed by:** ADR-0004 (append-only evidence ledger), ADR-0016 (estimator), ADR-0019 (test mode amendment), SPEC-12 section 5 (idempotent submit)

---

## 1. Context & Problem Statement

The owner failed a Cold Check and could not see what they had answered: the app keeps the result of an attempt, never the answer. The owner asked that every learner interaction be recorded, including what is not shown to the learner, so any progress decision can be traced to the exact answer behind it. A failed Cold Check also tells the learner almost nothing.

---

## 2. Decision

### 2.1 A separate, append-only interaction log

The evidence ledger keeps its job: evidence the estimator reads. Everything a learner does goes to a new table, `interaction_log`, which the estimator never reads. Rows are never updated or deleted by the app.

| Field | Meaning |
| --- | --- |
| `interaction_id` | A ULID: unique and time-sortable. For a submitted answer it is the client's `interaction_id` (SPEC-12 section 5), so the log, the receipt and the evidence entry share one code. Otherwise the server makes one. |
| `learner_id`, `recorded_at_ms` | Who, and when as epoch milliseconds. |
| `session_id` | One per app visit, sent by the client in the `X-Session-Id` header; null if absent or malformed. |
| `attempt_id` | Groups the interactions of one attempt (2.2). |
| `unit_id`, `activity`, `item_id` | Where it happened; `item_id` is the exercise id when there is one. |
| `event_type` | One of the types in 2.3. |
| `payload` | JSON, capped (2.4). |
| `test_mode` | As on ledger entries (ADR-0019 amendment). |

`(learner_id, interaction_id)` is unique: a repeated write is ignored, so logging is idempotent.

### 2.2 Attempt ids

An attempt id names one attempt, derived on the server so it needs no extra state:

| Attempt | `attempt_id` |
| --- | --- |
| Practice item | `<exercise_id>@<served_at>` |
| Unit Cold Check round | `<unit_id>/cold_check@<round start>`; the round starts at the unit's completion, or at the last failed attempt for a retry |
| Stage review or recheck round | `<kind>/<scope>` (a scope is reused only after the round ends) |
| Build submission | `<build exercise_id>@<served_at>` |

Ledger entries gain two nullable columns, `interaction_id` and `attempt_id`, filled for entries recorded from now on. Old rows keep nulls and are never rewritten.

### 2.3 What is logged

| `event_type` | When | Payload |
| --- | --- | --- |
| `answer_submitted` | Any attempt: practice, Cold Check, stage review, recheck, build | The exact answer fields and the outcome (passed, score, evidence entry id) |
| `concept_check` | `POST /explain` | The explanation text and the Solid / Shaky result |
| `run`, `verify` | A sandbox run, a playground verify, a build check | The code (capped) and an outcome summary: exit code, passed, timed out |
| `regenerate`, `reset` | Those actions | What was served next, or what was cleared |
| `axis` | An AXIS question and its answer | Mode, question, answer (capped), assistance level |
| `opened`, `closed`, `hint_viewed`, `feedback_viewed` | Sent by the client to `POST /learners/me/interactions` | Only allow-listed types and fields; the server stamps learner and time |

### 2.4 Failure, size and secrets

- **Never breaks learning.** A failed log write is reported in the server log and swallowed; the learner's request still succeeds.
- **Size.** Each text field is capped at 64 KB and the whole payload at 256 KB; a cut is marked `"…[truncated]"`.
- **No secrets.** The app logs only fields it chose. Any payload key containing `key`, `token`, `secret` or `password` is replaced with `"[redacted]"`. Environment values are never read into the log.

### 2.5 Cold Check feedback (option A, chosen by the owner)

After a failed unit Cold Check, the learner sees each item of the round: passed or not, the skill, **their own saved answer**, a short hint about the idea to revisit, and a link to the skill's practice activity. The worked answer (`why` and the key) is shown only for an item that will not come back: one that was passed. Hints are curriculum text in the seed (`hint`, with `hint_approved`); an unapproved hint is not shown. Grading stays deterministic and AXIS stays off.

### 2.6 Retention, privacy and export

The app is local-single today (ADR-0015): the log lives in the learner's own SQLite file. Before a second learner joins:

- **Consent.** The learner is told, before the first lesson, that their answers, code and AXIS questions are recorded to show their progress and improve the course.
- **Export.** `GET /learners/me/interactions` returns the learner's own log as JSON (built now).
- **Delete.** A learner can ask for their log and ledger to be deleted; that is an operator action with its own audit row (to build with multi-learner sign-in).
- **Retention.** Raw code and AXIS text are kept for 2 years, then reduced to their outcome summaries (to decide with the owner before multi-learner launch).

---

## 3. Consequences

### Positive
- Any decision on My progress can be traced: entry → `interaction_id` → the exact answer.
- A disputed Cold Check can be checked against what was actually submitted.
- The estimator and the ledger stay clean.

### Negative / Trade-offs
- The SQLite file grows with every run and AXIS turn; the caps bound one row, not the total.
- Hints are new curriculum text that the owner must approve per seed.
- Attempt ids are readable strings, not ULIDs, so they are derived without new state.
