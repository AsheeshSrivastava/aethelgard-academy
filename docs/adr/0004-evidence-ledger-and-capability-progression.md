# ADR 0004: Evidence Ledger and Capability Progression over Traditional Course Completion

- **Status:** Accepted
- **Decider:** Lead Educational Engineer & Systems Architect (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-29

---

## 1. Context & Problem Statement

Traditional LMS software measures progress via vanity metrics:
- Video watch percentage.
- Time spent on page.
- Superficial multiple-choice quiz scores.

This model is obsolete in the AI era. In our platform, learners are non-traditional career switchers developing real systems architecture and AI engineering capabilities. We need a progression system governed by observable technical evidence, aligned with:
- `Learning Method v2` (10 discrete activities, CO-6 concept check with soft gate).
- `Proficiency & Progression System v1` (4 levels: Understand, Apply, Adapt, Own; 4 decisions: Progress, Accelerate, Strengthen, Rebuild).
- `AI-Era Programming Skills Framework v1` (27 skills).

---

## 2. Decision

1. **Replace "Lesson Completion" with the Append-Only Evidence Ledger:**
   - Every learner action (predicting execution, modifying code, passing test assertions, writing specifications) creates an immutable `EvidenceEntry`.
   - Normal learning produces evidence implicitly; no separate high-stakes exam is required.
2. **The Soft-Gate Principle:**
   - Concept checks (`CO-6`) evaluate mental models into `Solid` or `Shaky`.
   - The gate is **soft**: A shaky concept check never hard-blocks the learner from attempting practical activities. If downstream activities fail repeatedly, the system guides them back to the concept.
3. **Four-Way Adaptive Decisions:**
   - Progress (depth met $\rightarrow$ next unit).
   - Accelerate (depth exceeded $\rightarrow$ skip ahead).
   - Strengthen (specific dimension fragile $\rightarrow$ targeted micro-task on smallest gap).
   - Rebuild (mental model broken $\rightarrow$ revisit foundational concept).

---

## 3. Consequences

### Positive
- **Authentic Engineering Assessment:** Evaluates whether the learner supplied the key reasoning, not whether they memorized syntax or had an AI write the code.
- **Adaptive Remediation:** Instead of forcing a learner to repeat an entire chapter, the system isolates the exact broken skill link (e.g., `VE-4 Exception flow`) for targeted strengthening.
- **Psychological Safety:** The soft gate eliminates test anxiety, encouraging learners to experiment and discover.

### Trade-offs / Mitigations
- Requires storing and indexing fine-grained telemetry events. Mitigated by using an indexed relational table (`evidence_ledger`) in SQLite with sub-millisecond query performance.
