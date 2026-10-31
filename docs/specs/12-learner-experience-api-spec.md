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
Unit.activities: ["video", "explain", ...unit.methods without "Explain", "cold_check"]   // video and explain always first, cold_check always last
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
- **Error:** a Cold Check would contain no deterministically graded activity. Predict, Trace, Modify, Debug & Validate and Build are gradable; Evaluate and Direct are gradable when the exercise carries a curator-written fixed answer key (ADR-0016 amendment B, SPEC-13).

Activities and evidence categories:

| Category | Activities |
| --- | --- |
| Explain / Reason | Explain, Predict, Trace |
| Perform / Solve | Specify, Decompose, Modify, Build, Direct |
| Diagnose / Judge / Transfer | Debug & Validate, Evaluate |

---

## 4. Exercises, Regenerate and Reset

| Method | Path | Response |
| --- | --- | --- |
| GET | `/learners/me/units/{unit_id}/activities/{activity}/exercise` | `Exercise` (the learner's current one; authored variant 1 by default) |
| POST | `/learners/me/units/{unit_id}/activities/{activity}/exercises:regenerate` | `Exercise` (a new variant) |
| POST | `/learners/me/units/{unit_id}/reset` | `204` |
| GET / PUT | `/learners/me/units/{unit_id}/state` | `{step, done_steps: [str]}` |
| PUT | `/learners/me/drafts/{exercise_id}` | `{files: {path: content}}` → `204` |

```text
Exercise { exercise_id, unit_id, activity, origin: "authored" | "generated", variant_no,
           prompt_markdown,
           predict?:    { code, options: [{key, text}] },
           trace?:      { code: [str], input: str },
           playground?: { starter, tasks: [{id, label}] } }
```

Rules:
- `explain` cannot be regenerated: `409`.
- `cold_check` can be regenerated only after an attempt on the current variant: `409` otherwise.
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
- `GET .../activities/cold_check/exercise` before `available_at` returns `423 Locked`.
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
                choice?: str,                       // predict
                trace_answers?: [str],              // trace, optional per-line answers
                files?: {path: content},            // playground and build
                ownership_note?: str }              // build only
AttemptResult { outcome: "passed" | "failed" | "recorded",
                feedback, checks?: [{label, passed, detail}],
                reveal?: {correct, why},            // predict, after commit
                evidence_entry_id, unit_decision: Decision }
```

The server derives the evidence entry:

| Activity | Category | Strength (before assistance) |
| --- | --- | --- |
| predict | Explain / Reason | Strong if correct, Weak if not |
| trace | Explain / Reason | Moderate when completed |
| playground | Perform / Solve | Strong if all checks pass first try, Moderate after retries |
| debug & validate | Diagnose / Judge / Transfer | Strong if fixed and verified |
| cold_check | category of the skill probed | Strong if passed, Weak if not (assistance always none) |
| build | Perform / Solve (Own context per ADR-0016) | Strong if all requirements met |

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

---

## 8. AXIS Streaming

`POST /api/v1/axis/stream` → `text/event-stream`. Body: existing `AxisQuery` plus `exercise_id?` and `page: "video" | "explain" | "predict" | "trace" | "playground" | "build" | "progress"`.

```text
event: token     data: {text}
event: citation  data: {concept_id, title, doc_url}
event: done      data: {assistance_level, cited_concepts: [str]}
```

The Socratic guardrail (ADR-0009) runs on the full reply before `done`; in Socratic mode tokens are buffered per sentence so no code fragment is streamed before it is checked. The assistance level is logged against `exercise_id`.

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
