# ADR 0017: Batch Exercise Variant Generation from Curator Seeds

- **Status:** Accepted (2026-10-30)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-30
- **Governed by:** ADR-0008 (lesson packages), ADR-0010 (local-first LLM), ADR-0016 (Cold Check), SPEC-12 section 4

---

## 1. Context & Problem Statement

Every activity except Explain has a Regenerate button, so learners need many exercise variants. Hand-writing 10–15 per activity is roughly 4,000+ exercises for the Python course alone. Generating a variant live with an LLM on every click is slow, costs money per learner and per click, and puts unchecked content in front of learners.

---

## 2. Decision

1. **Seeds:** the curator writes 1–3 seed exercises per activity in the unit package (prompt, reference solution, hidden checks, activity, skill, level).
2. **Offline batch generation:** a separate generation pipeline (`lms variants generate --unit <id>`), not the learner-facing AXIS, writes N variants per seed in one batch. It runs ahead of time, never on a learner's click.
3. **Automatic verification (every variant, no exceptions):**
   - The sandbox runs the variant's reference solution against its hidden checks; it must pass.
   - Deterministic checks: same activity, skill and level as the seed; required format fields present; uses only concepts introduced up to this unit; no near-duplicate of an existing variant.
   - A wrong-answer probe: at least one plausible wrong solution must fail the checks, so checks are not trivially passable.
   - Variants failing any check are discarded and logged.
4. **Pool:** verified variants are stored in the unit's variant pool. Regenerate serves from the pool instantly (no LLM call at learner time). When a learner exhausts the pool, the oldest-seen variant is reused.
5. **Curator control:** the curator can spot-check, reject or pin any variant. Variants used in the **Cold Check** must be curator-approved.
6. **Cost rule (AGENTS.md):** the command prints a cost estimate first and runs only after confirmation; the owner runs paid batches himself. With the local LLM (ADR-0010) the cost is zero. CI uses `MOCK_AI=true`.

---

## 3. Consequences

### Positive
- AI cost is paid once per pool, not per learner click; Regenerate latency is a database read.
- Learners never see an unverified exercise; Cold Check content is human-approved.

### Negative / Trade-offs
- Pools must be regenerated when a seed changes.
- The sandbox proves correctness, not teaching quality; curator spot-checks stay necessary.
