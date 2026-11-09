# SPEC-13: Exercise Seed Format

- **Status:** Accepted (2026-11-09, by the owner, as built). Was a draft.
- **Governed by:** ADR-0008 (lesson packages), ADR-0016 (Cold Check and its 2026-10-31 amendment), ADR-0017 (variants), SPEC-12 section 4 (Exercise API)
- **Date:** 2026-10-31

---

## 1. Purpose

A **seed** is one exercise written by the curator. It is the source for the first variant a learner sees, for Cold Checks, and for the variants generated later (ADR-0017). This spec defines what a seed file holds and how each item type is graded, so a curator can write seeds before any loader exists.

**Every seed is graded deterministically. No AI grades a seed.** If a question needs judgement to mark, it does not belong in a seed.

Out of scope: the free-text CO-6 concept check (it stays in `meta.json` as `concept_check`, stays Solid/Shaky practice as today, and cannot be regenerated), the variant pool's storage, and the generation pipeline.

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
    cold-explain-1.json
```

- **File name:** `<activity>-<n>.json`, or `cold-<activity>-<n>.json` for a Cold Check seed. `<activity>` is the slug in section 3. The name is a convention for people; the fields decide behaviour.
- **Code in JSON:** all code and multi-line text are arrays of strings, one per line. JSON needs no new dependency, and line arrays keep Git diffs readable.

---

## 3. Fields every seed has

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | int | `2` |
| `seed_id` | str | `<UNIT>/<file name without .json>`, e.g. `PY-0.1/predict-1`. Never reuse one: the ledger's `exercise_id` is built from it. |
| `unit_id` | str | Must match the package |
| `activity` | str | An `ActivityType` value, e.g. `Predict`, `Debug & Validate` |
| `skill_id` | str | The one target skill this seed tests |
| `level` | str | The unit's goal level for that skill |
| `topic` | str | One topic from the unit's roadmap **Topics** line, as written without its `(new)` or `(awareness)` mark; case does not matter. Public. Added 2026-11-04 (see "Curriculum guards" in section 4). |
| `prompt_markdown` | [str] | What the learner reads |
| `cold_check_eligible` | bool | Reserved for the Cold Check (section 5) |
| `curator_approved` | bool | The curator has reviewed this seed. Required for a Cold Check. |
| `hint` | str, optional | One sentence, 1 to 300 characters, naming the idea to revisit after a failed Cold Check item. Never the answer. Not sent with the item (ADR-0022 section 2.5). |
| `hint_approved` | bool, optional | The curator has approved the hint. An unapproved hint is never shown. Default false. |
| `template` | object | Optional variant slots (section 6) |

Each seed also has exactly one body block, named by its item type. The activity decides which item types are allowed:

| Activity | Slug | Item types (body block) | Graded by |
| --- | --- | --- | --- |
| Predict | `predict` | `predict` | Answer key |
| Trace | `trace` | `trace` | Expected output |
| Modify | `modify` | `playground` | Hidden tests |
| Build | `build` | `playground` | Hidden tests |
| Debug & Validate | `debug-validate` | `debug`, `debug_locate` | Hidden tests; answer key |
| Evaluate | `evaluate` | `choice` | Answer key |
| Direct | `direct` | `choice` | Answer key |
| Specify | `specify` | `specify_by_tests`, `specify_contract` | Mutants; answer key |
| Decompose | `decompose` | `decompose_plan`, `decompose_code` | Answer key; tests and structure |
| Explain | `explain` | `explain_spot_flaw`, `explain_model_choice` | Answer key |

SPEC-12's `playground` is the screen, not an activity: Modify and Build both use it. Units without Modify or Build still show an ungraded playground fed by `starter.py` and `test_solution.py` (SPEC-12 section 3.2). That practice needs no seed and writes no evidence.

---

## 4. Body blocks and grading

**Where hidden fields are stored (2026-11-04, ADR-0021 amendment).** Fields marked hidden, plus a trace item's `line_states`, are not in the public seed file. They live in the private answers folder at the same relative path, as `{"seed_id": ..., "<item_type>": {hidden fields}}`, and the loader joins the two. A seed with no private half is skipped (`seed-answers-missing`); a public file holding a hidden field is skipped (`seed-answers-public`).

Fields marked **hidden** never leave the server before an attempt (SPEC-12 section 4). `why` and `answer_key` may be shown in `reveal` after the learner commits. Strength follows SPEC-12 section 5: Strong if the item passes first try, Moderate after retries, Weak if not. A Cold Check has one try.

### `predict`
| Field | Type | Meaning |
| --- | --- | --- |
| `code` | [str] | The program shown |
| `stdin` | str | Input the program receives; the prompt must state it |
| `options` | [{key, text}] | 2 to 5 choices |
| `answer_key` | str | **Hidden.** The correct `key` |
| `why` | [str] | **Hidden.** Shown after the attempt |

**Pass:** the chosen key equals `answer_key`.

### `trace`
| Field | Type | Meaning |
| --- | --- | --- |
| `code` | [str] | The program shown |
| `input` | str | Input the program receives; empty string for none |
| `expected_output` | [str] | **Hidden.** Output lines |
| `line_states` | [{line, state}] | **Hidden, optional.** Variable values after a line, for `trace_answers` |

**Pass:** the learner's output lines equal `expected_output`, after trimming each line.

### `playground` (Modify, Build)
| Field | Type | Meaning |
| --- | --- | --- |
| `starter` | [str] | Code the learner begins with |
| `tasks` | [{id, label}] | The visible checklist |
| `reference_solution` | [str] | **Hidden.** Must pass `hidden_checks` |
| `hidden_checks` | [str] | **Hidden.** pytest code, in the style of a package's `test_solution.py` |
| `wrong_solution` | [str] | **Hidden.** A plausible wrong answer that must fail the checks (ADR-0017) |
| `make` | bool, optional | This item is the unit's **Make step** (Learning Method v2 Amendment A1.3). Default false. Visible. |

**Pass:** every hidden check passes.

#### Make items (Amendment A1.3, added 2026-11-04)

A Make step is a Build item in which the learner writes a small program from a blank file. It is a `playground` item with `make: true`, graded like any Build: every hidden check passes.

1. `make: true` only on a Build seed of a unit whose roadmap outcome names a Make step (`Unit.make`). Otherwise **Error** `make-seed-unexpected`.
2. The `starter` of a Make item holds no code: only blank lines and `#` comments. Otherwise **Error** `make-starter-not-blank`.
3. A Make item's `skill_id` is the skill the Make step credits (`Unit.make.skill_id`). Otherwise **Error** `make-seed-wrong-skill` (this rule already covers every Build seed of a Make unit).
4. A unit with a Make step and no approved Make item gets **Warning** `make-seed-missing`.

