# SPEC-13: Exercise Seed Format

- **Status:** Draft (Step 2: Specification Drafting). Spec only; no loader code yet.
- **Governed by:** ADR-0008 (lesson packages), ADR-0016 (Cold Check, fixed answer keys), ADR-0017 (variants), SPEC-12 section 4 (Exercise API)
- **Date:** 2026-10-31

---

## 1. Purpose

A **seed** is one exercise written by the curator. It is the source for the first variant a learner sees, for Cold Checks, and for the variants generated later (ADR-0017). This spec defines what a seed file holds, so a curator can write seeds before any loader exists.

Out of scope: the Explain step (it stays in `meta.json` as `concept_check` and cannot be regenerated), the variant pool's storage, and the generation pipeline.

---

## 2. Where seeds live

One file per seed, in an `exercises/` folder inside the unit package:

```text
curriculum/python/py-0.1/
  meta.json
  lesson.md
  exercises/
    predict-1.json
    trace-1.json
    cold-predict-1.json
    cold-trace-1.json
```

- **File name:** `<activity>-<n>.json`, or `cold-<activity>-<n>.json` for a Cold Check seed. `<activity>` is the slug in section 3. The name is a convention for people; the fields decide behaviour.
- **Code in JSON:** all code and multi-line text are arrays of strings, one per line. JSON needs no new dependency, and line arrays keep Git diffs readable.

---

## 3. Fields every seed has

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | int | `1` |
| `seed_id` | str | `<UNIT>/<file name without .json>`, e.g. `PY-0.1/predict-1`. Never reuse one: the ledger's `exercise_id` is built from it. |
| `unit_id` | str | Must match the package |
| `activity` | str | An `ActivityType` value, e.g. `Predict`, `Debug & Validate` |
| `skill_id` | str | A target skill of the unit |
| `level` | str | The unit's goal level for that skill |
| `prompt_markdown` | [str] | What the learner reads |
| `cold_check_eligible` | bool | Reserved for the Cold Check (section 5) |
| `cold_check_covers` | [str] | Target skills a pass gives evidence for. Required when eligible, else absent. |
| `curator_approved` | bool | The curator has reviewed this seed. Required for a Cold Check. |
| `template` | object | Optional variant slots (section 6) |

Each seed also has exactly one body block, chosen by activity:

| Activity | Slug | Body block | How it is graded |
| --- | --- | --- | --- |
| Predict | `predict` | `predict` | Answer key |
| Trace | `trace` | `trace` | Expected output |
| Modify | `modify` | `playground` | Hidden pytest checks |
| Build | `build` | `playground` | Hidden pytest checks |
| Debug & Validate | `debug-validate` | `debug` | Hidden pytest checks |
| Evaluate | `evaluate` | `choice` | Answer key |
| Direct | `direct` | `choice` | Answer key |
| Specify | `specify` | `choice` | Answer key; not Cold Check eligible |
| Decompose | `decompose` | `choice` | Answer key; not Cold Check eligible |

SPEC-12's `playground` is the screen, not an activity: Modify and Build both use it. Specify and Decompose are free-form work in the Learning Method. Until their grading is decided (section 9, question 2) their seeds use a fixed answer key and stay out of the Cold Check.

---

## 4. Body blocks

Fields marked **hidden** never leave the server before an attempt (SPEC-12 section 4). `why` and `answer_key` may be shown in `reveal` after the learner commits.

### `predict`
| Field | Type | Meaning |
| --- | --- | --- |
| `code` | [str] | The program shown |
| `stdin` | str | Input the program receives; the prompt must state it |
| `options` | [{key, text}] | 2 to 5 choices |
| `answer_key` | str | **Hidden.** The correct `key` |
| `why` | [str] | **Hidden.** Shown after the attempt |

### `trace`
| Field | Type | Meaning |
| --- | --- | --- |
| `code` | [str] | The program shown |
| `input` | str | Input the program receives; empty string for none |
| `expected_output` | [str] | **Hidden.** Output lines |
| `line_states` | [{line, state}] | **Hidden, optional.** Variable values after a line, for `trace_answers` |

### `playground` (Modify, Build)
| Field | Type | Meaning |
| --- | --- | --- |
| `starter` | [str] | Code the learner begins with |
| `tasks` | [{id, label}] | The visible checklist |
| `reference_solution` | [str] | **Hidden.** Must pass `hidden_checks` |
| `hidden_checks` | [str] | **Hidden.** pytest code, in the style of a package's `test_solution.py` |
| `wrong_solution` | [str] | **Hidden.** A plausible wrong answer that must fail the checks (ADR-0017) |

### `debug` (Debug & Validate)
| Field | Type | Meaning |
| --- | --- | --- |
| `broken_code` | [str] | The code with the fault |
| `stdin` | str | Optional input for a run |
| `reference_solution` | [str] | **Hidden.** Must pass `hidden_checks` |
| `hidden_checks` | [str] | **Hidden.** Must fail on `broken_code` |
| `wrong_solution` | [str] | **Hidden.** A plausible wrong fix that must fail the checks |

