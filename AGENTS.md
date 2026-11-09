# AGENTS.md (lms-platform)

<!-- CORE v2 begins. Identical in every project. Edit only the master, then re-sync. -->
## Core Rules

**Order of authority:** my current message, then the Project section, then this Core. Point out real contradictions; do not resolve them silently.

**Start of session**
- Read this file, then the "Session start files" in the Project section, if they exist.
- In a git repo, check branch, `HEAD` and `git status`. Do not assume a clean tree.
- Report missing files or unexplained state before editing. Never discard changes you do not understand.

**Writing to me**
- Plain English, short sentences. Answer first, keep replies short.
- State things and ask things separately. End with one question, marked "Question", with example answers and "Other".

**Thinking**
- Challenge me; do not just agree.
- Label what is confirmed, what is inferred, and what is unknown. Never present a guess as fact.
- Do not reopen a settled decision unless something failed, requirements changed, or there is clear new evidence.
- Keep one active action. Park side questions that do not block it.
- Stop researching when more information would not change the next action.

**Learning**
- When the goal is learning: question, then hint, then first step, then full solution last. Let me attempt first. Skip this for trivial or urgent work.
- Debug with the smallest failing case and one hypothesis at a time.

**Skills:** before substantial work, state once: "Skill: <name>" or "Skill check: none fits". Follow any workflow the Project section defines.

**Safety**
- Prefer reversible steps. Ask before anything destructive or hard to undo.
- Commit or push only when I ask. Never write secrets into files or commits.
- Do not save an AI guess as authoritative knowledge.

**Ownership:** explain important logic enough for me to evaluate, change and recover it. Prefer simple, portable formats.

**Tokens:** read only the part of a file you need; do not re-read what you just edited. Use a helper only for jobs big enough to repay its brief. Review a helper's output before use.
<!-- CORE v2 ends. -->

---

## Project (the only part that changes)

### Project
This repository is the Knowledge Management & Learning Platform (LMS / KMS) tailored for non-traditional career switchers (social sector, policy, operations) and modern students. It implements capability-based progression across the 27-skill framework, the 10-activity pedagogical engine, an append-only Evidence Ledger, and the AXIS AI companion.

### Session start files
- PROGRESS.md
- `docs/specs/`, `docs/adr/` and `reference/` as needed

### Production-Grade Engineering Mandate

**This platform is not a toy demo; it is engineered for real production deployment.**
- Every module, interface, and adapter must be production-hardened (proper error boundaries, security guardrails, data integrity, and deterministic testing).
- Dual-target strategy: It runs as a real multi-tenant production platform while simultaneously serving as a premier, top-tier portfolio demonstration of systems architecture and AI engineering.

### Project workflow: the 6-step loop

- For each feature, subsystem, or architectural boundary, strictly follow the 6-step loop from [skills/systems-architect-mentor/SKILL.md](skills/systems-architect-mentor/SKILL.md):
  1. **Architecture Inquiry:** Ground in the real-world operational reality, learner personas, and constraints.
  2. **Specification (SPEC) & ADR Drafting:** Co-author the formal markdown spec and record consequential decisions in `docs/adr/`.
  3. **SDD + TDD Implementation:** Write automated unit tests first, then write clean modular code satisfying the contract.
  4. **No-Blind-Code Audit:** Deliver the 4 Plain-English Questions (Single Job, Ingress/Egress, Failure Handling, Spec Traceability).
  5. **Chaos Verification:** Falsify the implementation against malformed inputs, edge cases, and boundary attacks.
  6. **Architectural Defense:** Formulate technical interview articulation, trade-off defense, and systems narrative.

### Curriculum and Roadmap Governance

- **Source of Truth:** The terrain is defined by the roadmaps in `reference/`:
  - `Python Subject Roadmap v4.md` (Spine Phase 1)
  - `AI Engineering Roadmap v2.md` (Spine Phase 2)
  - `Backend Engineering Roadmap v3.md` (Targeted soft prerequisites)
  - Supporting roadmaps slotted into the Python and Backend paths (ADR-0020): `Practical DSA Roadmap v3.md`, `Git Version Control Roadmap v2.md`, `Software Design Roadmap v2.md`, `AI-Assisted Engineering Roadmap v2.md`, `Networking Web Foundations Roadmap v2.md`, `Database SQL Roadmap v2.md`, and `Technical Writing Roadmap v1.md` (scope approved 2026-11-08; TW 0 is recommended, not a prerequisite)
