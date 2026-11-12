# System Architecture & Design Guide

> **Quest and Crossfire™ Curriculum Studio & Learning Platform**  
> Architected by **Asheesh Ranjan Srivastava**  
> Licensed under Business Source License (BSL 1.1)

---

## 1. Executive Summary & Problem Framing

### The Real-World Friction
In the era of modern Generative AI, traditional coding tutorials and bootcamps are fundamentally broken for career switchers:
- **Fragmented Toy Problems:** Traditional tutorials teach syntax in isolation (`foo()` and `bar()` functions) without showing how real production systems operate across an end-to-end operational pipeline (Ingress $\to$ Transformation $\to$ Egress).
- **The AI Handout Trap:** When modern learners get stuck, generic AI assistants (like unconstrained ChatGPT) dump complete code solutions. This deprives the learner of the **productive struggle** necessary to build diagnostic composure, mental models, and critical debugging habits.
- **The Modern Developer Identity Crisis:** If an AI model can generate boilerplate syntax in seconds, what is the developer's true value? A modern software engineer is no longer a "syntax typist"—they are a **System Architect, Auditor, and Boundary Verifier**.

### Our Solution
This platform acts as an **Andragogical Learning Facilitator & Architecture Engine**. It provides a cumulative operational project spine while strictly enforcing architectural guardrails that prevent AI from leaking answers, ensuring learners develop verifiable, independent problem-solving capabilities.

---

## 2. High-Level Architecture (Hexagonal / Ports & Adapters)

To guarantee that the platform remains modular, decoupled, and testable offline with zero infrastructure costs, the system follows a strict **Hexagonal Architecture (Ports and Adapters)**:

```
┌────────────────────────────────────────────────────────┐
│                   frontend/ (React/Vite)               │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP & WebSockets
┌───────────────────────────▼────────────────────────────┐
│                  src/lms/api/ (FastAPI)                │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  src/lms/core/                         │
│  - Domain Models (Unit, EvidenceEvent, Attempt)        │
│  - Proficiency Engine & Cold Check Decay Timer         │
│  - Abstract Interfaces / Ports (interfaces.py)         │
└───────┬───────────────────┬───────────────────┬────────┘
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  adapters/db/  │  │  adapters/ai/  │  │adapters/runner/│
│  SQLite Event  │  │ Socratic Gate  │  │ Subprocess run │
│     Ledger     │  │  & BM25 RAG    │  │ (Docker: seam) │
└────────────────┘  └────────────────┘  └────────────────┘
```

### The Architectural Invariant: Core Purity

- **`src/lms/core/` has zero external dependencies:** The domain core contains pure Python business logic, entity models, and abstract protocol ports (`interfaces.py`). It does not import FastAPI, SQLite, Docker, or AI client libraries.
- **Why this matters:** All domain rules (such as proficiency evaluation, 24-hour Cold Check retention, and exercise scoring) can be verified deterministically in milliseconds without running a database, spinning up containers, or paying for cloud API keys.
- **Pluggable Technology Providers:** The database, AI models, and execution runtimes are external adapters. We can swap local models (Unsloth / llama.cpp) for cloud APIs, or SQLite for PostgreSQL, without modifying core domain logic.

---

## 3. Repository Topology (Directory Guide)

| Directory | Role | Responsibility |
| :--- | :--- | :--- |
| **`src/lms/core/`** | **Domain Core** | Pure business rules, data models (`Unit`, `EvidenceEvent`, `Attempt`), proficiency scoring algorithms, and abstract interface contracts. |
| **`src/lms/adapters/`** | **External Providers** | Concrete implementations of the core interface ports: SQLite Event Ledger, Socratic Guardrails, Hybrid RAG, and execution sandboxing. |
| **`src/lms/api/`** | **Gateway Routes** | FastAPI REST endpoints and WebSockets that route communications between the frontend interface and core domain services. |
| **`frontend/`** | **User Interface** | Modern React + TypeScript + Vite learner workspace featuring the code editor, execution terminal, and collapsible AXIS AI panel. |
| **`curriculum/`** | **Course Artifacts** | Concrete lesson packages, stage builds, and deterministic exercise seeds used by the platform to evaluate learner capability. |
| **`reference/`** | **Curriculum Roadmaps** | Pinned roadmap specifications (Python, AI Engineering, Backend) defining the sequential capability terrain. |
| **`tests/`** | **Automated Suite** | Over 1,400 unit, integration, and chaos falsification tests proving system contracts, runner boundaries, and state transitions. They run on made-up exercise items (`tests/fixtures`), never the private answers. |
| **`docs/`** | **Architecture & ADRs** | Formal Architecture Decision Records (ADRs) and technical specifications recording every trade-off made during development. |
| **`scripts/`** | **Tooling & Data** | Automation utilities, including `fetch_upstream.py` to reproducibly download reference documentation. |

---

## 4. Subsystems & Key Architectural Decisions

### 4.1. The Append-Only Evidence Ledger (`src/lms/adapters/db/`)

