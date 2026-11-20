# Master plan (freeze plan) snapshot

> **Snapshot copied from the project folder (`lms-backlog/master-plan-2026-11-15.md`, last edited 2026-11-18) on 2026-11-20.** The body below is the 2026-11-18 text; its F7 to F9 rows are out of date. The block directly below is the current status. Where they differ, this block wins.

## Status update 2026-11-20

Freeze: 5 Dec 2026. Order from here: finish plan step 8, then 5b, A7 paused, A8 (F10), then F10a, F11.

| Item | State |
|---|---|
| F7, F8, F9 (retrieval, ADR-0035 section 5.1) | Plan steps 1 to 5 and 7 done (SPEC-20 to SPEC-25 and SPEC-27, PRs #47 to #56). Step 6a done: SPEC-26 search-only text, measured, default off (PR #60). Step 6b skipped by the owner 2026-11-19, to revisit after real use. Step 5b (mode stress test) skipped, to re-run later. Step 9 (query rewriting, agentic retry) last and optional. |
| Plan step 8 (tracing, metrics, evals; also F10b mode-usage report) | ADR-0037 accepted (#61). SPEC-28 tracing: spec #62, implementation merged #63. SPEC-29 report and thumbs: spec merged #64, tests and code in progress. SPEC-30 (answer evals) still to write. |
| F10a (stress-test all three AXIS modes) | Queued; this is plan step 5b. |
| F10 (split app.py, A8) | Waits for the retrieval and tracing PRs. |
| A7 (ConceptStore wiring) | Paused. |
| F1 to F6, F11 | As in the table below; not re-checked on 2026-11-20. |

---

# Master plan (2026-11-15), tracker thread "Track the freeze plan step by step"

Status: DRAFT, waiting for the owner's approval. No step thread is opened until the owner says go.
Freeze: 5 Dec 2026. Repo: D:\01-Project\lms on Zyric.

Source ids used below:
- **R1..R10** = action numbers in the Fable review (`lms-review/fable-independent-review-2026-11-15.md`), plan in `review-2026-11-15-plan.md`.
- **A0..A8** = independent audit steps (`independent-audit-plan.md`). **2d.x** = work-sequence steps.
- **G1..G10** = sandbox gaps (`a6-sandbox-known-gaps.md`).
- **S0-1..S0-4** = `after-stage0-round2.md` items. **RL-x** = review leftovers table.

Rules for every step brief: one step, one small PR. Decision > ADR > Spec > Tests (a failing test first) > Code, stop for the owner's go after ADR/spec. Answers stay private. Run e2e with the real answers (`LMS_ANSWERS_DIR`, optional `LMS_RUNNER=docker`) before merging grading or lesson changes. Commit, push and PR only when the owner says. Owner merges with "Create a merge commit". After merge: `git pull github main`, then `git push origin main`.

## 1. DONE

| Item | Source | Evidence |
|---|---|---|
| A0 green CI baseline | A0 | PR #2 |
| A1 honest docs | A1 | PR #3 |
| A2 SQLite connections, WAL | A2 | PR #24 |
| A3 course map queries | A3 | done |
| A4 run cap | A4 | PR #28 |
| A5 no work at import | A5 | done |
| A6 Docker runner, fail closed | A6, G-6.1 | PR #38 (ADR-0036) |
| A6b hidden checks via stdin | A6 | PR #39 |
| Windows test fix | A0 follow-up | PR #34 |
| 2d.5 build feedback | 2d.5 | PR #40, docs tick #41 |
| ADR-0034/0035 | 2d.7 | PR #37 |
| AXIS honest basics (2d.7 step 1) | 2d.7 | PR #42 (GitHub shows no open PR now; the thread believed the branch was still open, so confirm the branch is merged or delete it) |
| Stage 0 round 2 fixes 1-8 | S0 | merged |
| S0-1 repeated concept check counts once, S0-2 next-step wording | S0-1, S0-2 | PR #12 |
| S0-3 question variety | S0-3 | PRs #13-#15 |
| My progress redesign | S0-4 | done |
| e2e fixes | audit | done |
| Licence line, trademarks, contact email | owner | PRs #22, #23 |
| Review step 1: WebSocket Origin plus Host allow-list, cross-site write 403 | R1 | PR #43, main 1805402 |
| Review step 2: completion token for hidden-check grades | R4, G3 | PR #45, e21b371 |

## 2. Freeze steps still to do, in dependency order

| # | Status | Step | Source ids | Depends on / notes |
|---|---|---|---|---|
| F1 | **NEXT** | CI job that pulls `python:3.14-slim` and runs `pytest -m docker`. Also add the e2e-with-answers line to REVIEW.md (G9). | R5, G9 | None. Now meaningful because PR #45 added grading tests that need Docker. |
| F2 | **BLOCKED (owner decision)** | Demo mode `lms serve --demo` on the made-up course with fake answers, "Demo data" banner, README screenshots or GIF. | R2 | Decision: is a public made-up demo course allowed under the private-answers rule? (Fixtures with fake answers are already public by the 2026-11-11 exception, so likely yes.) |
| F3 | queued | Mock AXIS: no citations, reply starts "Offline demo reply (no model is connected)", active backend shown in the AXIS panel. | R3, 2d.7 step 1 follow-up | Touches AXIS mock only, not ranking. Agreed order puts it after F2. |
| F4 | queued | GET routes that also write (three routes) become POST/PUT or stop writing. | Follow-up from step 2 thread | Not in the review plan. I recommend scheduling it before F5, because it is a small correctness and security fix. Owner to confirm. |
| F5 | queued | Docs match code: stale ARCHITECTURE lines, soften "never"/"immutable"/"zero-dependency", state content status (7 of 296 units), fix AGENTS.md multi-tenant and provenance wording. | R6 | Do after F1-F4 so the docs describe the final state. Update the "Built today vs seams" table. |
| F6 | queued | Assistance rule detects code only: docs wording plus one failing test (full prose solution counted as no help). | R7 small | Test only, no change to crediting logic. |
| F7 | **BLOCKED (hold)** | Retrieved passages into a fenced "untrusted data" block; remove the "first 30 passages" fallback. | R8 small a, 2d.7 step 2 | Owner has not lifted the retrieval-code hold. |
| F8 | **BLOCKED (hold)** | Drop stop words and unit id from the query; minimum score so "not found" can fire with an index loaded. | R8 small b, 2d.7 step 5 | Same hold. Needs the owner's reading of Fable section 7. |
| F7-F9 note | **HOLD LIFTED 2026-11-15** | Retrieval work runs in its own thread "Build production-grade AXIS retrieval". New order (ADR-0035 amendment, PR #46 docs, section 4): R-1 fixture index + question set + CI gate; R-2 keyword vs HR on that set; R-3 retrieval port + index manifest; R-4 = F7 + F8 (fenced passages, not-found floor); R-5 prompt rules + no-index message; R-6 rag-core adapter + model wiring (only if R-2 says yes); R-7 optional query rewriting. rag-core packaged: Content-Library PR #1 merged, tag v0.1.0. A7 stays paused. F7 and F8 are therefore R-4, after R-1 to R-3; F9 = R-1..R-3, R-5..R-7. Track them in that thread, not here. **Update 2026-11-15 (later):** R-1 DONE (PR #47 merged: question set + CI gate). Measurement PR #48 open. Result on the real corpus: rag-core HR 81% first-hit, rag-core L 63%, current LMS keyword 20%; a score floor alone cannot do "not found". Owner direction: no Gemini (keep the test data as a record). HR adoption is justified, so R-6 (rag-core adapter) is planned, not conditional. Query transformation (R-7, for learner questions with pasted errors) and an agentic eval for generation move from optional to PLANNED. |
| F9 | (see note above) | Owner decision 2026-11-15 on Fable section 7: reject (c), upstream docs stay primary; accept (a) measure keyword search first and (b) labelled downgrade, (a) first; also considering rag-core as the retrieval backend (LMS does generation only; check it connects cleanly). Generation quality via system prompt, agentic eval if needed. Order to be settled in thread "Build production-grade AXIS retrieval"; update F7-F10 then. Rest of the RAG plan from ADR-0035 section 4: retrieval port plus versioned index, fixture index plus CI gate, model wiring, LLM query rewriting. A7 ConceptStore wiring (paused, not enough concept notes). | A7, 2d.7, RL (ADR-0035 disagreements) | Owner decides on Fable section 7: measure keyword search first, labelled downgrade instead of "unavailable", give AXIS the current lesson directly. If decided "after freeze", move to backlog. |
| F10 | **BLOCKED (after F9 decision)** | Split `app.py` into routers plus AppContext, with a service layer as the goal. | A8, RL (R10) | Waits on retrieval PRs so the two do not collide. |
| F10a | NEW 2026-11-18, queued | Stress-test AXIS in all three modes (Coach, Hybrid, Socratic) against real learner questions, including Hybrid, which the current no-source rules (SPEC-24) do not cover. Report what fails, then fix as separate small PRs. | Owner request 2026-11-18 | Run after the retrieval steps (R-4 to R-7) and the agentic eval, so it tests the final behaviour. Needs an ADR/spec amendment if Hybrid rules change. |
| F10b | NEW 2026-11-18, queued | Mode usage report: count how often each AXIS mode is used. The log already records mode per answer. Sub-step of the tracing step (the "plan step 8" in the retrieval thread; in this tracker, the retrieval/tracing work under F7-F9). | Owner request 2026-11-18 | Read-only report over the interaction log; no schema change expected. Can run any time, ahead of F10a to give it real usage numbers. |
| F11 | queued | Fresh independent audit after all steps (same prompt as 9 Nov), check README claims again. | Audit plan | After F1-F10. Before 5 Dec. |

## 3. Hosting gates (reminders, not freeze steps)

The owner must be reminded before any public hosting or other learners. Do not schedule.
- **G1** learner code and hidden checks share one process (needs a two-process redesign with its own ADR). PR #45 does not close it.
- **G5** containers share the host kernel (rootless Docker or gVisor for a real server).
- **G6** pin the base image by digest (digest recorded 2026-11-14 in the gaps file; re-check).
- **G2** policy only: never use `LMS_RUNNER=subprocess` where others run code.
- Operability list (real serve mode, health check, migrations, backup note, app Dockerfile), RL-operability, is needed before any pilot. The self-hosted pilot ADR is on hold.

## 4. Backlog (unscheduled; each needs the owner's go)

Sandbox and tests:
- G7 / G10 stdlib shadowing by an extra file (reject stdlib-like names or run the harness with `-P`); "next runner PR".
- G8 flaky e2e database (unique file, deleted at start).
- G4 give every hidden check an assertion message (content pass, private repo).

From the review (RL):
- Assistance accounting: any Coach or Hybrid reply counts as at least `structural_direction` (needs ADR-0009 amendment). R7 large.
- Ledger guard triggers on `evidence_ledger` and `interaction_log`. R9.
- One transaction per attempt; expire unfinished idempotency receipts. R9.
- Exclude `test_mode` evidence; no evidence from the mock judge (evidence rule, owner decision). R9.
- Delete the legacy shell and routes `/execute`, `/axis/consult`, `/explain-error`, `/learners/{id}/progress`, `/learners/{id}/ledger`. R10.
- Socratic filter: parse code spans; strip closing `</learner_query>`; judge twice before Strong.
- CI: committed `dist` matches `frontend/src`, e2e on the fixture course, Python type checker.
- Remove the local model's silent fallback to the mock.
- README "How this was built", one overview page, cut noise files, ADR index rows 0030-0032, dead `skills/` link in AGENTS.md.
- Ideas: signed evidence export, item-quality report, two-process grading (= G1).
- Check upstream source licences for quoting to learners.

Content and product:
- Stage 0 open follow-ups: TW-0.1/TW-0.2 longest-key fix, SPEC-16 note on Module review spares, PY-0.3 practice volume 12 of 15 (may be fixed by PR #21, confirm), Stage 0 Explain page discussion (thread "Improve Stage 0 Explain pages").
- Concept notes: on hold, do last, after the Fable review (PROGRESS.md "Parked").
- Videos: PY-0.4 pilot (needs YouTube-embed change).
- Writing-style pass: last.

## 5. Open owner decisions

1. Is a public made-up demo course acceptable? (unblocks F2)
2. ~~Retrieval hold and Fable section 7~~ ANSWERED 2026-11-15: hold lifting, (c) rejected, (a) then (b) accepted, rag-core as backend under consideration. Order of F7-F10 now settled (see F7-F9 note). F10 (split app.py) still waits for the retrieval PRs.
3. Schedule F4 (GET routes that write) before the docs step?
4. Is the freeze for a portfolio release, a pilot, or both? (decides how much of section 3 and the operability backlog moves up)

## 6. Coverage check against the two source threads

Review thread: all 9 ordered rows and all leftover rows are in sections 1, 2 or 4. Audit thread: A0-A8, 2d.5-2d.7, Stage 0 fixes, items 1-4, licence work, concept-notes hold, branch cleanup are in sections 1, 2 or 4. Not found in either thread file: nothing is known to be uncovered, but I could only read the audit thread through 14 Nov 02:50 (it is very long); later messages were taken from project memory and the coordinator note.
