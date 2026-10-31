---
title: AI-Era Programming Skills Framework v1
created-date: 2026-10-15
description: "The governing skills model for Aethelgard. Five ownership areas, 27 trackable skills and 3 always-on habits, each with level descriptors. Derived from Competency Model v1 and the AI-Era Programming Skills research note, and written to supersede both. Language-independent; subjects such as Python train these skills."
type: specification
status: locked
version: "1.0-draft"
supersedes:
  - "Programming-Engineering Competency Model v1"
  - "AI-Era Programming Skills - Research for Aethelgard (skill list and proposed sharpenings)"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
  - competency-model
  - ai-assisted-engineering
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-15 at Asheesh's direction: "make a new framework, which is derived from both of them and supersedes them." Sources: Competency Model v1 (Stable) and *AI-Era Programming Skills - Research for Aethelgard* (draft). Approved by Asheesh on 2026-10-15 and now the only locked document: changes need his approval (CO-6 added 2026-10-17).

> [!note] Change 2026-10-17
> Added **CO-6 Explain the concept** (27 skills). CO-1 to CO-5 test understanding of code; none checked that the learner understands the concept itself. Approved by Asheesh 2026-10-17 with a soft gate: a unit's concept check informs Apply-level work but does not block it. The gate itself is a Learning Method / progression rule, not part of this framework. Crosswalk: new, no source equivalent.

## Purpose

This framework defines what capable programming work looks like when AI writes much of the code, in a form that can be tracked skill by skill. It is the single model that the learning method, the progression system, subject roadmaps and the platform's tracking all refer to.

> [!principle]
> Capability is owning the work, not typing it. A capable programmer can say what is needed, understand what exists, make it work, prove it works, and decide what to accept, with tools doing as much of the production as is sensible.

It measures demonstrated skill, not lesson completion, syntax recall, exercise count, time spent, or how confident the learner feels.

### What it keeps and what it changes

| From Competency Model v1 | From the research note | New in this framework |
| --- | --- | --- |
| The five capability dimensions, renamed for what they protect. | The trackable skill list and "what the learner does" for each. | The five areas are organised as **ownership responsibilities**, one for each thing the practitioner must keep. |
| The four levels: Understand, Apply, Adapt, Own. | The three sharpenings: specifying, code you did not write, calibration. | **Always-on habits**: a separate layer recorded every session, instead of skills tied to units. |
| The AI and tool ownership boundary. | Evidence weighting and the "almost right" problem. | **Level descriptors per skill**, and a "looks like it, but isn't" line, so tracking rules can tell levels apart. |
| Explain / Perform / Diagnose evidence types. | | Three skills the research list dropped but the model named: **dependencies and data flow**, **integrating libraries and components**, **consulting the right source**. |
| | | Two skills the subject roadmaps train that neither source named: **bound authority and trust** (DE-5) and **compare alternatives by trade-off** (DE-6). VE-3 widened from debugging to investigation. Added 2026-10-15. |

---

## The ownership boundary

Tools may produce syntax, boilerplate, implementations, tests, explanations, searches, debugging hypotheses and refactors. The practitioner keeps five responsibilities. **Each one is an area of this framework:**

| The practitioner owns… | Area | Core question |
| --- | --- | --- |
| **the mental model** | **CO — Comprehend** | What is this code or system doing, and why? |
| **the intent** | **SP — Specify** | What exactly must be true when this is done? |
| **the consequences** of what ships | **BU — Build & Adapt** | Can it be made to work, and stay workable, in the real codebase? |
| **the verification** | **VE — Verify** | How do we know it works, and why does it fail? |
| **the decisions** | **DE — Decide & Direct** | What should be accepted, delegated or asked next, and on what evidence? |

The line is not "AI allowed or not". It is crossed when a tool supplies the reasoning a skill is about and the learner cannot inspect, challenge or reproduce it. Looking up syntax, an API detail or documentation is normal tool use and never disqualifies evidence by itself.

The areas are not steps. Real work moves between them constantly: read the existing code, specify the change, have a tool draft it, read the draft, verify it, decide, repeat.

## Levels

Every skill uses the same four levels. A level describes demonstrated behaviour in a context, not a person. A learner can be at different levels on different skills.

