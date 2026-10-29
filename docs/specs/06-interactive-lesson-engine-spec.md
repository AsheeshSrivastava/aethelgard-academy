# SPEC-06: Interactive Lesson Engine and Workspace Execution

## 1. Overview & Operational Persona
- **Audience:** Non-traditional career switchers (social sector, operations, policy) and modern students.
- **Mental Model:** Programs as operational intake desks (Ingress $\rightarrow$ Transformation $\rightarrow$ Egress).
- **Core Loop:**
  1. **Ingress:** Learner pulls lesson package to local workspace via `lms pull py-0.4`.
  2. **Exploration & Watching:** Inspects `README.md`, video walkthrough in `media`, and concept explanations.
  3. **Implementation:** Edits `solution.py` in **Zed** or **VS Code**.
  4. **Verification:** Executes `lms verify py-0.4` inside the sandboxed runner.
  5. **Concept Soft-Gate (`CO-6`):** Submits mental model explanation via `lms explain py-0.4` which logs assessment evidence into SQLite.

---

## 2. Lesson Package Grammar (`curriculum/<track>/<unit-id>/`)

Each authored lesson package contains:
- `lesson.md`: Student-facing concept exposition, operational scenario, and video walkthrough link.
- `starter.py`: Initial scaffolding code with comments and function stubs.
- `test_solution.py`: Automated pytest/unittest assertions checking correctness without leaking solutions.
- `meta.json`:
  ```json
  {
    "media": [
      {
        "media_id": "vid-py-0.4-walkthrough",
        "kind": "video",
        "title": "Lesson Walkthrough: Running Your First Program",
        "url": "https://cdn.example.org/videos/py-0.4.mp4",
        "duration_seconds": 360,
        "timestamps": [
          {"time": "00:00", "topic": "Top-to-Bottom Execution"},
          {"time": "01:45", "topic": "input() Always Returns Text"},
          {"time": "03:30", "topic": "Formatting Egress with f-strings"}
        ]
      }
    ],
    "concept_check": {
      "prompt": "Explain in your own words why input() always returns text, and what happens if you try to do math with it directly.",
      "solid_keywords": ["string", "text", "typeerror", "convert", "int", "concatenate"],
      "rubric": "Learner must recognize type distinction between text and numbers."
    }
  }
  ```

---

## 3. The 3-Method Sequence for `PY-0.4`

Governed by `reference/Python Subject Roadmap v3.md`:
1. **Explain (Concept):** A program is text that the Python interpreter reads and runs from top to bottom. `input()` ingresses text; `print()` egresses messages.
2. **Predict (CO-1):** Predict what happens when entering applicant names and numbers before running the code.
3. **Debug & Validate (VE-4):** Given a syntax or type error trace, identify the exact line number, error type, and cause.

---

## 4. Acceptance Criteria & Chaos Matrix
- [x] Pulling an authored unit populates `workspace/<unit-id>/` with `solution.py`, `test_solution.py`, and `README.md` containing video timestamps.
- [x] Verifying an incomplete or broken solution fails with descriptive runner output and records no passing progression.
- [x] Verifying a correct solution passes all assertions and records a `PERFORM_SOLVE` entry in the Evidence Ledger.
- [x] Submitting a `CO-6` concept check grades into `Solid` or `Shaky` and logs an `EXPLAIN_REASON` evidence entry without blocking forward progress.
