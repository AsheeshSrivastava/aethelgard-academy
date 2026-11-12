# ADR 0032: Varied concept prompts and unseen Cold Check items

- **Status:** Proposed. Owner decision 2026-11-12: backlog item 3, scope (a), "engine first, then content".
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-12
- **Governed by:** ADR-0016 (amendment G: a concept check carries `<unit>/explain/v<n>`), ADR-0019 (spaced review), ADR-0021 (private answer material), ADR-0026 (AI judgement)
- **Spec:** SPEC-18 section 1, SPEC-12 (explain), SPEC-16 section 2

---

## 1. Context & Problem Statement

After a retry or a unit reset, a learner meets the items they already answered:

- **Concept check.** A unit has one prompt. A reset serves the same prompt, so a second Solid answer can be memory, not understanding. Amendment G (ADR-0016) gave each prompt an id (`v1`, `v2`...) so repeats count once, but a unit still cannot hold a second prompt.
- **Unit Cold Check.** `cold_round` always takes the first approved items per skill. After a failed round, the failed item comes back unchanged, so a 4-option item becomes a 1-in-3 guess. After a reset, the learner gets the items they already passed.

The stage review already avoids this: "each failed item is replaced by the next unseen item for that unit and skill" (SPEC-16 section 3.3). The unit Cold Check should follow the same rule.

## 2. Decision

### 2.1 Several concept-check prompts per unit
1. `meta.json` `concept_check` keeps `prompt` (this is `v1`) and may add `more_prompts: [str]` (these are `v2`, `v3`, in order). At most 3 prompts in total.
2. Each prompt has its own private rubric. `concept_check.json` keeps `ideas` for `v1` and may add `variants: {"v2": {"ideas": [...]}, "v3": {...}}`. A prompt with no rubric is not judged (as today), and the warning `concept-check-rubric-missing` names the prompt.
3. **Serving.** The Explain step serves the lowest-numbered prompt that the learner has not answered since their last unit reset. When they have answered every prompt, it serves the one answered longest ago.
4. **Answering.** `POST /api/v1/explain` takes an optional `exercise_id` (`<unit>/explain/v<n>`). It judges against that prompt and its rubric, and writes it on the evidence. A missing id means `v1`, so older clients keep working. An id that names no prompt of the unit is `422`.

### 2.2 Unit Cold Check items the learner has not passed
1. **The round prefers fresh items.** For each target skill, the round takes the approved items in this order: items the learner has never answered, then items they failed, then items they passed. The 3-to-5 size and skill order (SPEC-16 section 2) are unchanged.
2. **A retry replaces a failed item.** After a failed round, each failed item is replaced by the next item for its skill in that order. The item just failed comes back only when the skill has no other approved item outside the round. The round keeps its size, and each skill keeps its number of slots.
3. **After a reset**, items the learner passed before the reset are taken last. History comes from the learner's Cold Check evidence in the ledger (the newest answer per item decides passed or failed). Nothing is written or changed to read it. Items answered in the current round keep their place, so a round can always finish. Cold Check feedback shows the round the learner last answered.
4. A unit with one approved item per skill behaves exactly as today.

## 3. Alternatives considered

- **Random choice of item or prompt.** Rejected: grading and tests must stay deterministic (ADR-0016). A fixed order over the learner's history gives variety without randomness.
- **Never repeat, and block when items run out.** Rejected: missing content must never lock a learner out (SPEC-16 section 3.4). Repeats are allowed as a last resort.
- **One file per prompt rubric** (`concept_check.v2.json`). Rejected: one file per unit keeps the private repo simple, and `variants` is an optional addition.

## 4. Consequences

- Variety now depends on content: a unit gains it only when it has more than one prompt, or more than one approved Cold Check item per skill. Stage 0 content follows in its own PRs.
- The concept-check id from amendment G is now real per prompt, so "repeats count once" works across prompts.
- The Explain step's served exercise names its prompt id, and the frontend sends it back.
