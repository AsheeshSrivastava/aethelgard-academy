# SPEC-12: Learner Experience API Contract

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed by:** ADR-0017 (variant generation), ADR-0014 (frontend stack), ADR-0015 (identity), ADR-0016 (proficiency), ADR-0004, ADR-0009, ADR-0010
- **Design reference:** Aethelgard LMS design canvas (2026-10-30): front page, courses, course map, unit map, lesson, stage build, My progress
- **Date:** 2026-10-30

---

## 1. Scope

Every endpoint the redesigned frontend calls. Existing endpoints keep working; new ones are added under `/api/v1`. FastAPI's OpenAPI document generated from these models is the frontend's type source (ADR-0014).

Conventions:
- Learner-scoped routes use `/learners/me/...`; the learner comes from the session (ADR-0015).
- Errors use RFC 9457 `application/problem+json`: `{type, title, status, detail}`.
- The client never sends evidence category, strength or assistance level. The server derives them.

---

## 2. Identity (ADR-0015)

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| POST | `/auth/sign-in` | `{email, password}` | `204`, sets session cookie |
| POST | `/auth/sign-out` | — | `204` |
| GET | `/learners/me` | — | `{learner_id, display_name, auth_mode}` |

---

## 3. Catalog

| Method | Path | Response |
| --- | --- | --- |
| GET | `/courses` | `[Course]` |
| GET | `/courses/{course_id}` | `CourseMap` |
| GET | `/units/{unit_id}` | `Unit` (existing) plus `activities` |
| GET | `/courses/{course_id}/stages/{stage}/build` | `StageBuild` |

```text
Course     { course_id: "python" | "backend" | "ai-engineering", title, summary, stage_count, unit_count }
CourseMap  { course: Course, stages: [ { stage, title, units: [UnitSummary], build: BuildSummary | null } ] }
UnitSummary{ unit_id, title, concept_line, target_skills: [{skill_id, goal_level}], authored: bool }
Unit.activities: ["video", "explain", ...unit.methods without "Explain", "playground" (section 3.2), "cold_check"]   // video and explain always first, cold_check always last
BuildSummary { title, kind: "script" | "mini_project", locked: bool, pending_units: [unit_id] }  // locked until every unit in the stage passed its Cold Check
StageBuild { course_id, stage, title, kind, brief_markdown, sample_run: [str],
             files: [{path, starter}], requirements: [{id, label, unit_id}] }
```

Course ids map to the three roadmaps: Python Subject Roadmap v3, Backend Engineering Roadmap v2 (shown as "Python for Backend/AI"), AI Engineering Roadmap v2.


### 3.1 Content ownership and curriculum checks

The curator decides each unit's content, activities, their order and their scaffolding. These live in the unit's package under `curriculum/` (`meta.json`, `lesson.md`, starters, hidden checks; ADR-0008), with the roadmap as fallback for units without a package. The backend reads and validates them and serves them through `Unit.activities`; it never chooses activities. The frontend renders whatever list it receives and holds no per-unit activity list. Regenerated variants keep the curator's activity, skill and level; only surface details change.

Checks run when curriculum is loaded (and in CI):
- **Error:** a unit's target level needs evidence its activities cannot produce (Apply needs a Perform/Solve activity or the skill's main activity; Adapt needs a Diagnose/Judge/Transfer activity or the skill's main activity; Own needs the stage build). Main activities come from Learning Method v2 (ADR-0016 amendment A).
- **Warning:** a stage has no activity producing one of the three evidence categories (Explain/Reason, Perform/Solve, Diagnose/Judge/Transfer). A stage uses 5 to 6 activity types, not all 10.
- **Warning:** a target skill has no approved Cold Check seed (SPEC-13 section 8, rule 11). The skill stays provisional until it has one. Every activity has a deterministic form (ADR-0016 amendments B and C), so this replaces judging by activity type.

Activities and evidence categories:

| Category | Activities |
| --- | --- |
| Explain / Reason | Explain, Predict, Trace |
| Perform / Solve | Specify, Decompose, Modify, Build, Direct |
| Diagnose / Judge / Transfer | Debug & Validate, Evaluate |

