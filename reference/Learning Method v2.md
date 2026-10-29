---
title: Learning Method v2
aliases:
  - Programming-Engineering Learning Method v2
type: specification
status: approved
version: "2.0"
created-date: 2026-10-17
supersedes: "Programming-Engineering Learning Method v1 (now in history/, superseded 2026-10-17)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills)"
domain: programming-engineering
scope: adaptive technical learning activities
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-17 at Asheesh's direction, from Learning Method v1 and the gap table in `docs/history/2026-10-17-method-framework-sync-step1-superseded.md`. Approved by Asheesh on 2026-10-17. The app and some docs still name Method v1 until they are updated (see docs/tasks.md, row SYNC-1).

# Learning Method v2

## Purpose

This document defines how a learner is taught and how skills are developed: the learning activities, how they are chosen, how scaffolding changes, and how a unit begins by making sure the concept is understood. It serves [[AI-Era Programming Skills Framework v1]], which owns the skills, levels and evidence types.

> [!principle]
> Use the smallest combination of activities that develops the unit's skills at the required level. **Every unit starts by making sure the learner understands what the topic is.**

## What changed from v1

| Change | Why |
| --- | --- |
| Activity **Understand** renamed **Explain**. | "Understand" is also the first level; one word had two meanings. |
| New activities **Specify** and **Direct**. | Seven skills (SP-1, SP-2, SP-4, DE-2 to DE-5) had no activity that developed them. |
| **Debug & Validate** and **Evaluate** widened. | VE-3 now covers improving by measurement; Evaluate now covers specs, prompts, and access and trust. |
| Every unit opens with **Explain** and a **concept check** (CO-6), with a **soft gate**. | Nothing checked that the concept itself was understood. |
| Activities are fixed **by unit and target skill**, not chosen by situation. | Situation-based choice was subjective and could not be tracked or reproduced. |
| Each unit has **one to three target skills**. | A unit with many targets cannot be judged clearly. |
| Alignment is by Framework **skill**, not the old five competencies. | The Framework supersedes Competency Model v1. |
| A **session habits** section. | The three always-on habits (H-1 to H-3) need a routine; they are not tied to units. |

---

## The ten activities

| Activity | The learner... | Use when |
| --- | --- | --- |
| **Explain** | Forms an accurate mental model of the unit's concept and says it in their own words, with their own example and a non-example. Uses explanation, worked examples, diagrams or reading code. | Always first in a unit. Longer when the concept is new, foundational or misunderstood. |
| **Predict** | Commits to what will happen before seeing the result. | State, branching, evaluation order, side effects or misconceptions matter. Skip for trivial work. |
| **Trace** | Follows execution, state or data step by step. | To answer where a value came from, why a branch ran, how an error propagated. A tool, not a ritual. |
| **Specify** | Clarifies a requirement and writes a spec precise enough to build and test from, or reviews a spec or prompt for missing details, before code exists. | Before building anything non-trivial; when a tool produced the wrong thing and the cause may be the spec. |
| **Decompose** | Splits a requirement into small pieces, each with a clear input, output and check. | Practical features and problems. |
| **Modify** | Changes existing code, keeping or deliberately changing behaviour, in small reversible steps. | Bridges understanding and production: extend, repair, adapt, refactor. |
| **Debug & Validate** | Diagnoses wrong behaviour, or improves working code by one change and one measurement at a time, then proves the result. | Whenever correctness or performance is uncertain. |
| **Build** | Creates a meaningful solution, integrating libraries and components through their documentation. | Selectively, when synthesis or less-scaffolded decisions give evidence that isolated work cannot. |
| **Evaluate** | Judges a solution, spec, prompt or proposal: accept, change or reject with a reason; compares alternatives by trade-off; checks access and trust. | When reviewing AI output, choosing between options, or granting a tool access. |
| **Direct** | Works with a tool or source on purpose: asks it to explain rather than do, decides what to delegate and what to own, picks the right source, limits its access. | Whenever AI, documentation or a person is part of the work. |

The activities are a toolkit, not stages. Only **Explain first** is a fixed rule.

---

## Unit rule

Each unit in a subject roadmap carries:

