# ADR-0013: Unified Platform Shell, Pedagogical Workspace & Concept Library Architecture

## Status
Accepted; section 1 (zero-build shell) superseded by [ADR-0014](0014-react-typescript-vite-frontend.md) on 2026-10-30

## Context
Our LMS/KMS platform has engineered the core domain models, execution runners, hybrid RAG retriever, and Stage 0 curriculum packages. However, adult learners transitioning from operations, policy, and social sectors require a cohesive, visual learning operating system rather than disconnected tools.

Learners need:
1. **Platform Topology & Navigation:** The ability to navigate seamlessly from the **Landing Dashboard** to the **Courses Catalog**, explore the **Python Track Roadmap (MoC)**, enter the **Unit Studio**, and search the **Concept Library (KMS)** without disorientation.
2. **Pedagogical Activity Stepper:** A structured step-by-step learning progression inside each unit:
   - **Phase 1: Explain** (side-by-side explanatory notes, video walkthrough, visual execution model for top-to-bottom and right-to-left evaluation, and the `CO-6` concept check soft gate).
   - **Phase 2: Predict** (committing to an outcome prediction before executing code).
   - **Phase 3: Practice & Playground** (interactive coding, live interactive terminal prompting for `input()`, and automated test verification).
3. **Concept Library (KMS):** A searchable dictionary of canonical terms (`input()`, `print()`, `Variables`, `Sequential Execution`, `Standard Streams`) with official technical anchors and bi-directional links to units.
4. **Graduated Hybrid Workspace (Zed CLI):** First-class support for transitioning from the browser playground into a local desktop editor (**Zed**) with automated scaffolds (`uv run lms pull`, `.zed/tasks.json`, `uv run lms verify`) reading and writing to the shared SQLite Evidence Ledger (`data/lms.db`).

## Decision

### 1. Unified Zero-Build Single-Page Platform Shell
We implement the entire frontend in `src/lms/web/` (`index.html`, `styles.css`, `app.js`) served directly by the FastAPI gateway (`/static` and root `GET /`):
- Eliminates Node.js build steps, Webpack, Vite, or npm dependencies for running the core LMS platform.
- Provides seamless client-side view switching between:
  1. **`dashboard`**: Landing page with active unit resume, track cards, and Evidence Ledger summary.
  2. **`roadmap`**: Visual Python Track Map of Content (Stage 0 to Stage 5 progression DAG).
  3. **`unit-studio`**: The 3-phase pedagogical workspace.
  4. **`concept-library`**: Searchable KMS dictionary with real-time filtering.
  5. **`ledger`**: Detailed view of all recorded competencies.

### 2. Three-Phase Pedagogical Activity Sequence
Inside the **Unit Studio**, learning is gated through explicit pedagogical phases:
- **Phase 1: Explain (Notes & Video):**
  - Side-by-side view: Explanatory notes on the left (60%) detailing real-world operational scenarios, sequential top-to-bottom execution, right-to-left assignment, and official Python doc anchors. Video walkthrough on the right (40%) with timestamped concept links.
  - Concludes with the **CO-6 Concept Check Soft Gate** evaluating mental models into `Solid` or `Shaky` without hard-blocking progression.
- **Phase 2: Predict (Commitment):**
  - Displays a code snippet under inspection. The learner must predict the terminal output before running code, building operational confidence.
- **Phase 3: Practice & Playground (Interactive Coding):**
  - 3-column layout: Task checklist and pseudocode on the left, code editor in the center, and live interactive terminal on the right.
  - Interactive terminal simulation: when `input()` is called, execution pauses, opens an interactive prompt line, receives learner keyboard input, and echoes output cleanly.
  - Automated test verification runs unit assertions and appends strong evidence to the ledger.

### 3. Searchable Concept Library (KMS)
- Implement `GET /api/v1/concepts` exposing a structured dictionary of canonical technical concepts, execution behaviors, upstream official documentation URLs, and cross-references to units where taught and tested.
- Global search input in the Concept Library view filters concepts in real-time.
- Terms highlighted in unit lesson notes link directly to the Concept Library.

### 4. Zed CLI Integration & Local Workspace Bridge
In accordance with ADR-0006:
- The UI exposes one-click commands and URIs (`uv run lms pull <unit> && zed workspace/<unit>`).
- The `lms` CLI generates `.zed/tasks.json` in the pulled unit directory for instant task execution (`uv run python solution.py`, `uv run lms verify <unit>`).
- Both CLI and Web UI operate on the same local SQLite database (`data/lms.db`), ensuring immediate state synchronization.

### 5. Modern Web Guidelines Compliance
- `color-scheme: light dark` with dual-mode CSS variables (`light-dark()`).
- `scrollbar-gutter: stable` and `overscroll-behavior: contain` to prevent layout jumps and scroll-chaining.
- CSS Grid and Flexbox with logical properties (`inline-size`, `padding-block`, `margin-inline`).

## Consequences

### Positive
- Learners experience an integrated, end-to-end learning environment from day one.
- Preserves zero-cost offline development (`MOCK_AI=true`) with no npm build requirements.
- Seamless bridge between browser exploration and professional developer tools (Zed / VS Code).
- High architectural cohesion: single source of truth in SQLite and uniform REST API.

### Negative
- Client-side routing is managed through lightweight vanilla JS view switching rather than a full frontend routing framework.
- UI assets must be maintained cleanly with modular CSS and JavaScript.
