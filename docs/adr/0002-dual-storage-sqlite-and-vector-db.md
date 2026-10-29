# ADR 0002: Dual-Store Strategy: SQLite for Evidence Ledger vs. Vector DB for RAG

- **Status:** Accepted
- **Decider:** Lead Educational Engineer & Systems Architect (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-29

---

## 1. Context & Problem Statement

The platform handles two fundamentally distinct types of data:
1. **Deterministic State & Telemetry:** User profiles, lesson completion status, and the append-only **Evidence Ledger** tracking observations across 27 skills.
2. **Semantic Curriculum Content:** Thousands of concept notes, authoritative documentation paragraphs, and pedagogical guidelines needed for AXIS AI retrieval.

We must decide the storage engine architecture: Should we use a single Vector DB for everything, a single Relational DB, or a decoupled Dual-Store strategy?

---

## 2. Decision

We adopt a **Dual-Store Strategy**:

1. **Relational Database (SQLite / PostgreSQL) for Deterministic State:**
   - **Engine:** Local SQLite file (`lms_state.db`) for development and single-node deployment, easily migrating to PostgreSQL via the repository adapter.
   - **Role:** Atomic transactions, ACID compliance, exact relational queries (e.g., *"What is the learner's evidence strength for skill `CO-1`?"*).
   - **Rationale:** SQLite is lightweight, zero-latency, requires zero server setup, and is mathematically safe against data loss.
2. **Vector Store (Chroma / Qdrant) for Semantic Retrieval (RAG):**
   - **Role:** Storing vector embeddings of our proprietary curriculum notes.
   - **Rationale:** Vector databases excel at fuzzy semantic matching (e.g., *"Find notes related to type coercion errors"*), but are inefficient and ill-suited for relational transactions or audit logs.

---

## 3. Consequences

### Positive
- **Correct Tool for the Job:** Relational integrity for user data; semantic vector indexing for AI retrieval.
- **Zero Complexity Overkill:** No distributed vector database required to test unit progression or user progress.
- **Clear Separation:** Changing the embedding model or vector database does not threaten user accounts or the evidence ledger.

### Trade-offs / Mitigations
- Managing two storage mechanisms. Mitigated by keeping the vector store strictly read-only at runtime for AXIS AI, while the SQLite database manages all read/write learner transactions.