| Level | Meaning | Typical scaffolding |
| --- | --- | --- |
| **Understand** | Can follow and explain it, with scaffolding. | Worked examples, hints, partly completed work. |
| **Apply** | Can do it in a familiar, clearly defined situation. | Clear task; attempt before help. |
| **Adapt** | Can do it under variation, with unfamiliar or AI-written code, or with imperfect requirements. | Unfamiliar code, incomplete requirements, review-style support. |
| **Own** | Takes responsibility for it in realistic work, directing tools, without step-by-step direction. | Problem and constraints only. |

> [!important]
> **Own does not mean tool-free.** It means accountable use of professional tools with little instructional scaffolding.

A subject roadmap sets the target level for each unit. This framework does not require every skill to reach Own.

## Evidence

A skill claim rests on observable performance. Output supplied entirely by a tool is a learning resource, not evidence. Evidence comes in three types:

- **Explain** — the learner explains behaviour, assumptions, a spec or a decision.
- **Perform** — the learner makes, adapts or integrates a working change.
- **Diagnose** — the learner finds a cause, validates a result, judges a proposal, or transfers the skill to a new context.

Each skill below says what the learner **does** and what **only looks like** the skill. Strength (weak / moderate / strong / insufficient) and progression decisions are interpreted by the Proficiency & Progression System, which mostly depends on **who supplied the important reasoning**.

---

## CO — Comprehend *(owns the mental model)*

| ID | Skill | What the learner does | Looks like it, but isn't |
| --- | --- | --- | --- |
| CO-1 | Predict before running | Writes down the output or final state before running, then compares and explains any mismatch. | Writing the prediction after seeing the output; a guess with no reason. |
| CO-2 | Trace state | Shows each relevant value after each step through loops and calls. | Copying a trace a tool produced. |
| CO-3 | Read unfamiliar code, including AI-written | Explains what someone else's code does, including on empty or odd input. | Paraphrasing the AI's explanation of its own code. |
| CO-4 | Explain the purpose, not the lines | Summarises a block in one accurate sentence. | Line-by-line narration. |
| CO-5 | Map dependencies and data flow | Says where data comes from, where it goes, and what depends on what across functions or modules. | Listing the files without their connections. |
| CO-6 | Explain the concept | Explains the idea behind a unit's topic in their own words, gives their own example and a non-example, and says what it is easily confused with. | Reciting a definition; repeating the tutor's or an AI's explanation. |

| ID | Understand | Apply | Adapt | Own |
| --- | --- | --- | --- | --- |
| CO-1 | Predicts a few lines' output when prompted. | Predicts the final state of a short program on ordinary input, unprompted, before running. | Predicts behaviour on edge input or in unfamiliar code, and explains each mismatch. | Predicts by habit and uses mismatches to direct investigation. |
| CO-2 | Completes a partly filled trace. | Produces a full trace of a loop or call chain. | Traces aliasing, mutation or nested calls in code they did not write. | Traces only the part that answers the question, when it is needed. |
| CO-3 | Explains a short function with hints. | Explains a short unfamiliar function, including its empty case. | Explains AI code in an unfamiliar style and says where it differs from what was asked. | Builds a working model of unfamiliar multi-part code before changing it. |
| CO-4 | Picks or completes a correct summary. | Writes a correct one-sentence purpose for a familiar block. | Does so for unfamiliar code, and notices when purpose and name disagree. | Others rely on their summaries (docstrings, write-ups). |
| CO-5 | Follows a given data-flow sketch. | Sketches data flow through a small multi-function program. | Does so for unfamiliar or AI-generated multi-module code. | Maps a realistic system's dependencies before changing it. |
| CO-6 | Picks or completes a correct explanation of the concept. | Explains a familiar concept in their own words with their own example and one non-example. | Explains it in a new context, and finds and corrects a wrong or misleading explanation, including an AI's. | Explains it clearly enough that someone else can use it; others rely on their explanations. |

## SP — Specify *(owns the intent)*

| ID | Skill | What the learner does | Looks like it, but isn't |
| --- | --- | --- | --- |
| SP-1 | Clarify before building | Lists the open questions and assumptions a requirement leaves, and separates the requirement from implementation choices, before code exists. | Generic questions that change nothing; starting code first. |
| SP-2 | Write a buildable spec | Writes inputs, outputs and 3–5 examples including edge cases, precise enough that a person or an AI could build from it and a check could test it. | Restating the requirement in other words. |
| SP-3 | Decompose | Splits work into small pieces, each with a clear input and output, buildable and checkable alone. | Pieces that can only be checked all together. |
| SP-4 | Spot the missing detail | Given a spec or prompt that produced wrong code, names the detail that was left out. | Blaming the tool without naming the gap. |

