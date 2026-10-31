---
title: Software Design / OOD / LLD Roadmap v2
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "2.0"
supersedes: "Software Design / OOD / LLD Roadmap v1 (38 units, Competency Model codes)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Supporting roadmap, slotted into the Python and Backend path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **The scope (which units are kept, merged or dropped) and their place in the path were approved by Asheesh on 2026-10-31.** Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2, and not yet reviewed by Asheesh. Detailed teaching tasks per unit are still to be written. The v1 file stays in `reference/` until it is moved to history.

# Software Design / OOD / LLD Roadmap v2

**Purpose.** Detailed design judgement: framing a design problem, boundaries and dependency direction, SOLID as change reasoning, a small set of patterns, modelling, and low-level design. Responsibilities, composition and refactoring stay in the Python roadmap.

## What changed from v1

- **Converted to the AI-Era Programming Skills Framework.** Each unit has one to three target skills from the 27, each with a goal level, a one-line concept for Explain and the CO-6 check, a Methods list (Explain first, then the main activity of each target skill) and an outcome line that can be graded without AI. The old five competencies are gone.
- **8 units replace 27 v1 units.** Small v1 units were merged into units the size of a Python unit; each unit lists the v1 units it replaces. Dropped: Already in Python: SD-1.1 to 1.4 (responsibilities and cohesion: PY-3.4, 3.5, 5.2, 12.3), SD-2.2, 3.1, 3.3 (domain modelling and composition: PY-6.7), SD-7.2 (testability: PY-9.4), SD-7.3 (refactoring: PY-12.5). Supporting: SD-6.1. SD-8.4 becomes the course project.
- **Entry rule (Learning Method Amendment A1).** No skill enters the learning path above Apply, and no skill rises more than one level from one unit to the next. Levels here are set for where these units sit in the path, after the Python units that precede them.
- **Slotted into the path.** Units are taught where the path first needs them, not as a separate course run after Python (see "Place in the path").
- **New unit IDs.** IDs restart at `SD-0.1`. The "Replaces (v1)" field maps each one to the old IDs.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | Design reasoning | after Python Stage 6 (classes and object design), before Stage 7 | 4 |
| 1 | Patterns and low-level design | after Python Stage 12, before Stage 13 | 4 |

**Course project.** SD v1 Stage 8 integration (SD-8.4) becomes a course project at maturity P2: a low-level design for one relief-centre subsystem, built and reviewed under a changed requirement.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | SD-0.1 Framing a design problem and its trade-offs | 0 | SP-1 (Adapt), DE-6 (Adapt) | Explain → Specify → Evaluate |
| 2 | SD-0.2 Interfaces, contracts and dependency direction | 0 | SP-2 (Adapt), BU-4 (Adapt), CO-5 (Adapt) | Explain → Specify → Modify |
| 3 | SD-0.3 SOLID as change reasoning | 0 | DE-1 (Adapt), BU-4 (Adapt) | Explain → Evaluate → Modify |
| 4 | SD-0.4 Substitutability: Liskov and interface segregation | 0 | CO-1 (Adapt), VE-2 (Adapt) | Explain → Predict → Debug & Validate |
| 5 | SD-1.1 Pattern intent and a small core set | 1 | DE-6 (Adapt), BU-3 (Adapt) | Explain → Evaluate → Build |
| 6 | SD-1.2 Pattern overuse and design smells | 1 | CO-3 (Adapt), DE-1 (Adapt) | Explain → Evaluate |
| 7 | SD-1.3 Modelling a workflow or state machine | 1 | SP-2 (Adapt), CO-5 (Adapt), VE-1 (Adapt) | Explain → Specify → Debug & Validate |
| 8 | SD-1.4 Producing and defending a low-level design | 1 | SP-3 (Adapt), DE-6 (Adapt), BU-2 (Adapt) | Explain → Decompose → Evaluate → Modify |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | SD-0.1 Framing a design problem and its trade-offs | implementation versus detailed design versus system architecture; requirements, constraints and change pressures; consequences and trade-offs; writing down a decision |
|  | SD-0.2 Interfaces, contracts and dependency direction | minimal interfaces; behavioural contracts; information hiding; dependency direction; dependency injection as a design tool; avoiding over-layering |
|  | SD-0.3 SOLID as change reasoning | single responsibility as one reason to change; open/closed without premature extension points; dependency inversion; simplicity versus duplication versus abstraction |
|  | SD-0.4 Substitutability: Liskov and interface segregation | behavioural subtyping; preconditions and postconditions; the Liskov test; caller-specific interfaces; Protocols as narrow interfaces |
| 1 | SD-1.1 Pattern intent and a small core set | strategy; adapter; factory; observer; decorator as a pattern versus Python decorators; pattern intent before pattern name |
|  | SD-1.2 Pattern overuse and design smells | speculative generality; needless indirection; god classes; shotgun surgery; duplication; necessary design debt versus premature cleanup |
|  | SD-1.3 Modelling a workflow or state machine | state ownership; valid transitions; state diagrams; sequence of a workflow; keeping models small and in step with the code; Enum for states |
|  | SD-1.4 Producing and defending a low-level design | from requirement to responsibilities; module and class sketch; interfaces between parts; implementing a slice; reviewing a design under a changed requirement |

