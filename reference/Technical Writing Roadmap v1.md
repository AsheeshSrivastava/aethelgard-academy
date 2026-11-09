---
title: Technical Writing Roadmap v1
created-date: 2026-11-08
status: scope-approved
approved-date: 2026-11-08
version: "1.0"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendments A1 (2026-10-31) and A2 (2026-11-09)"
roadmap-role: "Supporting roadmap, slotted into the Python path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-11-08 at Asheesh's direction. **The scope (course name, three stages of two units, what each unit teaches, and their place in the path) was approved by Asheesh on 2026-11-08** (proposal: `docs/proposals/technical-writing-course-2026-11-08.md`). Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2 with Amendment A1, and **not yet reviewed by Asheesh**. Learners see each stage as a module ("TW 0"), ADR-0027.

# Technical Writing Roadmap v1

**Purpose.** The writing a working engineer reviews every week: READMEs, decision records (ADRs) and specs. AI drafts these documents; the learner learns what a good one contains, finds what an AI draft gets wrong, checks its claims against the running code, and directs AI to draft one for their own work.

## Why this roadmap exists

- The Python Stage 0 build asks for a README that no unit teaches; AXIS could only ask questions about it.
- No roadmap teaches READMEs or ADRs. Python teaches function specs only (SP-1 to SP-4 from PY-3.4).
- AI is central to how documents are written now. Reviewing a draft is the skill, and it must be taught before it is tested.

## Teaching pattern (every stage)

1. A good example and a checklist.
2. Find the planted mistakes in an AI draft.
3. Check the draft's claims against reality: run it.
4. Direct AI to draft one for your own work, then review and fix it.

Scaffolding fades: in Stage 0 the learner is told how many mistakes are planted; in Stage 2 they are not.

**README checklist (Stage 0).** 1. What it does. 2. What you need first (Python, uv, setup). 3. How to run it (the exact command). 4. A sample run (real input and real output). 5. Limits.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | READMEs | in Python Stage 0, after PY-0.3 and before the Stage 0 build; **recommended, not a prerequisite** for the build | 2 |
| 1 | Decision records | after Python Stage 10, before Stage 11 | 2 |
| 2 | Specs | after Python Stage 12 (and its slotted units), before Stage 13 | 2 |

**Course project.** No separate project. Documents attach to the stage builds: the Stage 0 build's README; a short ADR in every build from Python Stage 11; the Stage 13 build starts from a spec.

**Built now.** Stage 0 is built first. Stages 1 and 2 are roadmap text now and are built after the 5 Dec feature freeze.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | TW-0.1 What a README is for | 0 | CO-4 (Understand), SP-4 (Understand) | Explain → Evaluate → Specify |
| 2 | TW-0.2 Reviewing an AI-drafted README | 0 | VE-2 (Understand), SP-4 (Understand) | Explain → Debug & Validate → Specify → Direct |
| 3 | TW-1.1 Reading an ADR | 1 | CO-4 (Apply), SP-4 (Adapt) | Explain → Evaluate |
| 4 | TW-1.2 Recording your own decision | 1 | DE-6 (Adapt), DE-1 (Adapt) | Explain → Direct → Evaluate |
| 5 | TW-2.1 From function spec to spec document | 2 | SP-2 (Adapt), SP-4 (Adapt) | Explain → Specify → Evaluate |
| 6 | TW-2.2 Spec before build | 2 | SP-1 (Adapt), SP-2 (Adapt) | Explain → Direct → Specify |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed. Every lesson keeps its Video page, Playground and Cold Check.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | TW-0.1 What a README is for | who reads a README and when; the five checklist points; a good README beside a weak one; marking what is missing |
|  | TW-0.2 Reviewing an AI-drafted README | AI drafts are plausible, not checked; running the command the README gives; comparing the sample run with real output; missing setup steps; asking AXIS for a draft and fixing it |
| 1 | TW-1.1 Reading an ADR | context, decision, options, consequences; what makes a decision worth recording; finding the option or consequence a record leaves out |
|  | TW-1.2 Recording your own decision | choosing a real decision from a build; directing AI to draft the record; correcting options and consequences against what was built |
| 2 | TW-2.1 From function spec to spec document | goal; inputs; outputs; failures; examples; out of scope; growing a function spec into a document; finding what an AI spec omits |
|  | TW-2.2 Spec before build | starting from a loose goal; the clarifying questions an AI draft skips; agreeing the spec before code |

## Unit details

### Stage 0: READMEs

#### TW-0.1 What a README is for

- **Objective:** Can say what a README must tell a reader and mark which of the five checklist points a README is missing.
- **The concept (Explain):** A README answers, in order, what this does, what you need first, how to run it, what a run looks like, and where it stops working.
- **Target skills:** CO-4 to Understand; SP-4 to Understand
- **Methods:** Explain → Evaluate → Specify
- **Outcome (measured at unit end):** CO-4: says in one sentence what a given script's README is for and who reads it. SP-4: compares a good and a weak README for the same script and marks each missing checklist point; graded against an exact key.
- **Topics:** who reads a README and when; the five checklist points; a good README beside a weak one; marking what is missing
- **Prerequisites:** PY-0.4 | **Importance:** Foundational

