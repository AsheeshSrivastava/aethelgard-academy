# AGENTS.md (lms-platform)

<!-- CORE v4 begins. Identical in every project. Edit only the master, then re-sync. -->
## Core Rules

**Order of authority:** my current message, then the Project section, then this Core, then skills, plugins and output styles. Point out real contradictions; do not resolve them silently.

**Start of session**
- Read this file, then the "Session start files" in the Project section, if they exist.
- In a git repo, check branch, `HEAD` and `git status`. Do not assume a clean tree.
- Report missing files or unexplained state before editing. Never discard changes you do not understand.
- A file marked "local only" is absent in cloud sessions and fresh clones. Say once that it is absent and carry on.

**Writing to me**
- Plain English, short sentences. Answer first, keep replies short.
- State things and ask things separately.
- If you need an answer from me, end with exactly one line that starts `Question:`, then 2 to 4 example answers and "Other". If you need nothing, do not ask.
- If your tool shows choices as a card, use the card and still start its text with `Question:`.

**Thinking**
- Challenge me; do not just agree.
- Label what is confirmed, what is inferred, and what is unknown. Never present a guess as fact.
- Do not reopen a settled decision unless something failed, requirements changed, or there is clear new evidence.
- Keep one active action. Park side questions that do not block it.
- Stop researching when more information would not change the next action.

**Learning**
- When the goal is learning: question, then hint, then first step, then full solution last. Let me attempt first. Skip this for trivial or urgent work.
- Debug with the smallest failing case and one hypothesis at a time.

**Skills:** before substantial work, state once: "Skill: <name>" or "Skill check: none fits". Follow any workflow the Project section defines. If a named skill has no local file, load it by name from your skill list.

**Build order:** decision, ADR, spec, tests, code. Before you write or change a test or code, name the ADR and the spec section it implements. If there is none, write or amend it first, show it to me, and stop until I say go. This covers features and fixes. A typo or comment fix needs no ADR; say so in one line.

**Safety**
- Prefer reversible steps. Ask before anything destructive or hard to undo.
- Commit or push only when I ask. Never write secrets into files or commits.
- Do not save an AI guess as authoritative knowledge.
- When you open a PR, end your report with a ready-to-paste merge commit title (`<subject> (#N)`) and merge commit body, each in its own code block, plus a reminder to use "Create a merge commit" (not squash). Do this without being asked. Do not repeat the PR description; it is already on GitHub.

**Ownership:** explain important logic enough for me to evaluate, change and recover it. Prefer simple, portable formats.

**Tokens:** read only the part of a file you need; do not re-read what you just edited. Use a helper only for jobs big enough to repay its brief. Review a helper's output before use.
<!-- CORE v4 ends. -->

---

## Project (the only part that changes)

### Project
This repository is the Knowledge Management & Learning Platform (LMS / KMS) tailored for non-traditional career switchers (social sector, policy, operations) and modern students. It implements capability-based progression across the 27-skill framework, the 10-activity pedagogical engine, an append-only Evidence Ledger, and the AXIS AI companion.

### Session start files
- PROGRESS.md (local only)
- `docs/specs/`, `docs/adr/` and `reference/` as needed

### Production-Grade Engineering Mandate

**This platform is not a toy demo; it is engineered for real production deployment.**
- Every module, interface, and adapter must be production-hardened (proper error boundaries, security guardrails, data integrity, and deterministic testing).
- Dual-target strategy: It runs as a real multi-tenant production platform while simultaneously serving as a premier, top-tier portfolio demonstration of systems architecture and AI engineering.

### Project workflow: the 6-step loop

- For each feature, subsystem, or architectural boundary, strictly follow the 6-step loop from [skills/systems-architect-mentor/SKILL.md](skills/systems-architect-mentor/SKILL.md) (local only; in a cloud session, load the `systems-architect-mentor` skill by name):
  1. **Architecture Inquiry:** Ground in the real-world operational reality, learner personas, and constraints.
  2. **ADR & Specification (SPEC) Drafting:** Record consequential decisions in `docs/adr/`, then co-author the formal markdown spec. Stop for the owner's go before step 3 (Core: Build order).
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
- **Unit Integrity:** Every unit carries 1 to 3 target skills (with goal levels: `Understand`, `Apply`, `Adapt`, `Own`) and a sequence of 2 to 5 discrete methods (ADR-0033) (beginning with `Explain` + `CO-6` concept check).
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
- Order for every platform change, feature or fix (this is not about curriculum units): Decision $\rightarrow$ ADR (`docs/adr/`) $\rightarrow$ Spec (`docs/specs/`) $\rightarrow$ Tests First $\rightarrow$ Code.
- A later step does not begin before the earlier one is done: the owner has said go on the ADR and spec, and the earlier step's tests pass.

### Project rules

- One step at a time.
- Learner-facing term (ADR-0027): stage (code, data, roadmaps, ADRs) = Module (anything a learner reads). Never rename code identifiers; change labels only.
- Answer material never goes into this repo: answer keys, hidden checks, Make tests, reference and wrong solutions, worked answers and build checks. Review docs holding answers stay git-ignored. Keep the guard test `tests/test_private_seed_answers.py`.
- Exception (owner, 2026-11-11): `tests/fixtures/answers/` holds fake answers for the made-up test items in `tests/fixtures/curriculum/` only, so CI runs without the private answers. Never put a real answer there; regenerate with `scripts/make_test_fixtures.py`. The guard test `test_the_test_fixtures_hold_only_made_up_items` enforces it.
- Changes reach main only through a GitHub PR (owner decision 2026-11-11). Work on a branch, never commit to main directly. Push the branch and open the PR only when the owner says. CI must pass; the owner merges. After a merge, pull main and push it to Entire (`origin`). Never print keys. No paid run without a printed cost estimate first; the owner runs paid steps himself.
- After substantive work, state **"Restarting review of the work"** and do a fresh pass against the approved scope, changed files, checks, and governing documents. Record findings and fixes.
- Commit only approved scope and verify the Git hash. Inspect staged paths first.

### Helpers (model split, owner 2026-11-05)

- The user-level helpers `implementer` (Sonnet) and `scout` (Haiku) are used here as the global CLAUDE.md says; the main session (Opus) orchestrates, reviews and commits.
- Every brief to a helper names this repo's rules: Decision -> ADR -> Spec -> Tests first -> Code; answer material never goes into this repo; never commit or push (the orchestrator commits); never read `.env`.
- Helpers never write or move answer material, never approve content, and never decide anything the owner decides. The orchestrator checks their work, runs the suites, then commits.

### Ownership

The owner (Asheesh Ranjan Srivastava) has final authority over direction and standing rules. Commit permission does not permit revising settled decisions. The main agent owns the active task, verification, and honest reporting.