The learner sees the unit's Make task (`Unit.make.task`, the approved roadmap wording), the visible task list, a blank editor, **Run** with typed input in the sandbox, and **Submit**. Submit is the check: the hidden checks run and the result shows which ones passed. A learner may submit again; the newest result counts, and a pass after a retry is Moderate (SPEC-12 section 5). There is no separate check that runs the hidden tests without recording, because unlimited free checks would let a learner probe the tests instead of reasoning.

#### Curriculum guards (Amendment A1, added 2026-11-04)

Reported by the curriculum check; none stops the app.

| Code | Severity | Rule |
| --- | --- | --- |
| `skill-enters-above-apply` | Error | A1.1: in path order, the first unit that targets a skill sets it to Understand or Apply. |
| `skill-skips-a-rung` | Error | A1.2: a skill rises at most one level from the last unit that targeted it, in path order. Going down is allowed. |
| `practice-volume-low` | Warning | A1.6: a unit with at least one seed has fewer approved seeds than 15 (Python Stages 0 to 5) or 8 (elsewhere). Regenerated variants are not counted. |
| `make-volume-low` | Warning | A1.6: a Make unit in Python Stages 0 to 5 has fewer than 3 approved Make items. |
| `seed-topic-missing` | Error | A seed names no `topic`. |
| `seed-topic-unknown` | Error | The `topic` is not on the unit's Topics line. |
| `cold-check-awareness-topic` | Error | A1.4: a Cold Check seed on an awareness topic. A topic is awareness when marked `(awareness)` or named "... awareness". |
| `exercise-awareness-topic` | Warning | A1.4: a practice seed on an awareness topic; it must not be needed to pass. |