| ID | Understand | Apply | Adapt | Own |
| --- | --- | --- | --- | --- |
| SP-1 | Recognises open questions when shown them. | Lists the questions that matter for a small, clear requirement. | Finds the questions that change the design in a vague requirement, and resolves them or states assumptions. | Frames the problem from a loose goal and knows which questions need a stakeholder. |
| SP-2 | Completes a partly written spec. | Writes a full spec with edge cases for one small function. | Writes a spec that an AI or another person builds from correctly without asking anything. | Writes specs with acceptance checks for multi-part work and directs tools with them. |
| SP-3 | Follows a given decomposition and explains each piece. | Splits a small task into pieces with inputs and outputs. | Decomposes an unfamiliar requirement so each piece can be checked alone. | Sizes pieces for building, delegating and verifying. |
| SP-4 | Finds the gap when pointed at the wrong output. | Names the omitted detail given the spec and the wrong code. | Finds it in a spec before any code is generated. | Reviews other people's specs and prompts for gaps. |

## BU — Build & Adapt *(owns the consequences)*

| ID | Skill | What the learner does | Looks like it, but isn't |
| --- | --- | --- | --- |
| BU-1 | Adapt existing code | Changes working code for a new requirement without breaking the old cases. | Rewriting from scratch; breaking old cases unnoticed. |
| BU-2 | Refine a draft to meet the spec | Edits an AI or example draft until it meets every line of the spec, and says which edit fixed which line. | Regenerating until the given checks pass. |
| BU-3 | Integrate libraries and components | Uses a library or existing component through its interface, from its documentation, instead of re-creating it, and handles what it returns and how it fails. | Copying AI usage without knowing what it returns; re-implementing the standard library. |
| BU-4 | Keep code maintainable | Reuses instead of near-copying; names clearly; prefers the simpler form. | Cosmetic renaming; adding cleverness. |
| BU-5 | Make small, reversible changes | Changes one thing at a time and can roll back. | Many edits at once, then hoping. |

| ID | Understand | Apply | Adapt | Own |
| --- | --- | --- | --- | --- |
| BU-1 | Makes a guided change. | Changes a familiar function; old checks still pass. | Does so in unfamiliar or AI-written code. | Makes realistic changes in an existing system and shows nothing broke. |
| BU-2 | Fixes one named gap in a draft, with hints. | Brings a short draft up to every spec line, mapping edits to lines. | Handles several subtle gaps in an unfamiliar style. | Runs generate → inspect → refine as normal practice. |
| BU-3 | Uses a call shown in a worked example. | Finds and uses a standard-library function from its docs for a clear need. | Integrates an unfamiliar library or module, handling its return values and failures. | Chooses and integrates dependencies responsibly. |
| BU-4 | Recognises duplication or an unclear name when shown. | Reuses and names clearly in own code. | Removes duplication or cleverness from a draft without changing behaviour. | Makes maintainability calls and explains the trade-off. |
| BU-5 | Explains why one change at a time helps. | Changes one thing and re-runs the checks. | Rolls back a failed change and narrows the next. | Works in small, reviewable commits. |

## VE — Verify *(owns the verification)*

| ID | Skill | What the learner does | Looks like it, but isn't |
| --- | --- | --- | --- |
| VE-1 | Write checks that catch a wrong answer | Writes checks, including edge cases, that a plausible wrong version would fail. | Happy-path checks only; checks derived from the code under test. |
| VE-2 | Find the bug in code you did not write | Given someone else's or an AI's code with a bug, finds it and names the input that exposes it. | Asking the AI to find it; rewriting without locating it. |
| VE-3 | Investigate by hypothesis | To debug or to improve working code, states one cause or idea, tests one change, measures or records whether it held, and narrows to the root cause or the real gain. | Changing things at random until it works; optimising without measuring before and after. |
| VE-4 | Read error messages | Uses a traceback or error to name the line and likely cause before asking for help. | Pasting the error into a tool first. |
| VE-5 | Prove the fix | Shows a check that failed before the fix and passes after, with old cases still passing. | "It runs now." |
| VE-6 | Check beyond "it runs" | Asks what happens with empty, huge, wrong-type or hostile input. | Testing only the example given. |