### 3.2 Playground in every lesson (owner decision, 2026-10-31)

Every lesson shows the interactive playground.

- **Unit methods include Modify or Build:** the playground is that activity. It is graded and writes evidence (section 5). `Unit.activities` lists `modify` or `build`, and adds no separate step.
- **Otherwise:** `Unit.activities` adds a `playground` step before `cold_check`. It is ungraded practice and **writes no evidence**: learners can run and check their work, and the server records nothing in the ledger.
- **Content:** the unit package's `starter.py` and `test_solution.py` feed the playground. Check results in ungraded practice are feedback only.
- **Not yet built:** `Unit.activities` gains the `playground` step when exercises are built (step 4).

---

## 4. Exercises, Regenerate and Reset

| Method | Path | Response |
| --- | --- | --- |
| GET | `/learners/me/units/{unit_id}/activities/{activity}/exercise` | `Exercise` (the learner's current one; authored variant 1 by default) |
| POST | `/learners/me/units/{unit_id}/activities/{activity}/exercises:regenerate` | `Exercise` (a new variant) |
| POST | `/learners/me/units/{unit_id}/reset` | `204` |
| GET / PUT | `/learners/me/units/{unit_id}/state` | `{step, done_steps: [str]}` |
| GET / PUT | `/learners/me/drafts/{exercise_id}` | `{files: {path: content}}`; PUT → `204` |

```text
Exercise { exercise_id, unit_id, activity, origin: "authored" | "generated", variant_no,
           item_type, prompt_markdown,
           predict?:          { code, stdin, options: [{key, text}] },
           trace?:            { code: [str], input: str },
           playground?:       { starter, tasks: [{id, label}] },
           debug?:            { broken_code, stdin },
           debug_locate?:     { broken_code, stdin, error_types: [{key, text}] },
           choice?:           { material, options: [{key, text}] },
           specify_by_tests?: { function_name, signature, starter_tests },
           specify_contract?: { material, fields: [{id, label, kind, options}] },
           decompose_plan?:   { material, steps: [{id, text}] },
           decompose_code?:   { entry_function, starter, structure },
           explain_spot_flaw?:    { sentences: [{key, text}] },
           explain_model_choice?: { material, options: [{key, text}] } }
```

Each block is built from a list of allowed fields (SPEC-13 section 4), never by removing hidden ones, so a new hidden field cannot leak by accident.

`activity` in URLs and `Unit.activities` is a slug: `video`, `explain`, `predict`, `trace`, `specify`, `decompose`, `modify`, `debug-validate`, `build`, `evaluate`, `direct`, `playground`, `cold_check`.

Rules:
- `explain` cannot be regenerated: `409`.
- `video` has no exercise: `404`. A unit with no seed for an activity also returns `404`.
- `explain` serves the unit's free-text concept check prompt. `playground` serves the package's `starter.py`.
- `cold_check` can be regenerated only after an attempt on the current variant: `409` otherwise.
- A seed with template slots gives one variant per slot value (SPEC-13 section 6); each is its own `exercise_id`.
- Hidden checks (correct option, expected output, test code) never leave the server.
- Regenerate serves the next unseen variant from the unit's verified pool (curator seeds first, then batch-generated variants; ADR-0017). No LLM is called at learner time. When the pool is exhausted, the oldest-seen variant is reused.
- Cold Check variants come only from curator-approved pool entries.
- Reset clears `unit_progress`, unit state, drafts and current-exercise pointers. It never touches `evidence_ledger`.

### 4.1 Cold Check (ADR-0016 section 2.6)

| Method | Path | Response |
| --- | --- | --- |
| GET | `/learners/me/units/{unit_id}/cold-check` | `ColdCheckStatus` |

```text
ColdCheckStatus { state: "not_ready" | "waiting" | "available" | "passed" | "failed_waiting",
                  available_at: datetime | null, last_attempt_at: datetime | null }
```

- `waiting` starts when the unit's last other activity is completed; `available_at` = completion + 24 h.
- `GET .../activities/cold_check/exercise` before `available_at` returns `423 Locked`. Once passed, it returns `409`.
- The Cold Check serves only seeds with `cold_check_eligible` and `curator_approved` both true. A unit with no such seed returns `404`.
- AXIS requests carrying a Cold Check `exercise_id` return `403`; the frontend hides the AXIS panel on this step.
- A fail sets `failed_waiting` with a new `available_at` 24 h later.
- `GET /courses/{course_id}/stages/{stage}/build` and attempts on it return `423 Locked` while any unit in the stage lacks a passed Cold Check.

---

## 5. Attempts and Evidence

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| POST | `/learners/me/attempts` | `Attempt` | `AttemptResult` |

```text
Attempt       { exercise_id, activity,
                choice?: str,                       // predict, choice, explain items
                trace_answers?: [str],              // trace: the output lines
                locate?: {line, error_type},        // debug_locate
                files?: {path: content},            // playground, debug, decompose_code
                tests?: str,                        // specify_by_tests
                fields?: {id: key | [key]},         // specify_contract
                plan?: [str],                       // decompose_plan: ordered step ids
                ownership_note?: str }              // build only
AttemptResult { outcome: "passed" | "failed" | "recorded",
                feedback, checks?: [{label, passed, detail}],
                score?: {passed, total},            // partial feedback, SPEC-13 section 4
                reveal?: {correct, why},            // after commit
                evidence_entry_id: str | null, unit_decision: Decision }
```

Rules:
- Unknown fields are refused with `422`, so a client cannot send strength, category or assistance.
- The attempt must be on the learner's current exercise: `409` otherwise.
- **Ungraded playground:** runs the checks, returns `outcome`, and writes no evidence. `evidence_entry_id` is null.
- **Explain:** the free-text concept check stays on `POST /explain`.
- **Evidence is per seed:** an entry stores `seed_id`, and repeats of a seed, including its name variants, count once. The newest result is the one that counts.
- **Completing a unit:** once every activity in the unit's methods has been attempted, and Explain has a concept check entry, the Cold Check clock starts.

Cold Check attempts:
- Accepted only when the status is `available`: `423` otherwise.
- One item per target skill, one try each. After an attempt the next item for an unfinished skill is served.
- When the round ends, the unit's Cold Check passes if every item passed. Otherwise it fails and retries in 24 hours, on the failed skills only.
- `reveal` is never sent on a failed Cold Check, because the same item may come back. AXIS is off, so assistance is always none.

The server derives the evidence entry:

| Activity | Category | Strength (before assistance) |
| --- | --- | --- |
| predict | Explain / Reason | Strong if correct, Weak if not |
| trace | Explain / Reason | Moderate when correct, Weak if not |
| playground (Modify or Build only; section 3.2) | Perform / Solve | Strong if all checks pass first try, Moderate after retries |
| playground (ungraded practice; section 3.2) | none | No evidence entry |
| debug & validate | Diagnose / Judge / Transfer | Strong if fixed and verified |
| cold_check | category of the skill probed | Strong if passed, Weak if not (assistance always none) |
| build | Perform / Solve (Own context per ADR-0016) | Strong if all requirements met |
| SPEC-13 item types | category of the activity | Strong if the item passes first try, Moderate after retries, Weak if not |

`POST /learners/me/units/{unit_id}/playground:verify` with `{code}` runs the unit's playground checks on the server and returns an `ExecutionResult`. It writes no evidence, and `GET /units/{unit_id}` no longer sends hidden checks or the concept check rubric.

Assistance level for the entry is the highest level AXIS logged against that `exercise_id` since it was served (ADR-0009). `SUPPLIED_REASONING` forces Weak.

---

## 6. Proficiency and Ledger (ADR-0016)

| Method | Path | Response |
| --- | --- | --- |
| GET | `/learners/me/proficiency?course_id=&stage=` | `ProficiencyView` |
| GET | `/learners/me/ledger?skill_id=&unit_id=` | `[EvidenceEntry]`, newest first |

```text
ProficiencyView {
  skills: [ { skill_id, target_level, current_level | null, confidence: "provisional" | "supported" | null,
              evidence_counts: {explain, perform, diagnose}, decision: Decision, reason, entry_ids: [str] } ],
  units:  [ { unit_id, decision: Decision } ],
  next_action: { unit_id, skill_id, activity, decision: Decision, message } }
Decision = "Progress" | "Accelerate" | "Strengthen" | "Rebuild" | "Undecided"
```

---

## 7. Interactive Runs (WebSocket)

`WS /api/v1/runs` — one connection per run, on the sandbox runner (ADR-0005).

```text
client → {type: "start", files: {path: content}, entry: "solution.py", exercise_id?}
server → {type: "stdout", data} | {type: "stderr", data}
server → {type: "awaiting_input"}            // program blocked on input()
client → {type: "stdin", data}               // one line, newline appended
server → {type: "exit", code, duration_ms, timed_out: bool}
```

Limits: 5 s CPU, 120 s wall clock including time waiting for input, 64 KB output, no network. Runs never write evidence; only attempts do.

- `files` keys must be plain file names ending in `.py`, and `entry` must be one of them. A bad `start` gets `{type: "error", message}` and the socket closes.
- A run exceeding a limit is stopped and reports `timed_out: true`. Output past 64 KB is cut off with a final `stderr` notice.
- Learner code runs with a minimal environment, so it never sees API keys or `.env` values.
- On this subprocess runner, the network limit blocks Python sockets. It is not an OS sandbox. Hosting other people's code needs the Docker runner (ADR-0005).

---

## 8. AXIS Streaming

`POST /api/v1/axis/stream` → `text/event-stream`. Body: existing `AxisQuery` plus `exercise_id?` and `page: "video" | "explain" | "predict" | "trace" | "playground" | "build" | "progress"`.

```text
event: token     data: {text}
event: citation  data: {concept_id, title, doc_url}
event: done      data: {assistance_level, cited_concepts: [str]}
event: error     data: {message}
```

The Socratic guardrail (ADR-0009) runs on the full reply before `done`; in Socratic mode tokens are buffered per sentence so no code fragment is streamed before it is checked. The assistance level is logged against `exercise_id`.

- A request whose `exercise_id` is a Cold Check item returns `403`, on this route and on `/axis/consult`.
- `citation` events go out before `done`, built from the reply's cited concepts.
- If the local model cannot be reached and fallback is on, the mock companion answers. If fallback is off, the stream sends `error` and stops.

---

## 9. Extension Points

- `GET /api/v1/features` → `{live_sessions: bool, forums: bool, gamification: bool}`; the frontend hides routes for disabled features.
- After every ledger append the repository emits `evidence.recorded {entry_id, learner_id, unit_id, skill_id, category, strength, assistance_level}` on an in-process event bus. Future modules (gamification, notifications) subscribe; none may write to the ledger or to `skill_proficiency`.

---

## 10. Acceptance Criteria

1. `GET /courses` returns the three courses with stage and unit counts matching the roadmaps (Python 14 stages, 78 units).
2. `Unit.activities` always starts with `video`, `explain`.
3. Regenerating `explain` returns `409`; regenerating `predict` returns a different `variant_no`; hidden answers never appear in any response before an attempt.
4. Reset leaves the ledger row count unchanged.
5. An attempt with a client-sent `evidence_strength` field is rejected (`422`).
6. A learner cannot read another learner's ledger by any route.
7. A WebSocket run that waits for input longer than 120 s ends with `timed_out: true`.
8. A Socratic stream never emits a code block, even when the model produces one.
9. `ProficiencyView` decisions match ADR-0016's tables in the progression test suite.
10. Cold Check exercise returns `423` before 24 h after unit completion and `200` after (tested with an injected clock).
11. A stage build returns `423` until every unit in the stage has a passed Cold Check.
12. A skill with two qualifying entries but no passed Cold Check stays `provisional`.
13. All of the above pass with `MOCK_AI=true` and no network.