### `debug` (Debug & Validate)
| Field | Type | Meaning |
| --- | --- | --- |
| `broken_code` | [str] | The code with the fault |
| `stdin` | str | Optional input for a run |
| `reference_solution` | [str] | **Hidden.** Must pass `hidden_checks` |
| `hidden_checks` | [str] | **Hidden.** Must fail on `broken_code` |
| `wrong_solution` | [str] | **Hidden.** A plausible wrong fix that must fail the checks |

**Pass:** every hidden check passes.

### `debug_locate` (Debug & Validate)
The learner reads a failing program, then picks where it fails and what kind of error it is. This grades reading an error, not fixing it.

| Field | Type | Meaning |
| --- | --- | --- |
| `broken_code` | [str] | The failing program, shown with line numbers |
| `stdin` | str | Input it receives; empty string for none |
| `error_types` | [{key, text}] | 2 to 5 error types to choose from |
| `answer_key` | {line, error_type} | **Hidden.** The line number, and the `key` of the error type |
| `why` | [str] | **Hidden.** Shown after the attempt |

**Pass:** both the line and the error type are right. **Feedback:** whether the attempt passed, with no detail on which part was wrong.

### `choice` (Evaluate, Direct)
| Field | Type | Meaning |
| --- | --- | --- |
| `material` | [str] | Optional output, spec, prompt or code being judged |
| `options` | [{key, text}] | 2 to 5 choices |
| `answer_key` | str | **Hidden.** The correct `key`, written by the curator (ADR-0016 amendment B) |
| `why` | [str] | **Hidden.** Shown after the attempt |

**Pass:** the chosen key equals `answer_key`.

### `specify_by_tests` (Specify)
The learner writes pytest tests for a described function. A spec is good when it accepts the right behaviour and rejects wrong behaviour, so the tests are run against hidden programs.

| Field | Type | Meaning |
| --- | --- | --- |
| `function_name` | str | The function under test; the learner's tests call it by this name |
| `signature` | str | Shown to the learner, e.g. `desk_for(age: int) -> str` |
| `starter_tests` | [str] | Tests the learner begins with |
| `reference` | [str] | **Hidden.** The one correct implementation |
| `mutants` | [{id, code}] | **Hidden.** 2 to 8 subtly wrong implementations |
| `sample_tests` | [str] | **Hidden.** The curator's own passing tests; prove the item can be solved |

**Pass:** all the learner's tests pass on `reference`, and every mutant is killed (at least one test fails on it).

Grading, in order:
1. **Static gate.** The learner's file is parsed, never executed, and refused if it does anything but test. Allowed: `import pytest`, `from solution import <function_name>`, and top-level `def test_*` functions containing `assert`, `pytest.raises` and calls to the function. Refused: any other import, `open`, `exec`, `eval`, `compile`, `__import__`, `getattr`, `globals`, and any double-underscore name. At least one `assert` or `pytest.raises` is required. A syntax error is refused.
2. **Reference run.** Any failing test rejects the attempt as a wrong spec: the tests contradict correct behaviour, so no mutant score is given.
3. **Mutant runs.** One run per mutant. A mutant is killed if any test fails, or the run errors or times out.

