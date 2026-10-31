# Project Progress: Knowledge Management & Learning Platform (LMS / KMS)

- **Branch:** `main` (tracking `origin/main` on Entire)
- **Latest Commit:** `ed9b9ec` (this update follows it; 30 commits since `609aca8`)
- **Entire Version Control:** Enabled (`origin` linked to `/et/rag-learning-projects/lms` on `aws-ap-south-1.entire.io`). Push is on hold by owner decision; recent commits are local only.
- **Current Phase:** Learner Experience Backend: steps 1 to 3 done, exercises (step 4) next (`530` Tests Passing)
- **Status:** In Progress

---

## 1. Architectural 6-Step Loop Tracker

| Step | Milestone | Status | Deliverables / Artifacts |
| :--- | :--- | :--- | :--- |
| **Step 1** | Real-World Architecture Inquiry | **Done** | [`docs/architecture/01-problem-statement.md`](docs/architecture/01-problem-statement.md) |
| **Step 2** | Specification (SPEC) & ADR Drafting | **Done** | [`docs/specs/`](docs/specs/) (SPEC-01 through 13)<br>[`docs/adr/`](docs/adr/README.md) (ADR-0001 through 0017) |
| **Step 3** | SDD + TDD Implementation | **Done** | Core, Ingestion, Lesson Packages, Runner Sandbox, CLI, API Gateway, Socratic Guardrail, LocalLLMCompanion, Hybrid Reranked Retriever, Persistent Upstream Indexer, Unified Web Platform Shell, Proficiency Estimator, Cold Check Timer, Course Catalog, Curriculum Checks (`530` tests passing) |
| **Step 4** | No-Blind-Code Audit | **Done** | Executive translations (4 plain-English questions per module) |
| **Step 5** | Chaos Verification | **Done** | Falsification against SQL injection, prompt injection, infinite loops, DAG cycles, tampered passages, dirty markups, syntax failures, malformed input streams |
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
  - SPEC-07: Socratic Boundary Guardrail and Assistance Accounting
  - SPEC-08: Runtime-Agnostic Local LLM Companion & Rubric Classifier
  - SPEC-09: RAG Indexing & Hybrid Reranked Retriever
  - SPEC-10: Persistent Upstream Indexer & Warm Retriever Loader
  - SPEC-11: Learner Workspace Frontend
  - SPEC-12: Learner Experience API Contract
  - SPEC-13: Exercise Seed Format (draft; no loader yet)
- **Architecture Decision Records (ADRs):**
  - ADR-0001: Hexagonal Architecture and Pluggable Boundary Ports
  - ADR-0002: Dual-Store Strategy (SQLite for Evidence Ledger vs. Vector DB for RAG)
  - ADR-0003: Two-Stage RAG (Research vs. AXIS Grounding Firewall)
  - ADR-0004: Evidence Ledger and Capability Progression over Traditional Course Completion
  - ADR-0005: Defer Kubernetes in Favor of Container-Isolated Runners
  - ADR-0006: Hybrid Learner Workspace (Local CLI with Zed / VS Code + Cloud Sandbox Fallback)
  - ADR-0007: Document Loaders, Format Normalization, and the Inspection Gate
  - ADR-0008: Modular Curriculum Lesson Packages and Overlay Loader
  - ADR-0009: Socratic Boundary Guardrails and Assistance Accounting
  - ADR-0010: Deterministic Telemetry, Andragogical Facilitation, and Local-First AI Stack (Unsloth Desktop / OpenAI-compatible Local LLM + `bge-reranker-v2-m3`)
  - ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking
  - ADR-0012: Persistent RAG Artifacts & Upstream Documentation Indexer
  - ADR-0013: Learner Workspace Frontend (section 1 superseded by ADR-0014)
  - ADR-0014: React + TypeScript + Vite Learner Frontend
  - ADR-0015: Learner Identity and Sessions (local-single mode now; sign-in deferred)
  - ADR-0016: Proficiency Estimation and Progression Decisions (amended 2026-10-31)
  - ADR-0017: Batch Exercise Variant Generation from Curator Seeds
- **Learner Experience Backend (steps 1 to 3):**
  - **Proficiency (`src/lms/core/proficiency.py`, `proficiency_view.py`):** whole-ledger estimator; a skill's main activity from Learning Method v2 counts for Apply and Adapt.
  - **Evidence Ledger (`src/lms/adapters/db/sqlite_repo.py`):** stores `exercise_id`, `activity` and `cold_check`, with an idempotent migration.
  - **Cold Check Timer (`src/lms/core/cold_check.py`):** 24-hour delay per learner and unit, with an injectable clock.
  - **Catalog (`src/lms/core/course_map.py`, `curriculum/loader.py`):** all three roadmaps load (Python 78 units, Backend 79, AI Engineering 81), with stage build locks.
  - **Curriculum Checks (`src/lms/core/curriculum_checks.py`):** run at load. 30 errors remain, all `own-needs-stage-build`, until stage builds are curated. The Cold Check check judges by activity type until seeds load.
  - **Routes:** `/courses`, `/courses/{id}`, `/learners/me`, `/learners/me/proficiency`, `/learners/me/ledger`, `/learners/me/units/{id}/cold-check`. Older learner-id routes answer only for the local learner. CORS reads `LMS_ALLOWED_ORIGINS`.
