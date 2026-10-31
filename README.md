# Aethelgard Academy™
### Autonomous Curriculum Studio & Socratic AI Engineering Platform

> Architected by **Asheesh Ranjan Srivastava** ([@AsheeshSrivastava](https://github.com/AsheeshSrivastava))  
> Licensed under **Business Source License (BSL 1.1)** — see [`LICENSE`](LICENSE)  
> Architectural Deep-Dive: [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## The Origin & Purpose

> *"I built Aethelgard Academy first and foremost for myself.*  
> *When transitioning into technical engineering, I quickly realized I could make AI generate code, but I could not yet confidently decide whether to trust or change it. I was picking up fragmented syntax without grasping how real systems connect, and unconstrained AI chatbots only made it worse by handing out direct solutions.*  
> *I needed an environment that offered small, realistic review-and-repair tasks, taught only the missing mental models, and verified whether I could handle new versions later without AI handholding. The goal is to show what the learner can actually do—with their help and limits made crystal clear."*  
> — **Asheesh Ranjan Srivastava**, Systems Architect

---

## What the System Does

Aethelgard Academy bridges the gap between **"vibe coding with AI"** and **"production-grade systems engineering"**.

1. **Cumulative Project Spine:** Replaces isolated toy puzzles (`foo()` / `bar()`) with continuous operational workflows (Ingress $\to$ Transformation $\to$ Egress) inspired by real-world triage, intake, and multi-agent pipelines.
2. **Socratic AI Companion (AXIS):** An AI mentor strictly forbidden from generating direct code solutions. It forces the learner through the "productive struggle" required to build diagnostic composure and debugging instincts.
3. **Deterministic Capability Tracking:** Replaces vanity completion percentages (`completed = true`) with an **immutable, append-only Evidence Ledger**. True mastery is calculated by analyzing historical attempts, assistance levels, and 24-hour Cold Check retention tests.

---

## High-Level Architecture (Hexagonal / Ports & Adapters)

To guarantee that the platform remains modular, decoupled, and testable offline with zero API key dependencies, the system follows a strict **Hexagonal Architecture**:

```mermaid
flowchart TD
    UI["Learner Workspace (React + TypeScript + Vite)"] -->|REST & WebSockets| API["API Gateway (FastAPI)"]
    API --> Core["Core Domain Engine (src/lms/core/)<br/>• Pure Python Business Logic<br/>• Proficiency Engine & Cold Check Timer<br/>• Abstract Ports (interfaces.py)"]
    
    Core --> DB["SQLite Evidence Ledger<br/>(Immutable Event Sourcing)"]
    Core --> AI["AXIS AI Companion<br/>• Socratic Boundary Guardrails<br/>• Hybrid RAG (BM25 + Vectors + Reranker)"]
    Core --> Runner["Execution Sandbox<br/>• Ephemeral Docker Containers<br/>• Subprocess Fallback"]
```

### Architectural Highlights
- **Zero-Dependency Domain Core:** `src/lms/core/` does not import FastAPI, SQLite, Docker, or AI libraries. All business rules and capability logic can be verified in milliseconds offline.
- **Assistance Accounting:** Distinguishes between syntax lookups (`SYNTAX_LOOKUP`, encouraged developer practice) and algorithmic shortcuts (`SUPPLIED_REASONING`). If AI supplies the reasoning path, the skill is routed to targeted unassisted practice (`STRENGTHEN`).
- **Empirical Hybrid Reranked RAG:** Combines Inverted BM25 (for exact keywords, flags, and function identifiers) with dense semantic vectors via Reciprocal Rank Fusion ($k=60$) and `bge-reranker-v2-m3` cross-encoder reranking. Retrieved documentation passages are mathematically verified exact byte-slices (`verify_passage == True`).
- **Container-Isolated Sandboxing:** Executes untrusted student code inside rootless, network-disabled ephemeral Docker containers (`256MB` RAM, `0.5` CPU), falling back gracefully to a restricted subprocess runner for offline development.

---

## Quickstart (Run Locally in Under 1 Minute)

The platform is designed to run **100% offline with zero external API keys or cloud accounts** via built-in deterministic mock adapters (`MOCK_AI=true`).

### Prerequisites
- Python 3.12+ (or 3.14)
- [`uv`](https://github.com/astral-sh/uv) (fast Python package manager)

### 1. Clone & Run the Web Application
```bash
# Clone the repository
git clone https://github.com/AsheeshSrivastava/lms.git
cd lms

# Launch the unified web platform (serves the pre-built React frontend + FastAPI backend)
uv run lms serve
```
Open **`http://localhost:8000`** in your browser.  
Try selecting any unit from Stage 0, execute code in the playground, or open the **AXIS AI** side panel to test the Socratic boundary in action.

### 2. Run the Automated Test Suite
To verify the system contracts, sandboxing boundaries, and guardrail invariants:
```bash
uv run pytest
```
Runs **970+ automated tests** in ~48 seconds.

---

## Repository Guide

For a detailed explanation of folder responsibilities and architectural decisions, read [`ARCHITECTURE.md`](ARCHITECTURE.md).

```text
├── src/lms/
│   ├── core/           # Pure domain business logic, entities, and interface ports
│   ├── adapters/       # Concrete providers: SQLite DB, Socratic AI, Hybrid RAG, Runner
│   ├── api/            # FastAPI REST & WebSocket gateway
│   └── web/dist/       # Production React learner workspace bundle
├── frontend/           # React + TypeScript + Vite source code
├── curriculum/         # Stage lesson packages, stage builds, and exercise seeds
├── reference/          # Pinned curriculum roadmaps (Python, AI Engineering, Backend)
├── scripts/            # Tooling and reproducible doc fetcher (fetch_upstream.py)
├── tests/              # 970+ unit, integration, and chaos falsification tests
├── ARCHITECTURE.md     # In-depth System Architecture & Repository Topology
└── LICENSE             # Business Source License (BSL 1.1)
```

---

## Licensing & Contact

- **License:** Business Source License 1.1 (BSL 1.1) transitioning to Apache 2.0 on `2027-11-09`. Non-commercial educational use is permitted.
- **Architect & Maintainer:** Asheesh Ranjan Srivastava
- **Email:** `asheeshsrivastava9@gmail.com`
- **GitHub:** [@AsheeshSrivastava](https://github.com/AsheeshSrivastava)