**Feedback:** only `mutants killed / N`, as a partial score. Never which mutant survived or what it does, because that would give the answer away.

**Sandbox:** this runs learner code and hidden code, so it uses the sandbox runner with the same limits as any run (SPEC-12 section 7: 5 s CPU, 120 s wall clock, 64 KB output, no network), per run. One attempt is up to 9 runs, which is why `mutants` stops at 8. Each run sees the program under test as `solution.py`, so a test cannot tell which one it has by name.

### `specify_contract` (Specify)
| Field | Type | Meaning |
| --- | --- | --- |
| `material` | [str] | The requirement being specified |
| `fields` | [{id, label, kind, options}] | `kind` is `single` or `multi`. Input types, output type, and edge cases chosen from a list with distractors. |
| `answer_key` | {field id: key or [keys]} | **Hidden.** |
| `why` | [str] | **Hidden.** Shown after the attempt |

**Pass:** every field is exact. A `multi` field must match the full set, with no extra picks. **Feedback:** `fields correct / fields`.

### `decompose_plan` (Decompose)
| Field | Type | Meaning |
| --- | --- | --- |
| `material` | [str] | The requirement |
| `steps` | [{id, text}] | Needed sub-tasks and distractors, served shuffled |
| `needed` | [str] | **Hidden.** Ids of the steps that belong |
| `order_constraints` | [[before, after]] | **Hidden.** Pairs of needed ids |
| `why` | [str] | **Hidden.** Shown after the attempt |

The learner chooses steps, then orders them (Parsons style).

**Pass:** the chosen set equals `needed`, and for every pair `before` comes earlier than `after`. Any order meeting the constraints passes, so independent steps can go either way. **Feedback:** whether the choice is right, then whether the order is right. No per-step detail.

### `decompose_code` (Decompose)
The learner splits a solution into functions.

| Field | Type | Meaning |
| --- | --- | --- |
| `entry_function` | str | The function the hidden tests call |
| `starter` | [str] | Code the learner begins with |
| `structure` | {min_helpers, max_lines_per_function} | Structure the code must have |
| `reference_solution` | [str] | **Hidden.** Must pass both checks |
| `hidden_checks` | [str] | **Hidden.** Behaviour tests, run in the sandbox |
| `wrong_solution` | [str] | **Hidden.** Must pass `hidden_checks` and fail the structure check, proving the structure check does real work |

**Pass:** every behaviour test passes, and the structure check passes.

The structure check parses the learner's code with Python's `ast` module and never executes it. A helper is any top-level `def` other than `entry_function`. It requires:
1. `entry_function` exists at the top level.
2. At least `min_helpers` helpers exist.
3. Every helper is called directly in the body of `entry_function`.
4. Every top-level function, from its `def` line to its last line, is at most `max_lines_per_function` lines.

**Feedback:** behaviour tests passed, and which structure rule failed. These rules are visible to the learner, so naming one gives nothing away.

### `explain_spot_flaw` (Explain)
| Field | Type | Meaning |
| --- | --- | --- |
| `sentences` | [{key, text}] | An explanation, one sentence per entry, with one flawed |
| `answer_key` | str | **Hidden.** The flawed sentence's `key` |
| `why` | [str] | **Hidden.** Shown after the attempt |

**Pass:** the chosen key equals `answer_key`.

### `explain_model_choice` (Explain)
| Field | Type | Meaning |
| --- | --- | --- |
| `material` | [str] | Optional code or situation |
| `options` | [{key, text}] | 2 to 5 mental models |
| `answer_key` | str | **Hidden.** The correct model |
| `why` | [str] | **Hidden.** Shown after the attempt |

**Pass:** the chosen key equals `answer_key`.

`explain_*` seeds must set `cold_check_eligible: true`: the Explain step has no regenerated exercise (SPEC-12 section 4), so they are served only in the Cold Check.

---

## 5. Cold Check seeds

