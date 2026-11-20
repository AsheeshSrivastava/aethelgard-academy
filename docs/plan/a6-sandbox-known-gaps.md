> **Snapshot copied from the project folder on 2026-11-20.** Source: lms-backlog/a6-sandbox-known-gaps.md. Hosting gates G1, G5, G6 and G2 are repeated in master-plan-2026-11-15.md section 3.

# A6 sandbox: known gaps to close later

Source: PR #38 (Docker runner, merged 8a6bfa3) and PR #39 (hidden checks via stdin, merged afb6a09). Recorded 2026-11-14.
Also written in the repo: SPEC-03 section 2.4 and the ADR-0036 amendment (PR #39).

| # | Gap | Why it matters | Likely fix | When |
|---|-----|----------------|-----------|------|
| 1 | Hidden checks and the learner's functions share one process. A program written to attack the grader can walk call frames or scan its own memory (one leftover copy of the check text was found). | Learner could read or bypass hidden checks | Run learner code and grader in separate processes/containers | Before public hosting (owner, 2026-11-15); remind owner before hosting |
| 2 | Subprocess runner runs as the server's user, so it can read the private answers folder. | Answers exposed if LMS_RUNNER=subprocess is used with others | Never use subprocess where others run code; Docker is the default | Policy now; no code needed |
| 3 | `os._exit(0)` at import still passes a check run (old behaviour). | Learner can fake a pass | Completion token in runner layer (ADR-0036 am. 5) | DONE: PR #45 merged (e21b371) |
| 4 | A bare `assert` in a hidden check now reports only `AssertionError`. | Weaker feedback | Give every hidden check an assertion message (content task, private repo) | Content pass |
| 5 | Containers share the host kernel (Docker Desktop VM on Windows adds a layer). | Docker/kernel escape bugs | Keep Docker Desktop updated; rootless Docker or gVisor for a real server | Before public hosting |
| 6 | Base image pinned by tag `python:3.14-slim`, not digest. | Tag can change | Pin by digest after pull (digest pulled 2026-11-14: sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f; re-check when pinning) | Before public hosting |
| 7 | An authored extra file that shadows a stdlib module could run before the checks are read (low confidence; only the build spec can cause it). Not recorded in the repo. | Edge case for builds | Check file names against stdlib names, or load checks before any extra file | Next runner PR |
| 8 | Flaky e2e: one Docker-runner run failed 6 of 27 because the e2e database already held 11 PY-0.1 rows (reused file named by process id, cause unproven). Rerun passed 27/27. | Flaky test, not a sandbox flaw | Make the e2e database file unique and deleted at start | Test hygiene |
| 9 | Process: run e2e with `LMS_ANSWERS_DIR=D:\01-Project\lms-answers` (and `LMS_RUNNER=docker`, then `npm run e2e` in frontend) before merges that touch grading. | Catches answer-dependent regressions CI cannot see | Owner habit; consider a checklist line in REVIEW.md | Ongoing |
| 10 | Item 7 mitigation idea: reject stdlib-like names in `extra_file_problem`, or run the harness with `-P`. | | | |

Rule: never set LMS_RUNNER=subprocess on a machine running other people's code.

> 2026-11-15: an independent review added new items and an agreed order for the freeze. See `review-2026-11-15-plan.md` in this folder.

> 2026-11-15 HOSTING GATE (owner decision, from "Close the os._exit grading bypass"): gap 1 is not the next step. It must be fixed before any public hosting or other learners, and the owner must be reminded before hosting. The completion-token fix (gap 3) does not close it: the token lives in the same process as learner code. Gaps 5 and 6 are also hosting gates.