| ID | Understand | Apply | Adapt | Own |
| --- | --- | --- | --- | --- |
| VE-1 | Explains why a given check catches a given bug. | Writes checks that fail on a planted wrong version they were shown. | Writes checks that fail on wrong versions they have **not** seen. | Decides what checking is enough and includes it by default. |
| VE-2 | Finds the bug when its region is pointed out. | Finds a planted bug in a short AI-written function and names the exposing input. | Finds near-miss bugs in unfamiliar style or across functions. | Reviews AI and peer code as routine, before running it. |
| VE-3 | States a hypothesis when prompted. | One cause, one change, result recorded; for an improvement, measures before and after. | Revises after a failed hypothesis without random edits. | Runs disciplined investigations on unfamiliar failures and performance problems. |
| VE-4 | Finds the line and error type, with help. | Names the line and likely cause for common errors. | Follows multi-frame tracebacks into code they did not write. | Uses errors and logs as first evidence by habit. |
| VE-5 | Explains why red-then-green proves a fix. | Shows the failing-then-passing check. | Also shows old cases pass and the fix is not over-narrow. | Every fix ships with its proof. |
| VE-6 | Names one odd input when prompted. | Tries empty, wrong-type and very large input on a small function. | Finds boundary or hostile input in unfamiliar code. | Chooses checks by risk, including basic security. |

## DE — Decide & Direct *(owns the decisions)*

| ID | Skill | What the learner does | Looks like it, but isn't |
| --- | --- | --- | --- |
| DE-1 | Accept, change or reject with a reason | For a suggestion from AI or a person, decides accept / change / reject and gives the reason in one or two sentences. | "Looks good"; accepting because it ran. |
| DE-2 | Ask the tool to explain, not to do | Uses AI to understand a concept or error, then does the step themself. | Asking for the answer, then reading it. |
| DE-3 | Decide what to delegate | Says which parts are fine to hand to a tool (syntax, boilerplate) and which they must own (intent, checks). | Delegating by convenience. |
| DE-4 | Consult the right source | Picks between documentation, a quick experiment, AI and a person, and knows which answer is authoritative. | Trusting the first answer; asking AI for everything. |
| DE-5 | Bound authority and trust | Gives code, tools, agents and services only the access a task needs, and treats what they return or receive as untrusted until checked. | Granting broad permissions because it is easier; trusting input because it came from your own tool. |
| DE-6 | Compare alternatives by trade-off | Lays out two or more options, compares them by their consequences (cost, risk, change, performance), and chooses with a stated reason. | Picking the first or most familiar option; listing pros and cons without choosing. |

| ID | Understand | Apply | Adapt | Own |
| --- | --- | --- | --- | --- |
| DE-1 | Explains a verdict someone else gave. | Gives a verdict and reason on a short suggestion. | Does so on plausible-but-wrong or over-complicated suggestions. | Governs tool output routinely in real work. |
| DE-2 | Asks for an explanation when prompted. | Asks a conceptual question, then does the step without the tool. | Asks a precise question about an unfamiliar error. | Learns new libraries quickly through targeted questions and experiments. |
| DE-3 | Explains what must be owned and why. | Sorts a small task's parts into delegate / own. | Adjusts the split for an unfamiliar or riskier task. | Directs tools and agents while keeping intent and verification. |
| DE-4 | Names which source would settle a given question. | Checks an API detail in the official docs instead of trusting recall. | Resolves a conflict between an AI answer and the docs by experiment. | Picks the cheapest reliable source by habit. |
| DE-5 | Explains why least access and untrusted input matter. | Limits a script's or agent's access for a small task and validates what it receives. | Finds over-broad permissions or unchecked trust in unfamiliar code or agent setups. | Designs trust boundaries and approval gates for real systems. |
| DE-6 | Explains a trade-off someone else made. | Compares two given options for a small task and chooses with a reason. | Generates the options as well, for an unfamiliar problem, and names what would change the choice. | Records decisions and their trade-offs so others can revisit them. |

---

## Always-on habits

Three habits are recorded in **every** session instead of being targeted by particular units. They cost almost nothing to capture, and they are what the research says erodes quietly with AI use: people feel more capable than they are, and stop forming their own view first.