All item types in section 4 are Cold Check eligible. A seed may be drafted with `cold_check_eligible: true` and `curator_approved: false`, but the Cold Check serves a seed only when both are `true`.

Rules for the unit (ADR-0016 amendment C):

- **One seed, one skill:** a pass counts only for the seed's `skill_id`.
- **Its own activity:** the seed's `activity` must be that skill's main activity in Learning Method v2.
- **Coverage:** the unit needs an eligible seed for each target skill. A skill with no seed stays provisional.
- **Reserved:** an eligible seed is served only in the Cold Check, never in the normal activity step, so it stays unseen (ADR-0016 section 2.6).
- **Evidence:** a passed seed records one entry with `cold_check: true`, the seed's `activity`, and Strong strength. A failed seed records a Weak entry.

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
| `playground` | `starter`, `tasks`; a `debug` block serves `broken_code` as `starter`; `decompose_code` serves `starter` and `structure` |

SPEC-12 section 4 lists the Exercise blocks served for every item type. It still needs these additions when attempts are built (step 5):
- **Attempt:** optional `tests` (`specify_by_tests`), `fields` (`specify_contract`) and `plan` (`decompose_plan`, ordered step ids).
- **AttemptResult:** optional `score: {passed, total}` for the partial feedback in section 4.

---

## 8. Validation rules

The loader, when it is built, reports these. Each one is an error for that seed unless marked.

1. The file parses, has the fields in section 3, and has exactly one body block allowed for its activity.
2. `seed_id` matches its file and is unique in the unit. `unit_id` matches the package.
3. `activity` is in the unit's Methods. `skill_id` is a target skill, and `level` is its goal level.
4. Every `answer_key` value matches a real option, and `needed` and `order_constraints` use real step ids with no cycle.
5. Sandbox checks: Predict's `answer_key` text and Trace's `expected_output` equal the real output. `reference_solution` passes. `wrong_solution` fails. `broken_code` fails. For `debug_locate`, running `broken_code` raises exactly the keyed error type at the keyed line.
6. `specify_by_tests`: `sample_tests` pass the static gate, pass on `reference`, and kill every mutant. Mutants number 2 to 8.
7. `decompose_code`: `reference_solution` passes both checks. `wrong_solution` passes `hidden_checks` and fails the structure check.
8. Section 5's rules hold for eligible seeds.
9. Every slot used is defined, and every slot defined is used.
10. **Warning:** an activity of the unit, other than Explain, has no seed.
11. **Warning:** a target skill has no Cold Check seed.

Rules 3, 8 and 11 run in the curriculum check. A bad file is reported as `seed-invalid` and skipped; it never stops the app. Rule 5's sandbox checks run in the test suite.

---

## 9. Open questions for the owner

1. **Own-level targets on Specify, Decompose and Explain skills.** Own still needs a stage build (ADR-0016), so a Cold Check item alone does not reach Own.

---

## 10. Worked example: PY-0.1

PY-0.1 targets CO-1, CO-2 and CO-6, all at Understand. Its activities are Explain, Predict and Trace. The free-text concept check stays in `meta.json`. The seeds are one Predict and one Trace for the normal steps, plus one Cold Check seed per target skill, each through that skill's main activity.

### `exercises/predict-1.json`