#### TW-0.2 Reviewing an AI-drafted README

- **Objective:** Can find the mistakes in an AI-drafted README by running the script, and direct AXIS to draft a README, then fix it.
- **The concept (Explain):** An AI draft reads well whether or not it is true; you find out by running what it claims.
- **Target skills:** VE-2 to Understand; SP-4 to Understand
- **Methods:** Explain → Debug & Validate → Specify → Direct
- **Outcome (measured at unit end):** VE-2: finds the three planted mistakes (wrong run command, sample output the code cannot produce, missing setup step) by running the script, told there are three; graded against an exact key. SP-4: marks every checklist point an AI-drafted README gets wrong or leaves out, against a real run; graded against an exact key. After asking AXIS to draft a README for a tiny script, fixes it so every checklist point is met; the fixed draft is judged by AXIS against the checklist (ADR-0026 style), with the status always shown.
- **Topics:** AI drafts are plausible, not checked; running the command the README gives; comparing the sample run with real output; missing setup steps; asking AXIS for a draft and fixing it
- **Prerequisites:** TW-0.1 | **Importance:** Core

### Stage 1: Decision records

#### TW-1.1 Reading an ADR

- **Objective:** Can read a decision record, say what was decided and why, and find the gap a record leaves.
- **The concept (Explain):** A decision record keeps the reason for a choice, the options turned down and what the choice costs, so a later reader need not guess.
- **Target skills:** CO-4 to Apply; SP-4 to Adapt
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-4: states the decision and its main reason from a short ADR. SP-4: finds the planted gap (a missing option or an unstated consequence) in an ADR, not told how many; graded against an exact key. Used again when reading decisions in Python Stage 12.
- **Topics:** context, decision, options, consequences; what makes a decision worth recording; finding the option or consequence a record leaves out
- **Prerequisites:** TW-0.2 | **Importance:** Core

#### TW-1.2 Recording your own decision

- **Objective:** Can direct AI to draft an ADR for a real choice in their own build and correct it until it matches what was built.
- **The concept (Explain):** The draft is AI's; the decision and its reasons are yours, so you correct the record until it says what you actually chose and why.
- **Target skills:** DE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Direct → Evaluate
- **Outcome (measured at unit end):** DE-6: the corrected ADR names at least two options and the trade-off that decided it. DE-1: marks each part of the AI draft as kept, changed or removed, with a reason. From Python Stage 11, every build includes a short ADR.
- **Topics:** choosing a real decision from a build; directing AI to draft the record; correcting options and consequences against what was built
- **Prerequisites:** TW-1.1 | **Importance:** Core

### Stage 2: Specs

#### TW-2.1 From function spec to spec document

- **Objective:** Can grow a function spec into a spec document and find what an AI-drafted spec leaves out.
- **The concept (Explain):** A spec document says the goal, the inputs, the outputs, the failures, examples and what is out of scope, so someone else could build it.
- **Target skills:** SP-2 to Adapt; SP-4 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-2: turns a function spec into a spec document with all six parts. SP-4: lists what an AI-drafted spec omits, not told how many; graded against an exact key.
- **Topics:** goal; inputs; outputs; failures; examples; out of scope; growing a function spec into a document; finding what an AI spec omits
- **Prerequisites:** TW-1.2, PY-3.4 | **Importance:** Core

#### TW-2.2 Spec before build

- **Objective:** Can take a loose goal, ask the clarifying questions an AI draft skipped, and agree a spec before any code.
- **The concept (Explain):** An AI will draft a spec from a vague goal without asking; the questions it skipped are where the build goes wrong.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt
- **Methods:** Explain → Direct → Specify
- **Outcome (measured at unit end):** SP-1: lists the clarifying questions an AI-drafted spec skipped for a loose goal. SP-2: revises the spec with the answers so it covers all six parts. The Python Stage 13 build starts from this spec.
- **Topics:** starting from a loose goal; the clarifying questions an AI draft skips; agreeing the spec before code
- **Prerequisites:** TW-2.1 | **Importance:** Core

## Skill coverage (target skills, this roadmap)

6 units carry 12 targets: Understand 4, Apply 1, Adapt 7. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-4 | 2 | Apply |
| SP-1 | 1 | Adapt |
| SP-2 | 2 | Adapt |
| SP-4 | 4 | Adapt |
| VE-2 | 1 | Understand |
| DE-1 | 1 | Adapt |
| DE-6 | 1 | Adapt |

## Decisions

1. **Scope and placement** approved by Asheesh on 2026-11-08: name Technical Writing (TW); three stages of two units; the README stage is recommended, not required (adult learning principles); learners see "Module" (ADR-0027).
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Documents and AI:** for documents, AI drafting is expected and the learner's review is the evidence (Learning Method v2 Amendment A2, ADR-0028). Cold Checks still use no AI; exact keys wherever possible. Keys go in the private answers repo (ADR-0021).
4. **Specify added (owner, 2026-11-09):** TW-0.1 and TW-0.2 gain Specify, so SP-4 (main activity Specify) can have a Cold Check: the learner marks which checklist points a README is missing (`specify_contract`, multi-select). TW-0.2 now has four methods, as GIT-2.1 does.
5. **Stage builds:** no separate builds; the documents attach to the Python stage builds named above.
