# SPEC-15: Stage Build

- **Status:** Accepted for implementation
- **Governed by:** ADR-0016 (Own rule, section 2.6 gate), ADR-0009 (Socratic boundary), ADR-0014 (feature modules), SPEC-12 (sections 3, 4.1, 5 and 9), SPEC-13 (findings, not crashes)
- **Design reference:** Aethelgard LMS design canvas, Stage 0 build artboard
- **Date:** 2026-10-31

---

## 1. Purpose

Each stage ends in one build: a small piece of real work that pulls the stage's units together. It is the only place a learner can show Own (ADR-0016). A build unlocks when its stage review passes, or when every unit has a passed Cold Check and the stage has no review items (SPEC-16 section 3.4).

Out of scope for now: generated briefs (the canvas's Regenerate brief button). A stage has one authored brief. Other stages keep placeholders until their briefs are written.

---

## 2. Where a build lives

```text
curriculum/python/builds/stage-0/
  build.json      served to the learner, except `requirements[].check`
  checks.py       hidden behaviour checks; never served
  solution.py     reference solution; never served; a test proves it passes
```

### 2.1 `build.json`

| Field | Rule |
| :--- | :--- |
| `schema_version` | `1` |
| `course_id`, `stage` | Must match the folder and a real stage |
| `title`, `brief_markdown` | Shown to the learner |
| `kind` | `script` or `mini_project` |
| `status` | `draft` or `approved`. A draft shows a Draft label |
| `sample_run` | Lines of what a correct run looks like |
| `entry` | The `.py` file that runs. Must be in `files` |
| `files` | `[{path, starter: [lines]}]`. Plain file names |
| `requirements` | `[{id, label, unit_id, check}]`, ids unique, at least one `behaviour` |
| `proves` | `[{skill_id, unit_id, label}]`. Each skill must be a target skill of that unit. One evidence entry is written per item |

Unknown fields are refused. A bad build is skipped with a finding and never stops the app.

### 2.2 Requirement checks

Every check is deterministic. All of them live on the server, so the browser never holds a rule.

| `check.kind` | Fields | Met when |
| :--- | :--- | :--- |
| `comment_lines` | `min` | The entry file has at least `min` full comment lines that are not in its starter |
| `input_assignments` | `min` | At least `min` lines of the form `name = input(...)` |
| `fstring_prints` | `min` | At least `min` `print()` calls with an f-string argument |
| `file_contains` | `path`, `any` | The file holds one of the given texts |
| `ownership_note` | `min_chars` | The note, trimmed, has at least `min_chars` characters |
| `behaviour` | `function` | The named function in `checks.py` passes when run against the entry file in the sandbox |

`behaviour` is the only kind that runs code. A check that reads the code reports not met, with a plain detail, if the file has a syntax error.

### 2.3 A behaviour check cannot be skipped

The runner reports success on exit code 0, so `sys.exit(0)` in a script could look like a pass. For each check, the server adds a one-time token that is printed only after the function returns. A behaviour check passes only if the run succeeded and the token is in the output.

Only the entry file is run. This fits a one-file script. A multi-file mini-project needs the runner port to take several files.

---

## 3. API

`exercise_id` of a build is `<course_id>/stage-<n>/build`.

### `GET /api/v1/courses/{course_id}/stages/{stage}/build`

Returns `StageBuild`, built from a list of allowed fields, so hidden checks cannot leak:

```text
StageBuild { exercise_id, course_id, stage, title, kind, status, brief_markdown, sample_run: [str],
             entry, files: [{path, starter: [str]}],
             requirements: [{id, label, unit_id}],
             proves: [{skill_id, unit_id, label}],
             submitted: bool }
```

| Case | Answer |
| :--- | :--- |
| Unknown course or stage | `404` |
| A unit lacks a passed Cold Check, or the stage review is not passed | `423`, and the detail says which |
| Unlocked, and no build is written yet | `404` |

The first successful read records when the learner was served the build. Assistance is counted from then.

### `POST /api/v1/learners/me/courses/{course_id}/stages/{stage}/build:check`

Body `{files: {path: content}, ownership_note?: str, run_checks: bool}`. Same `404` and `423` as above. Writes no evidence.

Returns `{requirements: [{id, met: bool | null, detail?}]}`. With `run_checks: false`, every `behaviour` requirement is `met: null`, which means not checked yet. The page calls this as the learner types. Verify calls it with `run_checks: true`.

### `POST /api/v1/learners/me/courses/{course_id}/stages/{stage}/build:reset`

`204`. Clears the saved files and note, and the served time. Never touches the ledger.

### `POST /api/v1/learners/me/attempts`

With the build's `exercise_id`, `activity: "build"`, `files` and `ownership_note`.

- `423` while locked. Any other `activity` is `422`. Files or a note over the draft limit are `413`.
- Every requirement is checked on the server, whatever the page showed.
- **All met:** `outcome: "passed"`, and one evidence entry per `proves` item.
- **Any unmet:** `outcome: "failed"`, `checks` says which, and **no evidence is written**. An unfinished build is work in progress, so it should not lower a learner's level.

Each entry: category Perform / Solve, activity `Build`, `seed_id` = the build's `exercise_id`, `observed_reasoning` = the ownership note, `cold_check` false. Strength is Strong. `SUPPLIED_REASONING` forces Weak (ADR-0009). Assistance is the highest level logged against the build since it was served. Submitting again adds new entries, and the newest counts (SPEC-12 section 5, evidence is per seed).

Own needs Strong with assistance none, so any AXIS hint keeps the entry from counting for Own. That is ADR-0016 working as written.

### AXIS

A request carrying a build's `exercise_id` always runs in Socratic mode, on `/axis/stream` and `/axis/consult`, whatever mode the client sends.

### Drafts

`GET` and `PUT /learners/me/drafts/{exercise_id}` accept a build's `exercise_id`. The note is saved beside the files under the key `ownership-note.txt`.

---

## 4. Course map

`BuildSummary` gains `authored: bool` and `status`. Authored builds use their real title and kind. Others keep the placeholder.

---

## 5. Curriculum checks

| Code | Severity | Means |
| :--- | :--- | :--- |
| `build-invalid` | error | The build could not be loaded; the message says why |
| `build-unit-unknown` | error | A requirement or `proves` item names a unit that is not in the stage |
| `build-skill-unknown` | error | A `proves` skill is not a target skill of its unit |

An authored build also satisfies `own-needs-stage-build` for its stage.

---

## 6. Extension points (SPEC-12 section 9)

`GET /api/v1/features` returns `{live_sessions: false, forums: false, gamification: false}`.

After each ledger append the repository publishes `evidence.recorded` on an in-process bus (`repo.events`):

```text
{entry_id, learner_id, unit_id, skill_id, category, strength, assistance_level}
```

- The event is a frozen copy. A subscriber gets no repository and no ledger entry object.
- A subscriber that fails is logged. It cannot fail the append or stop other subscribers.
- While subscribers run, `record_evidence` refuses to write, even for a subscriber that kept a reference to the repository.

---

## 7. Frontend

Route `/courses/:courseId/stages/:stage/build`, loaded only when opened. The course map's build tile links here once unlocked.

- **Head:** back arrow to the course map, stage label, kind, Draft label if draft, title, Reset build with a confirm step that says evidence stays.
- **Brief column:** brief, sample run, requirements with a count such as `3 of 7 met`, each with its unit.
- **Workspace:** file tabs, the editor, Run and Verify, the terminal, the ownership note with the PY-0.3 prompt, Submit build. Submit is enabled only when every requirement is met.
- **AXIS column:** the AXIS panel locked to Socratic, then "What this build proves".
- Editing the entry file clears Verify's result, so a stale pass cannot unlock Submit.
- Locked: a plain message naming the units, with the back arrow.
- Phone width: columns stack, with no sideways scroll.

---

## 8. Acceptance

1. A stage returns `423` until its build is open (SPEC-16 section 3.4), on the build, on `build:check` and on attempts.
2. No response holds `check`, `checks.py` or `solution.py` content.
3. Each check kind is met and not met as specified; a syntax error is reported, not raised.
4. `sys.exit(0)` and `os._exit(0)` scripts do not pass a behaviour check.
5. The reference solution meets every requirement. The starter meets none of the code requirements.
6. A passing submit writes one Strong `Build` entry per `proves` item. With no help, it qualifies for Own.
7. A failed submit writes nothing. `SUPPLIED_REASONING` gives Weak.
8. A client cannot send a strength or category, or get AXIS out of Socratic mode on a build.
9. Reset clears the draft and leaves the ledger alone.
10. `GET /features` is all false. A subscriber cannot write to the ledger, and a failing subscriber does not affect the append.
11. Browser: locked, then unlocked; run, verify, submit; in light, dark and phone width.
