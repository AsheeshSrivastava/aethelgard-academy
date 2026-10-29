# AGENTS.md (lms-platform)

This repository is the Knowledge Management & Learning Platform (LMS / KMS) tailored for non-traditional career switchers (social sector, policy, operations) and modern students. It implements capability-based progression across the 27-skill framework, the 10-activity pedagogical engine, an append-only Evidence Ledger, and the AXIS AI companion.

---

## 1. Production-Grade Engineering Mandate

**This platform is not a toy demo; it is engineered for real production deployment.**
- Every module, interface, and adapter must be production-hardened (proper error boundaries, security guardrails, data integrity, and deterministic testing).
- Dual-target strategy: It runs as a real multi-tenant production platform while simultaneously serving as a premier, top-tier portfolio demonstration of systems architecture and AI engineering.

---

## 2. Startup and Handoff

- Read this file, then [PROGRESS.md](PROGRESS.md). Read specs in `docs/specs/`, ADRs in `docs/adr/`, and reference frameworks in `reference/` as needed.
- Check `pwd`, branch, `HEAD`, and `git status`; compare them with PROGRESS.md. Do not assume a clean worktree. An unborn branch is `no commits yet`, not a hash.
- Report missing files, conflicting instructions, or unexplained state before editing. Do not reset or discard changes you do not understand. Observed Git state outranks remembered chat.

---

## 3. Skill Usage & The 6-Step Facilitation Loop

- Before substantial work, state a skill check line: `"Skill: systems-architect-mentor"` or `"Skill check: none fits, proceeding directly"`.
- For each feature, subsystem, or architectural boundary, strictly follow the 6-step loop from [skills/systems-architect-mentor/SKILL.md](skills/systems-architect-mentor/SKILL.md):
  1. **Architecture Inquiry:** Ground in the real-world operational reality, learner personas, and constraints.
  2. **Specification (SPEC) & ADR Drafting:** Co-author the formal markdown spec and record consequential decisions in `docs/adr/`.
  3. **SDD + TDD Implementation:** Write automated unit tests first, then write clean modular code satisfying the contract.
  4. **No-Blind-Code Audit:** Deliver the 4 Plain-English Questions (Single Job, Ingress/Egress, Failure Handling, Spec Traceability).
  5. **Chaos Verification:** Falsify the implementation against malformed inputs, edge cases, and boundary attacks.
  6. **Architectural Defense:** Formulate technical interview articulation, trade-off defense, and systems narrative.

---

## 4. Curriculum & Roadmap Governance

- **Source of Truth:** The terrain is defined by the roadmaps in `reference/`:
  - `Python Subject Roadmap v3.md` (Spine Phase 1)
  - `AI Engineering Roadmap v2.md` (Spine Phase 2)
  - `Backend Engineering Roadmap v2.md` (Targeted soft prerequisites)
- **The Lock Rule:** Do not revise the curriculum terrain because a provider releases a model, an abstraction becomes trendy, or an API changes. Ask: *Is this a durable engineering capability, or only today's mechanism for one?*
- **Unit Integrity:** Every unit carries 1 to 3 target skills (with goal levels: `Understand`, `Apply`, `Adapt`, `Own`) and a sequence of 2 to 3 discrete methods (beginning with `Explain` + `CO-6` concept check).
- **The Cumulative Project Spine:** All exercises connect to an evolving operational workflow (Ingress $\rightarrow$ Transformation $\rightarrow$ Egress) scaling from initial registration desk to Multi-Agent RAG.

---

## 5. AI & RAG Rules (The Provenance Firewall)

- **Two-Stage Isolation (ADR-0003):**
  - **Stage 1 (Research RAG - Build-Time):** Ingests official specs, standards, and academic papers to establish provenance and technical facts. Never served directly to learners.
  - **Stage 2 (Proprietary Curriculum):** Authored content and concept notes created by us, incorporating the pedagogical 10 activities and project spine.
  - **Stage 3 (AXIS AI RAG - Runtime):** Indexes **only** our proprietary curriculum. Direct web search or raw ungrounded chat is prohibited during learner execution to guarantee zero hallucinations and IP safety.
- **Zero-Cost Local Development:** The platform core and test suites must run completely offline with `MOCK_AI=true`. No API keys required for development or CI.
- **Provider Agnostic:** All external LLM calls are isolated behind the `IAXISCompanion` interface.

---

## 6. Pedagogical Safeguards

- **Invisible Assessment:** Evidence is gathered implicitly during normal builder activities; the LMS must never feel like an interrogation or school exam.
- **The Soft Gate:** Concept checks (`CO-6`) evaluate mental models into `Solid` or `Shaky`. Shaky explanations record a warning but **never hard-block** the learner from progressing.
- **Socratic Boundary:** In Socratic mode, AXIS AI is strictly forbidden from generating direct code solutions. It must ask guiding questions that prompt the learner to inspect their own logic.
- **Assistance Accounting:** Looking up syntax or docs is not disqualifying. However, if AI supplies the reasoning path, the evidence entry is tagged as `supplied_reasoning` and routes to `STRENGTHEN` (targeted practice) rather than full progression.

---

## 7. Architecture & Implementation Order

- Keep the order for platform development:
  1. Core Domain Contracts & Schemas (`src/lms/core/models.py`)
  2. Interface Ports (`src/lms/core/interfaces.py`)
  3. Evidence Ledger & State Persistence (`src/lms/adapters/db/`)
  4. Execution Sandbox Runner (`src/lms/adapters/runner/`)
  5. AXIS AI Companion & Curriculum RAG (`src/lms/adapters/ai/`)
- Order for every unit: Decision $\rightarrow$ ADR (`docs/adr/`) $\rightarrow$ Spec (`docs/specs/`) $\rightarrow$ Tests First $\rightarrow$ Code.
- A later step does not begin before the earlier one has verified passing tests.

---

## 8. Rules of this Project

- Plain simple words with the owner. One step at a time.
- Local only: commit locally, never push. Never print keys. No paid run without a printed cost estimate first; the owner runs paid steps himself.
- After substantive work, state **"Restarting review of the work"** and do a fresh pass against the approved scope, changed files, checks, and governing documents. Record findings and fixes.
- Commit only approved scope and verify the Git hash. Inspect staged paths first.

---

## 9. Ownership

The owner (Asheesh Ranjan Srivastava) has final authority over direction and standing rules. Commit permission does not permit revising settled decisions. The main agent owns the active task, verification, and honest reporting.
