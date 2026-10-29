---
title: Proficiency & Progression System v1
aliases:
  - Programming-Engineering Proficiency and Progression System
type: specification
status: stable
version: "1.0"
domain: programming-engineering
scope: evidence interpretation and learning progression
tags:
  - proficiency
  - progression
  - evidence-based-learning
  - programming
  - engineering
---

# Proficiency & Progression System v1

## Purpose

This artifact determines what a learner's demonstrated performance justifies doing next in Programming/Engineering learning.

> [!principle]
> Progress when evidence is sufficient for the required depth; investigate only the smallest missing capability when it is not.

It evaluates demonstrated capability rather than lesson completion, time spent, subjective confidence, or the amount of generated output. It is deliberately lightweight: normal learning activities should produce most evidence, without turning every capability unit into a formal examination.

---

## Operating Relationship

Three concepts must remain distinct:

| Concept | Meaning | Owner |
| --- | --- | --- |
| **Target Proficiency** | The level required for a capability unit. | Roadmap |
| **Current Proficiency** | The current, evidence-supported estimate of what the learner can do. It is marked **provisional** when evidence is suggestive but incomplete, and **supported** when the available evidence justifies treating it as established for current execution. | This system / learning state |
| **Evidence** | Observable learner performance that supports or challenges the estimate. | This system / evidence ledger |

```text
Roadmap target
→ Current proficiency
→ Learning activity
→ Learner performance
→ Evidence
→ Progression decision
→ Next learning action
```

The roadmap describes the terrain. This system interprets the learner's traversal of it.

---

## Evidence Categories

Evidence is categorized by what it reveals, not assigned a numeric score.

### Explain / Reason

Shows an accurate enough mental model. Examples include explaining behavior, predicting an outcome, tracing important flow, identifying cause and effect, and separating known facts from assumptions.

### Perform / Solve

Shows usable application. Examples include modifying code, solving a problem, decomposing a requirement, using a tool effectively, or implementing a working change.

### Diagnose / Judge / Transfer

Shows capability under variation, uncertainty, or imperfect conditions. Examples include debugging an unfamiliar issue, validating a result, evaluating AI-generated work, choosing between alternatives, or applying a concept in a new context.

The third category is especially important for higher target levels, but every evidence category is evaluated relative to the competency and target depth required by the roadmap.

---

## Evidence Strength

Evidence is assessed qualitatively as **weak**, **moderate**, **strong**, or **insufficient**. The assessment is transparent and considers:

- **correctness** — whether the important understanding, decision, or result is technically sound;
- **reasoning ownership** — whether the learner supplied the key reasoning rather than merely following it;
- **transfer** — whether capability survives a meaningful variation or unfamiliar condition when required; and
- **validation** — whether the learner can establish why a result should be trusted.

| Strength | Interpretation |
| --- | --- |
| **Weak** | Success relied mainly on externally supplied reasoning, close imitation, or unexamined output. Useful learning evidence, but limited proficiency evidence. |
| **Moderate** | The learner supplied meaningful reasoning and performed correctly, with bounded instructional support or in a familiar context. Often supports Understand or Apply. |
| **Strong** | The learner supplied the important reasoning, handled relevant variation or uncertainty, and validated the result appropriately. Can support Adapt or contribute to Own. |
| **Insufficient** | The observation is too ambiguous, limited, or incomplete to support a reliable proficiency conclusion. |

> [!important]
> Evidence strength depends more on who supplied the important reasoning than on whether tools were used.

Assistance must be recorded before strength is interpreted. The detailed assistance scale and ledger fields belong to [[07 - Learning State & Evidence Ledger Specification v1]]; this system requires that the distinction between syntax/documentation lookup, a small hint, structural direction, and supplied reasoning remains visible when evidence is judged.

The same performance can be sufficient at one target level and insufficient at another. For example, accurate explanation may be strong enough when a roadmap requires **Understand**, but cannot by itself demonstrate **Adapt**.

---

## Progression Interpretation

The shared levels are defined by [[AI-Era Programming Skills Framework v1]]. This system interprets evidence against them.

| Target level | Evidence normally needed |
| --- | --- |
| **Understand** | Accurate explanation or reasoning that reconstructs the important idea rather than merely recognizes it. |
| **Apply** | Correct performance in a familiar or clearly defined situation, with the learner increasingly supplying the important reasoning. |
| **Adapt** | At least one meaningful variation, unfamiliar condition, or imperfect situation handled without the full reasoning path being supplied. |
| **Own** | Strong evidence in a sufficiently realistic context: the learner frames what is needed, directs tools, makes decisions, handles uncertainty or failure, and validates the outcome with minimal instructional scaffolding. |

Increasing progression means more realism, meaningful variation, less instructional scaffolding, and greater technical responsibility. It does **not** require avoiding professional tools.

---