- **One to three target skills**: at least one, at most three, set by the unit's scope. The target skills are the ones the unit develops and is judged on.
- A **goal level** for each target skill (the roadmap's old "target").
- A **Methods** list: Explain first, then the main activity for each target skill (see the table below), plus a helper activity only where the roadmap names it.

Other skills may come up during the work as part of the process. They are not targets: they get no goal level from this unit and no progression decision.

The **CO-6 concept check** happens in every unit as part of Explain. It counts as a target skill only when the unit lists it among its one to three.

The roadmap owns each unit's list. This Method owns the activity vocabulary and the skill-to-activity table.

## Concept check and soft gate

At the end of Explain, the learner does a short **CO-6 check**: explain the concept in their own words, give an example and a non-example, and spot what is wrong in a plausible but incorrect explanation. The learner's own words are the evidence; an explanation supplied by a tool or the tutor is not.

| Result | What happens |
| --- | --- |
| **Solid** | Continue to the unit's other activities. |
| **Shaky** | The tutor explains again with a different example and offers one more check. The learner may continue. |
| **Skipped or still shaky** | The learner continues. The result is recorded and stays visible. If later work on the unit fails twice, the tutor first returns to the concept before changing anything else. |

The gate is **soft**: it never blocks. Whether a shaky concept affects progression decisions is for the Proficiency & Progression System to say; an amendment is proposed separately.

---

## Which activities develop which skills

| Skill | Main activity | Also helps |
| --- | --- | --- |
| CO-1 Predict before running | Predict | Trace |
| CO-2 Trace state | Trace | |
| CO-3 Read unfamiliar code | Explain | Trace, Evaluate |
| CO-4 Explain the purpose | Explain | |
| CO-5 Map dependencies and data flow | Explain | Trace |
| **CO-6 Explain the concept** | Explain | |
| SP-1 Clarify before building | Specify | Decompose |
| SP-2 Write a buildable spec | Specify | Decompose |
| SP-3 Decompose | Decompose | |
| SP-4 Spot the missing detail | Specify | Evaluate |
| BU-1 Adapt existing code | Modify | |
| BU-2 Refine a draft to the spec | Modify | Evaluate |
| BU-3 Integrate libraries and components | Build | Modify, Direct |
| BU-4 Keep code maintainable | Modify | Evaluate |
| BU-5 Small, reversible changes | Modify | |
| VE-1 Write checks that catch a wrong answer | Debug & Validate | |
| VE-2 Find the bug in code you did not write | Debug & Validate | Evaluate |
| VE-3 Investigate by hypothesis | Debug & Validate | |
| VE-4 Read error messages | Debug & Validate | Trace |
| VE-5 Prove the fix | Debug & Validate | |
| VE-6 Check beyond "it runs" | Debug & Validate | |
| DE-1 Accept, change or reject | Evaluate | |
| DE-2 Ask the tool to explain, not to do | Direct | |
| DE-3 Decide what to delegate | Direct | |
| DE-4 Consult the right source | Direct | |
| DE-5 Bound authority and trust | Direct | Evaluate |
| DE-6 Compare alternatives by trade-off | Evaluate | |

Activities can have secondary benefits; the method does not assume every activity develops every skill.

## How activities are chosen

Activities follow the **unit**, not the situation. A unit's topic and target skills fix its Methods list: Explain, then the main activity of each target skill from the table above. The roadmap's list is the single source; the tutor does not choose activities by judgment.

What does change, and only from evidence:

- the amount of scaffolding, by the target skill's goal level (next section);
- repeating or re-teaching the unit's listed activities when the Proficiency & Progression System decides Strengthen or Rebuild;
- going back to the concept check first after two failed attempts on a task in the unit.

Illustrative examples (the real lists belong to the roadmap):

| Unit | Target skills | Methods |
| --- | --- | --- |
| PY-2.2 Iteration | CO-2, VE-2, VE-5 | Explain → Trace → Debug & Validate |
| PY-1.5 Choosing structures | DE-6 | Explain → Evaluate |
| PY-3.5 Decompose a requirement into functions | SP-2, SP-3 | Explain → Specify → Decompose |

## Scaffolding across levels

Levels are the Framework's: Understand → Apply → Adapt → Own. The shift is from high to low **instructional scaffolding**, not from tool use to tool abstinence.

| Level | Emphasis | Typical scaffolding |
| --- | --- | --- |
| **Understand** | A correct mental model. | Explanation, worked examples, focused prompts, partial traces, hints. |
| **Apply** | Use it in familiar situations. | Clear requirements, incomplete code, fewer hints, an attempt before help. |
| **Adapt** | Variation, unfamiliar or AI-written code, imperfect requirements. | Unfamiliar code, incomplete requirements, review-style support. |
| **Own** | Responsibility for realistic outcomes. | Problem and constraints only; the learner directs decomposition, tools, implementation and verification. |

Step-by-step instructions, pre-made decomposition, instant answers, many hints and complete starter solutions recede as capability grows. Documentation, AI, IDEs, tests, debuggers, search and libraries stay normal professional tools.

## Session habits

Every session, whatever the unit, the tutor does three small things. They capture the Framework's habits and need no extra unit.

- **H-2 Calibrate:** before each check runs, ask "how sure are you?" and record it.
- **H-3 Think first:** before giving help, ask for the learner's own attempt or guess; record whether it came unprompted.
- **H-1 Fact vs assumption:** when the learner explains, ask which parts they checked and which they are guessing.

## AI-assisted learning posture

AI may be explainer, questioner, collaborator, reviewer or tool, depending on the activity and scaffolding.

- Explain directly when missing information blocks reasoning.
- Invite an attempt first when the attempt reveals the learner's mental model.
- Generate code freely when code generation is not what the activity develops; do not supply the reasoning or implementation the activity is meant to develop.
- Challenge plausible but weak, incomplete or suspicious solutions when evaluation has learning value.
- Critique reasoning and verification, not only final answers.
- Raise assistance when productive struggle has ended: attempt → hint → stronger hint → explanation.

Assistance stays visible to later evidence interpretation. The method does not score it; it only avoids treating a heavily guided activity as independent performance.

> [!important]
> AI assistance can support learning, but AI output alone is never evidence of learner capability.

## Boundaries

This document owns the activities, their selection, scaffolding direction, the concept check and soft gate, and the session habits routine.

It does **not** own:

- skills, levels, evidence types, the tool-ownership boundary: [[AI-Era Programming Skills Framework v1]];
- evidence strength, current proficiency, progression decisions: [[04 - Proficiency & Progression System v1]];
- subject scope, prerequisites, sequencing, each unit's Methods list and goal level: the subject roadmaps and their skill maps;
- record schemas and ledgers: the Learning Record and Evidence Ledger specs;
- the operational learning cycle: the Learning Execution Blueprint.

## Decided and still open

Decided by Asheesh 2026-10-17: the names Explain, Specify and Direct; one to three target skills per unit, others only as part of the process; activities follow unit and skill, not situation; no change to the Proficiency & Progression System.

Approved 2026-10-17: the concept check runs in every unit as part of Explain and counts as a target only when the unit lists it.

Still to do: update the MVP Scope v0.2, the architecture spec and the app (26-skill expectation, Method v1 wording). Tracked as SYNC-1 in docs/tasks.md.
