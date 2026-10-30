# ADR-0010: Deterministic Telemetry, Andragogical Facilitation, and Local-First AI Stack

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Asheesh Ranjan Srivastava (Platform Architect & Owner), AI Systems Architect

---

## 1. Context and Problem Statement

As we wire the AXIS AI Companion, the Evidence Ledger, and the Stage 3 Curriculum RAG into an end-to-end learning loop, three architectural questions must be settled:

1. **Agent Complexity vs. Determinism:** Should workspace state assembly (`Context Assembler`) and Evidence Ledger recording (`Ledger Gatekeeper`) be implemented as autonomous AI sub-agents, or as deterministic Python services?
2. **Pedagogical Stance (Andragogy):** How should AXIS AI interact with adult career-switchers without feeling like an authoritarian teacher or a school exam?
3. **Inference Economics & Local Model Stack:** Given strict budget constraints during development and the long-term goal of minimizing per-learner LLM token costs in production, how should we architect LLM inference, embedding, and reranking without locking into a single local runner (e.g., Unsloth Desktop vs. Ollama vs. vLLM) or cloud vendor?

---

## 2. Decisions

### 2.1 Deterministic Telemetry + 10% Lightweight Classification (No "Telemetry Agents")
We explicitly reject multi-agent LLM swarms for state tracking and database logging:
- **90% Pure Deterministic Python:** Assembling unit context (`unit_progress`, `carry_forward` state, `git diff`, `SubprocessRunner` exit codes, `stderr`, execution timing) and appending immutable rows to the `evidence_ledger` are executed by standard, deterministic Python services.
- **10% Lightweight Rubric Classification:** Only unstructured human text—specifically evaluating `CO-6` mental model explanations (`Solid` vs. `Shaky`) and classifying free-form chat interactions (`AssistanceClassifier`)—uses a lightweight classifier/rubric check (deterministic keyword/AST rules when `MOCK_AI=true`, or a fast structured JSON classification call against a local model).
- **Separation of State vs. Ledger:**
  - `unit_progress` table records **mutable current state** (active unit bookmark, current activity step, status).
  - `evidence_ledger` table records **immutable historical capability receipts** (`skill_id`, `evidence_category`, `evidence_strength`, `assistance_level`, `demonstration_context`, `observed_reasoning`).

### 2.2 Facilitation over Teaching (Adult Learning / Andragogy)
- AXIS AI operates strictly as an **adult learning facilitator**, never as a lecturing teacher or grading judge.
- Instead of maintaining separate autonomous agents per mode, a single `IAXISCompanion` port switches deterministically between three facilitator system-prompt stances (**Socratic**, **Coach**, **Hybrid**), enforced post-generation by the mechanical `SocraticGuardrail` (ADR-0009).
- Competency progression decisions (`Progress`, `Accelerate`, `Strengthen`, `Rebuild`) remain 100% outside the LLM inside the deterministic `evaluate_progression()` domain engine.

### 2.3 Local-First, Runtime-Agnostic AI & Retrieval Stack
To achieve **\$0.00 marginal token cost** during development and sustainable unit economics in production:
1. **Runtime-Agnostic Local LLM Adapter:**
   - Rather than coupling to a single tool (such as Ollama), local inference connects via a standard OpenAI-compatible HTTP interface (`LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`), supporting **Unsloth Desktop** (preferred local runner), `llama.cpp`, `LM Studio`, `vLLM`, or `Ollama` interchangeably.
   - Supported local GGUF models on the 16 GB VRAM workstation include `gemma-4-12b-it`, `Qwen3.6-35B-A3B` (MoE), `Qwopus3-5-9B-Coder-Flash`, and `qwen3.5-9b`.
2. **Two-Stage Retrieval with Cross-Encoder Reranking:**
   - Smaller/medium local LLMs (9B–12B active parameters) perform at frontier quality when fed clean, high-precision context without noise.
   - **Stage A (Bi-Encoder Retrieval):** Local embedding model (`BAAI/bge-m3` or `jinaai/jina-embeddings-v2-base-en`, pending final benchmark evaluation) retrieves initial candidate passages (`top-k`, e.g., $k=15$).
   - **Stage B (Cross-Encoder Reranker):** Local `BAAI/bge-reranker-v2-m3` (Safetensors) re-scores candidate passages against the learner's query and filters down to the highest-precision `top-3` verified passages before prompt assembly.
3. **Offline CI Guarantee:**
   - `MOCK_AI=true` remains the default for automated `pytest` suites so all unit and chaos tests run in milliseconds without requiring a live GPU server.

---

## 3. Consequences

### Positive
- **Zero Cloud API Spend:** Development, testing, RAG indexing, reranking, and AXIS facilitation run 100% locally on existing GPU hardware.
- **No Runner Lock-In:** Switching between Unsloth Desktop, `llama.cpp`, or `vLLM` requires changing only an environment variable (`LOCAL_LLM_BASE_URL`), with zero code changes.
- **High-Precision Grounding for Local LLMs:** Pairing `bge-reranker-v2-m3` with our 1,312 zero-noise documentation sources ensures local 9B/12B/35B-A3B models receive only exact, relevant passages—eliminating context-window dilution.
- **Simpler, Auditable Codebase:** Eliminating unnecessary "telemetry AI agents" keeps state management fast, debuggable, and 100% deterministic.

### Negative / Trade-offs
- Local Cross-Encoder reranking (`bge-reranker-v2-m3`) adds ~50–150ms per query on local GPU, which is well within interactive tutoring latency budgets (< 1.5s total response time).