- **The Problem:** Naive learning platforms store progress as a mutable flag (`UPDATE users SET completed = true`). Overwriting state destroys historical context: you cannot know whether a learner succeeded on attempt 1 or attempt 10, or whether they had answers spoon-fed to them by an AI.
- **The Solution:** We adopt an **Append-Only Event Ledger (Event Sourcing)**. Every graded attempt (practice item, concept check, Cold Check, stage build) is appended as an immutable evidence entry. AXIS help is logged separately and changes how the attempt is credited; other learner actions go to an interaction log (ADR-0022). Ungraded playground runs write no evidence. A reset adds a marker and never deletes entries.
- **Capability Estimation:** The proficiency engine (`src/lms/core/proficiency.py`) analyzes the entire event trail to estimate real-world competence across the 27-skill framework.

### 4.2. Socratic Boundary Guardrail & Assistance Accounting (`src/lms/adapters/ai/`)

- **Productive Struggle:** Learning requires diagnosing one's own mistakes.
- **The Hard Filter:** In `AxisMode.SOCRATIC`, model output is intercepted and scanned for code blocks and executable syntax. If code leaks are detected, the response is automatically sanitized or rejected before reaching the learner.
- **Assistance Accounting:** Looking up documentation or syntax (`SYNTAX_LOOKUP`) is encouraged as standard professional practice. However, if the AI supplies the core architectural reasoning path (`SUPPLIED_REASONING`), the ledger tags the event to route the learner to targeted unassisted practice (`STRENGTHEN`) before true mastery is credited.

### 4.3. Hybrid Reranked Retrieval (RAG) (`src/lms/adapters/ai/rag/`)

- **Why Vector Search Alone Fails:** Dense vector embeddings excel at semantic similarity, synonyms, and natural language questions, but frequently fail on exact syntax matches, rare function names, CLI flags, and error codes.
- **BM25 Lexical Index:** Inverted index with 2x weighted heading paths to ensure exact-token and keyword recall.
- **Reciprocal Rank Fusion (RRF) & Reranking (seams):** The retriever can merge dense and BM25 candidates ($k=60$) and pass them to a cross-encoder such as `bge-reranker-v2-m3`, but no embedding model or reranker is wired yet. Without them it falls back to token overlap, and saved indexes do not store vectors. Ranking today is lexical.
- **Provenance Firewall:** Enforces exact byte-slice verification (`verify_passage(source, passage) == True`) against authoritative documentation.
- **What AXIS retrieves from today:** the upstream-docs index when it has been built locally (`data/index`, not in git), under ADR-0003's temporary exception. Curriculum concept notes are not yet passed to AXIS, and a fresh clone has no index, so a live model gets no grounding passages there. Moving AXIS onto the curriculum is planned (work sequence 2d.7, audit step A7).

### 4.4. Containerized Code Execution Sandbox (`src/lms/adapters/runner/`)

- **The Danger:** Executing untrusted learner code directly on the host operating system risks server compromise, malicious file deletion, or socket abuse.
- **Today:** `SubprocessRunner` runs learner code in a temporary folder with a timeout, and strips API keys and `.env` secrets from the child's environment. It is not an isolation boundary, so the app is for single-learner local use.
- **Seam, not wired yet:** `DockerRunner` builds an ephemeral container command with `--network none`, `128m` memory, `1.0` CPU and a 64-process limit, but its `execute()` still calls the subprocess runner. Wiring it in (and running as a non-root user) is planned before anyone else uses the platform (work sequence 6.1, audit step A6).

---

## 5. Operational Reality & Production Roadmap

Engineering maturity means acknowledging both what is built today and what is required for Day-2 high-scale production.

### Currently Implemented:

1. **Warm Memory Indexing:** The compiled BM25 index and passage slices warm-load into memory in $< 50\text{ms}$.
2. **Deterministic Telemetry:** Zero-latency SQLite event persistence recording immutable audit logs.
3. **Structured Module Logging:** Standard logging across API routes, curriculum ingestion, and runner processes.
4. **Zero-Key Offline Development:** Complete test suite and mock companions run offline with `MOCK_AI=true`.

### Built Today vs Pluggable Seams

| Area | Built and tested today | Seam ready, not wired yet |
| :--- | :--- | :--- |
| Persistence | SQLite append-only ledger | PostgreSQL behind `ILearnerRepository` |
| Code execution | Subprocess runner (timeout, secrets stripped) | Docker sandbox behind `ICodeRunner` |
| Retrieval | BM25 + byte-slice verification + RRF code | Dense embeddings, cross-encoder reranker |
| AXIS grounding | Upstream-docs index if built locally | Curriculum concept notes (ADR-0003) |

### Planned Hardening (Production Roadmap):

0. **Audit fixes in progress (2026-11):** close SQLite connections and enable WAL with a busy timeout; batch the course-map queries; cap concurrent code runs; stop building the app at import time; wire the Docker sandbox; ground AXIS in the curriculum.

1. **Distributed Tracing & OpenTelemetry:** Adding correlation IDs across HTTP requests, sandbox execution, and LLM generation to monitor exact latency breakdowns (BM25 vs Vector search vs Reranker vs Model generation).
2. **Semantic Response Caching:** Implementing a semantic cache layer for recurring student conceptual queries to reduce local/cloud LLM inference load by 25–35%.
3. **Multi-Tenant Postgres Migration:** Migrating the SQLite Evidence Ledger to PostgreSQL with connection pooling as user concurrency scales beyond single-node requirements.
