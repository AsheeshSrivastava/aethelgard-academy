---
title: AI-Assisted Engineering / Coding Agents Roadmap v2
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "2.0"
supersedes: "AI-Assisted Engineering / Coding Agents Supporting Track v1 (58 units, Competency Model codes)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Supporting roadmap, slotted into the Python and Backend path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **The scope (which units are kept, merged or dropped) and their place in the path were approved by Asheesh on 2026-10-31.** Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2, and not yet reviewed by Asheesh. Detailed teaching tasks per unit are still to be written. The v1 file stays in `reference/` until it is moved to history.

# AI-Assisted Engineering / Coding Agents Roadmap v2

**Purpose.** Directing, constraining, reviewing and verifying AI coding agents in real software work, while the engineer keeps the intent, the checks and the decisions.

## What changed from v1

- **Converted to the AI-Era Programming Skills Framework.** Each unit has one to three target skills from the 27, each with a goal level, a one-line concept for Explain and the CO-6 check, a Methods list (Explain first, then the main activity of each target skill) and an outcome line that can be graded without AI. The old five competencies are gone.
- **7 units replace 36 v1 units.** Small v1 units were merged into units the size of a Python unit; each unit lists the v1 units it replaces. Dropped: AAE-10.3 (recovery: in GIT-2.1), AAE-12.x (subagents and parallel agents), AAE-13.x (MCP and external tools, dropped by owner decision 2026-10-31), AAE-14.x (traceability: goes to the project maturity rule, ADR-0018), AAE-15.x (learning with agents: already in Learning Method v2), Supporting units AAE-3.3, 4.2, 4.4, 4.5, 11.1. AAE-16.x becomes the course project.
- **Entry rule (Learning Method Amendment A1).** No skill enters the learning path above Apply, and no skill rises more than one level from one unit to the next. Levels here are set for where these units sit in the path, after the Python units that precede them.
- **Slotted into the path.** Units are taught where the path first needs them, not as a separate course run after Python (see "Place in the path").
- **New unit IDs.** IDs restart at `AAE-0.1`. The "Replaces (v1)" field maps each one to the old IDs.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | Directing coding agents | after Python Stage 12, before Stage 13 (PY-13.4 builds on it) | 7 |

**Course project.** AAE v1 Stage 16 (integrated workflow) becomes the course project at maturity P2, and feeds PY-13.4: prepare a repository, delegate a non-trivial change with acceptance criteria, review and correct it, verify it independently, and record who did what.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | AAE-0.1 Agent modes and human ownership | 0 | DE-3 (Adapt), DE-2 (Adapt) | Explain → Direct |
| 2 | AAE-0.2 The task contract | 0 | SP-1 (Adapt), SP-2 (Adapt), SP-3 (Adapt) | Explain → Specify → Decompose |
| 3 | AAE-0.3 Inspect before changing | 0 | CO-3 (Adapt), DE-4 (Adapt) | Explain → Trace → Direct |
| 4 | AAE-0.4 Context and instruction files | 0 | SP-4 (Adapt), DE-3 (Adapt) | Explain → Specify → Direct |
| 5 | AAE-0.5 Permissions, least privilege and untrusted content | 0 | DE-5 (Adapt), DE-1 (Adapt) | Explain → Direct → Evaluate |
| 6 | AAE-0.6 Reviewing and verifying agent work | 0 | VE-2 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 7 | AAE-0.7 Diagnosing agent failures and steering | 0 | VE-3 (Adapt), DE-2 (Adapt) | Explain → Debug & Validate → Direct |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | AAE-0.1 Agent modes and human ownership | suggestion, conversation, agentic editing, delegated execution; when not to use an agent; human ownership of intent and verification |
|  | AAE-0.2 The task contract | goal and observable outcome; scope and non-goals; acceptance and verification criteria; asking for a plan first; reviewing the plan; smallest verified change |
|  | AAE-0.3 Inspect before changing | asking for an inspection before a change; requiring file and line evidence; forming a change hypothesis; catching invented functions and files |
|  | AAE-0.4 Context and instruction files | task context versus repository instructions; minimal instruction files (AGENTS.md, CLAUDE.md); loading detail only when relevant; context bloat and pollution; skills; hooks for rules that must always hold; avoiding skill sprawl |
|  | AAE-0.5 Permissions, least privilege and untrusted content | read, write, execute, network and external-system permissions; least privilege; approval gates; prompt injection through files, web pages and tool output; secrets |
|  | AAE-0.6 Reviewing and verifying agent work | reviewing the complete diff; behaviour, not only syntax; asking for explanations of non-obvious changes; running relevant tests; adding tests for changed behaviour; tool success versus engineering proof; validating an AI reviewer's findings |
|  | AAE-0.7 Diagnosing agent failures and steering | inspect, reason, plan, modify, verify; keeping intermediate changes reviewable; classifying a failure; correcting the smallest broken assumption; steering with evidence |