## Unit details

### Stage 0: Design reasoning

#### SD-0.1 Framing a design problem and its trade-offs

- **Objective:** Can frame a design problem from requirements, constraints and likely changes, and compare designs by their consequences.
- **The concept (Explain):** Design is choosing what will be easy to change and what will be hard, on purpose.
- **Target skills:** SP-1 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-1: lists the requirements, constraints and likely changes for a relief-centre feature before any code, and states assumptions. DE-6: compares two designs by what each makes easy and hard to change, and chooses.
- **Topics:** implementation versus detailed design versus system architecture; requirements, constraints and change pressures; consequences and trade-offs; writing down a decision
- **Prerequisites:** PY-6.7 | **Importance:** Foundational | **Replaces (v1):** SD-0.1, SD-0.2, SD-0.3

#### SD-0.2 Interfaces, contracts and dependency direction

- **Objective:** Can design a minimal interface around required behaviour, keep volatile details behind it, and point dependencies toward stable policy.
- **The concept (Explain):** Callers should depend on what they need, not on how it is done.
- **Target skills:** SP-2 to Adapt; BU-4 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Specify → Modify
- **Outcome (measured at unit end):** SP-2: writes a minimal interface contract for a notifier, with examples. BU-4: refactors a module so business rules no longer import the database client, using dependency injection, without changing behaviour. CO-5: sketches the dependency direction before and after.
- **Topics:** minimal interfaces; behavioural contracts; information hiding; dependency direction; dependency injection as a design tool; avoiding over-layering
- **Prerequisites:** SD-0.1, PY-6.6 | **Importance:** Core | **Replaces (v1):** SD-1.5, SD-2.3, SD-2.4, SD-2.5, SD-2.6

#### SD-0.3 SOLID as change reasoning

- **Objective:** Can use single responsibility, open/closed and dependency inversion to judge a design by the cost of a real change.
- **The concept (Explain):** SOLID principles are tests of how a design copes with change, not rules to apply everywhere.
- **Target skills:** DE-1 to Adapt; BU-4 to Adapt
- **Methods:** Explain → Evaluate → Modify
- **Outcome (measured at unit end):** DE-1: judges three AI-proposed refactors against single responsibility, open/closed and dependency inversion, and accepts, changes or rejects each with a reason. BU-4: applies the one that removes a real duplication or change cost.
- **Topics:** single responsibility as one reason to change; open/closed without premature extension points; dependency inversion; simplicity versus duplication versus abstraction
- **Prerequisites:** SD-0.2 | **Importance:** Core | **Replaces (v1):** SD-4.1, SD-4.2, SD-4.5, SD-4.6

#### SD-0.4 Substitutability: Liskov and interface segregation

- **Objective:** Can test whether a subtype can stand in for its parent, and split an interface that forces callers to depend on what they do not use.
- **The concept (Explain):** A subtype is safe only if every caller of the parent still works with it.
- **Target skills:** CO-1 to Adapt; VE-2 to Adapt
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts which caller breaks when a subclass is swapped in. VE-2: finds the substitution bug in an AI-written subclass and names the call that exposes it.
- **Topics:** behavioural subtyping; preconditions and postconditions; the Liskov test; caller-specific interfaces; Protocols as narrow interfaces
- **Prerequisites:** SD-0.2, PY-6.5 | **Importance:** Core | **Replaces (v1):** SD-3.2, SD-4.3, SD-4.4