### `choice` (Evaluate, Direct, Specify, Decompose)
| Field | Type | Meaning |
| --- | --- | --- |
| `material` | [str] | Optional output, spec, prompt or code being judged |
| `options` | [{key, text}] | 2 to 5 choices |
| `answer_key` | str | **Hidden.** The correct `key`, written by the curator (ADR-0016 amendment B) |
| `why` | [str] | **Hidden.** Shown after the attempt |

No AI grades a seed. If a question needs judgement to mark, it does not belong in `choice`.

---

## 5. Cold Check seeds

A seed may set `cold_check_eligible: true` only if:

1. `curator_approved` is `true`.
2. Its activity is Predict, Trace, Modify, Build, Debug & Validate, Evaluate or Direct.
3. `cold_check_covers` lists only the unit's target skills, and includes `skill_id`.

Rules for the unit:

- **Reserved:** an eligible seed is served only in the Cold Check, never in the normal activity step, so it stays unseen (ADR-0016 section 2.6).
- **Coverage:** together, the unit's eligible seeds must cover every target skill.
- **Evidence:** a passed seed records one entry per skill in `cold_check_covers`, with `cold_check: true`. A failed seed records a Weak entry for the same skills.

---

## 6. Variant template slots (ADR-0017)

`template` tells the offline pipeline which surface details may change. Activity, skill and level never change.

```json
"template": {
  "slots": {
    "person": {"kind": "person_name", "values": ["Amara Okafor", "Kofi Mensah", "Lina Haddad"]}
  }
}
```

- A slot is written `{{person}}` in any text or code field, and `values` lists safe replacements. `kind` names what the slot is, so the pipeline can add more of the same kind. Slots are the only part it may change.
- `answer_key` never changes, so options must be written so the same key stays correct for every value.
- A template seed cannot contain a literal `{{` in its code, because that marks a slot.
- Without `template`, the seed is served as written and the pipeline writes variants from it freely, within ADR-0017's checks.

---

## 7. Mapping to the SPEC-12 Exercise

| Exercise field | From |
| --- | --- |
| `exercise_id` | `<seed_id>/v<variant_no>`; the seed itself is `v1` |
| `origin`, `variant_no` | `authored`, `1` for a seed |
| `prompt_markdown` | Lines joined with newlines |
| `predict` | `code`, `options` |
| `trace` | `code`, `input` |
| `playground` | `starter`, `tasks`; a `debug` block serves `broken_code` as `starter` |
| Fixed-answer choice | Needs a new optional `choice: {material, options}` on Exercise in SPEC-12 |

---

## 8. Validation rules

The loader, when it is built, reports these. Each one is an error for that seed unless marked.

1. The file parses, has the fields in section 3, and has exactly the body block its activity needs.
2. `seed_id` matches its file and is unique in the unit. `unit_id` matches the package.
3. `activity` is in the unit's Methods. `skill_id` is a target skill, and `level` is its goal level.
4. `answer_key` matches an option's `key`.
5. Sandbox checks: Predict's `answer_key` text and Trace's `expected_output` equal the real output. `reference_solution` passes. `wrong_solution` fails. `broken_code` fails.
6. Section 5's rules hold for eligible seeds.
7. Every slot used is defined, and every slot defined is used.
8. **Warning:** an activity of the unit, other than Explain, has no seed.
9. **Warning:** the unit has no Cold Check seed, or its seeds do not cover every target skill.

---

## 9. Open questions for the owner

1. **Cold Check evidence for skills with no gradable main activity.** 190 skill targets have Explain, Specify or Decompose as their main activity (84 and 106). No machine-graded seed can use that activity, and ADR-0016's amendment says a Cold Check entry records the activity taken. So at Apply or Adapt its entry does not qualify, and the skill can never become *supported*. Proposed fix: a passed Cold Check entry qualifies for its covered skills at the unit's target level, as ADR-0016 section 2.6 already says ("at the unit's target level"). Until this is decided, `cold_check_covers` carries these skills but the estimator will not count them.
2. **Grading Specify and Decompose.** They are free-form in the Learning Method. This spec gives them fixed answer keys and keeps them out of the Cold Check.
3. **Two units still have no gradable activity:** BE-7.1 and AI-0.1 (curriculum check `cold-check-not-graded`).
4. **PY-0.1's existing `starter.py` and `test_solution.py`** are a playground, but the unit's Methods (Explain, Predict, Trace) have no Modify or Build. They stay as they are; this spec does not move them.

---

## 10. Worked example: PY-0.1

PY-0.1 targets CO-1, CO-2 and CO-6, all at Understand. Its activities are Explain, Predict and Trace. Explain stays in `meta.json`, so the seeds are one Predict and one Trace for the normal steps, plus two reserved for the Cold Check. Together those two cover all three skills.

### `exercises/predict-1.json`