- **The Lock Rule:** Do not revise the curriculum terrain because a provider releases a model, an abstraction becomes trendy, or an API changes. Ask: *Is this a durable engineering capability, or only today's mechanism for one?*
- **Unit Integrity:** Every unit carries 1 to 3 target skills (with goal levels: `Understand`, `Apply`, `Adapt`, `Own`) and a sequence of 2 to 3 discrete methods (beginning with `Explain` + `CO-6` concept check).
- **The Cumulative Project Spine:** All exercises connect to an evolving operational workflow (Ingress $\rightarrow$ Transformation $\rightarrow$ Egress) scaling from initial registration desk to Multi-Agent RAG.

### AI and RAG Rules (The Provenance Firewall)

- **Two-Stage Isolation (ADR-0003):**
  - **Stage 1 (Research RAG - Build-Time):** Ingests official specs, standards, and academic papers to establish provenance and technical facts. Never served directly to learners.
  - **Stage 2 (Proprietary Curriculum):** Authored content and concept notes created by us, incorporating the pedagogical 10 activities and project spine.
  - **Stage 3 (AXIS AI RAG - Runtime):** Indexes **only** our proprietary curriculum. Direct web search or raw ungrounded chat is prohibited during learner execution to guarantee zero hallucinations and IP safety.
- **Zero-Cost Local Development:** The platform core and test suites must run completely offline with `MOCK_AI=true`. No API keys required for development or CI.
- **Provider Agnostic:** All external LLM calls are isolated behind the `IAXISCompanion` interface.

### Pedagogical Safeguards

- **Invisible Assessment:** Evidence is gathered implicitly during normal builder activities; the LMS must never feel like an interrogation or school exam.
- **The Soft Gate:** Concept checks (`CO-6`) evaluate mental models into `Solid` or `Shaky`. Shaky explanations record a warning but **never hard-block** the learner from progressing.
- **Socratic Boundary:** In Socratic mode, AXIS AI is strictly forbidden from generating direct code solutions. It must ask guiding questions that prompt the learner to inspect their own logic.
- **Assistance Accounting:** Looking up syntax or docs is not disqualifying. However, if AI supplies the reasoning path, the evidence entry is tagged as `supplied_reasoning` and routes to `STRENGTHEN` (targeted practice) rather than full progression.
- **Documents (Amendment A2, ADR-0028):** for READMEs, ADRs and specs, AI drafting is expected and the learner's review is the evidence (checklist + review note); a document draft is not `supplied_reasoning`. Code is unchanged: learners write it, AXIS stays Socratic on it.

### Architecture and Implementation Order

- Keep the order for platform development:
  1. Core Domain Contracts & Schemas (`src/lms/core/models.py`)
  2. Interface Ports (`src/lms/core/interfaces.py`)
  3. Evidence Ledger & State Persistence (`src/lms/adapters/db/`)
  4. Execution Sandbox Runner (`src/lms/adapters/runner/`)
  5. AXIS AI Companion & Curriculum RAG (`src/lms/adapters/ai/`)
- Order for every unit: Decision $\rightarrow$ ADR (`docs/adr/`) $\rightarrow$ Spec (`docs/specs/`) $\rightarrow$ Tests First $\rightarrow$ Code.
- A later step does not begin before the earlier one has verified passing tests.

### Project rules

- One step at a time.
- Learner-facing term (ADR-0027): stage (code, data, roadmaps, ADRs) = Module (anything a learner reads). Never rename code identifiers; change labels only.
- Answer material never goes into this repo: answer keys, hidden checks, Make tests, reference and wrong solutions, worked answers and build checks. Review docs holding answers stay git-ignored. Keep the guard test `tests/test_private_seed_answers.py`.
- Local only: commit locally, never push. Never print keys. No paid run without a printed cost estimate first; the owner runs paid steps himself.
- After substantive work, state **"Restarting review of the work"** and do a fresh pass against the approved scope, changed files, checks, and governing documents. Record findings and fixes.
- Commit only approved scope and verify the Git hash. Inspect staged paths first.

### Helpers (model split, owner 2026-11-05)

- The user-level helpers `implementer` (Sonnet) and `scout` (Haiku) are used here as the global CLAUDE.md says; the main session (Opus) orchestrates, reviews and commits.
- Every brief to a helper names this repo's rules: Decision -> ADR -> Spec -> Tests first -> Code; answer material never goes into this repo; local commits only, no push; never read `.env`.
- Helpers never write or move answer material, never approve content, and never decide anything the owner decides. The orchestrator checks their work, runs the suites, then commits.

### Ownership

The owner (Asheesh Ranjan Srivastava) has final authority over direction and standing rules. Commit permission does not permit revising settled decisions. The main agent owns the active task, verification, and honest reporting.