| ID | Habit | What the learner does | How it is captured | Understand → Own |
| --- | --- | --- | --- | --- |
| H-1 | Separate fact from assumption | Says which parts of an explanation were checked and which are guesses. | From the learner's explanations and write-ups. | Labels when asked → unprompted → checks load-bearing assumptions → write-ups state what was verified and how. |
| H-2 | Calibrate confidence | States how sure they are before a check runs; over time it matches results. | The facilitator asks "how sure are you?" before each check. | States when asked → unprompted → confidence tracks results → uses own calibration to decide how much to verify. |
| H-3 | Think first, then ask | Shares their own plan or guess before asking an AI or a person. | From the help log. | Shares when asked → unprompted → narrows the question with an attempt → asks only after narrowing. |

Habits get levels and decisions like skills, but no unit has to carry them.

---

## Subjects and roadmaps

The framework is language-independent within programming and software engineering. A **subject roadmap** (Python first) supplies units, content, prerequisites and a target level per unit, and says which skills each unit trains. The learner's record is kept **per skill**, with the unit as context, so evidence from Python and a later language accumulates on the same skills.

Python Roadmap v2 tags units with the old competency codes. Read them as:

| Roadmap code | Area |
| --- | --- |
| CR Comprehension & Reasoning | CO Comprehend |
| PD Problem Framing & Decomposition | SP Specify |
| IA Implementation & Adaptation | BU Build & Adapt |
| DV Debugging & Validation | VE Verify |
| TJ Technical Judgment & Tool Direction | DE Decide & Direct |

So the locked roadmap needs no edit. The Python mapping is in *Python under AI-Era Skills v1*.

The other eleven roadmaps (Backend, AI Engineering, Software Design, Practical DSA, Database/SQL, System Architecture, Git, OS/Process, Networking/Web, AI-Assisted Engineering, and the Projects & Capstones layer) use the same five codes, so the same table applies to them. How they are learned together is in *Roadmaps under AI-Era Skills v1*.

## Crosswalk from the sources

| Old | New | | Old | New |
| --- | --- | --- | --- | --- |
| 1a Predict | CO-1 | | 4a Write checks | VE-1 |
| 1b Trace | CO-2 | | 4b Bug in code you did not write | VE-2 |
| 1c Read unfamiliar code | CO-3 | | 4c Debug by hypothesis | VE-3 (widened) |
| 1d Explain purpose | CO-4 | | 4d Read errors | VE-4 |
| 1e Fact vs assumption | H-1 | | 4e Prove the fix | VE-5 |
| *(model: dependencies, data flow)* | CO-5 | | 4f Beyond "it runs" | VE-6 |
| 2a Clarify | SP-1 | | 5a Accept / change / reject | DE-1 |
| 2b Specify | SP-2 | | 5b Calibrate | H-2 |
| 2c Decompose | SP-3 | | 5c Ask to explain | DE-2 |
| 2d Missing detail | SP-4 | | 5d Think first | H-3 |
| 3a Adapt | BU-1 | | 5e Delegate | DE-3 |
| 3b Refine a draft | BU-2 | | *(model: consulting appropriate sources)* | DE-4 |
| *(model: libraries, connecting components)* | BU-3 | | MVP "skill 3" | VE-1 |
| 3c Maintainable | BU-4 | | MVP "skill 4" | VE-2 + VE-5 |
| 3d Small changes | BU-5 | | *(model: assessing alternatives)* | DE-6 |
| *(roadmaps: permissions, trust boundaries)* | DE-5 | | | |

## Relationship to other documents

- **Supersedes** Competency Model v1, and the research note's skill list and proposed sharpenings. The research note stays as the evidence base this framework cites.
- **Unchanged and still in force:** Learning Method v1 (activities and scaffolding), Proficiency & Progression System v1 (evidence strength and decisions), Python Roadmap v2 (LOCKED; read through the code table above).
- **Not owned here:** activity design, strength interpretation, progression decisions, unit sequencing, record schemas.

## Status

**Locked v1 (approved 2026-10-15), supersedes Competency Model v1.** The superseding edits below were made on 2026-10-17 (Competency Model v1 and the research note are in `history/` marked superseded; `index.md` and the Proficiency System links updated; journal entry 8). Learning Method v1 was moved to history when Learning Method v2 was started; its links were not changed.

The original list of edits:

1. Competency Model v1: set status to superseded, with a pointer here.
2. Research note: mark its skill list as superseded by this framework.
3. `index.md`: list this framework as the governing model.
4. Learning Method v1 and Proficiency & Progression System v1: change their links to Competency Model v1 to point here, and rename the five competencies in the Learning Method's alignment table. These are wording changes only.
5. `docs/design_journal.md`: record the decision and why.