- **Core Engine & Adapters:**
  - **Persistent Upstream Ingestion & Fast Warm Loader (`src/lms/adapters/ai/rag/indexer.py`):**
    - Batch command: `uv run lms index-upstream` indexes 1,262 clean upstream sources into 12,667 verified exact-slice passages in 2.4 seconds.
    - Serializes `passages.jsonl`, `sources.jsonl`, and `bm25.json` to `data/index/`.
    - `HybridRerankedRetriever.load("data/index")` warm-loads the full index into memory in $< 50\text{ms}$.
    - Automatically wired into `LocalLLMCompanion` via `get_axis_companion()` to ground live AXIS consultations without runtime parsing latency.
  - **Empirical RAG Chunking & Hybrid Reranked Retriever (`src/lms/adapters/ai/rag/`):**
    - Governed by empirical retrieval comparison report across 598 file-level questions and 137 quote-anchored passage-level questions.
    - `HeadingSentenceSplitter`: Heading-aware sentence chunker targeting ~375 tokens (~1500 chars max, ~640 median), guaranteeing the 100% exact-slice invariant (`verify_passage(source, passage) == True`).
    - `InvertedBM25Index`: Zero-dependency in-memory BM25 index over passage text and 2x weighted heading paths to guarantee exact-symbol and flag matches.
    - `reciprocal_rank_fusion`: Parameter-free Reciprocal Rank Fusion ($k=60$) combining top-200 dense and top-200 lexical candidates into top-30 merged candidates.
    - `HybridRerankedRetriever`: Coordinates Dense (`jinaai/jina-embeddings-v2-base-en`), Lexical BM25, RRF, Cross-Encoder reranking (`BAAI/bge-reranker-v2-m3`), and 1-per-source deduplication.
    - Integrated with `LocalLLMCompanion` for grounding AXIS AI responses with mechanically verifiable passages.
  - **Runtime-Agnostic Local LLM Companion (`src/lms/adapters/ai/local_llm_companion.py`):**
    - Connects to Unsloth Desktop, `llama.cpp`, `LM Studio`, `vLLM`, or `Ollama` via OpenAI-compatible `/v1/chat/completions` and `/v1/models`.
    - Auto-discovers loaded model (`LOCAL_LLM_MODEL=auto`) and injects verified `ConceptStore` passages.
    - Implements the 10% lightweight rubric classifier (`evaluate_concept_check`) for `CO-6` mental models with deterministic fallback.
    - Enforces XML prompt-injection delimiters (`<learner_code>`, `<execution_stderr>`, `<learner_query>`) and bounded payload truncation.
    - `get_axis_companion()` factory switches cleanly via `MOCK_AI=true|false`.
  - **Socratic Boundary Guardrail & Assistance Accounting (`src/lms/adapters/ai/socratic_guardrail.py`):**
    - Enforces zero-executable-code boundary in `AxisMode.SOCRATIC`.
    - Auto-sanitizes leaked code blocks or raises `SocraticBoundaryViolation` in strict mode.
    - Classifies assistance tiers: `NONE`, `SYNTAX_LOOKUP`, `SMALL_HINT`, `STRUCTURAL_DIRECTION`, `SUPPLIED_REASONING`.
    - Links to Evidence Ledger and progression evaluation (`evaluate_progression` routes `SUPPLIED_REASONING` to `STRENGTHEN` while protecting `SYNTAX_LOOKUP`).
  - **Dev Environment & Editor Tasks (`.devcontainer/` & `.zed/`):**
    - Production `.devcontainer/devcontainer.json` featuring Python 3.12, `uv` autoinstall, and Ruff VS Code extensions.
    - Zed editor tasks (`.zed/tasks.json`) configured for single-keystroke test runs and Ruff checks.
  - **Interactive Lesson Engine & Learner Loop (`curriculum/` & `src/lms/cli.py`):**
    - **Stage 0 Complete (All 3 Units Delivered on Intake Desk Spine):**
      - `curriculum/python/py-0.4/`: Run a first program (Intake Desk Registration scenario).
      - `curriculum/python/py-0.1/`: Python as an executing program (Sequential execution order, variables & state, input() return value capture, blank line output with print(), and modern f-strings).
      - `curriculum/python/py-0.3/`: Tool help versus your own reasoning (Developer ownership boundary, auditing flawed AI snippets, DE-3 ownership matrix, and DE-4 authoritative documentation verification).
    - Structured unit metadata with `MediaAsset` video walkthroughs, timestamped chapters, and `concept_check` rubric (`meta.json`).
    - Automated learner verification suite (`test_solution.py`) assessing whitespace normalization, uppercase formatting, and string formatting.
    - Overlay loader (`overlay_curriculum_packages`) dynamically upgrading parsed catalog units with real lesson packages.
    - CLI commands: `lms list`, `lms pull <unit>`, `lms verify <unit>`, `lms explain <unit>`, `lms ask <unit> <question>`.
  - **Lesson Media & Extensibility (`src/lms/core/models.py`):** `MediaAsset` model supporting video walkthroughs, audio lectures, slides, and transcript timestamps on each `Unit`.
  - **RAG Grounding Contracts (`src/lms/core/rag_contracts.py`):** 100% matched with `rag-core` (`Source`, `Span`, `Passage`, `verify_passage`).
  - **RAG Document Loaders (`src/lms/adapters/ai/loaders/`):** Full format loader suite matching `rag-core` specifications (`markdown.py`, `rst.py`, `html.py`, `notebook.py`, `snapshot.py`).
  - **Upstream Pinned Reference Bedrock (`reference/upstream/`):** 14 curated, official technical documentation bedrocks pinned at immutable commits with strict anti-noise filtering (1,312 verified sources, < 9.8 MB total):
    - **Backend Spine:**
      - `python-docs` (`3d6d2a6`): 29 sources (PSF-2.0, tutorial & language reference)
      - `uv-docs` (`d2152bc`): 92 sources (MIT, packaging, CLI, virtualenvs)
      - `ruff-docs` (`0a7cf4a`): 25 sources (MIT, linter, formatter, configuration)
      - `zed-docs` (`0373366`): 216 sources (Apache-2.0, editor, tasks, LSP)
      - `fastapi-docs` (`79cab5b`): 157 sources (MIT, English tutorials, APIRouter, schemas)
      - `pydantic-docs` (`dd0c36a`): 20 sources (MIT, core concepts, validation, models)
      - `httpx-docs` (`b5addb6`): 24 sources (BSD-3-Clause, async client, streaming, transports)
      - `pytest-docs` (`a7b2446`): 253 sources (MIT, automated testing, fixtures, assertions)
    - **AI Engineering Spine:**
      - `llms-from-scratch` (`f184d22`): 58 sources (Apache-2.0, Sebastian Raschka chapters)
      - `prompt-engineering-guide` (`5767372`): 133 sources (MIT, DAIR.AI English guides, 1000+ translations excluded)
      - `generative-ai-for-beginners` (`5abe9a5`): 32 sources (MIT, Microsoft 21 lessons, translations excluded)
      - `huggingface-course` (`8b893f0`): 96 sources (Apache-2.0, English chapters on NLP, transformers, tokenizers)
      - `dspy-docs` (`25162c4`): 170 sources (MIT, Stanford LM programming & optimization)
      - `openai-evals` (`8eac7a7`): 7 sources (MIT, completion evaluation protocols)
      - `llamaindex-docs` (`619d746`): 109 sources (MIT, LlamaIndex data framework documentation)
      - `llama-index-core==0.14.25`: pinned in `pyproject.toml` (`[dependency-groups] variants`) for deterministic boundary evaluation.
  - **FastAPI HTTP Gateway (`src/lms/api/`):** REST API endpoints for `/units`, `/execute`, `/axis/consult`, `/learners/{id}/ledger`, and `/learners/{id}/progress`.
  - 530 automated tests passing.