```json
{
  "schema_version": 2,
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
  "schema_version": 2,
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

```json
{
  "schema_version": 2,
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
  "schema_version": 2,
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

### `exercises/cold-explain-1.json` (`explain_spot_flaw`)

```json
{
  "schema_version": 2,
  "seed_id": "PY-0.1/cold-explain-1",
  "unit_id": "PY-0.1",
  "activity": "Explain",
  "skill_id": "CO-6",
  "level": "Understand",
  "prompt_markdown": [
    "A new colleague explains how the intake script runs.",
    "",
    "One sentence is wrong. Which one?"
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "explain_spot_flaw": {
    "sentences": [
      {"key": "A", "text": "Python runs the statements from top to bottom."},
      {"key": "B", "text": "`input()` waits for the person, then returns what they typed as text."},
      {"key": "C", "text": "A variable stores the code that made its value, and that code runs again each time the variable is used."},
      {"key": "D", "text": "`print()` with no arguments writes a blank line."}
    ],
    "answer_key": "C",
    "why": [
      "A variable holds the value that was produced. Using it does not run `input()` again."
    ]
  }
}
```

---

## 11. Worked examples: the other item types

### `specify_by_tests`: PY-2.1, SP-1 at Adapt

```json
{
  "schema_version": 2,
  "seed_id": "PY-2.1/cold-specify-1",
  "unit_id": "PY-2.1",
  "activity": "Specify",
  "skill_id": "SP-1",
  "level": "Adapt",
  "prompt_markdown": [
    "The intake desk sends each visitor to a desk by age: under 18 to `youth`, 18 to 64 to `main`, and 65 or older to `senior`. A negative age is `invalid`.",
    "",
    "Write tests that pin this rule down. Your tests must pass on a correct program and catch wrong ones."
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "specify_by_tests": {
    "function_name": "desk_for",
    "signature": "desk_for(age: int) -> str",
    "starter_tests": [
      "from solution import desk_for",
      "",
      "",
      "def test_adult_goes_to_main():",
      "    assert desk_for(30) == 'main'"
    ],
    "reference": [
      "def desk_for(age):",
      "    if age < 0:",
      "        return 'invalid'",
      "    if age < 18:",
      "        return 'youth'",
      "    if age < 65:",
      "        return 'main'",
      "    return 'senior'"
    ],
    "mutants": [
      {"id": "m1", "code": [
        "def desk_for(age):",
        "    if age < 0:",
        "        return 'invalid'",
        "    if age <= 18:",
        "        return 'youth'",
        "    if age < 65:",
        "        return 'main'",
        "    return 'senior'"
      ]},
      {"id": "m2", "code": [
        "def desk_for(age):",
        "    if age < 0:",
        "        return 'invalid'",
        "    if age < 18:",
        "        return 'youth'",
        "    if age <= 65:",
        "        return 'main'",
        "    return 'senior'"
      ]},
      {"id": "m3", "code": [
        "def desk_for(age):",
        "    if age < 18:",
        "        return 'youth'",
        "    if age < 65:",
        "        return 'main'",
        "    return 'senior'"
      ]},
      {"id": "m4", "code": [
        "def desk_for(age):",
        "    if age <= 0:",
        "        return 'invalid'",
        "    if age < 18:",
        "        return 'youth'",
        "    if age < 65:",
        "        return 'main'",
        "    return 'senior'"
      ]}
    ],
    "sample_tests": [
      "from solution import desk_for",
      "",
      "",
      "def test_boundaries():",
      "    assert desk_for(-1) == 'invalid'",
      "    assert desk_for(0) == 'youth'",
      "    assert desk_for(17) == 'youth'",
      "    assert desk_for(18) == 'main'",
      "    assert desk_for(64) == 'main'",
      "    assert desk_for(65) == 'senior'"
    ]
  }
}
```

### `specify_contract`: PY-3.4, SP-2 at Adapt

```json
{
  "schema_version": 2,
  "seed_id": "PY-3.4/cold-specify-1",
  "unit_id": "PY-3.4",
  "activity": "Specify",
  "skill_id": "SP-2",
  "level": "Adapt",
  "prompt_markdown": [
    "Write the contract for `parse_age` before anyone codes it."
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "specify_contract": {
    "material": [
      "The form gives us the age exactly as the visitor typed it.",
      "We need a whole number we can compare, or nothing if the entry cannot be used."
    ],
    "fields": [
      {"id": "input_type", "label": "Input type", "kind": "single", "options": [
        {"key": "str", "text": "str"},
        {"key": "int", "text": "int"},
        {"key": "list", "text": "list[str]"}
      ]},
      {"id": "output_type", "label": "Output type", "kind": "single", "options": [
        {"key": "int", "text": "int"},
        {"key": "int_none", "text": "int | None"},
        {"key": "str", "text": "str"}
      ]},
      {"id": "edge_cases", "label": "Edge cases the contract must state", "kind": "multi", "options": [
        {"key": "empty", "text": "Empty input"},
        {"key": "letters", "text": "Letters instead of digits"},
        {"key": "spaces", "text": "Spaces around the number"},
        {"key": "timeout", "text": "A network timeout"},
        {"key": "unicode_file", "text": "A file with the wrong encoding"}
      ]}
    ],
    "answer_key": {
      "input_type": "str",
      "output_type": "int_none",
      "edge_cases": ["empty", "letters", "spaces"]
    },
    "why": [
      "Typed input is text, and \"nothing\" means the output can be None.",
      "No network or file is involved, so those are not this function's cases."
    ]
  }
}
```

### `decompose_plan`: PY-3.5, SP-3 at Adapt

```json
{
  "schema_version": 2,
  "seed_id": "PY-3.5/cold-decompose-1",
  "unit_id": "PY-3.5",
  "activity": "Decompose",
  "skill_id": "SP-3",
  "level": "Adapt",
  "prompt_markdown": [
    "Choose the sub-tasks this requirement needs, then put them in a working order."
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "decompose_plan": {
    "material": [
      "At the end of the day, read the visitor records and print a report with one line per valid visitor, then the total."
    ],
    "steps": [
      {"id": "read", "text": "Read the visitor records"},
      {"id": "validate", "text": "Drop records with no name"},
      {"id": "format", "text": "Format one line per valid visitor"},
      {"id": "count", "text": "Count the valid visitors"},
      {"id": "print", "text": "Print the lines and the total"},
      {"id": "email", "text": "Email the report to every visitor"},
      {"id": "login", "text": "Add a login page for staff"}
    ],
    "needed": ["read", "validate", "format", "count", "print"],
    "order_constraints": [
      ["read", "validate"],
      ["validate", "format"],
      ["validate", "count"],
      ["format", "print"],
      ["count", "print"]
    ],
    "why": [
      "Formatting and counting both need the valid records, and neither needs the other, so they can go in either order.",
      "Email and login were never asked for."
    ]
  }
}
```

### `decompose_code`: PY-3.5, SP-3 at Adapt

```json
{
  "schema_version": 2,
  "seed_id": "PY-3.5/cold-decompose-2",
  "unit_id": "PY-3.5",
  "activity": "Decompose",
  "skill_id": "SP-3",
  "level": "Adapt",
  "prompt_markdown": [
    "`intake_report(records)` does everything in one place. Split it into functions without changing what it returns.",
    "",
    "It needs at least 2 helper functions, each called from `intake_report`, and no function over 8 lines."
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "decompose_code": {
    "entry_function": "intake_report",
    "starter": [
      "def intake_report(records):",
      "    lines = []",
      "    for record in records:",
      "        name = record['name'].strip()",
      "        if name:",
      "            lines.append(f\"{name.upper()} ({record['age']})\")",
      "    lines.append(f'Total: {len(lines)}')",
      "    return '\\n'.join(lines)"
    ],
    "structure": {"min_helpers": 2, "max_lines_per_function": 8},
    "reference_solution": [
      "def keep_named(records):",
      "    named = []",
      "    for record in records:",
      "        if record['name'].strip():",
      "            named.append(record)",
      "    return named",
      "",
      "",
      "def format_line(record):",
      "    return f\"{record['name'].strip().upper()} ({record['age']})\"",
      "",
      "",
      "def intake_report(records):",
      "    lines = []",
      "    for record in keep_named(records):",
      "        lines.append(format_line(record))",
      "    lines.append(f'Total: {len(lines)}')",
      "    return '\\n'.join(lines)"
    ],
    "hidden_checks": [
      "from solution import intake_report",
      "",
      "",
      "def test_report():",
      "    records = [",
      "        {'name': ' Amara ', 'age': 30},",
      "        {'name': '   ', 'age': 41},",
      "        {'name': 'Kofi', 'age': 17},",
      "    ]",
      "    assert intake_report(records) == 'AMARA (30)\\nKOFI (17)\\nTotal: 2'",
      "",
      "",
      "def test_empty():",
      "    assert intake_report([]) == 'Total: 0'"
    ],
    "wrong_solution": [
      "def unused_helper(record):",
      "    return record['name']",
      "",
      "",
      "def intake_report(records):",
      "    lines = []",
      "    for record in records:",
      "        name = record['name'].strip()",
      "        if name:",
      "            lines.append(f\"{name.upper()} ({record['age']})\")",
      "    lines.append(f'Total: {len(lines)}')",
      "    return '\\n'.join(lines)"
    ]
  }
}
```

### `debug_locate`: PY-0.4, VE-4 at Understand

```json
{
  "schema_version": 2,
  "seed_id": "PY-0.4/cold-debug-validate-1",
  "unit_id": "PY-0.4",
  "activity": "Debug & Validate",
  "skill_id": "VE-4",
  "level": "Understand",
  "prompt_markdown": [
    "This script stops with an error when a citizen types `north-01`.",
    "",
    "Run it in your head or read it closely: on which line does it fail, and what kind of error is it?"
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "debug_locate": {
    "broken_code": [
      "print(\"Reception open\")",
      "ward = input()",
      "print(\"Registering\", citizen)",
      "print(\"Ward:\", ward)"
    ],
    "stdin": "north-01",
    "error_types": [
      {"key": "name", "text": "NameError: a name Python does not know"},
      {"key": "syntax", "text": "SyntaxError: the code is not written correctly"},
      {"key": "type", "text": "TypeError: an operation on the wrong kind of value"}
    ],
    "answer_key": {"line": 3, "error_type": "name"},
    "why": [
      "`citizen` was never given a value, so Python stops at line 3 with a NameError."
    ]
  }
}
```

### `explain_model_choice`: PY-1.1, CO-6 at Apply

```json
{
  "schema_version": 2,
  "seed_id": "PY-1.1/cold-explain-1",
  "unit_id": "PY-1.1",
  "activity": "Explain",
  "skill_id": "CO-6",
  "level": "Apply",
  "prompt_markdown": [
    "Running this prints `['Amara', 'Kofi']` for `queue`, though the code only changed `today`.",
    "",
    "Which mental model explains that?"
  ],
  "cold_check_eligible": true,
  "curator_approved": true,
  "explain_model_choice": {
    "material": [
      "queue = ['Amara']",
      "today = queue",
      "today.append('Kofi')",
      "print(queue)"
    ],
    "options": [
      {"key": "A", "text": "`today = queue` makes a second, separate list with the same items."},
      {"key": "B", "text": "`queue` and `today` are two names for one list object."},
      {"key": "C", "text": "`append` changes every list in the program."},
      {"key": "D", "text": "Python copies the change across at the `print`."}
    ],
    "answer_key": "B",
    "why": [
      "Assignment binds a name to an object. It does not copy the object."
    ]
  }
}
```

---

## 12. Acceptance Criteria

1. Every JSON block in sections 10 and 11 parses and meets section 8's rules.
2. A curator can write a seed for any activity using this document alone.
3. No field marked hidden appears in an `Exercise` response before an attempt.
4. `specify_by_tests`: a test file that fails the reference gets no mutant score, a mutant-surviving file gets a partial score, and a file breaking the static gate never runs.
5. `decompose_code`: a solution that passes the behaviour tests but fails a structure rule does not pass.
