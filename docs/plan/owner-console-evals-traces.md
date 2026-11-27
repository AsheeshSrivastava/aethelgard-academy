# Owner console for evals, traces and observability (backlog)

> **2026-11-27: the "demo mode is deferred" note below is superseded (demo mode is a freeze step). The console stays backlog.** See [freeze-2026-12-05.md](freeze-2026-12-05.md).

Status: **Proposed** 2026-11-26 (owner), for **after the 5 Dec 2026 freeze**. Nothing is decided or built. Tracker row: ADR-0035 section 5.1, step 8d.

## Need
The owner wants a proper graphical view of eval results, traces and observability, instead of reading files and command output.

## What exists today
- `lms report axis-modes`, `axis-latency` and `axis-html` (SPEC-29). The HTML report is one static local file with counts and timings only.
- The trace file (SPEC-28): ids, timings and allow-listed attributes, no text.
- `lms eval axis-obedience` (SPEC-30): each run writes a folder with `results.json`, `report.txt` and the replies.
- ADR-0037 section 2.7 already records a later live page (SPEC-29b), and section 5 plans ADR-0038 (LangSmith, owner-run eval runs only). Neither is written.

## Options, to decide later
| | Option | Notes |
| :--- | :--- | :--- |
| a | Local static pages, extending the SPEC-29 report to eval runs and single traces. **Start here.** | Offline, no login, no new server route |
| b | An owner page inside the app (SPEC-29b) | Needs an owner/admin gate first; the backend has no admin role today, so that is its own decision |
| c | An outside viewer (self-hosted Langfuse, or LangSmith) | Needs its own decision (ADR), because data leaves the app |

## Privacy rule, for every option
- Traces and anything built from them hold **no learner text**.
- Eval review files hold **model replies**. They stay on the owner's machine: not committed, not published, not sent to a viewer without a decision that says so.

## Before building
Decision, ADR, spec, tests, code, as for any change.

## Also deferred: demo mode
A demo mode with made-up sample content is **deferred until the RAG and AXIS issues are fixed** (owner, 2026-11-26). It is a separate piece of work from the console.
