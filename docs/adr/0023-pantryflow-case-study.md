# ADR 0023: One Case Study for the Whole Path (PantryFlow)

- **Status:** Proposed (2026-11-04)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-04
- **Governed by:** AGENTS.md section 4 (the cumulative project spine), Python Subject Roadmap v4, `docs/architecture/02-operational-narrative-spine-79-units.md`

---

## 1. Context & Problem Statement

Every exercise is meant to grow one operational workflow (ingress, transformation, egress). Until 2026-11-04 the platform used a 78-unit case study written for an earlier roadmap, with an intake desk story. Python v4 has a different unit list and order, and the owner rewrote the case study as a food pantry network (PantryFlow), so the old story no longer matched the units.

---

## 2. Decision

1. **PantryFlow is the one case study.** `docs/architecture/02-operational-narrative-spine-79-units.md` is the source for every unit's scenario, from the first registration desk to the RAG copilot. The owner edits it; agents follow it.
2. **The case study follows the roadmap.** Its unit table uses Python v4's units and order. When the roadmap changes, the table changes with it, never the other way round (the Lock Rule).
3. **The old 78-unit case study is removed** (commit 725b88d), and Stage 0 was re-themed to PantryFlow (e060919).
4. **Make outcomes use the story.** A Make step's wording in the roadmap names the PantryFlow task (d3c0f8c).

---

## 3. Consequences

### Positive
- One story a learner understands in seconds, from Stage 0 to the capstone.
- Seeds, builds and Make steps can be checked against one table.

### Negative / Trade-offs
- Each new unit's content must be written to fit the story, which constrains examples.
- The case study is a long owner document; a unit added to the roadmap needs a matching row.
