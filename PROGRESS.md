# Project Progress: Knowledge Management & Learning Platform (LMS / KMS)

- **Branch:** `main` (tracking `origin/main` on Entire)
- **Latest Commit:** `609aca8`
- **Entire Version Control:** Enabled (`origin` linked to `/et/rag-learning-projects/lms` on `aws-ap-south-1.entire.io`, all 25 checkpoint refs synced)
- **Current Phase:** Upstream Persistent Ingestion & Warm Loader (`lms index-upstream`) Complete (`330` Tests Passing)
- **Status:** In Progress

---

## 1. Architectural 6-Step Loop Tracker

| Step | Milestone | Status | Deliverables / Artifacts |
| :--- | :--- | :--- | :--- |
| **Step 1** | Real-World Architecture Inquiry | **Done** | [`docs/architecture/01-problem-statement.md`](docs/architecture/01-problem-statement.md) |
| **Step 2** | Specification (SPEC) & ADR Drafting | **Done** | [`docs/specs/`](docs/specs/) (SPEC-01 through 10)<br>[`docs/adr/`](docs/adr/README.md) (ADR-0001 through 0012) |
| **Step 3** | SDD + TDD Implementation | **Done** | Core, Ingestion, Lesson Packages, Runner Sandbox, CLI, API Gateway, Socratic Guardrail, LocalLLMCompanion, Hybrid Reranked Retriever, Persistent Upstream Indexer (`330` tests passing) |
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
  - SPEC-07: Socratic Boundary Guardrail and Assistance Accounting
  - SPEC-08: Runtime-Agnostic Local LLM Companion & Rubric Classifier
  - SPEC-09: RAG Indexing & Hybrid Reranked Retriever
  - SPEC-10: Persistent Upstream Indexer & Warm Retriever Loader
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
    - First complete unit package: `curriculum/python/py-0.4/` (Intake Desk Registration scenario).
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
  - **FastAPI HTTP Gateway (`src/lms/api/`):** REST API endpoints for `/units`, `/execute`, `/axis/consult`, `/learners/{id}/ledger`, and `/learners/{id}/progress`.
  - 316 automated tests passing in under 3.5 seconds.

---

## 3. Next Action
- Await user's benchmark evaluation results (BAAI/bge-m3 vs jina-embeddings-v2-base-en across 600 eval questions) to configure the upstream RAG chunking and indexing pipeline.
