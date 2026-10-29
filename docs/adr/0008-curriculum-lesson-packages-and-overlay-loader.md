# ADR-0008: Modular Curriculum Lesson Packages and Overlay Loader

## Status: Accepted (2026-10-30, systems-architect)

## Context
The platform roadmap terrain is strictly locked in `reference/Python Subject Roadmap v3.md` across 78 units. However, concrete lesson execution requires rich instructional materials: starter code, automated test verification suites, video walkthrough metadata (`Unit.media`), concept check rubrics (`CO-6`), and learner workbooks. Editing the large roadmap markdown document for every lesson asset would violate the Lock Rule (AGENTS.md Section 4) and create merge conflicts.

## Decision
1. **Modular Lesson Packages (`curriculum/<track>/<unit-id>/`):**
   - Each authored unit lives in its own directory:
     - `lesson.md`: Explanatory concept notes, operational context, and video walkthrough link.
     - `starter.py`: The initial scaffolding code provided to the learner.
     - `test_solution.py`: Deterministic unit tests checking syntax, output egress, and error diagnosis.
     - `meta.json`: Structured metadata including `media` (video URL, duration, timestamps), `wiki_links`, and carry-forward contexts.
2. **Catalog Overlay Pattern:**
   - The curriculum catalog initially parses the locked roadmap `reference/Python Subject Roadmap v3.md`.
   - When a lesson package exists in `curriculum/python/<unit-id>/`, `CurriculumCatalog` overlays the rich starter code, test code, and media assets onto the in-memory `Unit` model.
   - Units without an authored package retain their roadmap metadata with fallback scaffolding.
3. **Workspace Ingress & Egress (`lms pull` / `lms verify`):**
   - `lms pull <unit-id>` materializes the lesson into `workspace/<unit-id>/` with editor instructions for Zed and VS Code.
   - `lms verify <unit-id>` executes the solution against `test_solution.py` in the execution sandbox and logs immutable evidence into the Evidence Ledger.

## Consequences & Trade-Offs
- **Benefits:** Complete decoupling of the authoritative curriculum framework from lesson implementation; allows independent authoring of video, code, and rubrics; non-breaking backwards compatibility.
- **Trade-offs:** Requires catalog loading to scan the `curriculum/` directory at startup (lightweight disk I/O, cached in memory).
