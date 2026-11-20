> **Snapshot copied from the project folder on 2026-11-20.** Source: lms-backlog/independent-audit-plan.md. Steps A0 to A6 are done; A7 is paused; A8 is queued (master plan F10). Status lives in master-plan-2026-11-15.md.

# Plan from the independent audit (2026-11-09 report)

Status: AGREED 2026-11-11 (owner chose: A0 to A5 first, during Stage 0 round 2; then 2d.5, 2d.6, 2d.7; A6 to A8 before the 5 Dec freeze). Verification: each step reproduces its finding with a failing test on local main first; per-PR CI + /code-review + /security-review; one fresh independent audit after all 9 steps. Thread "Plan next steps from independent audit".
Source: owner's report `C:\Users\sashe\orca\workspaces\lms\merrow\reports\independent-audit-2026-11-09.md` (audited branch `feature-isolated-experiment` b1390b5).
Re-checked 2026-11-11 against GitHub main (9679e98): every code finding below still holds there.

Rules for every step: one step at a time, one small PR per step (CI + /code-review + /security-review, owner merges), tests first, answers stay in the private answers repo.

## Already covered elsewhere (not new work)
| Audit finding | Where it already lives |
|---|---|
| No CI workflow | "Refine the project workflow" thread, branch chore/review-workflow |
| DockerRunner.execute() never uses Docker | Work sequence 6.1 "Docker sandbox on by default" (now known to be a stub, not a switch) |
| AXIS loads upstream index, not curriculum (ADR-0003) | Work sequence 2d.7 (AXIS answers vs RAG) and 6.3 (close upstream exception) |
| Dense vectors / bge reranker not wired | Decide in 2d.7; until then, describe as a seam (step A1) |
| PostgreSQL adapter missing | Not needed for single learner; describe as a seam (step A1) |

None of the audit findings overlap the PY-0.4 backlog (after-stage0-round2.md) or Phase 4 content work.

## New steps, proposed order
| Step | What | Severity | Effort |
|---|---|---|---|
| A0 | Green baseline for CI. On a clean checkout with no private answers (what CI sees): 105 failed, 23 errors (test_attempts_api, test_stage_review, test_exercise_api, test_progress_fixes, test_cold_check_feedback need answer material; only test_stage_build skips). Plus the 1 curriculum test failing on Zyric, 73 ruff findings incl. F821 `Any` at loader.py:309. Approach for answer-dependent tests: decision pending | Blocker for CI | M |
| A1 | Honest docs: "Built today vs pluggable seams" in README + ARCHITECTURE (Docker limits 128m/1.0 vs claimed 256MB/0.5, reranker, Postgres, RAG grounding); pyproject description + licence; devcontainer Python 3.12 -> 3.14 | High (portfolio trust) | S |
| A2 | SQLite: close every connection, WAL + busy_timeout | High | M |
| A3 | Course map N+1 (~373 queries -> ~4): hoist resets/seen, batch Cold Check timers, query-count test | Medium | S |
| A4 | Cap concurrent code runs (/execute and /runs), 429 / WebSocket error when full | High before any public demo | S |
| A5 | No work at import: drop module-level `app = create_app()`, uvicorn factory mode | Medium (tests, DX) | S |
| A6 | Real Docker runner (= 6.1, pulled forward), limits match docs, --user, --network none | High before others use it | M |
|  | **A6 status (2026-11-14):** PR #38 MERGED (Docker runner, fail closed, ADR-0036). PR #39 (A6b) MERGED (afb6a09). Remaining sandbox gaps (8 items, not yet tracked as tasks): see `a6-sandbox-known-gaps.md` in this folder and SPEC-03 2.4. | | |
| A7 | RAG wiring (= 2d.7): pass ConceptStore, say so when no index on a fresh clone | Medium | M |
|  | **Status 2026-11-14:** A0-A5 DONE (A2 = #24, A4 run cap = #28, A5 done, Windows test fix #34). 2d.5 build feedback DONE (#40, docs tick #41). A7/2d.7 in progress: ADR-0034/0035 merged (#37), code PRs waiting on the owner's go. A8 last. | | |
| A8 | Split app.py (1,689 lines) into routers + AppContext, pure refactor | Low | L |

Still open: reranker wire vs describe (decide in 2d.7). A0 starts once the workflow PR (chore/review-workflow) has merged, since it sets up CI and ruff.

> 2026-11-15: an independent review added new items and an agreed order for the freeze. See `review-2026-11-15-plan.md` in this folder.