## Unit details

### Stage 0: Directing coding agents

#### AAE-0.1 Agent modes and human ownership

- **Objective:** Can tell suggestion, chat, agentic editing and delegated execution apart, decide when not to use an agent, and say what the human must own.
- **The concept (Explain):** An agent can do the typing and the running; the engineer still owns the intent, the checks and the decision.
- **Target skills:** DE-3 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Direct
- **Outcome (measured at unit end):** DE-3: for five tasks, decides between an agent, a chat, or no AI, and names what the human must own in each. DE-2: rewrites two "just do it" requests as "explain it" requests and then does the step themself.
- **Topics:** suggestion, conversation, agentic editing, delegated execution; when not to use an agent; human ownership of intent and verification
- **Prerequisites:** PY-0.3, PY-12.4 | **Importance:** Foundational | **Replaces (v1):** AAE-0.1, AAE-0.2, AAE-0.3

#### AAE-0.2 The task contract

- **Objective:** Can brief an agent with a goal, an observable outcome, scope, non-goals and acceptance checks, and split a large change into reviewable steps.
- **The concept (Explain):** An agent builds what you specify; a vague brief gives you a confident wrong change.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-3 to Adapt
- **Methods:** Explain → Specify → Decompose
- **Outcome (measured at unit end):** SP-1 and SP-2: writes a task brief with goal, observable outcome, scope, non-goals and acceptance checks that an agent builds from correctly. SP-3: splits a large change into steps that can each be reviewed and checked alone.
- **Topics:** goal and observable outcome; scope and non-goals; acceptance and verification criteria; asking for a plan first; reviewing the plan; smallest verified change
- **Prerequisites:** AAE-0.1 | **Importance:** Core | **Replaces (v1):** AAE-1.1, AAE-1.2, AAE-1.3, AAE-1.4, AAE-5.1, AAE-5.2, AAE-5.3

#### AAE-0.3 Inspect before changing

- **Objective:** Can direct an agent to inspect the relevant code first, and check its claims about the repository against evidence.
- **The concept (Explain):** An agent's claim about your code is a hypothesis until you see it in the code.
- **Target skills:** CO-3 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Trace → Direct
- **Outcome (measured at unit end):** CO-3: checks each claim an agent makes about the code (which file, which function, what it does) against the code itself. DE-4: chooses the source that settles a disagreement: the code, the tests, the docs, or a quick experiment.
- **Topics:** asking for an inspection before a change; requiring file and line evidence; forming a change hypothesis; catching invented functions and files
- **Prerequisites:** AAE-0.1 | **Importance:** Core | **Replaces (v1):** AAE-2.1, AAE-2.2, AAE-2.3

#### AAE-0.4 Context and instruction files

- **Objective:** Can write a minimal repository instruction file, and decide what belongs in always-on instructions, an on-demand skill, or a deterministic hook.
- **The concept (Explain):** An agent only knows what is in its context; more context is not better context.
- **Target skills:** SP-4 to Adapt; DE-3 to Adapt
- **Methods:** Explain → Specify → Direct
- **Outcome (measured at unit end):** SP-4: writes a minimal instruction file and names what a bloated sample file gets wrong. DE-3: places five rules correctly as always-on instruction, on-demand skill, or hook.
- **Topics:** task context versus repository instructions; minimal instruction files (AGENTS.md, CLAUDE.md); loading detail only when relevant; context bloat and pollution; skills; hooks for rules that must always hold; avoiding skill sprawl
- **Prerequisites:** AAE-0.2 | **Importance:** Core | **Replaces (v1):** AAE-3.1, AAE-3.2, AAE-3.4, AAE-3.5, AAE-4.1, AAE-4.3

