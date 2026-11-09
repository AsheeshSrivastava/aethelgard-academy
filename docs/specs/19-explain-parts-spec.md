# SPEC-19: Explain in Parts, Step Diagrams and Quick Checks

- **Governed by:** ADR-0029 (this design), ADR-0021 (answers private), ADR-0026 / SPEC-18 (the concept check), ADR-0027 (learner term "Module")
- **Date:** 2026-11-09
- **Status:** Accepted (2026-11-09) with ADR-0029 by the owner ("1a + 2a").

---

## 1. Parts

1. The Explain text is `lesson.md` without its first `# ` heading and without the sections other steps show (headings matching `Video Walkthrough` or `Local Editor/Workflow Instructions`), as today (`splitLessonForExplain`).
2. Each `## ` section of that text is one part, in order; its heading text is the part's name. Text before the first `## ` (an intro) belongs to part 1. With no `## ` section, the whole text is one part named "Read".
3. The app adds a last part, **Say it back**: the unit's concept check (`concept_check.prompt`, else "Explain in your own words: <concept line>"), sent to `POST /api/v1/explain` and judged per SPEC-18. Submitting it is what completes the Explain step, as today.
4. The learner sees one part at a time:
   - a list of parts on the left ("Explain · N short parts"), the current one marked and done ones ticked;
   - "Part k of N", the part's content, then buttons to the previous and next part (the next button names the next part);
   - a box "Already know this?" linking to the unit's next lesson step;
   - the unit's concept notes as links, when the unit has wiki links.
5. Moving between parts does not change the URL and adds no browser history (the Back arrow leaves the lesson, as on every page).
6. A blockquote that begins with `**Key idea:**` is drawn as a key-idea box. It is plain Markdown, so it reads fine anywhere else.

## 2. The `steps` block

A fenced code block whose language is `steps`:

````markdown
```steps
caption: Picture to remember: a desk. Paper comes in, you tidy it, a slip goes out.

title: Take in
code: input("Name: ")
result: "  meera "
note: Waits for typing. Always gives back text.

title: Clean up
code: name.strip().title()
result: "Meera"
note: Fix spaces and capitals before you use it.
```
````

- One `key: value` per line, split at the first `": "`. Keys: `caption` (block, at most one), `title`, `code`, `result`, `note` (per step). A `title` line starts a new step. Blank lines are ignored.
- Valid: 2 to 5 steps, each with a `title`; no other keys. `code` and `result` are shown in monospace, `note` as plain text.
- Drawn as a figure: an ordered list of numbered boxes with arrows between them (arrows hidden from screen readers), the caption under it. On a phone the boxes stack.
- Invalid: shown as an ordinary code block; the curriculum check reports `explain-steps-invalid` (warning) naming the unit.

## 3. The `quickcheck` block

````markdown
```quickcheck
id: py-0.4-strip-upper
question: Someone types `  north-01 `. Which line gives `NORTH-01`?
A: `code.upper()`
B: `code.strip().upper()`
C: `code.title()`
```
````

- `id`: lowercase letters, digits, `.` and `-`; unique within the unit. `question`: one line; backticks mark code. Options `A:` to `D:`, 2 to 4, consecutive from `A`; backticks mark code.
- Never in the public block: `answer`, `why`. If present, the curriculum check reports `quickcheck-answers-public` (error) and a test fails (`tests/test_private_seed_answers.py` scans every `lesson.md`).
- The private key: `<answers dir>/<course>/<unit folder>/quick_checks.json`, for example `lms-answers/python/py-0.9/quick_checks.json` (a made-up unit; real keys never appear in this repo):

  ```json
  { "py-0.9-example": { "answer": "C", "why": "One sentence on why C is right." } }
  ```

  The answers dir is found as for builds and seeds (`LMS_ANSWERS_DIR`, else the sibling `../lms-answers`).
- With an answers dir, a quick check whose key is missing (or whose `answer` is not one of its options) is reported as `quickcheck-answers-missing` (error). Without an answers dir, the same report is a warning (offline development and CI).
- Drawn as: a "Quick check" chip, "Not graded. Just for you.", the question, one button per option. A right choice shows "Right." and the why; a wrong choice shows "Not quite. Try another." and marks that option; the learner may try again. If the server cannot mark it, the box says "This check can't be marked here." Invalid blocks are shown as code blocks and reported as `explain-quickcheck-invalid` (warning).

## 4. API

`POST /api/v1/units/{unit_id}/quick-checks/{check_id}` with `{"choice": "B"}`:

| Case | Status | Body |
| :--- | :--- | :--- |
| Choice checked | 200 | `{"correct": true, "why": "…"}` or `{"correct": false, "why": null}` |
| Unknown unit, or no quick check with that id in the unit | 404 | problem+json |
| Choice is not one of the check's option letters | 422 | problem+json |
| No private key loaded for this check | 503 | problem+json, title "Quick check not available" |

- The why is returned only for a right choice, so wrong tries do not reveal the answer.
- Nothing is written to the evidence ledger (ADR-0029 section 2.5).

## 5. Tests

- Backend: parsing of `quickcheck` blocks; key loading from a temporary answers dir; the four API cases; the public-answer guard over every real `lesson.md`; the curriculum findings.
- Frontend: parts from headings (Video and Editor sections left out, intro in part 1, "Say it back" last); next and previous; a valid and an invalid `steps` block; the quick check's right, wrong and not-available states; no extra browser history.
- PY-0.4 is the pilot: its `lesson.md` has three parts ("Why it matters", "In, clean, out", "Cleaning recipes") plus "Say it back", one `steps` block and one quick check; its key is only in the private repo.