```json
{
  "schema_version": 1,
  "seed_id": "PY-0.1/predict-1",
  "unit_id": "PY-0.1",
  "activity": "Predict",
  "skill_id": "CO-1",
  "level": "Understand",
  "prompt_markdown": [
    "The intake desk runs this program, and the applicant types `{{person}}`.",
    "",
    "Commit to your answer before you run anything: what appears on the terminal?"
  ],
  "cold_check_eligible": false,
  "curator_approved": true,
  "template": {
    "slots": {
      "person": {"kind": "person_name", "values": ["Amara Okafor", "Kofi Mensah", "Lina Haddad"]}
    }
  },
  "predict": {
    "code": [
      "print(\"Desk open\")",
      "applicant = input()",
      "print(\"Applicant:\", applicant)",
      "print()",
      "print(f\"Record: {applicant}\")"
    ],
    "stdin": "{{person}}",
    "options": [
      {"key": "A", "text": "Desk open\nApplicant: {{person}}\n\nRecord: {{person}}"},
      {"key": "B", "text": "Desk open\nApplicant: {{person}}\nRecord: {{person}}"},
      {"key": "C", "text": "Desk open\nApplicant: applicant\n\nRecord: {applicant}"},
      {"key": "D", "text": "{{person}}\nDesk open\nApplicant: {{person}}\n\nRecord: {{person}}"}
    ],
    "answer_key": "A",
    "why": [
      "Statements run from top to bottom, so `Desk open` comes first.",
      "`input()` returns the text and `applicant` stores it, so both later lines show the value.",
      "`print()` with no arguments writes one blank line."
    ]
  }
}
```

### `exercises/trace-1.json`

```json
{
  "schema_version": 1,
  "seed_id": "PY-0.1/trace-1",
  "unit_id": "PY-0.1",
  "activity": "Trace",
  "skill_id": "CO-2",
  "level": "Understand",
  "prompt_markdown": [
    "Follow the applicant's status line by line.",
    "",
    "Write the value of `status` after each line, then what the terminal shows."
  ],
  "cold_check_eligible": false,
  "curator_approved": true,
  "trace": {
    "code": [
      "status = \"waiting\"",
      "print(status)",
      "status = \"checked in\"",
      "print(status)"
    ],
    "input": "",
    "expected_output": ["waiting", "checked in"],
    "line_states": [
      {"line": 1, "state": {"status": "waiting"}},
      {"line": 3, "state": {"status": "checked in"}}
    ]
  }
}
```

### `exercises/cold-predict-1.json`

This seed also covers CO-6: choosing correctly depends on the mental model that `input()` returns a value and statements run in order.

```json
{
  "schema_version": 1,
  "seed_id": "PY-0.1/cold-predict-1",
  "unit_id": "PY-0.1",
  "activity": "Predict",
  "skill_id": "CO-1",
  "level": "Understand",
  "prompt_markdown": [
    "A visitor types `Kofi Mensah` at the queue desk.",
    "",
    "What appears on the terminal?"
  ],
  "cold_check_eligible": true,
  "cold_check_covers": ["CO-1", "CO-6"],
  "curator_approved": true,
  "predict": {
    "code": [
      "print(\"Queue open\")",
      "visitor = input()",
      "print()",
      "print(\"Next:\", visitor)"
    ],
    "stdin": "Kofi Mensah",
    "options": [
      {"key": "A", "text": "Queue open\nNext: Kofi Mensah"},
      {"key": "B", "text": "Queue open\n\nNext: Kofi Mensah"},
      {"key": "C", "text": "Queue open\n\nNext: visitor"},
      {"key": "D", "text": "Next: Kofi Mensah\n\nQueue open"}
    ],
    "answer_key": "B",
    "why": [
      "The lines run in order, so the blank line from `print()` comes before `Next:`.",
      "`visitor` holds the text `input()` returned."
    ]
  }
}
```

### `exercises/cold-trace-1.json`

```json
{
  "schema_version": 1,
  "seed_id": "PY-0.1/cold-trace-1",
  "unit_id": "PY-0.1",
  "activity": "Trace",
  "skill_id": "CO-2",
  "level": "Understand",
  "prompt_markdown": [
    "Two names point at a desk label.",
    "",
    "Follow the values, then write what the terminal shows."
  ],
  "cold_check_eligible": true,
  "cold_check_covers": ["CO-2"],
  "curator_approved": true,
  "trace": {
    "code": [
      "desk = \"A\"",
      "next_desk = desk",
      "desk = \"B\"",
      "print(desk, next_desk)"
    ],
    "input": "",
    "expected_output": ["B A"],
    "line_states": [
      {"line": 2, "state": {"desk": "A", "next_desk": "A"}},
      {"line": 3, "state": {"desk": "B", "next_desk": "A"}}
    ]
  }
}
```

---

## 11. Acceptance Criteria

1. Every JSON block in section 10 parses and meets section 8's rules.
2. A curator can write a seed for any activity using this document alone.
3. No field marked hidden appears in an `Exercise` response before an attempt.