---

## 3. Decisions Settled (2026-10-31)
- My progress opens on the learner's current stage.
- A skill's main activity counts for Apply and Adapt (ADR-0016 amendment A).
- A passed Cold Check counts only for the skill it tests, through that skill's own activity. Explain, Specify and Decompose are graded through SPEC-13's deterministic item types; AI never grades a Cold Check (amendments B and C).
- Every lesson shows the playground; it writes evidence only when the unit's methods include Modify or Build (SPEC-12 section 3.2).
- Reset clears a unit's timer, including a passed Cold Check, and never touches the ledger.
- Stage 0 seeds: Claude drafts, the owner approves.
- Push is on hold.

## 4. Next Action
- Python stage titles and the 20 Stage 0 seeds are approved (2026-10-31). Each Stage 0 skill still has only one Cold Check seed, so a retry after a fail has no unseen item; add more before real learners use it.
- Next is step 4: exercises (seed loader, grader, exercise, regenerate, reset, state and drafts routes, and the `playground` step in `Unit.activities`).
- Then step 5 attempts and evidence, step 6 live runs and AXIS streaming, step 7 stage builds, then the frontend.
- Known gap for step 5: `/explain` and `/axis/consult` still accept a `learner_id` in the request body.
- Separate open item: benchmark results (BAAI/bge-m3 vs jina-embeddings-v2-base-en) for the upstream RAG pipeline.
