# SPEC-11: Unified Platform Shell, Navigation Topology & Concept Library Specification

- **Status:** Accepted (2026-11-09, by the owner, as built). The React shell (ADR-0014) differs in places, for example the route is `/courses`, not `/tracks`; where they differ, the code and its tests are current.

> **Learner wording (ADR-0027):** screens say "Module" where this spec says "stage"; code, routes and data keep "stage".

## 1. Executive Summary
This specification defines the complete information architecture, page navigation topology, data contracts, and interaction mechanics of the **Aethelgard Academy Unified Web Platform**. It formalizes the five core platform views:
1. **Academy Landing Dashboard** (`/`)
2. **Courses Catalog (MoC)** (`/tracks`)
3. **Python Track Roadmap (MoC)** (`/tracks/python`)
4. **Unit Studio & 3-Phase Playground** (`/units/{unit_id}`)
5. **Searchable Concept Library (KMS)** (`/concepts`)

---

## 2. Navigation Architecture & View States

The single-page application orchestrates view states via client-side routing and top-bar navigation:
- `data-view="dashboard"`: High-level overview, quick resume, competency highlights.
- `data-view="roadmap"`: Visual stage-by-stage DAG of Python Track units.
- `data-view="unit-studio"`: Active unit workspace with 3-phase pedagogical flow.
- `data-view="concept-library"`: Searchable technical concept dictionary with real-time filtering.
- `data-view="ledger"`: Append-only evidence ledger audit log.

---

## 3. View Specifications

### 3.1 Academy Landing Dashboard (`dashboard`)
- **Quick Resume Hero:** Displays the current active unit (e.g. `PY-0.1`), stage name, and an instant `"Resume Unit ➔"` button.
- **Evidence Ledger Metric Card:** Live tally of recorded evidence entries and top mastered skills.
- **Track Catalog Cards:**
  - *Python Backend Engineering (Spine Phase 1)*: Active (Stage 0 to Stage 5).
  - *AI Engineering & LLM Systems (Spine Phase 2)*: Locked until Stage 3 completion.
  - *Systems Architecture & Cloud Infrastructure*: Coming soon.

### 3.2 Python Track Map of Content (`roadmap`)
- **Stage Progression Headers:** Stage 0 (Foundations), Stage 1 (Data Ingress), Stage 2 (Control Flow), Stage 3 (Object Modeling), Stage 4 (HTTP Protocols), Stage 5 (Intake Capstone).
- **Unit Cards:** Shows unit ID, title, concept line, target skills badges (`CO-1`, `VE-4`), and live status (`Completed`, `In Progress`, `Pending`).
- Clicking any unit card loads that unit and switches the view to `unit-studio`.

### 3.3 Unit Studio (`unit-studio`)
Follows the **3-Phase Pedagogical Activity Sequence**:
- **Phase 1: Explain (Notes & Video Walkthrough)**
  - Left Column (60%): Explanatory notes, operational scenario narrative, execution models (Top-to-Bottom, Right-to-Left assignment), technical doc anchors.
  - Right Column (40%): Video walkthrough player with topic timestamps and local CLI hints.
  - Footer: **CO-6 Concept Check Soft Gate** evaluating mental model (`Solid` vs. `Shaky`).
- **Phase 2: Predict (Commitment Before Running)**
  - Code snippet inspection with multiple-choice output prediction.
  - Commit button validates understanding before opening the code editor.
- **Phase 3: Practice & Playground**
  - Left Sub-Pane: Task requirements checklist and pseudocode blueprints.
  - Center Sub-Pane: Interactive code editor with line numbers, tab indentation, `Run Code`, and `Verify Solution`.
  - Right Sub-Pane: Interactive Terminal with live stdin prompting (when `input()` runs, prompt appears, waits for user typing, and echoes output), plus verification results.

### 3.4 Concept Library & KMS (`concept-library`)
- **Global Search Bar:** Instant client-side filtering across concept titles, keywords, and descriptions.
- **Concept Cards:**
  - Concept Title (e.g., `input()`, `Variables & Memory`, `Sequential Execution`, `f-strings`).
  - Plain-English Operational Meaning.
  - Execution Rules (e.g., *"Right-to-Left evaluation; always returns str"*).
  - Pinned Official Documentation Link.
  - Cross-Reference: Linked tags to units where taught or tested.
- **Drawer / Modal Access:** Clicking a concept wiki link inside `unit-studio` opens a slide-over preview without leaving the lesson.

### 3.5 Zed CLI Integration Modal
- Step-by-step instructions for transitioning to local desktop development:
  1. `uv` verification and installation commands.
  2. Pulling unit files: `uv run lms pull <unit_id>`.
  3. Opening in Zed: `zed workspace/<unit_id>`.
  4. Pre-configured `.zed/tasks.json` runner.
  5. Local verification: `uv run lms verify <unit_id>`.

---

## 4. API Endpoints & Contracts

### 4.1 Concept Library
SPEC-14 replaces this section for the Concept Library.

- **`GET /api/v1/concepts`**
  - Query parameters: `search: Optional[str]`, `category: Optional[str]`
  - Response:
    ```json
    [
      {
        "concept_id": "built-in-input",
        "name": "input() Built-in Function",
        "category": "Core Primitives",
        "summary": "Pauses program execution, reads standard input from keyboard, and returns it as a string.",
        "execution_rules": "Evaluates on the right-hand side first; always produces str even for digits.",
        "doc_url": "https://docs.python.org/3/library/functions.html#input",
        "units": ["PY-0.1", "PY-0.4"]
      }
    ]
    ```

### 4.2 Concept Check Evaluation
- **`POST /api/v1/explain`**
  - Request: `{"unit_id": "PY-0.1", "explanation": "...", "learner_id": "default_learner"}`
  - Response: `{"unit_id": "PY-0.1", "status": "Solid" | "Shaky", "feedback": "...", "evidence_logged": true}`

### 4.3 Full Unit Metadata
- **`GET /api/v1/units/{unit_id}`**
  - Includes `lesson_markdown`, `starter_code`, `test_code`, `media`, and `concept_check_config`.

### 4.4 Static Web Assets
- **`GET /`**: Serves `src/lms/web/index.html`.
- **`GET /static/{path:path}`**: Serves CSS, JS, and image assets from `src/lms/web/`.

---

## 5. Verification Plan

1. **API Automated Tests (`tests/test_web_api.py`):**
   - Verify `GET /api/v1/concepts` returns populated concepts and filters by query.
   - Verify `POST /api/v1/explain` scores solid/shaky and records evidence into SQLite.
   - Verify `GET /` serves HTML and `/static/styles.css` is accessible.
   - Verify `GET /api/v1/units/PY-0.1` includes `lesson_markdown`.
2. **Regression Verification:**
   - Run `uv run pytest` to ensure all 330+ tests continue passing with zero regressions.
3. **End-to-End Live Verification:**
   - Launch server on port 8000 and verify full navigation across Dashboard, Roadmap, Unit Studio, and Concept Library.
