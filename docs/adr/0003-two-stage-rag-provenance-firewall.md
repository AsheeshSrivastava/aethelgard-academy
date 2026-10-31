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

---

## 4. Amendment (2026-10-31): Temporary Exception for Upstream Citations

**What is true today.** At runtime AXIS retrieves from `data/index`, which holds upstream documentation (Python, FastAPI, pytest and others), not only our curriculum. AXIS replies show those sources as citation chips. This does not match Stage 3 above.

**Decision.** The owner has seen the chips and is fine with them for now. We keep the upstream index and its citations as a deliberate, temporary exception to Stage 3. This is a recorded exception, not a change to the firewall: Stage 3 stays the target.

**What holds during the exception.**
- Retrieval stays limited to the curated, licence-tracked `data/index`. Direct web search and ungrounded chat stay prohibited.
- A chip shows a readable source name, never a raw passage id, and never passage text.
- Cold Checks stay free of AXIS.

**What it costs.** While the exception holds, the Positive consequences above are not fully met: AXIS can use terms our lessons do not use, and the licence safety rests on AXIS not repeating upstream text at length.

**When it must be looked at again.** Before anyone other than the owner learns on the platform, or when the curriculum and concept notes are large enough to ground AXIS on their own, whichever comes first. That review decides whether AXIS moves to the Stage 3 target.
