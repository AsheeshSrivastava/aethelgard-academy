> **Snapshot copied from the project folder on 2026-11-20.** Source: lms-backlog/review-2026-11-15-plan.md. The order was agreed 2026-11-15; for what is done now, see master-plan-2026-11-15.md section 1.

# Plan from the independent review (2026-11-15)

- **Source:** `lms-review/fable-independent-review-2026-11-15.md` (main at `cad782a`). Action numbers below are the report's "Top 10" numbers.
- **Status:** order AGREED by the owner 2026-11-15 (thread "Review LMS for production and portfolio"). Step 1 (action 1): owner reported it done 2026-11-15 (not re-checked by the review thread). Step 2 (action 4) approved 2026-11-15 and handed to its own thread. Each later step still needs the owner's go.
- **Rules for every step:** one step at a time, one small PR each, a failing test first that reproduces the finding, CI + /code-review + /security-review, owner merges. Answers stay private.
- Line numbers in the report are for `cad782a` and will drift.

## 1. Ordered list for the 5 Dec freeze

| Order | Action | What | Effort | Already tracked? |
|---|---|---|---|---|
| 1 | 1 | Check `Origin` on the `/api/v1/runs` WebSocket against the allow-list plus the app's own origin; add a Host allow-list (TrustedHostMiddleware). | S | New |
| 2 | 4 | Completion token for every hidden-check grade (reuse the token in `core/builds.py` `_run_behaviour`), so `os._exit(0)` no longer passes. | S | Yes: `a6-sandbox-known-gaps.md` gap 3. Moved earlier. |
| 3 | 5 | CI job that pulls `python:3.14-slim` and runs `pytest -m docker`. | S | New |
| 4 | 2 | Demo mode (`lms serve --demo`) on a made-up course with fake answers, with a "Demo data" banner; screenshots or a short GIF in the README. | M | New. Needs an owner decision: is a public made-up demo course allowed under the private-answers rule? |
| 5 | 3 | Mock AXIS: no citations, reply starts "Offline demo reply (no model is connected)"; show the active backend in the AXIS panel. | S | Partly: 2d.7 step 1 (PR #42) is marked done but did not cover the mock. |
| 6 | 6 | Docs match the code: stale ARCHITECTURE lines (subprocess "today", Docker "seam", "audit fixes in progress"), soften "never", "immutable event sourcing", "zero-dependency"; state content status (7 of 296 units); fix AGENTS.md wording on multi-tenant and the provenance firewall. List in report section 4.3. | S | New drift since A1 |
| 7 | 7 (small part) | Docs say the assistance rule detects code only; one failing test showing a full prose solution counted as no help. | S | New |
| 8 | 8 (small part) | Move retrieved passages out of the system prompt into a fenced "untrusted data" block; remove the "first 30 passages" fallback. | S | New. Owner has not yet said whether the retrieval-code hold is lifted for this. |
| 9 | 8 (small part) | Drop stop words and the unit id from the query; add a minimum score so "not found" can fire with an index loaded. | S to M | Partly: 2d.7 step 5. Same hold question as above. |

## 2. Leftovers (backlog, not scheduled)

| Item | From | Note |
|---|---|---|
| Assistance accounting logic: any Coach or Hybrid reply on a graded item counts as at least `structural_direction`, or a model label with the rule as a floor | Action 7 | Changes how evidence is credited. Needs an owner decision and an ADR-0009 amendment first. |
| Ledger guard: `BEFORE UPDATE` / `BEFORE DELETE` triggers on `evidence_ledger` and `interaction_log` | Action 9 | Small; the report suggested it before the freeze. |
| One transaction per attempt; expire unfinished idempotency receipts | Action 9 | A crash mid-attempt blocks the retry for ever today. |
| Exclude `test_mode` evidence from estimates; never write evidence from the mock judge | Action 9 | Evidence rule, so owner decision first. |
| Delete the legacy shell (`src/lms/web/app.js`, `index.html`, `styles.css`, `vendor/`) and routes `/execute`, `/axis/consult`, `/explain-error`, `/learners/{id}/progress`, `/learners/{id}/ledger` | Action 10 | Small. `/explain-error` also gives AXIS help with no Cold Check block. |
| Split `app.py` with a service layer as the goal | Action 10 | Same as audit step A8; the review adds the goal. |
| Socratic filter: parse code spans instead of regex, or structured model output; fewer false blocks | Report 3.4 | Leaks in-sentence code and blocks honest questions today. |
| Strip closing `</learner_query>` in `build_user_message`; judge twice before Strong | Report 3.4 | |
| Operability: real serve mode (host, no reload), paths not tied to the working folder, logging config, health that reports database, runner, AXIS and index, `PRAGMA user_version` migrations, SQLite backup note, app Dockerfile | Report 3.7 | Needed before a pilot with other people. |
| CI: check that committed `src/lms/web/dist` matches `frontend/src`; e2e on the fixture course; Python type checker | Report 3.6 | |
| Remove the local model's silent fallback to the mock | Report 3.3 | ADR-0035 2.7 already rejects it. |
| README "How this was built" (AI use), one overview page, cut noise files, ADR index rows 0030 to 0032, dead `skills/` link in AGENTS.md | Report 4.4, 4.5 | Owner decision on the AI-use statement. |
| ADR-0035 disagreements: measure keyword search on LMS questions before wiring models; labelled downgrade instead of "unavailable"; give AXIS the current lesson directly | Report section 7, idea 1 | Owner decision. Remaining retrieval PRs stay on hold until then. |
| Ideas: signed evidence export, item-quality report from the interaction log, two-process grading | Report section 6 | Two-process grading = sandbox gap 1. |
| Check upstream source licences for quoting to learners | Report 4.5 | Not verified by the review. |

## 3. Backlog items the review did not look at

Sandbox gap 7 (stdlib shadowing), gap 8 (flaky e2e database), and the Stage 0 content follow-ups in `after-stage0-round2.md`. They stay where they are.

## 4. Open owner decisions

1. Does the retrieval-code hold lift for order 8 and 9?
2. Is a public made-up demo course acceptable?
3. Is the freeze for a portfolio release, a pilot with other people, or both?
