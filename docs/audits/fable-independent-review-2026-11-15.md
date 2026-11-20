# Independent review: Aethelgard Academy LMS

- **Reviewed:** `github.com/AsheeshSrivastava/aethelgard-academy`, `main` at `cad782a` (PR #42), read-only.
- **Date:** 2026-11-15. Brief: `lms-review/fable-independent-review-prompt.md`.
- **Not available to me, by design:** the private answers folder, a Docker daemon, a local model, `data/index`.
- **Evidence labels:** **[ran]** means I confirmed it by running something. **[read]** means I inferred it from the code. Anything else is marked as a guess.

What I ran: `uv run pytest -q` (1726 passed, 31 skipped, 80 s; the skips are the Docker tests plus tests that need real answers), `uv run ruff check` (clean), `npm run typecheck` (clean), `npm test` (364 passed, 18 files). I also started the server with `LMS_RUNNER=subprocess MOCK_AI=true` on a scratch database and probed it, and I called the Socratic filter, the assistance classifier and the retriever directly with test inputs.

---

## 1. Executive summary

- **Production: ready with fixes, for the scope it has today (one learner on their own machine). Not ready for a pilot with other people.** The sandbox, the answer split and the test suite are solid, but there is no sign-in, no way to serve it other than a dev server, one cross-origin hole, and the two AI honesty claims (Socratic filter, assistance accounting) are weaker than the docs say.
- **Portfolio: good, not yet strong.** The engineering judgment is real and visible in the later ADRs, the sandbox and the tests. The first five minutes hide it: no screenshot, a fresh clone cannot run one graded exercise, the AXIS demo shows invented citations, and start-up prints "129 errors".
- The biggest single lever for both lenses is the same: a **demo mode** that lets a stranger see the whole loop work, with honest labels.
- Content is the long pole, not code: 7 of 296 units have a lesson. No review can fix that; say it plainly in the README.

---

## 2. Top 10 actions (ranked by impact divided by effort)

| # | Lens | Finding | Evidence | Why it matters | Suggested fix | Effort | Before 5 Dec? |
|---|---|---|---|---|---|---|---|
| 1 | A | The run WebSocket accepts any `Origin`, and the app accepts any `Host`. | `src/lms/api/app.py:1027-1029` (no origin check). **[ran]** a connection with `Origin: https://evil.example` ran my code on the host as the server user under `LMS_RUNNER=subprocess`. | CORS does not cover WebSockets. Any web page the learner opens can run code through the local server. With the subprocess runner (the README's suggested opt-in) that is code execution on the learner's machine. | Check `Origin` against `allowed_origins()` plus the app's own origin before `accept()`. Add `TrustedHostMiddleware` (blocks DNS rebinding). Add a test for both. | S | Yes |
| 2 | B (and A) | A fresh clone cannot run a single graded exercise, so the core loop is invisible. | **[ran]** catalog on a fresh clone: 296 units, 7 lessons, 0 units with seeds, build locked behind Cold Checks that cannot be served. Loader logs `Curriculum checks: 129 errors, 1050 warnings`. | A hiring engineer sees lessons and a canned chatbot, not the ledger, Cold Check, review or build. The best work cannot be seen. | Add `lms serve --demo`: point `LMS_CURRICULUM_DIR` and `LMS_ANSWERS_DIR` at a small made-up course (the `tests/fixtures` items already exist), turn test mode on, show a "Demo data" banner. Put 3 screenshots or one short GIF in the README. | M | Yes |
| 3 | A, B | The default (mock) AXIS shows invented citations and canned replies with no label. | `src/lms/adapters/ai/mock_axis.py:68` always cites "Operational Communication Cycle". **[ran]** `POST /api/v1/axis/stream` returned chips "Operational Communication Cycle" and "Schema Validation"; neither is a concept note. `frontend/src/lesson/AxisPanel.tsx:123-133` shows them; nothing says "mock". | PR #42 is titled "drop fake citations", and ADR-0034 item 3 says mock mode must say so plainly. The first thing a reviewer tries contradicts both. | Mock returns no citations and starts with "Offline demo reply (no model is connected)". Show the active backend in the AXIS panel header. | S | Yes |
| 4 | A | Hidden-check grading trusts exit code 0, so `os._exit(0)` passes any code item, including a Cold Check. | `src/lms/core/grading.py:188-190, 193`. **[ran]** `/api/v1/execute` with `import os; os._exit(0)` and a failing check returned `success: true`. | Known and recorded (SPEC-03 2.4, "Still open"). I disagree with leaving it: the fix already exists in the repo for builds and is about ten lines. | Reuse the random completion token from `core/builds.py:262-275` in `_run_checks`: pass only when exit is 0 and the token is printed after the last check. | S | Yes |
| 5 | A | CI never runs the sandbox tests, though GitHub runners have Docker. | `.github/workflows/ci.yml:18-19` sets `LMS_RUNNER: subprocess` and skips them. **[ran]** all 20 tests in `tests/test_docker_integration.py` skip without Docker. | The main security control is only ever tested on one laptop. A change to `docker_cli.py` can break isolation and CI stays green. | Add a CI job: `docker pull python:3.14-slim`, then `uv run pytest -m docker`. | S | Yes |
| 6 | B | README and ARCHITECTURE make claims the code does not back, and ARCHITECTURE contradicts itself. | See section 4.3 for the list. Example: `ARCHITECTURE.md:44, 98, 119` still say the subprocess runner is "today" and Docker is a seam, while `ARCHITECTURE.md:99` and the README say Docker is the default. | A senior reader checks one claim. If it fails, they discount the rest, including the parts that are true and good. | One pass: fix the stale lines, soften "never", "immutable event sourcing" and "zero-dependency", and state the content status (7 of 296 units). | S | Yes |
| 7 | A | Assistance accounting only detects code, not supplied reasoning. | `src/lms/adapters/ai/socratic_guardrail.py:115-146`. **[ran]** a complete step-by-step solution in prose, in Coach mode, was classified `none`; the same text ending in a question was `small_hint`. | "If AI supplies the reasoning path, the evidence is tagged" is the platform's central promise (README line 47, AGENTS.md). Today a learner can be walked through the whole answer in words and get full credit. | Short term: say in the docs that the rule detects code only. Then make it conservative: any Coach or Hybrid reply on a graded item counts as at least `structural_direction`, or ask the model for a structured label and take the higher of model and rule. | S (docs), M (logic) | Docs yes; logic after |
| 8 | A | With an index loaded, retrieval always returns passages, and they go into the system prompt unfenced. | `src/lms/adapters/ai/rag/retriever.py:80-93, 111-112, 126` (no stop words, no score floor, falls back to the first 30 passages). `axis_rules.py:57, 132`. **[ran]** "what is the capital of France?" returned 3 cited passages from a 3-document index; an instruction planted in a passage appeared under the heading "VERIFIED CURRICULUM GROUNDING" in the system prompt. | The "not in the course yet" path from PR #42 can only fire when there is no index at all. Third-party text sits in the most trusted part of the prompt, labelled as verified curriculum. | Drop stop words and the unit id from the query, require a minimum BM25 score, remove the "first 30 passages" fallback, and move passages to a fenced block in the user message with the same "untrusted data" rule the other prompts already use. | S to M | The fence and floor: yes |
| 9 | A | The ledger is append-only by convention, an attempt is several separate transactions, and test-mode or mock-judged evidence counts as real. | `sqlite_repo.py:846-881` (no trigger guards the table); each repo call opens its own connection (`:66-75`), so `app.py:1729-1734` and `:1665` are separate commits; no use of `test_mode` in `core/proficiency*.py`; `router.py:153-156` lets the keyword mock judge write Strong CO-6 evidence. All **[read]**. | "Immutable" should be enforced where the data lives. A crash mid-attempt leaves evidence without a receipt, and the retry is blocked forever (`:1652-1655`, the claim never expires). Evidence made with waits at zero should not raise a level. | Add `BEFORE UPDATE` and `BEFORE DELETE` triggers that `RAISE(ABORT)` on `evidence_ledger` and `interaction_log`. Give the repository one `attempt()` transaction. Exclude `test_mode` rows from estimates and never write evidence from the mock judge. Expire unfinished receipts after a minute. | M | Triggers yes; rest after |
| 10 | A, B | About 3,000 lines of legacy shell and four unused routes ship with the app, and `app.py` is one 1,500-line function. | `src/lms/web/{app.js,index.html,styles.css}` (3,045 lines; `vendor/prism*.{js,css}` are 0 bytes); `app.py:1017, 1165, 1292, 1810-1831` are not called by `frontend/src` **[ran grep]**; `create_app` spans `app.py:334-1846`. `/explain-error` returns 500 on a non-string `unit_id` **[ran]** and gives AXIS help with no Cold Check block and no assistance log **[read]**. | Dead code is attack surface and noise. The god function is the first file a reviewer opens. | Delete the legacy shell and the four routes now. Then split `create_app` (the planned A8): one router module per area, and move the orchestration in `handle_attempt`, `attempt_build` and `attempt_review` into plain service functions that take the ports. | S (delete), M to L (split) | Delete yes; split after |

---

## 3. Lens A: production grade

### 3.1 Architecture

**Medium. The hexagon is real in `core/`, but the application layer lives inside the web framework.** `core/` imports only the standard library and pydantic **[ran grep]**, and adapters sit behind small ports. That part matches the docs. The missing piece is a use-case layer: `submit_attempt`, `handle_attempt`, `attempt_build`, `attempt_review`, `open_stage_round`, `finish_cold_item` and `unit_cold_status` are closures inside `create_app` (`app.py:654-729, 947-1002, 1424-1451, 1647-1746`). They hold real business rules (what counts as the current exercise, when a round closes, when a clock starts), they can only be tested through HTTP, and the CLI re-implements parts of them (`cli.py:128-175`). Fix: a `lms/services/` package of plain functions or small classes that take `repo`, `runner`, `catalog`, `clock`. Routes become thin. This is the same work as the planned A8, and I would make the service layer its goal, not just "smaller files".

**Medium. Ports are checked with `hasattr`.** `app.py:879, 916, 1221` test `hasattr(axis, "draft_readme")` and so on, and `app.py:1048` uses `getattr(runner, "start_interactive", None) or InteractiveRun`. `IAXISCompanion` no longer describes what the app needs. Fix: put `stream`, `judge_explanation`, `draft_readme` and `summarise_feedback` on the port (or a second small port), and `start_interactive` on `ICodeRunner`.

**Low. Some things are over-built for the scale.** `EventBus` has no subscriber anywhere in `src/` (`core/events.py`, published at `sqlite_repo.py:883`). `ILearnerRepository` still carries `get_learner`, `get_unit_progress` and `save_unit_progress`, used only by the legacy route and CLI. The "Postgres seam" and "vector DB" (ADR-0002) are stories, not seams anyone has exercised. None of this hurts, but each is a claim a reviewer may test.

**Low. Under-built for its own goal:** there is no notion of a tenant or user below `LOCAL_LEARNER_ID` (`app.py:153, 185-187`). That is a recorded deferral (ADR-0015) and fine for now. AGENTS.md still says "real multi-tenant production platform"; the code and README say single learner. Pick one wording.

### 3.2 Code quality

**Good overall.** `core/` is the best code in the repo: small pure functions, each with a one-line reason and an ADR pointer (`core/grading.py`, `core/proficiency.py`, `core/builds.py`). `docker_cli.py` and `docker_runner.py` are clear and careful. The frontend has no `dangerouslySetInnerHTML`, pinned dependencies and types generated from the OpenAPI schema **[ran grep]**.

**High. `app.py` is a god file and `create_app` a god function** (action 10). 1,854 lines, about 60 routes and 30 helpers in one closure.

**Medium. Duplication.** The Docker and subprocess runners repeat the file-writing and timeout result (`docker_runner.py:109-160`, `subprocess_runner.py:36-96`). The interactive harness and the check harness are two separate embedded programs. `problem()` exists twice (`app.py:194`, `model_settings.py:33`). `load_dotenv_if_present` is a hand-written parser inside the LLM adapter, imported by the API (`app.py:79`). The system prompt, user message and budget check are assembled the same way in `consult` and `stream` for each provider.

**Medium. Names promise more than the code does.** `HybridRerankedRetriever` is described as "Production-grade hybrid retriever combining sparse BM25, dense embeddings, RRF and cross-encoder reranking" (`retriever.py:22-24`); as wired it is BM25 plus a word-overlap scan. `LocalLLMCompanion` is an alias for the OpenAI adapter. `verify_passage` is called at index-build time (`indexer.py:88`), not at retrieval.

**Low. Dead or stale:** legacy shell, four routes (action 10), `SocraticBoundaryViolation` and `strict=True` are never used by the app, `FALLBACK_MODEL = "qwen3.5-9b"`.

### 3.3 Correctness and robustness

**High. An attempt is not atomic** (action 9). Evidence, the cold-item row, the round result and the idempotency receipt are separate commits. Two effects: a crash between them leaves a receipt with no response, and every retry then gets 409 "still being checked" for ever, because `claimed_at` is stored but never read (`sqlite_repo.py:650-658`, `app.py:1652-1655`). Sending the same answer without an `interaction_id` writes a second evidence row.

**Medium. Reads grow with history.** `get_evidence_ledger` loads and validates the learner's whole ledger, and one attempt calls it three to five times (`app.py:1688, 1712, 1745` plus helpers). `dispute_judgement` and Cold Check feedback scan the newest 10,000 interactions in Python (`app.py:1278, 1372`); beyond 10,000 events an older judgement can no longer be disputed. Fine for one learner for months. Add an indexed lookup by `interaction_id` and pass one loaded ledger through the request.

**Medium. GET requests write.** `GET /courses/{id}` and `GET .../cold-check` start a missing Cold Check clock (`app.py:577, 1436-1438`); `GET .../build` sets the served pointer (`:833`). It is deliberate self-healing, but it makes reads unsafe to cache or retry and surprising to a reviewer. Move the repair to start-up or to the write that should have done it.

**Medium. Interactive run edge cases.** The first WebSocket message is read with no timeout and no type check (`app.py:1030-1032`): a non-object JSON value raises, and a silent client holds a connection (not a run slot). The receiver task's disconnect exception is never collected (`:1071-1085`). **[read]**

**Low.** `/api/v1/explain-error` takes an untyped body and 500s on bad input **[ran]**. `/api/v1/execute` and `playground:verify` accept code of any size; a 20 MB body was accepted **[ran]**. The interaction log stores full file contents on every "verify" (`app.py:855-859`), so it grows without bound. A local-model failure silently answers from the mock (`router.py:72`, `local_llm_companion.py:206-209`), which ADR-0035 2.7 already rejects.

**Good.** WAL plus busy timeout, idempotent attempts by key, the reset marker that never deletes evidence, output and time caps, refusal instead of queueing when run slots are full.

### 3.4 Security

**High. Cross-origin WebSocket and no Host check** (action 1). **[ran]**

**Sandbox: sound for its stated threat model.** One throw-away container per run, no network, read-only root, non-root user, all capabilities dropped, no-new-privileges, memory equal to swap, CPU, pids, file-count and file-size limits, `--pull never`, nothing copied from the host environment, and it fails closed (`docker_cli.py:56-83`). I could not run it (no Docker here), so this is **[read]** plus the unit tests. The residual risks in ADR-0036 are correctly named. Two additions: pin the image by digest, and note that `open_to_container` makes the run folder world-readable on a shared host (`docker_cli.py:86-93`).

**Medium. Grading shares a process with learner code.** Recorded. My only disagreement is on `os._exit(0)` (action 4), because that one is trivial to hit and trivial to close.

**Medium. Prompt injection.** Learner text is wrapped in tags and the model is told to treat it as data, which is good. Three gaps: retrieved passages go into the system prompt with no fence (action 8) **[ran]**; `build_user_message` does not strip a closing `</learner_query>` from learner text, although the README, judging and summary prompts do strip theirs (`axis_rules.py:138-151` versus `:254, 262, 290-295`); and the judge's verdict writes Strong evidence from a single model call that reads learner text (`app.py:1225-1250`). The code-level controls (code stripped from summaries, verdict decided by code from per-idea booleans) limit the damage. Add the strip, and consider judging twice and requiring agreement before writing Strong.

**Medium. The Socratic filter is a heuristic, in both directions.** **[ran]** Four of five replies that gave code inside a sentence passed (`"Just write total = price * quantity and then call print(total)"`, `"Use name.strip().upper()..."`, `"Loop with for item in items: ..."`, `"Change line 3 so it reads print(f\"Ticket: {n}\")"`). Three of four honest Socratic questions were withheld because they contained "return (", "import the module" or "assert" (`socratic_guardrail.py:39-66`). Withheld sentences are replaced by a fixed line about "data flow" and "egress", which will read as a broken tutor. Fix options: detect code by trying to parse backticked and line-level spans with `ast`, or ask the model for structured output (question text only) and reject anything else. Either way, say "filtered" and not "never" in the README.

**Low. Answer material.** The split is clean: public seeds carry no keys **[ran grep]**, `public_unit` and `public_build` use allow-lists, hidden checks travel on stdin, a guard test exists. Two notes: rubric ideas are sent to whichever cloud provider judges (expected, but say so in ADR-0021), and the app silently uses a sibling `../lms-answers` folder if one exists (`adapters/curriculum/builds.py:28-37`), which is convenient and surprising.

**Low. Secrets and CORS.** Keys stay in the environment, provider error text is never echoed, the wildcard origin is refused, gitleaks runs in CI. Good.

### 3.5 AI features

**High. Assistance accounting** (action 7) and **the mock's fake citations** (action 3).

**Medium. Retrieval quality today** (action 8). The query is `"{unit_id} {question}"` with no stop-word handling, and the fallback "dense" search is a Python loop over every passage for every question (`retriever.py:80-93`). On the real upstream corpus that is slow as well as noisy. I could not measure it without `data/index`.

**Cost control is good.** The monthly cap is checked before each paid call against a worst-case cost, a call with no usage numbers is costed at its limit, paid providers need explicit confirmation, and a paid failure is never hidden behind the mock (`metering.py`, `router.py`). The check and the record are not one atomic step, so two parallel calls can pass the cap by one call. That is acceptable at US$5.

**Model failure.** Timeouts are 30 s with no retries, errors reach the learner as "AXIS is unavailable right now" (`app.py:1158-1161`). The exception is the local profile's silent mock fallback (3.3).

**Is ADR-0035 sound and right-sized?** Sound in its parts, over-sized in its order. See section 7.

### 3.6 Testing and CI

**What the tests prove.** 1,726 backend tests in 80 s and 364 component tests in 18 s, all offline **[ran]**. The API tests are real integration tests through `create_app` with a real SQLite file. The made-up fixture course is a smart answer to the private-answers split: CI exercises every grader without a real key.

**What they miss.**
- The sandbox, in CI (action 5).
- The end-to-end browser flows: `frontend/e2e` (7 specs) needs the private answers and runs only on the owner's machine. Point a CI e2e job at the fixture course, even for two flows.
- Whether the committed `src/lms/web/dist` matches `frontend/src`. Nothing checks it. My Linux build produced different chunk names from the committed ones; I could not tell platform noise from drift, which is itself the problem. Build in CI and fail on a diff, or build at release and stop committing it.
- The negative cases I found by hand: cross-origin WebSocket, `os._exit(0)`, in-sentence code in Socratic mode, a full prose solution in Coach mode, an off-topic question against a loaded index. Each deserves one failing test first.
- Lint is narrow by choice (`E4, E7, E9, F`; `pyproject.toml:33-34`) and there is no type checker for Python. For a typed, pydantic-heavy codebase, `pyright` or `mypy` in CI would be cheap credibility.

**Private-answers split.** It weakens CI less than I expected, because the graders are tested on fixtures. What CI cannot see is real content: a wrong key, a hidden check that passes wrong code, a rubric that does not fit its prompt. A nightly job on a private runner, or a required local command before content PRs with its output pasted in the PR, would close that.

### 3.7 Operability

**High for a pilot. There is no way to serve it except the dev server.** `lms serve` hard-codes `host="127.0.0.1"` and `reload=True` (`src/lms/__init__.py:99`). Every path is relative to the working directory (`app.py:375, 402`; `profiles.py:18`; `local_llm_companion.py:47, 373`), so it only works when started from the repo root, and the built package would not find its curriculum. There is no Dockerfile or compose file for the app, and no note on how the app container would reach Docker for runs.

**Medium.** No logging configuration (only the runner logger attaches a handler, `docker_runner.py:39-45`), no request id, no access to "which runner, which model, which index" in one place. `/api/v1/health` is a constant (`app.py:487-489`); it should report database, runner, AXIS backend and index status, which the code already knows. Schema changes are ad hoc `ALTER TABLE` inside `initialize()` (`sqlite_repo.py:117-121, 193-196`) with no version number; add `PRAGMA user_version` and numbered steps before the next change. No backup note for `lms_state.db` (with WAL, a file copy is not safe; use `VACUUM INTO` or the backup API).

**Low.** `pytest` is a runtime dependency (`pyproject.toml:18`). Start-up prints `Curriculum checks: 129 errors, 1050 warnings` on a healthy fresh clone **[ran]**; 90 of the errors are "no private answers" and 953 warnings are units with no content yet. Summarise expected gaps in one info line and keep "error" for real faults.

### 3.8 Better strategies

See sections 5 and 6.

---

## 4. Lens B: portfolio readiness

### 4.1 The first five minutes

**High. No picture.** There is no screenshot, GIF or hosted demo in the repo **[ran]**. A reviewer who does not clone sees a wall of bold text.

**High. Cloning does not show the product** (action 2). Without Docker the playground refuses to run; without answers every exercise says "no exercise yet"; AXIS is a canned mock with made-up sources; the terminal shows 129 errors. Each has a good reason, and each is explained somewhere, but together they read as "does not work".

**Medium. The README leads with adjectives.** The subtitle is "Autonomous Curriculum Studio & Socratic AI Engineering Platform"; nothing in the repo is autonomous. Phrases such as "diagnostic composure", "Andragogical Learning Facilitator & Architecture Engine" and "Ingress → Transformation → Egress" cost trust. The origin quote is the best paragraph in the file; the "Built Today vs Pluggable Seams" table is the second best. Lead with those and a screenshot.

**Medium. Quickstart gaps.** It works as written **[ran, with uvicorn]**, but it does not say that Docker is needed for anything interesting until after the command, and "Run locally in under 1 minute" only holds for a server that cannot run code.

### 4.2 Evidence of engineering judgment

**Strong where it is specific.** ADR-0036 states the old behaviour was a silent fallback, names the residual risk and amends earlier limits with a reason. ADR-0034 lists five ways the current behaviour is dishonest. ADR-0021 and the fixture course show a real trade-off handled well. The 2026-11-04 gap audit says "not built" in plain words. SPEC-03 2.4 lists what the harness does not close.

**Weak where it is generic.** ADR-0001 to 0012 were written on two days and read like templates: ADR-0002 decides on "Chroma / Qdrant" that never arrived and calls SQLite "mathematically safe against data loss". 36 ADRs and 19 specs (about 330 KB) for about 14,000 lines of Python in two and a half weeks reads as volume. Mark the early ones "superseded" or "aspirational" where true, and give `docs/adr/README.md` a "start with these five" line.

### 4.3 Honesty: claims the code does not back

| Claim | Where | What the code does |
|---|---|---|
| Subprocess runner is "today", Docker is a "seam" | `ARCHITECTURE.md:44, 98, 119` | Docker is the default and fails closed. The same file says so at line 99. Stale. |
| "Audit fixes in progress: close SQLite connections, WAL, batch queries, cap runs, wire Docker" | `ARCHITECTURE.md:125` | All done except AXIS grounding. Stale, and it undersells the work. |
| Socratic output "is filtered so it never hands over a code solution" | `README.md:24` | A regex heuristic; in-sentence code passes **[ran]**. |
| "If AI supplies the reasoning path, the skill is routed to STRENGTHEN" | `README.md:47` | Only replies that contain code are tagged **[ran]**. |
| "Immutable Event Sourcing", "immutable, append-only ledger" | `README.md:25, 40` | Append-only by convention, no database guard; state also lives in mutable tables (`unit_cold_check`, `review_item`, `cold_check_item`) that cannot be rebuilt from the ledger. It is an append-only evidence log, which is a fine thing to be. |
| "Deterministic Capability Tracking"; REVIEW.md: wrong if "AI grades something" | `README.md:25`, `REVIEW.md` item 2 | The concept check is judged by a model and writes Strong evidence (`ai_judgement.py:18`, ADR-0026). A recorded decision, but the two documents disagree with it. |
| "Every retrieved passage is checked to be an exact byte-slice" | `README.md:48` | Checked when the index is built, not when a passage is retrieved or loaded. |
| "Zero-Dependency Domain Core" | `README.md:46` | Depends on pydantic. "No framework or I/O imports" is true and is the point. |
| AXIS RAG "indexes only our proprietary curriculum ... zero hallucinations" | `AGENTS.md` (Provenance Firewall) | AXIS reads upstream third-party docs when an index exists; the curriculum is not searched at all. ADR-0034 admits this; AGENTS.md is public and does not. |
| "real multi-tenant production platform" | `AGENTS.md` | Single learner, no sign-in. |
| "PR #42: drop fake citations" | commit `10e8f8e` | True for live models with no index; the default mock still invents them **[ran]**. |
| Mermaid arrows `Core --> DB/AI/Runner` | `README.md:38-42` | In a hexagon the adapters depend on the core. The picture shows the opposite of the rule the text states. |

What is honest and should stay: the "Built today vs seams" table, the skill-level limit note, the fresh-clone note about answers, "not a sandbox" on the subprocess runner.

### 4.4 Signal versus noise

**Cut or move:** the legacy shell; `.zed/`, `.claude/settings.json`; `docs/plan/work-sequence.md` (a personal task list); the 16 roadmap files in `reference/` (about 370 KB that a reviewer will not read, though the loader needs them, so move them under `curriculum/roadmaps/` and describe them in one line); `docs/architecture/02-operational-narrative-spine-79-units.md` (79 units in the title, 296 in the catalog).

**Fix a broken pointer:** `AGENTS.md:59` links to `skills/systems-architect-mentor/SKILL.md`, which is git-ignored, so the link is dead for everyone else. `docs/adr/README.md` has no rows for ADR-0030 to 0032.

**Promote:** a single `docs/architecture/overview.md` with one diagram of the attempt path and one of the AXIS path; the sandbox ADR; the answer-split design; the proficiency estimator. A "Design decisions I would defend" section with five links beats 36 files.

### 4.5 History, licence, branding, contact

- **History.** The clone I was given is shallow (128 commits from 2026-11-09), so I cannot judge the full history. In what I can see: small, well-named commits, PRs with "Testing / Risk / How to revert", a protected `main`. That is a good signal.
- **AI use.** 85 of the 128 visible commits carry a Claude co-author line and 25 are authored by Claude. `AGENTS.md`, `CLAUDE.md` and the work sequence ("Claude builds, tests and commits") are public. The README says "Architected by" and nothing else. A reviewer will find this in one click, so say it first: a short "How this was built" section stating what the owner decided and reviewed, and what was AI-written. Directing and auditing AI work is the skill the platform teaches; owning that openly is a strength, hiding it is a risk.
- **Licence.** BUSL-1.1 with a non-commercial education grant and a one-year change date to Apache 2.0 is coherent. Two notes: the README and LICENSE say "BSL 1.1" and "BUSL-1.1" by turns; and for a portfolio, some reviewers will not clone source-available code at work. One README line ("you may read, run and evaluate this freely") removes the doubt. The LICENSE names the licensor "Asheesh Srivastava", the README "Asheesh Ranjan Srivastava".
- **Branding.** Three ™ marks and two company names in the first screen is heavy for a portfolio. Keep TRADEMARKS.md, use the mark once in the README.
- **Contact.** Consistent (`asheeshsrivastava9@gmail.com`) across README, LICENSE, TRADEMARKS and `pyproject.toml`.
- **Third-party text.** `data/index` is not in git, which is right. The source list includes books and courses ("LLMs from Scratch", "Generative AI for Beginners", "Hugging Face course"; `axis_stream.py:28-44`). Before any pilot, check each licence allows quoting passages to learners. I did not verify the licences.

### 4.6 What a senior reviewer would praise and doubt

**Praise:** the fail-closed sandbox and its written threat model; answers kept private without crippling CI; idempotent attempts; the spend cap; the honest "built versus seam" table; 2,000 fast offline tests; pinned CI actions and a secrets scan.

**Doubt:** 2% of the curriculum exists; documentation volume and vocabulary outrun the product; one 1,500-line function; AI honesty claims that a five-minute test breaks; no way to see it work; unclear how much the owner wrote.

---

## 5. Simplification opportunities

1. **Delete the legacy shell and its routes** (about 3,050 lines plus `/execute`, `/axis/consult`, `/explain-error`, `/learners/{id}/progress`, `/learners/{id}/ledger`, and the repository methods only they use).
2. **One runner core.** Write the files, start a process, feed stdin, cap output, time out: one function parameterised by "how to start the process" would serve `DockerRunner`, `SubprocessRunner` and both interactive runs. Today that logic exists four times.
3. **One companion base.** Grounding, prompt building, budget check, record and `finish_reply` are identical across providers. A provider should supply only `complete(system, user, limit)` and `stream(...)`.
4. **Drop `EventBus`** until something subscribes. Keep the "subscribers must not write" rule in the ADR.
5. **Replace the hand-rolled CLI parser** (`src/lms/__init__.py`) with `argparse`, and the hand-rolled `.env` reader with `python-dotenv` or pydantic-settings, with one `Settings` object read once. There are 22 `os.environ` reads spread over 8 modules.
6. **Retriever:** delete the Jaccard "mock dense" branch and the "first 30 passages" fallback. BM25 alone, with a score floor, is simpler and more honest than a fake hybrid. Rename the class to what it does until models are wired.
7. **One `problem()` helper**, raised as an exception with a handler, so routes stop returning `Union[Model, JSONResponse]` and `isinstance(build, JSONResponse)` checks disappear (`app.py:828, 848, 875, 907, 950, 1606`).
8. **Load the ledger once per request** and pass it down, instead of five reads.
9. **Docs:** fold ARCHITECTURE.md into the README's architecture section plus one overview page; they repeat each other and have drifted.

---

## 6. Strategy and creative ideas (at most five)

1. **Give AXIS the lesson, not a search engine.** With 7 lessons and 10 concept notes, the current unit's lesson and its linked notes fit in the prompt. That is exact grounding in the proprietary curriculum, which is the ADR-0003 target, with no index, no models and no threshold to tune. Keep upstream search as an optional second source. Trade-off: prompt size grows with lesson length, and it stops scaling at some point (then retrieval earns its place, with a question set to prove it). Cost: about a day, mostly tests.
2. **Demo mode as a product feature** (action 2). The same switch gives the owner a safe place to record videos and gives e2e tests a public data set. Trade-off: a second small course to maintain. Cost: one to two days, since the fixture items exist.
3. **A signed evidence export.** The ledger is the product. Add `GET /learners/me/evidence.json` plus a rendered "capability report" page: each skill, its level, the entries behind it, the help used, a hash chain over the rows. It is cheap because the data model already carries it, it is a strong portfolio artefact, and a hash chain makes "append-only" checkable. Trade-off: a public format is a promise to keep. Cost: two to three days.
4. **Use the interaction log to improve items.** The log already records every answer per item. A small offline report (pass rate on first try, most-picked wrong option, items nobody fails) tells the author which items are too easy, ambiguous or broken. No new runtime code. Cost: a day.
5. **Split grading into two processes cheaply.** Run the learner's module in a child process inside the same container, with the checks in the parent calling it over a pipe for the functions they test. It closes frame-walking and `os._exit` together without a second container. Trade-off: checks must call through a small proxy, so check style changes; do it only if a pilot with strangers is planned. Cost: about a week with tests.

---

## 7. Disagreements with existing ADRs and audits

1. **ADR-0035 (retrieval strategy): right parts, wrong order, too heavy for now.** Keep the port, the `index_version` in the log, the fenced untrusted text, the citation check and the CI question set. I disagree with three things. (a) Wiring an embedder and a cross-encoder (torch, a GPU or slow CPU, `trust_remote_code`) is justified by numbers from another corpus (rag-core); section 2.8 says "measure first" for query rewriting but not for the models. Build the question set first and measure BM25 with stop words and a floor on the LMS's own questions; only then decide. (b) "No reranker means AXIS is unavailable" ties the tutor's uptime to a component that only improves ranking. Fail closed on the answering model; if a ranking model is missing, answer with a visible "keyword search only" label. A labelled downgrade is not a quiet one. (c) The simplest grounding for the real target corpus is idea 1 above, and the ADR does not consider it.
2. **SPEC-03 2.4 leaves `os._exit(0)` open.** I rate it higher than "old behaviour": it makes Strong Cold Check evidence forgeable in one line, and the fix exists in `builds.py`. Close it before the freeze.
3. **ADR-0026 / `CONCEPT_CHECK_WRITES_EVIDENCE = True`.** I do not object to AI judging with a dispute button; that is a fair design. I object to three surroundings: REVIEW.md and the README still say AI never grades; the mock keyword judge can write Strong evidence; and one model call is enough for Strong. Suggest: Moderate from one call, Strong only on two agreeing calls or after a passed Cold Check, and never from the mock.
4. **ADR-0002 (dual store with a vector DB) and ADR-0011.** Accepted, never built. Mark them as "direction, not built" so the index page is honest.
5. **"Event sourcing".** ADR-0004 and the README use the term. The ledger is not the source of the state tables. Either make the Cold Check and review state derivable from the ledger (a real, larger change) or call it an append-only evidence log.
6. **ADR-0014 (commit the built frontend).** Acceptable for "clone and run", but only with a CI check that the build matches the source.
7. **The audit plan's A8 ("split app.py").** Agree, with a different goal: extract a service layer, not just smaller route files.

---

## 8. What is good and should be kept or highlighted

- The Docker runner: one profile, named constants, fail closed, no host environment, tested against the README and spec by a test.
- The private-answers design and the fixture course, including the guard tests.
- The pure domain core and the proficiency estimator, recomputable from the ledger.
- Idempotent attempts, reset markers that never delete evidence, WAL and busy timeout.
- The spend cap that prices the worst case before the call and never hides a paid failure.
- Provider-neutral AXIS rules in one module, so a provider switch cannot change the guardrails.
- Prompt hygiene on the judge, README and summary prompts (tagged, stripped, verdict decided by code).
- The later ADRs' plain, self-critical voice, and the "built versus seam" table.
- CI hygiene: pinned action SHAs, least permissions, gitleaks, a PR template that asks how to revert.
- A lean, typed frontend with no unsafe HTML and tests that read like behaviour.

---

## 9. Open questions for the owner

1. Is the 5 Dec freeze for a portfolio release, a pilot with other people, or both? Several ratings above change with the answer (sign-in, serving, grading isolation).
2. Should assistance accounting stay rule-based, or may the model label its own help (with the rule as a floor)?
3. Is a public made-up demo course acceptable, given the "answers stay private" rule? It would hold only fake items.
4. Do you want the README to state how AI was used in building this?
5. Will the pilot run on your own computer with the subprocess runner anywhere in the picture? If yes, action 1 is urgent, not just important.
6. Is the full Git history (before 2026-11-09) public? I only saw a shallow clone.
7. Have the licences of the upstream sources been checked for quoting to learners?

---

## 10. Nits

- `pytest` is listed under runtime dependencies (`pyproject.toml:18`).
- `README.md` says "1,400+ tests"; there are 1,726 plus 364 frontend tests.
- `FastAPI(title="LMS / KMS Production Platform Gateway")` and "Aethelgard Academy Web Shell" are leftover names.
- `GET /api/v1/units` returns `List[Dict[str, Any]]` and `explain-error` returns an untyped dict, so the OpenAPI schema is blind there.
- `docker_runner.py` adds a log handler at import time.
- `.env.example` sets `MOCK_AI=false` while the README promises offline by default; a copied `.env` flips the default.
- `interactive.py` passes the input token on the command line, where the program can read it from `/proc/self/cmdline`; harmless today (it only fakes an input prompt).
- `ARCHITECTURE.md` section 5 claims index load "in < 50 ms" and "zero-latency SQLite"; neither is measured in the repo.
- Vitest warns that jsdom is created 18 times; `isolate: false` or one pool would cut the frontend test time by about a quarter.