### Stage 1: Patterns and low-level design

#### SD-1.1 Pattern intent and a small core set

- **Objective:** Can recognise the problem a pattern solves before naming it, and apply strategy, adapter, factory and observer where they help.
- **The concept (Explain):** A pattern is a known answer to a recurring design problem; the problem comes first.
- **Target skills:** DE-6 to Adapt; BU-3 to Adapt
- **Methods:** Explain → Evaluate → Build
- **Outcome (measured at unit end):** DE-6: chooses between a strategy and a plain if-chain for a rule set that changes monthly, with the reason. BU-3: builds an adapter so two data sources share one interface, and handles what each returns and how each fails.
- **Topics:** strategy; adapter; factory; observer; decorator as a pattern versus Python decorators; pattern intent before pattern name
- **Prerequisites:** SD-0.3, PY-12.5 | **Importance:** Core | **Replaces (v1):** SD-5.1, SD-5.2

#### SD-1.2 Pattern overuse and design smells

- **Objective:** Can spot accidental complexity and design smells through the cost of change, and decide what to simplify now and what debt to keep.
- **The concept (Explain):** A smell is a sign that a common change is harder than it should be.
- **Target skills:** CO-3 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-3: reads an over-patterned module and names the smells and what each costs. DE-1: decides what to simplify and what to leave, with reasons.
- **Topics:** speculative generality; needless indirection; god classes; shotgun surgery; duplication; necessary design debt versus premature cleanup
- **Prerequisites:** SD-1.1 | **Importance:** Core | **Replaces (v1):** SD-5.3, SD-7.1, SD-7.4

#### SD-1.3 Modelling a workflow or state machine

- **Objective:** Can model a workflow or state-dependent behaviour so that its rules are explicit and checkable.
- **The concept (Explain):** When behaviour depends on state, write the states and allowed moves down before writing code.
- **Target skills:** SP-2 to Adapt; CO-5 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Specify → Debug & Validate
- **Outcome (measured at unit end):** SP-2: models a case's states and allowed transitions (Pending, Verified, Disbursed, Rejected). CO-5: sketches the workflow between components. VE-1: writes checks that reject illegal transitions they were not shown.
- **Topics:** state ownership; valid transitions; state diagrams; sequence of a workflow; keeping models small and in step with the code; Enum for states
- **Prerequisites:** SD-0.2, PY-6.9 | **Importance:** Core | **Replaces (v1):** SD-2.1, SD-6.2, SD-6.3, SD-6.4

#### SD-1.4 Producing and defending a low-level design

- **Objective:** Can produce a low-level design for a bounded requirement, implement a slice without losing its boundaries, and defend it under change.
- **The concept (Explain):** A low-level design names the parts, their jobs and their interfaces, so the build can be split and checked.
- **Target skills:** SP-3 to Adapt; DE-6 to Adapt; BU-2 to Adapt
- **Methods:** Explain → Decompose → Evaluate → Modify
- **Outcome (measured at unit end):** SP-3: produces a design (modules, classes, interfaces) for a bounded requirement, each part checkable alone. DE-6: defends one decision when the requirement changes. BU-2: brings an AI-drafted slice up to the design, mapping each edit to a design line.
- **Topics:** from requirement to responsibilities; module and class sketch; interfaces between parts; implementing a slice; reviewing a design under a changed requirement
- **Prerequisites:** SD-1.1, SD-1.3 | **Importance:** Core | **Replaces (v1):** SD-8.1, SD-8.2, SD-8.3

## Skill coverage (target skills, this roadmap)

8 units carry 19 targets: Adapt 19. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-1 | 1 | Adapt |
| CO-3 | 1 | Adapt |
| CO-5 | 2 | Adapt |
| SP-1 | 1 | Adapt |
| SP-2 | 2 | Adapt |
| SP-3 | 1 | Adapt |
| BU-2 | 1 | Adapt |
| BU-3 | 1 | Adapt |
| BU-4 | 2 | Adapt |
| VE-1 | 1 | Adapt |
| VE-2 | 1 | Adapt |
| DE-1 | 2 | Adapt |
| DE-6 | 3 | Adapt |

## Decisions

1. **Scope, cuts and placement** approved by Asheesh on 2026-10-31 (review "New roadmaps: framework fit and scope").
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Stage builds:** every stage needs one build (owner rule). Not yet written for this roadmap.
