# ADR 0003: Two-Stage RAG: Upstream Research vs. Downstream AXIS AI Grounding

- **Status:** Accepted
- **Decider:** Lead Educational Engineer & Systems Architect (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-29

---

## 1. Context & Problem Statement

Building an industry-grade curriculum requires referencing authoritative documentation (Python official specs, PEP standards, OWASP GenAI, academic papers). 

However:
1. Third-party materials have varying licenses and copyright restrictions; serving them directly to learners creates intellectual property risks.
2. Raw documentation lacks our specific pedagogical scaffolding (`Explain`, `Predict`, `Modify`, `CO-6` checks, Cumulative Project Spine).
3. If AXIS AI directly searches raw external documentation, it risks hallucinating syntax or explaining concepts with different terminology than what is taught in our lessons.

---

## 2. Decision

We establish an **IP & Provenance Firewall** dividing RAG into two strictly isolated stages:

```text
┌────────────────────────────────────────────────────────┐
│ Stage 1: Upstream Research RAG (Build-Time / Internal)  │
│ - Ingests external authoritative docs, PEPs, papers.   │
│ - Used internally by curriculum authors / engineers.   │
│ - Establishes provenance and technical facts.          │
└──────────────────────────┬─────────────────────────────┘
                           │ (Curated & Authored)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Proprietary Curriculum & Concept Notes Store  │
│ - Authored by us with our pedagogical frameworks.      │
│ - Licensed to our platform.                            │
└──────────────────────────┬─────────────────────────────┘
                           │ (Indexed)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Downstream AXIS AI RAG (Runtime / Learner)    │
│ - Indexes ONLY our proprietary curriculum store.       │
│ - Zero access to uncurated raw external web text.      │
│ - Guarantees 100% alignment with course terminology.   │
└────────────────────────────────────────────────────────┘
```

---

## 3. Consequences

### Positive
- **Legal & License Safety:** No third-party copyrighted text is served directly to learners.
- **Pedagogical Consistency:** AXIS AI speaks the exact terminology used in our lesson notes and project spine.
- **Zero Hallucination:** AXIS AI's retrieval boundary is restricted to our validated, curated curriculum corpus.

### Trade-offs / Mitigations
- Requires a human-in-the-loop authoring step between research ingestion and curriculum publication. This is a deliberate educational choice to maintain high quality.