## Progression Decisions

Only four substantive decisions are used. Each represents a practical next action.

### Progress

Current evidence is sufficient for the roadmap's required depth. Move to the next capability or integration point. Progress does not claim maximum mastery.

### Accelerate

Prior or current evidence is clearly stronger than the current requirement. Compress or skip detailed instruction and move to a more appropriate challenge.

### Strengthen

Capability is present, but a specific dimension is fragile or missing. Target the smallest gap rather than restarting the whole topic.

Examples: the learner can explain but not modify; can implement but not validate; can work with familiar examples but not variation; or depends too heavily on hints.

### Rebuild

The underlying mental model is unreliable enough that targeted practice alone will not resolve the problem. Return briefly to foundational understanding, then re-attempt application.

Use Rebuild when incorrect reasoning recurs, apparent success is mostly imitation, or a prerequisite gap repeatedly undermines later work.

### Undecided

**Undecided** is an operational state, not a fifth progression outcome. Use it when current evidence is insufficient or contradictory and a decision would be premature. Gather the smallest additional evidence needed rather than inventing certainty.

> [!principle]
> Mixed capability is normal. Find the smallest broken link; do not collapse evidence into pass or fail.

---

## Current-Proficiency Check

A current-proficiency check is not a placement exam. It is the smallest representative demonstration needed to decide whether to accelerate, strengthen, rebuild, or begin new learning.

For a meaningful competency unit:

1. **Sample** with one representative explanation, prediction, modification, interpretation, or task.
2. **Probe** with one meaningful variation only if the first response suggests stronger capability or leaves uncertainty.
3. **Decide** once evidence is sufficient; if a clear gap appears, stop probing and address that gap.

Checks normally occur at the competency-unit level, not for every tiny topic or as one large diagnostic. They should be re-informed naturally by subsequent learning performance.

---

## Evidence-Interpretation Safeguards

- **Observable performance only.** Explanations or solutions supplied entirely by ChatGPT are learning resources, not learner evidence.
- **No automatic overwrite.** One weak attempt does not erase an established proficiency estimate; one lucky answer does not justify a large promotion.
- **Recent relevant evidence carries forward.** Do not repeatedly retest capability that has already been demonstrated recently and remains relevant.
- **Contradictory evidence creates uncertainty.** Retain the existing estimate as provisional, record the conflict, and probe only if a decision is needed.
- **Syntax lookup is not disqualifying.** Looking up exact syntax or documentation does not invalidate evidence when the learner still owns the relevant intent, reasoning, decision, and validation.

These safeguards preserve both speed and trustworthy interpretation.

---

## AI Assistance and Proficiency Evidence

AI and other professional tools may contribute syntax, boilerplate, documentation, searches, alternatives, tests, debugging hypotheses, or critique. This can coexist with strong learner evidence when the learner retains the ability to frame the problem, understand important behavior, choose an approach, challenge suggestions, and validate the result.

Evidence is weak when a tool supplies almost the entire cognitive path and the learner mostly accepts it, even if the final software works.

> [!question]
> If the tool disappeared at this reasoning step, would the learner know what question needs answering next?

The learner need not know every syntax detail without help. They should increasingly know what they are trying to establish, what evidence is needed, and what decision follows.

---

## Boundaries with Other Artifacts

This artifact owns evidence categories and strength interpretation, current-proficiency estimation, proficiency checks, and Progress / Accelerate / Strengthen / Rebuild decisions.

It does **not** own:

- competency definitions, the progression vocabulary, or the durable AI-ownership boundary — [[AI-Era Programming Skills Framework v1]];
- activity design, activity dosage, or scaffolding choices — [[Learning Method v2]];
- capability-unit scope, target proficiency, prerequisites, or sequencing — [[05 - Programming-Engineering Roadmap Design Rules v1]] and subject roadmaps;
- evidence-ledger schema, learning-state fields, or durable record-selection rules — [[07 - Learning State & Evidence Ledger Specification v1]] and [[06 - Learning Record System v1]];
- the full learning-cycle workflow — [[11 -Learning Execution Blueprint v1]].

---
## Artifact Relationships

### Governing / Upstream
- [[01 - Learning System Architecture v1]]
- [[AI-Era Programming Skills Framework v1]]
- [[05 - Programming-Engineering Roadmap Design Rules v1]]

### Learning Input
- [[Learning Method v2]]

### Operational Companion
- [[07 - Learning State & Evidence Ledger Specification v1]]

### Durable-History Output
- [[06 - Learning Record System v1]]

### Downstream Execution
- [[11 - Learning Execution Blueprint v1]]

---

## Artifact Status

**Stable v1.** This is the evidence and progression system for Programming/Engineering learning. It should evolve only when needed to clarify evidence interpretation or actionable progression, without introducing grading bureaucracy or duplicating related artifacts.