#### AAE-0.5 Permissions, least privilege and untrusted content

- **Objective:** Can give an agent only the access a task needs, gate risky actions behind approval, and treat external content as untrusted.
- **The concept (Explain):** An agent should have only the access the task needs, and anything it reads can try to steer it.
- **Target skills:** DE-5 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Direct → Evaluate
- **Outcome (measured at unit end):** DE-5: sets read, write, run and network permissions to the least a task needs and marks which actions need approval. DE-1: rejects an agent step that follows instructions found inside fetched content, with the reason.
- **Topics:** read, write, execute, network and external-system permissions; least privilege; approval gates; prompt injection through files, web pages and tool output; secrets
- **Prerequisites:** AAE-0.1, PY-8.3 | **Importance:** Core | **Replaces (v1):** AAE-6.1, AAE-6.2, AAE-6.3, AAE-6.4

#### AAE-0.6 Reviewing and verifying agent work

- **Objective:** Can review a complete agent diff for behaviour, and verify it with checks that go beyond the agent's own claim of success.
- **The concept (Explain):** "The agent says it passed" is a claim; the evidence is the diff and the checks you ran.
- **Target skills:** VE-2 to Adapt; VE-6 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-2: reviews a full agent diff and finds the behaviour bug it missed, naming the exposing input. VE-6: runs existing checks and adds ones for odd and hostile input. DE-1: accepts, changes or rejects the change with reasons.
- **Topics:** reviewing the complete diff; behaviour, not only syntax; asking for explanations of non-obvious changes; running relevant tests; adding tests for changed behaviour; tool success versus engineering proof; validating an AI reviewer's findings
- **Prerequisites:** AAE-0.3, PY-9.5 | **Importance:** Core | **Replaces (v1):** AAE-8.1, AAE-8.2, AAE-8.3, AAE-9.1, AAE-9.2, AAE-9.3, AAE-9.4, AAE-11.2

#### AAE-0.7 Diagnosing agent failures and steering

- **Objective:** Can classify why an agent's change failed before re-prompting, and steer it with evidence.
- **The concept (Explain):** Re-asking the same question rarely fixes an agent; finding the broken assumption does.
- **Target skills:** VE-3 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-3: classifies three failed agent changes (vague spec, missing context, wrong tool, model error) and corrects the smallest broken assumption. DE-2: steers the agent with a precise question and evidence, not repetition.
- **Topics:** inspect, reason, plan, modify, verify; keeping intermediate changes reviewable; classifying a failure; correcting the smallest broken assumption; steering with evidence
- **Prerequisites:** AAE-0.6 | **Importance:** Core | **Replaces (v1):** AAE-7.1, AAE-7.2, AAE-7.3, AAE-10.1, AAE-10.2

## Skill coverage (target skills, this roadmap)

7 units carry 16 targets: Adapt 16. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-3 | 1 | Adapt |
| SP-1 | 1 | Adapt |
| SP-2 | 1 | Adapt |
| SP-3 | 1 | Adapt |
| SP-4 | 1 | Adapt |
| VE-2 | 1 | Adapt |
| VE-3 | 1 | Adapt |
| VE-6 | 1 | Adapt |
| DE-1 | 2 | Adapt |
| DE-2 | 2 | Adapt |
| DE-3 | 2 | Adapt |
| DE-4 | 1 | Adapt |
| DE-5 | 1 | Adapt |

## Decisions

1. **Scope, cuts and placement** approved by Asheesh on 2026-10-31 (review "New roadmaps: framework fit and scope").
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Stage builds:** every stage needs one build (owner rule). Not yet written for this roadmap.
