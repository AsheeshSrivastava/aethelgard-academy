# Project Progress: Knowledge Management & Learning Platform (LMS / KMS)

- **Branch:** `main`
- **Latest Commit:** `adb590e`
- **Entire Version Control:** Enabled (`entire status` active for Antigravity)
- **Current Phase:** Interactive Lesson Engine & Unit `PY-0.4` First-Program Spine (307 Tests Passing)
- **Status:** In Progress

---

## 1. Architectural 6-Step Loop Tracker

| Step | Milestone | Status | Deliverables / Artifacts |
| :--- | :--- | :--- | :--- |
| **Step 1** | Real-World Architecture Inquiry | **Done** | [`docs/architecture/01-problem-statement.md`](docs/architecture/01-problem-statement.md) |
| **Step 2** | Specification (SPEC) & ADR Drafting | **Done** | [`docs/specs/`](docs/specs/) (SPEC-01 through 06)<br>[`docs/adr/`](docs/adr/README.md) (ADR-0001 through 0008) |
| **Step 3** | SDD + TDD Implementation | **Done** | Core, Ingestion, Lesson Packages, Runner Sandbox, CLI, API Gateway, RAG Contracts, Loaders, and Inspector (`307` tests passing) |
| **Step 4** | No-Blind-Code Audit | **Done** | Executive translations (4 plain-English questions per module) |
| **Step 5** | Chaos Verification | **Done** | Falsification against SQL injection, prompt injection, infinite loops, DAG cycles, tampered passages, dirty markups |
| **Step 6** | Architectural Defense | **Done** | Interview defense playbook, trade-off narratives, and ADRs |

---

## 2. Completed Architecture & Subsystems
- **Problem Statement & Governance:** [`docs/architecture/01-problem-statement.md`](docs/architecture/01-problem-statement.md), [`AGENTS.md`](AGENTS.md)
- **Technical Specifications:**
  - SPEC-01: Lesson & Curriculum Contract
  - SPEC-02: Curriculum Ingestion & Catalog
  - SPEC-03: Code Execution Sandbox & Runner
  - SPEC-04: Platform API Gateway
  - SPEC-05: Curriculum RAG & AXIS Grounding Contracts
  - SPEC-06: Interactive Lesson Engine & Learner Loop
- **Architecture Decision Records (ADRs):**
  - ADR-0001: Hexagonal Architecture and Pluggable Boundary Ports
  - ADR-0002: Dual-Store Strategy (SQLite for Evidence Ledger vs. Vector DB for RAG)
  - ADR-0003: Two-Stage RAG (Research vs. AXIS Grounding Firewall)
  - ADR-0004: Evidence Ledger and Capability Progression over Traditional Course Completion
  - ADR-0005: Defer Kubernetes in Favor of Container-Isolated Runners
  - ADR-0006: Hybrid Learner Workspace (Local CLI with Zed / VS Code + Cloud Sandbox Fallback)
  - ADR-0007: Document Loaders, Format Normalization, and the Inspection Gate
  - ADR-0008: Modular Curriculum Lesson Packages and Overlay Loader
- **Core Engine & Adapters:**
  - **Interactive Lesson Engine & Learner Loop (`curriculum/` & `src/lms/cli.py`):**
    - First complete unit package: `curriculum/python/py-0.4/` (Intake Desk Registration scenario).
    - Structured unit metadata with `MediaAsset` video walkthroughs, timestamped chapters, and `concept_check` rubric (`meta.json`).
    - Automated learner verification suite (`test_solution.py`) assessing whitespace normalization, uppercase formatting, and string formatting.
    - Overlay loader (`overlay_curriculum_packages`) dynamically upgrading parsed catalog units with real lesson packages.
    - CLI commands: `lms pull <unit>`, `lms verify <unit>`, and `lms explain <unit>` (`CO-6` mental model soft gate evaluating Solid vs. Shaky without blocking progression).
  - **Lesson Media & Extensibility (`src/lms/core/models.py`):** `MediaAsset` model supporting video walkthroughs, audio lectures, slides, and transcript timestamps on each `Unit`.
  - **RAG Grounding Contracts (`src/lms/core/rag_contracts.py`):** 100% matched with `rag-core` (`Source`, `Span`, `Passage`, `verify_passage`).
  - **RAG Document Loaders (`src/lms/adapters/ai/loaders/`):** Full format loader suite matching `rag-core` specifications:
    - Markdown / MDX (`markdown.py`, `read_md`, `read_mdx`): Front matter extraction, JSX and HTML tag stripping, code fence preservation.
    - reStructuredText (`rst.py`, `read_rst`): Python & Sphinx directive and role translation into clean Markdown without syntax noise.
    - HTML (`html.py`, `read_html`): Standard library zero-dependency parser converting headings, tables, and lists while dropping scripts and styles.
    - Jupyter Notebooks (`notebook.py`, `read_ipynb`): Extracts prose and code fences while discarding execution counts, outputs, and metadata.
    - Snapshot & Folder Loader (`snapshot.py`, `load_snapshot`): Loads multi-format documentation trees with skip policies (`SkipShareExceeded`).
  - **Upstream Pinned Reference Bedrock (`reference/upstream/`):** Curated, official factual documentation pinned at immutable commits and verified through inspection gates (`skip_share <= 0.25`):
    - `python-docs` (`3d6d2a6`): 28 sources loaded (tutorial & language reference, PSF-2.0, 0 skips).
    - `uv-docs` (`d2152bc`): 80 sources loaded (packaging, CLI, virtualenvs, MIT, 1 skip).
    - `ruff-docs` (`0a7cf4a`): 16 sources loaded (linter, formatter, rules, configuration, MIT, 0 skips).
    - `zed-docs` (`0373366`): 207 sources loaded (editor, tasks, keymaps, LSP, Apache-2.0, 3 skips).
    - Total: 331 verified, provenance-hashed sources (under 3 MB).
  - **Upstream Fetch Engine (`scripts/fetch_upstream.py`):** Partial-clone blobs-on-demand fetcher ensuring zero bloat and reproducible snapshots.
  - **Source Inspection Engine & CLI (`scripts/inspect_sources.py`):** Pre-indexing audit tool ensuring 0% unreadable or dropped files on curriculum notes.
  - **Proprietary Concept Store (`src/lms/adapters/ai/concept_store.py`):** Ingests and verifies curriculum notes from `docs/concepts/` (tested via fixtures in `tests/fixtures/concepts/`).
  - **FastAPI HTTP Gateway (`src/lms/api/`):** REST API endpoints for `/units`, `/execute`, `/axis/consult`, `/learners/{id}/ledger`, and `/learners/{id}/progress`.
  - **Curriculum Ingestion:** 78 units parsed into `CurriculumCatalog` with acyclic DAG validation.
  - **Evidence Ledger:** Append-only relational tracking across 27 skills in SQLite.
  - **Execution Sandbox:** `DockerRunner` with hardened security cgroup flags + `SubprocessRunner` with timeout defense.
  - **Platform CLI (`lms`):** Supports `lms list`, `lms pull`, `lms verify`, `lms explain` for Zed and VS Code local workflows.
  - 307 automated tests passing in under 3.5 seconds.

---

## 3. Next Action
- Implement AXIS AI Socratic Guardrails & Assistance Accounting (distinguishing syntax assistance vs reasoning supplied, routing to STRENGTHEN).
