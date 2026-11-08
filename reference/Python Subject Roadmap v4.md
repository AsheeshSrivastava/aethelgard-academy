---
title: Python Subject Roadmap v4
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "4.0"
supersedes: "Python Subject Roadmap v3 (kept in reference/ until the app loader moves to v4)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction, from Python Subject Roadmap v3 (approved 2026-10-17). **Asheesh approved on 2026-10-31 the seven changes from the roadmap review and slotting the new Git, Practical DSA, Software Design and AI-Assisted Engineering units into this path.** The new wording (Make tasks, PY-1.9, changed levels) is AI-drafted and not yet reviewed. Everything not listed under "Changed in v4" is v3 text unchanged.

# Python Subject Roadmap v4

## What changed from v3

All changes follow the roadmap review of 2026-10-31 and Learning Method v2 Amendment A1. Each changed unit says what changed in its **Changed in v4** line; the table at the end lists them all.

1. **Make step.** 15 code units in Stages 1 to 5 end with a Make step: a small program written from a blank file and graded by tests. It uses the Build activity and credits one of the unit's own target skills, named in the outcome line. PY-3.1 gains BU-2 (Apply) for this.
2. **Entry rule.** No skill enters the path above Apply, and no skill rises more than one level at a time. Thirteen goal levels were lowered (ten first appearances, two DE skills that skipped a rung, and CO-2 in the split PY-1.3).
3. **Cold Check and spaced review.** A short Cold Check at the end of each unit, a mixed stage review at the end of each stage that unlocks the stage build, and 7-day and 30-day rechecks (ADR-0019). No roadmap text changes.
4. **Practice volume.** 15 to 20 graded items per unit in Stages 0 to 5, at least 3 of them Make; 8 to 12 later (ADR-0019). No roadmap text changes.
5. **Foundations.** Practical DSA, Git, Software Design and AI-Assisted Engineering units are slotted into this path (see "Path order"). `map`, `filter` and bitwise operators (awareness) are added. OS / Process topics are added to seven units.
6. **Thinner early units.** PY-0.1 loses its preview topics. PY-1.3 is split: **PY-1.9 Copies, aliases and nested data** is new. Topics marked "awareness" are explained but not tested in Cold Check.
7. **More Predict and Decompose.** PY-2.2 adds Predict with CO-1 (Adapt). PY-4.2 and PY-8.3 add Decompose as a helper for SP-1 and SP-2.

## Path order

The learning path is this roadmap's units with the supporting units slotted in where they are first needed. Table 1 lists the whole path in order (117 units: 79 Python units and 38 slotted units). Slotted units keep their own IDs and details in their own roadmaps.

| After | Slotted units | From |
| --- | --- | --- |
| PY-0.3 (end of Stage 0, before its build; recommended, not required) | TW-0.1 to TW-0.2 | Technical Writing Roadmap v1, Stage 0 |
| PY-3.5 (end of Stage 3) | DSA-0.1 to DSA-0.4 | Practical DSA Roadmap v3, Stage 0 |
| PY-4.4 (end of Stage 4) | GIT-0.1 to GIT-0.4 | Git Version Control Roadmap v2, Stage 0 |
| PY-6.7 (end of Stage 6) | SD-0.1 to SD-0.4 | Software Design Roadmap v2, Stage 0 |
| PY-8.5 (end of Stage 8) | DSA-1.1 to DSA-1.4 | Practical DSA Roadmap v3, Stage 1 |
| PY-10.5 (end of Stage 10) | TW-1.1 to TW-1.2 | Technical Writing Roadmap v1, Stage 1 |
| PY-11.4 (end of Stage 11) | GIT-1.1 to GIT-1.4 | Git Version Control Roadmap v2, Stage 1 |
| PY-12.5 (end of Stage 12) | SD-1.1 to SD-1.4, GIT-2.1, AAE-0.1 to AAE-0.7 | Software Design v2 Stage 1, Git v2 Stage 2, AI-Assisted Engineering v2 |
| AAE-0.7 (end of the Stage 12 slotted units) | TW-2.1 to TW-2.2 | Technical Writing Roadmap v1, Stage 2 (added 2026-11-08, owner-approved scope) |

Backend Engineering Roadmap v3 continues the path with the Networking and Database units.

## Table 1: path sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | PY-0.4 Run a first program | 0 | CO-1 (Understand), VE-4 (Understand) | Explain → Predict → Debug & Validate |
| 2 | PY-0.1 Python as an executing program | 0 | CO-1 (Understand), CO-2 (Understand), CO-6 (Understand) | Explain → Predict → Trace |
| 3 | PY-0.3 Tool help versus your own reasoning | 0 | DE-2 (Understand), DE-3 (Understand), DE-4 (Understand) | Explain → Direct |
| 4 | TW-0.1 What a README is for *(Technical Writing v1)* | TW 0 | CO-4 (Understand), SP-4 (Understand) | Explain → Evaluate |
| 5 | TW-0.2 Reviewing an AI-drafted README *(Technical Writing v1)* | TW 0 | VE-2 (Understand), SP-4 (Understand) | Explain → Debug & Validate → Direct |
| 6 | PY-1.2 Numbers, booleans and None | 1 | CO-1 (Apply), VE-6 (Apply) | Explain → Predict → Debug & Validate → Build |
| 7 | PY-1.7 Text | 1 | BU-1 (Apply), VE-6 (Apply) | Explain → Modify → Debug & Validate → Build |
| 8 | PY-1.1 Names, objects and expressions | 1 | CO-1 (Apply), CO-2 (Apply), CO-6 (Apply) | Explain → Predict → Trace |
| 9 | PY-1.8 Checking code with assert | 1 | VE-1 (Apply) | Explain → Debug & Validate → Build |
| 10 | PY-1.3 Lists and tuples | 1 | CO-2 (Apply), VE-2 (Apply) | Explain → Trace → Debug & Validate |
| 11 | PY-1.9 Copies, aliases and nested data | 1 | CO-2 (Adapt), VE-2 (Adapt) | Explain → Trace → Debug & Validate |
| 12 | PY-1.4 Mappings | 1 | CO-3 (Apply), BU-1 (Adapt), VE-6 (Adapt) | Explain → Modify → Debug & Validate → Build |
| 13 | PY-1.5 Choosing data structures | 1 | DE-6 (Apply), DE-1 (Apply) | Explain → Evaluate |
| 14 | PY-1.6 Specialised collections and the standard library | 1 | BU-3 (Apply), DE-4 (Apply) | Explain → Build → Direct |
| 15 | PY-2.1 Conditions | 2 | VE-1 (Adapt), VE-6 (Adapt), SP-1 (Apply) | Explain → Specify → Debug & Validate → Build |
| 16 | PY-2.2 Iteration | 2 | VE-1 (Adapt), VE-2 (Adapt), VE-5 (Apply), CO-1 (Adapt) | Explain → Predict → Trace → Debug & Validate → Build |
| 17 | PY-2.5 Debugging basics | 2 | VE-3 (Apply), VE-4 (Apply) | Explain → Debug & Validate |
| 18 | PY-2.3 Comprehensions | 2 | BU-2 (Apply), BU-4 (Apply) | Explain → Modify → Evaluate → Build |
| 19 | PY-2.4 Choosing control flow | 2 | DE-6 (Apply), BU-4 (Apply) | Explain → Evaluate → Modify → Build |
| 20 | PY-3.1 Function calls and scope | 3 | CO-2 (Adapt), CO-3 (Adapt), CO-6 (Adapt), BU-2 (Apply) | Explain → Trace → Build |
| 21 | PY-3.6 Recursion | 3 | CO-2 (Apply), VE-2 (Apply) | Explain → Trace → Debug & Validate |
| 22 | PY-3.2 Function interfaces | 3 | BU-1 (Adapt), DE-1 (Adapt), VE-2 (Adapt) | Explain → Modify → Evaluate → Debug & Validate → Build |
| 23 | PY-3.3 Functions as values | 3 | CO-3 (Apply), CO-4 (Apply), DE-1 (Apply) | Explain → Evaluate |
| 24 | PY-3.4 Coherent functions | 3 | SP-1 (Adapt), SP-2 (Apply), SP-4 (Apply), VE-1 (Adapt) | Explain → Specify → Debug & Validate → Build |
| 25 | PY-3.5 Decomposing a requirement | 3 | SP-1 (Adapt), SP-3 (Apply), BU-2 (Adapt), DE-3 (Apply) | Explain → Specify → Decompose → Modify → Direct |
| 26 | DSA-0.1 Growth and the cost of common operations *(Practical DSA v3)* | DSA 0 | CO-1 (Apply), DE-6 (Apply) | Explain → Predict → Evaluate |
| 27 | DSA-0.2 Finding repeated and nested work *(Practical DSA v3)* | DSA 0 | CO-3 (Apply), BU-1 (Adapt) | Explain → Trace → Modify |
| 28 | DSA-0.3 Theory versus measured runtime *(Practical DSA v3)* | DSA 0 | VE-3 (Apply), DE-1 (Apply) | Explain → Debug & Validate → Evaluate |
| 29 | DSA-0.4 Sorting and binary search *(Practical DSA v3)* | DSA 0 | CO-2 (Adapt), VE-1 (Adapt) | Explain → Trace → Debug & Validate |
| 30 | PY-4.1 Exception flow | 4 | CO-2 (Adapt), VE-4 (Adapt), DE-1 (Adapt), DE-2 (Apply) | Explain → Trace → Debug & Validate → Evaluate → Direct |
| 31 | PY-4.2 Failure contracts | 4 | SP-1 (Adapt), SP-2 (Adapt), SP-4 (Adapt), VE-1 (Adapt) | Explain → Specify → Decompose → Debug & Validate → Build |
| 32 | PY-4.3 Validation | 4 | BU-1 (Adapt), VE-6 (Adapt), DE-5 (Apply) | Explain → Modify → Debug & Validate → Direct → Build |
| 33 | PY-4.4 Making failures explicit | 4 | VE-3 (Adapt), VE-5 (Adapt), BU-5 (Apply) | Explain → Debug & Validate → Modify |
| 34 | GIT-0.1 Repository state: working tree, staging and history *(Git v2)* | GIT 0 | CO-2 (Apply), CO-6 (Apply) | Explain → Trace |
| 35 | GIT-0.2 Diffs, staging and meaningful commits *(Git v2)* | GIT 0 | CO-3 (Apply), BU-5 (Apply) | Explain → Trace → Modify |
| 36 | GIT-0.3 Branches, HEAD and merging *(Git v2)* | GIT 0 | CO-1 (Apply), CO-2 (Apply) | Explain → Predict → Trace |
| 37 | GIT-0.4 Resolving merge conflicts *(Git v2)* | GIT 0 | BU-1 (Adapt), VE-5 (Apply) | Explain → Modify → Debug & Validate |
| 38 | PY-5.1 Modules and imports | 5 | VE-3 (Adapt), VE-4 (Adapt), CO-6 (Adapt) | Explain → Debug & Validate |
| 39 | PY-5.2 Splitting code across modules | 5 | SP-3 (Adapt), BU-4 (Adapt), CO-4 (Adapt), BU-5 (Adapt) | Explain → Decompose → Modify → Evaluate → Build |
| 40 | PY-5.3 Packages | 5 | CO-5 (Apply), VE-3 (Adapt) | Explain → Trace → Debug & Validate |
| 41 | PY-5.4 Entry points | 5 | CO-1 (Apply), BU-1 (Apply), DE-4 (Apply) | Explain → Predict → Modify → Direct → Build |
| 42 | PY-0.2 Reading a small Python application | 5 | CO-4 (Apply), CO-5 (Apply) | Explain → Trace |
| 43 | PY-6.1 Classes, instances and state | 6 | CO-2 (Adapt), CO-6 (Adapt), BU-1 (Adapt) | Explain → Trace → Modify |
| 44 | PY-6.2 Constructing objects | 6 | VE-1 (Adapt), VE-2 (Adapt) | Explain → Debug & Validate |
| 45 | PY-6.3 Instance, class and static methods | 6 | DE-6 (Apply), BU-4 (Apply) | Explain → Evaluate → Modify |
| 46 | PY-6.4 Controlled object interfaces | 6 | DE-1 (Adapt), BU-4 (Adapt), VE-6 (Adapt) | Explain → Evaluate → Modify → Debug & Validate |
| 47 | PY-6.8 Special methods | 6 | CO-1 (Apply), DE-1 (Apply) | Explain → Predict → Evaluate |
| 48 | PY-6.9 Data classes and named values | 6 | DE-6 (Adapt), BU-3 (Adapt) | Explain → Evaluate → Build |
| 49 | PY-6.5 Inheritance and resolution | 6 | CO-1 (Adapt), CO-6 (Adapt), VE-2 (Adapt) | Explain → Predict → Debug & Validate |
| 50 | PY-6.6 Polymorphism and shared contracts | 6 | SP-2 (Adapt), DE-6 (Adapt), DE-1 (Adapt), VE-1 (Adapt) | Explain → Specify → Evaluate → Debug & Validate |
| 51 | PY-6.7 Composition and object responsibility | 6 | SP-3 (Adapt), DE-6 (Adapt), BU-4 (Adapt), BU-5 (Adapt) | Explain → Decompose → Evaluate → Modify |
| 52 | SD-0.1 Framing a design problem and its trade-offs *(Software Design v2)* | SD 0 | SP-1 (Adapt), DE-6 (Adapt) | Explain → Specify → Evaluate |
| 53 | SD-0.2 Interfaces, contracts and dependency direction *(Software Design v2)* | SD 0 | SP-2 (Adapt), BU-4 (Adapt), CO-5 (Adapt) | Explain → Specify → Modify |
| 54 | SD-0.3 SOLID as change reasoning *(Software Design v2)* | SD 0 | DE-1 (Adapt), BU-4 (Adapt) | Explain → Evaluate → Modify |
| 55 | SD-0.4 Substitutability: Liskov and interface segregation *(Software Design v2)* | SD 0 | CO-1 (Adapt), VE-2 (Adapt) | Explain → Predict → Debug & Validate |
| 56 | PY-7.1 Iterables and iterators | 7 | CO-1 (Apply), CO-6 (Apply), VE-2 (Apply) | Explain → Predict → Debug & Validate |
| 57 | PY-7.2 Generators | 7 | CO-2 (Adapt), CO-5 (Adapt), BU-2 (Adapt), DE-6 (Adapt) | Explain → Trace → Modify → Evaluate |
| 58 | PY-7.3 Decorators | 7 | CO-4 (Apply), BU-1 (Apply), VE-2 (Apply) | Explain → Modify → Debug & Validate |
| 59 | PY-7.4 Context managers | 7 | CO-2 (Adapt), BU-3 (Adapt), VE-6 (Adapt) | Explain → Trace → Build → Debug & Validate |
| 60 | PY-7.5 Type annotations | 7 | CO-3 (Adapt), DE-1 (Adapt), VE-4 (Adapt) | Explain → Evaluate → Debug & Validate |
| 61 | PY-7.6 Interface-style type contracts | 7 | SP-2 (Apply), SP-4 (Apply), DE-6 (Apply) | Explain → Specify → Evaluate |
| 62 | PY-8.1 Files and paths | 8 | BU-3 (Adapt), VE-6 (Adapt), DE-5 (Adapt) | Explain → Build → Debug & Validate → Direct |
| 63 | PY-8.2 Structured data | 8 | VE-1 (Adapt), VE-6 (Adapt), BU-3 (Adapt) | Explain → Debug & Validate → Build |
| 64 | PY-8.6 Pattern matching in text | 8 | CO-3 (Apply), VE-1 (Apply) | Explain → Debug & Validate |
| 65 | PY-8.3 Configuration | 8 | SP-1 (Adapt), SP-2 (Adapt), SP-4 (Adapt), DE-5 (Adapt) | Explain → Specify → Decompose → Direct |
| 66 | PY-8.7 Command-line programs and running other programs | 8 | BU-3 (Apply), DE-5 (Apply), VE-4 (Apply) | Explain → Build → Direct → Debug & Validate |
| 67 | PY-8.4 Calling HTTP services | 8 | BU-2 (Adapt), VE-2 (Adapt), VE-6 (Adapt), DE-4 (Adapt) | Explain → Modify → Debug & Validate → Direct |
| 68 | PY-8.5 Dates, times and timezones | 8 | VE-2 (Apply), VE-6 (Apply), DE-4 (Apply) | Explain → Debug & Validate → Direct |
| 69 | DSA-1.1 Stacks, queues and priority queues *(Practical DSA v3)* | DSA 1 | DE-6 (Adapt), BU-3 (Apply) | Explain → Evaluate → Build |
| 70 | DSA-1.2 Trees and hierarchical data *(Practical DSA v3)* | DSA 1 | CO-2 (Adapt), VE-2 (Adapt) | Explain → Trace → Debug & Validate |
| 71 | DSA-1.3 Graphs, BFS, DFS and dependency order *(Practical DSA v3)* | DSA 1 | CO-2 (Adapt), SP-3 (Adapt) | Explain → Trace → Decompose |
| 72 | DSA-1.4 Choosing under changing constraints *(Practical DSA v3)* | DSA 1 | DE-6 (Adapt), DE-1 (Adapt), VE-6 (Adapt) | Explain → Evaluate → Debug & Validate |
| 73 | PY-9.1 Debugging | 9 | VE-3 (Adapt), VE-5 (Adapt), CO-2 (Adapt), DE-2 (Adapt) | Explain → Debug & Validate → Trace → Direct |
| 74 | PY-9.2 Logging and runtime evidence | 9 | VE-4 (Adapt), BU-4 (Adapt), DE-5 (Adapt) | Explain → Debug & Validate → Modify → Direct |
| 75 | PY-9.3 Behavioural tests with pytest | 9 | VE-1 (Adapt), VE-5 (Adapt), VE-6 (Adapt), DE-3 (Adapt) | Explain → Debug & Validate → Direct |
| 76 | PY-9.4 Isolating code under test | 9 | VE-1 (Apply), DE-6 (Apply) | Explain → Debug & Validate → Evaluate |
| 77 | PY-9.5 When passing is not proof | 9 | VE-2 (Adapt), VE-6 (Adapt), DE-1 (Adapt), SP-4 (Adapt) | Explain → Debug & Validate → Evaluate → Specify |
| 78 | PY-9.6 Measuring runtime | 9 | VE-3 (Apply), CO-1 (Apply), DE-1 (Apply) | Explain → Predict → Debug & Validate → Evaluate |
| 79 | PY-10.1 Environments | 10 | VE-3 (Adapt), VE-4 (Adapt), CO-6 (Adapt) | Explain → Debug & Validate |
| 80 | PY-10.2 Dependencies | 10 | DE-5 (Adapt), DE-6 (Adapt), BU-5 (Adapt) | Explain → Direct → Evaluate → Modify |
| 81 | PY-10.3 Project metadata and packaging | 10 | CO-3 (Apply), CO-4 (Apply), CO-5 (Apply) | Explain → Trace |
| 82 | PY-10.4 Diagnosing install and environment failures | 10 | VE-3 (Adapt), VE-5 (Adapt) | Explain → Debug & Validate |
| 83 | PY-10.5 Quality gates | 10 | BU-4 (Apply), VE-4 (Apply), DE-3 (Apply) | Explain → Modify → Debug & Validate → Direct |
| 84 | TW-1.1 Reading an ADR *(Technical Writing v1)* | TW 1 | CO-4 (Apply), SP-4 (Adapt) | Explain → Evaluate |
| 85 | TW-1.2 Recording your own decision *(Technical Writing v1)* | TW 1 | DE-6 (Adapt), DE-1 (Adapt) | Explain → Direct → Evaluate |
| 86 | PY-11.1 Concurrency mental model | 11 | CO-6 (Understand), DE-6 (Understand) | Explain → Evaluate |
| 87 | PY-11.5 Threads and processes | 11 | BU-3 (Apply), VE-2 (Apply) | Explain → Build → Debug & Validate |
| 88 | PY-11.2 Tracing async code | 11 | CO-1 (Adapt), CO-2 (Adapt), DE-2 (Adapt) | Explain → Predict → Trace → Direct |
| 89 | PY-11.3 Concurrent I/O | 11 | BU-2 (Adapt), VE-2 (Adapt), VE-3 (Adapt), DE-4 (Adapt) | Explain → Modify → Debug & Validate → Direct |
| 90 | PY-11.4 Async failures | 11 | VE-3 (Adapt), VE-5 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Evaluate |
| 91 | GIT-1.1 Remotes: fetch, pull, push and divergence *(Git v2)* | GIT 1 | CO-1 (Adapt), VE-3 (Adapt) | Explain → Predict → Debug & Validate |
| 92 | GIT-1.2 The pull-request workflow *(Git v2)* | GIT 1 | SP-4 (Adapt), DE-1 (Adapt) | Explain → Specify → Evaluate |
| 93 | GIT-1.3 Undo and recovery *(Git v2)* | GIT 1 | VE-3 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Evaluate |
| 94 | GIT-1.4 Reading history for context *(Git v2)* | GIT 1 | CO-3 (Adapt), CO-4 (Adapt) | Explain → Trace |
| 95 | PY-12.1 Navigating an unfamiliar codebase | 12 | CO-3 (Own), CO-4 (Own), CO-5 (Own), SP-3 (Own) | Explain → Trace → Decompose |
| 96 | PY-12.2 Learning a library from its documentation | 12 | DE-2 (Adapt), DE-4 (Adapt), BU-3 (Adapt) | Explain → Direct → Build |
| 97 | PY-12.3 Organising a Python application | 12 | SP-3 (Adapt), DE-6 (Adapt), BU-4 (Adapt), CO-5 (Adapt) | Explain → Decompose → Evaluate → Modify |
| 98 | PY-12.4 Changing an existing subsystem safely | 12 | BU-1 (Own), BU-5 (Own), VE-1 (Own), VE-5 (Own) | Explain → Modify → Debug & Validate |
| 99 | PY-12.5 Refactoring | 12 | BU-4 (Adapt), BU-5 (Adapt), VE-5 (Adapt), DE-6 (Adapt) | Explain → Modify → Debug & Validate → Evaluate |
| 100 | SD-1.1 Pattern intent and a small core set *(Software Design v2)* | SD 1 | DE-6 (Adapt), BU-3 (Adapt) | Explain → Evaluate → Build |
| 101 | SD-1.2 Pattern overuse and design smells *(Software Design v2)* | SD 1 | CO-3 (Adapt), DE-1 (Adapt) | Explain → Evaluate |
| 102 | SD-1.3 Modelling a workflow or state machine *(Software Design v2)* | SD 1 | SP-2 (Adapt), CO-5 (Adapt), VE-1 (Adapt) | Explain → Specify → Debug & Validate |
| 103 | SD-1.4 Producing and defending a low-level design *(Software Design v2)* | SD 1 | SP-3 (Adapt), DE-6 (Adapt), BU-2 (Adapt) | Explain → Decompose → Evaluate → Modify |
| 104 | GIT-2.1 Git as the safety net for agent work *(Git v2)* | GIT 2 | BU-5 (Adapt), DE-5 (Adapt), VE-5 (Adapt) | Explain → Modify → Direct → Debug & Validate |
| 105 | AAE-0.1 Agent modes and human ownership *(AI-Assisted Engineering v2)* | AAE 0 | DE-3 (Adapt), DE-2 (Adapt) | Explain → Direct |
| 106 | AAE-0.2 The task contract *(AI-Assisted Engineering v2)* | AAE 0 | SP-1 (Adapt), SP-2 (Adapt), SP-3 (Adapt) | Explain → Specify → Decompose |
| 107 | AAE-0.3 Inspect before changing *(AI-Assisted Engineering v2)* | AAE 0 | CO-3 (Adapt), DE-4 (Adapt) | Explain → Trace → Direct |
| 108 | AAE-0.4 Context and instruction files *(AI-Assisted Engineering v2)* | AAE 0 | SP-4 (Adapt), DE-3 (Adapt) | Explain → Specify → Direct |
| 109 | AAE-0.5 Permissions, least privilege and untrusted content *(AI-Assisted Engineering v2)* | AAE 0 | DE-5 (Adapt), DE-1 (Adapt) | Explain → Direct → Evaluate |
| 110 | AAE-0.6 Reviewing and verifying agent work *(AI-Assisted Engineering v2)* | AAE 0 | VE-2 (Adapt), VE-6 (Adapt), DE-1 (Adapt) | Explain → Debug & Validate → Evaluate |
| 111 | AAE-0.7 Diagnosing agent failures and steering *(AI-Assisted Engineering v2)* | AAE 0 | VE-3 (Adapt), DE-2 (Adapt) | Explain → Debug & Validate → Direct |
| 112 | TW-2.1 From function spec to spec document *(Technical Writing v1)* | TW 2 | SP-2 (Adapt), SP-4 (Adapt) | Explain → Specify → Evaluate |
| 113 | TW-2.2 Spec before build *(Technical Writing v1)* | TW 2 | SP-1 (Adapt), SP-2 (Adapt) | Explain → Direct → Specify |
| 114 | PY-13.1 Building a Python subsystem | 13 | SP-1 (Own), SP-3 (Own), BU-2 (Own), DE-3 (Own) | Explain → Specify → Decompose → Modify → Direct |
| 115 | PY-13.2 Interchangeable components behind contracts | 13 | SP-2 (Own), BU-3 (Own), DE-5 (Own), DE-6 (Own) | Explain → Specify → Build → Direct → Evaluate |
| 116 | PY-13.3 An integrated, reliable workflow | 13 | BU-2 (Own), VE-4 (Own), VE-6 (Own), DE-5 (Own) | Explain → Modify → Debug & Validate → Direct |
| 117 | PY-13.4 Owning AI-assisted Python work | 13 | SP-4 (Own), DE-1 (Own), DE-2 (Own), DE-3 (Own) | Explain → Specify → Direct → Evaluate |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics (Python units)

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | PY-0.4 Run a first program | checking Python is installed; running a script file; the interactive prompt (REPL); `print()`; `input()` always returns text; comments; running the same program with different input; reading a first error: type, message, line number; the app's playground |
|  | PY-0.1 Python as an executing program | Python interpreter mental model; statements and expressions; execution order; values and objects; names/bindings; state changes |
|  | PY-0.3 Tool help versus your own reasoning | AI-generated syntax/code; documentation lookup; IDE assistance; developer intent; assumptions; code comprehension; validation; debugging; technical responsibility; uncertainty identification |
| 1 | PY-1.2 Numbers, booleans and None | integers; floats; booleans; `None`; arithmetic operators including `//`, `%` and `**` (new); comparison and logical operators; conversions with `int()`, `float()`, `str()` (new); turning `input()` text into numbers (new); `abs`, `round`, `min`, `max`, `sum` (new); `math` module basics (new); `decimal` for exact values such as money (awareness, new); equality; truthiness; numeric precision awareness; writing a small program from a blank file (Make); bitwise operators `&`, `|`, `^`, `<<`, `>>` (awareness, new) |
|  | PY-1.7 Text | strings and immutability; indexing and slicing; common methods: `split`, `join`, `strip`, `replace`, `find`, `startswith`, `lower`, `upper`; f-strings and formatting; escape characters and multi-line strings; text from `input()`; basic Unicode awareness (encodings are covered in Stage 8); writing a small program from a blank file (Make) |
|  | PY-1.1 Names, objects and expressions | names versus objects; assignment/binding; reassignment; references; aliasing; mutable versus immutable behavior; literals; expressions; basic operators; evaluation; identity `is`; equality `==`; `None`; object/value mental model |
|  | PY-1.8 Checking code with assert | `assert`; expected value versus actual value; edge cases: empty, zero, one, many; reading an assertion failure; small check functions run by hand (pytest comes in Stage 9); a check that fails on a wrong version; writing a small program from a blank file (Make) |
|  | PY-1.3 Lists and tuples | lists; tuples; indexing; negative indexing; slicing; membership; append/remove/update patterns; sequence unpacking; empty sequences |
|  | PY-1.9 Copies, aliases and nested data | nested sequences; mutation; assignment aliasing; shallow-copy behavior; nested-mutable-structure risks; `copy.copy` / `copy.deepcopy` awareness |
|  | PY-1.4 Mappings | dictionaries; keys/values/items; membership; safe retrieval; insertion/update/removal; iteration; nested mappings; dictionary unpacking; missing-key behavior; structured external/config-style data; writing a small program from a blank file (Make) |
|  | PY-1.5 Choosing data structures | list versus tuple; sets; uniqueness; membership-performance awareness; mutability; hashability awareness; ordering guarantees at useful level; choosing representation; shallow/deep-copy judgment at practical depth; avoid choosing structures by habit alone |
|  | PY-1.6 Specialised collections and the standard library | `collections.Counter`; `collections.defaultdict`; `collections.deque`; counting patterns; grouped accumulation; FIFO/LIFO queue-like usage; when ordinary list/dict is clearer; avoid manually recreating standard collection behavior; how to look things up: `help()`, `dir()`, the official documentation (new); a tour of useful standard-library modules and when to use one instead of writing your own (new); `random` basics (new) |
| 2 | PY-2.1 Conditions | boolean expressions; comparison operators; logical operators; truthiness/falsiness; chained comparisons; `if / elif / else`; membership; identity where appropriate; nested conditions; guard clauses; edge-condition reasoning; `match` statement (supporting); conditional expressions (new); writing a small program from a blank file (Make) |
|  | PY-2.2 Iteration | `for`; `while`; `range`; iteration over lists/dicts/sets; `enumerate`; `zip`; accumulation; nested iteration; `break`; `continue`; loop `else` awareness; mutation-while-iterating pitfalls; `sorted`, `reversed`, `any`, `all` (new); writing a small program from a blank file (Make) |
|  | PY-2.5 Debugging basics | reproduce the failure first; reading a traceback: type, message, line; print-based debugging; shrinking the failing input; one hypothesis, one change, record the result; `breakpoint()` and stepping, introduced; when to stop guessing and ask |
|  | PY-2.3 Comprehensions | list comprehensions; dictionary comprehensions; set comprehensions; filtering; expression transformation; nested-comprehension readability limits; generator-expression preview; assignment expressions `:=` (awareness only); writing a small program from a blank file (Make) |
|  | PY-2.4 Choosing control flow | expression versus branch; branch versus loop; comprehension versus loop; early return awareness; readability; simple versus clever implementation; writing a small program from a blank file (Make) |
| 3 | PY-3.1 Function calls and scope | `def`; parameters versus arguments; call frames conceptual model; local variables; return; implicit `None`; local/global/enclosing/builtin scope; LEGB mental model; `global`/`nonlocal` awareness; recursion awareness; docstrings; writing a small program from a blank file (Make) |
|  | PY-3.6 Recursion | base case and recursive case; the call stack growing and unwinding; `RecursionError` and the depth limit; recursion over nested data; when a loop is clearer |
|  | PY-3.2 Function interfaces | positional arguments; keyword arguments; defaults; mutable-default pitfall; keyword-only parameters; positional-only awareness; `*args`; `**kwargs`; argument unpacking; interface clarity; backwards-compatibility awareness; writing a small program from a blank file (Make) |
|  | PY-3.3 Functions as values | functions as objects; assigning/passing functions; callbacks; lambda expressions; `key=` style callbacks; nested functions; closures at practical depth; avoiding unnecessary functional cleverness; `sorted(key=)`, `min` and `max` with `key=` (new); `functools.partial` awareness (new); `map` and `filter`, and when a comprehension is clearer (new) |
|  | PY-3.4 Coherent functions | coherent function responsibility; input/output boundaries; pure-ish versus stateful functions; avoiding hidden state; side effects; naming; return contracts; small interfaces; distinction from formal SOLID responsibility principles; writing a small program from a blank file (Make) |
|  | PY-3.5 Decomposing a requirement | requirements → function responsibilities; step decomposition; transformation pipelines; function composition; data flow; failure-boundary preview; function-level decomposition boundary |
| 4 | PY-4.1 Exception flow | exception hierarchy awareness; `try`; `except`; specific versus broad catching; `raise`; propagation; traceback; `else`; `finally`; reraising; exception context/chaining awareness |
|  | PY-4.2 Failure contracts | expected domain/application failure; programmer error versus runtime condition; custom exception classes; exception messages; preserving context; translation across Python boundaries; recoverable versus unrecoverable conditions; writing a small program from a blank file (Make) |
|  | PY-4.3 Validation | preconditions; missing input; malformed data; range/value constraints; state invariants; validation versus exception handling; boundary validation; checking and converting user input (new); writing a small program from a blank file (Make) |
|  | PY-4.4 Making failures explicit | propagation; failure boundaries; useful errors; cleanup; preserving context; validation; avoiding silent failure |
| 5 | PY-5.1 Modules and imports | modules; `import x`; `from x import y`; module namespace; import execution; import caching awareness; search path / `sys.path` conceptual awareness; name collisions; circular imports; import-time side effects |
|  | PY-5.2 Splitting code across modules | Python module responsibility; public/internal functions; avoiding kitchen-sink modules; dependency direction at module/import level; import boundaries; cohesion; boundary between Python organization and general software design; writing a small program from a blank file (Make) |
|  | PY-5.3 Packages | package directories; `__init__.py`; absolute imports; relative imports; package API exposure; subpackages; circular dependencies |
|  | PY-5.4 Entry points | module import versus execution; `__name__`; `__main__`; `if __name__ == "__main__"`; `python file.py`; `python -m package.module`; `__main__.py` awareness; keeping side effects out of imports; `sys.argv` and a first look at `argparse` (new); exit codes (new); writing a small program from a blank file (Make); program versus process; exit status as the process's result (from OS / Process) |
|  | PY-0.2 Reading a small Python application | entry point; application logic; data transformation; external services awareness; configuration; persistence awareness; libraries/dependencies; validation; observability awareness; interfaces/boundaries; Python versus adjacent technologies; application responsibility map |
| 6 | PY-6.1 Classes, instances and state | class definitions; instances; `self`; attributes; methods; object identity; attribute access; instance namespace mental model; when a class is appropriate; state changes over time; methods as controlled state transitions; valid versus invalid state |
|  | PY-6.2 Constructing objects | `__init__`; initialization; instance attributes; class attributes; shared mutable class-state risks; defaults; invariants during construction |
|  | PY-6.3 Instance, class and static methods | instance methods; `self`; `@classmethod`; `cls`; alternate constructors; `@staticmethod`; when a module-level function is better; method binding mental model |
|  | PY-6.4 Controlled object interfaces | encapsulation; Python conventions; public/private-by-convention; `_name`; double-underscore name mangling awareness; why name mangling is not true access control; property access; `@property`; setters where justified; invariants; avoiding Java-style accessor boilerplate |
|  | PY-6.8 Special methods | `__repr__`; `__str__`; `__eq__`; ordering awareness; `__len__`; selected protocol methods as needed; operator/protocol behavior; avoid unnecessary operator overloading |
|  | PY-6.9 Data classes and named values | `@dataclass`; generated initializer; representation/equality behavior; defaults; `field`; mutable-default concerns; frozen awareness; dataclass versus ordinary class; dataclass versus dictionary; `Enum` awareness/use for bounded named values; when plain constants remain clearer |
|  | PY-6.5 Inheritance and resolution | base/subclasses; inherited methods/attributes; overriding; `super()`; MRO; `isinstance`; `issubclass`; multiple inheritance awareness; cooperative inheritance awareness; common inheritance mistakes |
|  | PY-6.6 Polymorphism and shared contracts | polymorphism; duck typing; substitutability at Python implementation level; behavioral contracts; ABC awareness; `abc.ABC`; abstract methods where relevant; interface-like reasoning; avoiding inheritance merely for reuse; distinction from formal SOLID/LSP design analysis |
|  | PY-6.7 Composition and object responsibility | composition; has-a versus is-a; dependency relationships; delegation; responsibility boundaries at Python object level; class-versus-function judgment; class-versus-dataclass judgment; plain-data-structure judgment; avoiding unnecessary OOP; distinction from full LLD/pattern/SOLID ownership |
| 7 | PY-7.1 Iterables and iterators | iterable; iterator; `iter()`; `next()`; iterator exhaustion; single-pass behavior; iteration protocol concept; common iterable types; `itertools` basics (new) |
|  | PY-7.2 Generators | `yield`; generator functions; generator objects; generator expressions; lazy evaluation; memory/streaming motivation; state suspension; common exhaustion mistakes |
|  | PY-7.3 Decorators | functions as values; nested functions/closures; wrapper function; decorator syntax; arguments; `functools.wraps`; parameterized-decorator awareness; common framework usage; when not to write decorators; `functools.lru_cache` (new) |
|  | PY-7.4 Context managers | `with`; `__enter__`; `__exit__`; exception interaction; file/resource cleanup; `contextlib` awareness; custom context-manager concept; file handles and resource leaks (from OS / Process) |
|  | PY-7.5 Type annotations | annotations; runtime-versus-static distinction; built-in generic forms; unions; optional/`None`; return types; type aliases; callable types at useful depth; type narrowing awareness; type-checker role |
|  | PY-7.6 Interface-style type contracts | Protocol awareness/use; structural typing; generic type variables at practical depth; collections/interfaces; avoiding typing over-complexity; interaction with polymorphic design |
| 8 | PY-8.1 Files and paths | `pathlib.Path`; relative/absolute paths; existence; directories; file reading/writing; modes; context-managed files; text versus binary awareness; encoding awareness; missing paths; filesystem errors; bytes and text encodings (new); current working directory and why relative paths break (from OS / Process) |
|  | PY-8.2 Structured data | JSON; Python ↔ JSON types; load/dump; malformed data; serialization boundaries; nested structures; data validation; CSV awareness if useful; unsafe serialization awareness (`pickle` caution, not mastery); the `csv` module (new) |
|  | PY-8.6 Pattern matching in text | `re` module basics; `search`, `match`, `findall`, `sub`; groups; raw strings; common patterns; greedy versus lazy matching; when string methods are clearer; testing patterns on edge cases; catastrophic backtracking awareness |
|  | PY-8.3 Configuration | environment variables; configuration files; defaults; required settings; type conversion/validation; config objects; secrets versus non-secret config; avoiding hardcoded environment-specific values; `.env` as an implementation option, not a roadmap requirement |
|  | PY-8.7 Command-line programs and running other programs | `argparse`: options, arguments, help; `sys.argv`; standard input, output and error; exit codes; `subprocess.run` with argument lists; avoiding shell injection; capturing output; timeouts; environment variables; parent and child processes (from OS / Process) |
|  | PY-8.4 Calling HTTP services | HTTP client library usage concept; URL/parameters/headers/body; status codes; JSON responses; timeout; connectivity; retry awareness; validation; failure boundaries; dependency/library documentation; HTTP client capability versus API-server design |
|  | PY-8.5 Dates, times and timezones | `datetime`; `date`; `timedelta` at practical depth; naive versus timezone-aware datetime values; UTC; ISO 8601 awareness; `isoformat()`; `fromisoformat()`; timezone conversion awareness; `zoneinfo` where useful; timestamp comparison/arithmetic; external API/persistence boundary considerations |
| 9 | PY-9.1 Debugging | tracebacks; exception location; stack frames; reproduction; minimal failing case; print-versus-debugger judgment; breakpoint/debugger awareness; inspecting state; hypothesis testing; binary-search-style narrowing; root cause versus symptom |
|  | PY-9.2 Logging and runtime evidence | logging versus `print`; levels; named loggers; logger hierarchy awareness; handlers; formatting; structured/contextual information; exception logging; avoiding sensitive data; avoiding log noise; configuration awareness |
|  | PY-9.3 Behavioural tests with pytest | arrange-act-assert concept; pytest discovery/naming; test functions/cases; plain assertions; `pytest.raises`; happy path; edge cases; failure paths; deterministic tests; regression tests; `@pytest.mark.parametrize`; basic fixtures; basic fixture-scope awareness where useful; standard-library `unittest` awareness |
|  | PY-9.4 Isolating code under test | dependencies; fakes/stubs/mocks conceptual distinctions; patching awareness; dependency injection as test aid; avoiding over-mocking; external network/service isolation; test boundaries |
|  | PY-9.5 When passing is not proof | false confidence; insufficient assertions; wrong test target; missing edge cases; happy-path-only testing; AI-generated tests; requirement-to-test alignment; validation evidence |
|  | PY-9.6 Measuring runtime | `time.perf_counter()`; basic timing; measurement variability awareness; repeat measurements enough to avoid obvious false conclusions; basic profiler awareness/use; hot-path identification; CPU-bound versus I/O-bound symptoms; measure-before-optimize principle; deciding when deeper investigation is justified; memory pressure as a runtime limit (awareness, from OS / Process) |
| 10 | PY-10.1 Environments | interpreter; environment; `venv`; activation; installed packages; project-local environment; multiple Python versions awareness; environment mismatch; `python`/`pip` alignment; tool-specific environment managers as execution choices |
|  | PY-10.2 Dependencies | `pip`; package-index awareness; package versions; dependency declarations; requirements-style files; dependency groups awareness; direct/transitive dependency concept; pinning/ranges at useful depth; reproducibility; upgrade risks; `uv`, Poetry, Conda or similar tools as implementation choices, not roadmap requirements |
|  | PY-10.3 Project metadata and packaging | `pyproject.toml`; `[build-system]`; `[project]`; dependencies; tool configuration awareness; package layout; build-backend concept; editable/local installation awareness; distribution package versus import package; basic build/distribution flow |
|  | PY-10.4 Diagnosing install and environment failures | wrong interpreter; missing dependency; incompatible versions; editable/local install issues; import package versus distribution-name mismatch; environment recreation; reproducibility checks; locating a failure: application, process, filesystem or environment (from OS / Process) |
|  | PY-10.5 Quality gates | formatter role; linter role; type-checker role; tests as a distinct behavioral-evidence mechanism; tool configuration in project metadata; running checks locally; interpreting and fixing actionable findings; suppressing/ignoring findings only with justification; examples may include Ruff, Black, mypy, Pyright without requiring mastery of any one tool |
| 11 | PY-11.1 Concurrency mental model | blocking; synchronous execution; concurrency; parallelism distinction; CPU-bound versus I/O-bound; thread/process awareness; async I/O; when async adds complexity without value; distinction between Python mechanics and general OS/process theory |
|  | PY-11.5 Threads and processes | `threading` basics; `concurrent.futures`: thread and process pools; `multiprocessing` awareness; the GIL and what it means; shared state and race conditions; locks (awareness); choosing thread, process or async; passing data between processes; cost of starting workers |
|  | PY-11.2 Tracing async code | `async def`; coroutine objects; `await`; event-loop mental model; tasks; scheduling; sequential awaits versus concurrent tasks; gather-style coordination concept |
|  | PY-11.3 Concurrent I/O | multiple concurrent calls; task creation; gathering results; blocking sync calls; async-compatible libraries; async context-manager awareness; async-iteration awareness |
|  | PY-11.4 Async failures | forgotten `await`; coroutine-not-awaited failures; blocking calls; task exceptions; timeout awareness; cancellation awareness; exception propagation; leaked tasks/resources; unnecessary async complexity; graceful versus abrupt shutdown (from OS / Process) |
| 12 | PY-12.1 Navigating an unfamiliar codebase | directory/package inspection; entry points; imports; call-graph reasoning; configuration; recognition of service/domain layers without claiming their architectural ownership; tests as behavioral evidence; search/navigation tooling; identifying likely change boundaries |
|  | PY-12.2 Learning a library from its documentation | API documentation; signatures; examples; source inspection where useful; minimal experiments; version-specific docs; assumptions; library conventions; AI-assisted documentation use; verifying generated library usage; distinguishing authoritative source material from assistant explanation |
|  | PY-12.3 Organising a Python application | Python responsibility boundaries; import/dependency direction; modules/packages; configuration boundaries; side-effect boundaries; avoiding circular coupling; appropriate Python abstraction; recognition of service-layer concepts; boundary between Python organization and Software Design / Backend ownership |
|  | PY-12.4 Changing an existing subsystem safely | change impact; existing tests; new regression tests; interface stability; refactoring versus behavior change; incremental changes; validation; dependency effects |
|  | PY-12.5 Refactoring | duplication; cohesion; coupling; extraction; naming; Python interfaces; decomposition; avoiding premature abstractions; maintaining behavior; recognizing when a problem has moved beyond Python refactoring into broader design |
| 13 | PY-13.1 Building a Python subsystem | input boundary; structured data; validation; transformation; functions/classes; external dependency/client; failure propagation; typing; configuration; tests |
|  | PY-13.2 Interchangeable components behind contracts | contracts/interfaces; composition; polymorphism/protocols; dependency boundaries; validation; failure translation; testability; replacement/fakes; generic components rather than retriever/model/service-specific ownership |
|  | PY-13.3 An integrated, reliable workflow | configuration; boundary validation; typing; exceptions; structured/contextual logs; tests; external calls; async selection; cleanup; observable failure; explicit boundary: reliable Python workflow does not equal full production-system competence |
|  | PY-13.4 Owning AI-assisted Python work | prompt/requirement framing; code generation; code review; reasoning about generated dependencies; checking API/library assumptions; tracing generated code; debugging; generating/reviewing tests; rejecting inappropriate solutions; validating outcomes; identifying uncertainty; consulting authoritative documentation when generated claims are uncertain; future cross-cutting extraction candidate after multi-roadmap evidence |

## Unit details

### Stage 0

#### PY-0.4 Run a first program

- **Objective:** Can set up and run a Python program, give it text input and output, and read a first error message.
- **The concept (Explain):** A program is text that the Python interpreter reads and runs from top to bottom.
- **Target skills:** CO-1 to Understand; VE-4 to Understand
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts the output of a 5-line script before running it. VE-4: names the line and kind of error in a first error message.
- **Topics:** checking Python is installed; running a script file; the interactive prompt (REPL); `print()`; `input()` always returns text; comments; running the same program with different input; reading a first error: type, message, line number; the app's playground
- **Prerequisites:** None | **Importance:** Foundational | **Integration link:** Entire Python roadmap

#### PY-0.1 Python as an executing program

- **Objective:** Can explain at a useful level how Python source becomes executing program behavior and trace values, state and control through a small program.
- **The concept (Explain):** Python runs statements in order, and each statement can change the program's state.
- **Target skills:** CO-1 to Understand; CO-2 to Understand; CO-6 to Understand
- **Methods:** Explain → Predict → Trace
- **Outcome (measured at unit end):** CO-1: predicts the output of a 10-line script. CO-2: fills in a state table step by step and explains any mismatch.
- **Topics:** Python interpreter mental model; statements and expressions; execution order; values and objects; names/bindings; state changes
- **Prerequisites:** PY-0.4 | **Importance:** Foundational | **Integration link:** Entire Python roadmap
- **Changed in v4:** topics thinned: call flow (PY-3.1), exceptions as altered control flow (PY-4.1) and modules, functions and objects as future layers removed

#### PY-0.3 Tool help versus your own reasoning

- **Objective:** Can distinguish professional tool assistance from technical reasoning and verification the developer must retain.
- **The concept (Explain):** A tool can write code, but the developer still owns the intent, the checking and the decision.
- **Target skills:** DE-2 to Understand; DE-3 to Understand; DE-4 to Understand
- **Methods:** Explain → Direct
- **Outcome (measured at unit end):** DE-3: sorts an AI session's contributions into 'fine to delegate' and 'must own'. DE-2: says what to ask a tool to explain rather than do. DE-4: names which source would settle a question. The three always-on habits are introduced here.
- **Topics:** AI-generated syntax/code; documentation lookup; IDE assistance; developer intent; assumptions; code comprehension; validation; debugging; technical responsibility; uncertainty identification
- **Prerequisites:** PY-0.4 | **Importance:** Core | **Integration link:** Entire roadmap; future cross-cutting AI-assisted engineering ownership


### Stage 1

#### PY-1.2 Numbers, booleans and None

- **Objective:** Can use and reason about numbers, booleans and `None`, including operators, conversions and precision. *(changed from v2)*
- **The concept (Explain):** Every value has a type, and the type decides what operations mean.
- **Target skills:** CO-1 to Apply; VE-6 to Apply
- **Methods:** Explain → Predict → Debug & Validate → Build
- **Outcome (measured at unit end):** CO-1: predicts results of mixed int/float/bool expressions. VE-6: tries zero, negative and text-that-is-not-a-number on a small calculator. Make (VE-6): a rice-donation calculator that reads the price per kilogram and the kilograms with `input()`, converts them, and prints the total rounded to 2 decimal places, checked on an amount that needs rounding.
- **Topics:** integers; floats; booleans; `None`; arithmetic operators including `//`, `%` and `**` (new); comparison and logical operators; conversions with `int()`, `float()`, `str()` (new); turning `input()` text into numbers (new); `abs`, `round`, `min`, `max`, `sum` (new); `math` module basics (new); `decimal` for exact values such as money (awareness, new); equality; truthiness; numeric precision awareness; writing a small program from a blank file (Make); bitwise operators `&`, `|`, `^`, `<<`, `>>` (awareness, new)
- **Prerequisites:** PY-0.1 | **Importance:** Foundational | **Integration link:** All data-processing work
- **Changed in v4:** Make step added as Build, credited to VE-6 (recommendation 1); bitwise operators added as awareness (recommendation 5); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-1.7 Text

- **Objective:** Can read, build and transform text with indexing, slicing, string methods and f-strings.
- **The concept (Explain):** A string is an ordered, unchangeable sequence of characters.
- **Target skills:** BU-1 to Apply; VE-6 to Apply
- **Methods:** Explain → Modify → Debug & Validate → Build
- **Outcome (measured at unit end):** BU-1: adapts a string formatter to a new format without breaking old cases. VE-6: tries empty, whitespace-only and very long text. Make (VE-6): a pickup-slip name formatter that cleans and reformats one typed family name, including empty and whitespace-only input.
- **Topics:** strings and immutability; indexing and slicing; common methods: `split`, `join`, `strip`, `replace`, `find`, `startswith`, `lower`, `upper`; f-strings and formatting; escape characters and multi-line strings; text from `input()`; basic Unicode awareness (encodings are covered in Stage 8); writing a small program from a blank file (Make)
- **Prerequisites:** PY-1.2 | **Importance:** Foundational | **Integration link:** All text and data-processing work
- **Changed in v4:** Make step added as Build, credited to VE-6 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-1.1 Names, objects and expressions

- **Objective:** Can reason about Python names, objects, assignments and expression evaluation sufficiently to predict state changes.
- **The concept (Explain):** A name points to an object; assignment moves the name, it does not copy the object.
- **Target skills:** CO-1 to Apply; CO-2 to Apply; CO-6 to Apply
- **Methods:** Explain → Predict → Trace
- **Outcome (measured at unit end):** CO-1 and CO-2: predicts then traces state after a chain of assignments with aliasing, and `is` versus `==`.
- **Topics:** names versus objects; assignment/binding; reassignment; references; aliasing; mutable versus immutable behavior; literals; expressions; basic operators; evaluation; identity `is`; equality `==`; `None`; object/value mental model
- **Prerequisites:** PY-1.2, PY-1.7 | **Importance:** Foundational | **Integration link:** Functions, collections, OOP, debugging

#### PY-1.8 Checking code with assert

- **Objective:** Can write simple `assert` checks that state what a function should return, including edge cases, and read a failing check.
- **The concept (Explain):** A check is a prediction written as code that passes or fails.
- **Target skills:** VE-1 to Apply
- **Methods:** Explain → Debug & Validate → Build
- **Outcome (measured at unit end):** VE-1: writes checks, including edge cases, that fail on a plausible wrong version of a short function they were shown. Make (VE-1): a small script that totals a family's parcel weights, with its own `assert` checks that must fail on a planted wrong version. **Fix:** v4 asks for a function here, but functions are taught in PY-3.1, so the new wording uses a script.
- **Topics:** `assert`; expected value versus actual value; edge cases: empty, zero, one, many; reading an assertion failure; small check functions run by hand (pytest comes in Stage 9); a check that fails on a wrong version; writing a small program from a blank file (Make)
- **Prerequisites:** PY-1.1 | **Importance:** Foundational | **Integration link:** Stage 4 failure checks; Stage 9 behavioral testing
- **Changed in v4:** Make step added as Build, credited to VE-1 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-1.3 Lists and tuples

- **Objective:** Can use and change lists and tuples while reasoning correctly about indexing, slicing, unpacking and empty sequences.
- **The concept (Explain):** A list holds objects in order and can change; a tuple holds them in order and cannot.
- **Target skills:** CO-2 to Apply; VE-2 to Apply
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-2: traces indexing, slicing and appends through a short program. VE-2: finds the off-by-one slice in an AI-written list function and names the input that exposes it.
- **Topics:** lists; tuples; indexing; negative indexing; slicing; membership; append/remove/update patterns; sequence unpacking; empty sequences
- **Prerequisites:** PY-1.1, PY-1.8 | **Importance:** Foundational | **Integration link:** Data processing; Cross-Link → Practical DSA
- **Changed in v4:** VE-2 goal lowered Adapt to Apply (first appearance); CO-2 goal kept at Apply here; Adapt moves to the new PY-1.9; split: copying, aliasing and nested data moved to the new PY-1.9

#### PY-1.9 Copies, aliases and nested data (new unit)

- **Objective:** Can predict and trace what changes when two names share a list or when lists are nested, and copy deliberately.
- **The concept (Explain):** Two names can point to the same list, so changing it through one name changes what the other sees.
- **Target skills:** CO-2 to Adapt; VE-2 to Adapt
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-2: traces aliasing and mutation through a short program with nested lists. VE-2: finds the shared-list bug in AI-written code that builds a grid with `[[0] * 3] * 3`.
- **Topics:** nested sequences; mutation; assignment aliasing; shallow-copy behavior; nested-mutable-structure risks; `copy.copy` / `copy.deepcopy` awareness
- **Prerequisites:** PY-1.3 | **Importance:** Foundational | **Integration link:** Functions, OOP, debugging
- **Changed in v4:** new unit, split from PY-1.3 (recommendation 6)

#### PY-1.4 Mappings

- **Objective:** Can represent, retrieve, modify and validate structured data using mappings.
- **The concept (Explain):** A dictionary finds a value by its key instead of its position.
- **Target skills:** CO-3 to Apply; BU-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Build
- **Outcome (measured at unit end):** CO-3: explains AI code that reads nested config. BU-1: adapts it to safe retrieval. VE-6: tests a missing key. Make (BU-1): extends their own household-lookup script (family ID to household size) to a second field, dietary needs, without breaking the first, handling a missing family ID with a safe lookup.
- **Topics:** dictionaries; keys/values/items; membership; safe retrieval; insertion/update/removal; iteration; nested mappings; dictionary unpacking; missing-key behavior; structured external/config-style data; writing a small program from a blank file (Make)
- **Prerequisites:** PY-1.3, PY-1.8 | **Importance:** Foundational | **Integration link:** JSON/configuration; Cross-Link → Backend Engineering and AI Engineering data boundaries
- **Changed in v4:** CO-3 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to BU-1 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-1.5 Choosing data structures

- **Objective:** Can choose among lists, tuples, sets and mappings based on data responsibility, mutability, uniqueness, ordering and access requirements.
- **The concept (Explain):** The data's job (order, uniqueness, lookup, change) decides which structure fits.
- **Target skills:** DE-6 to Apply; DE-1 to Apply
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** DE-6: compares two structures for a stated need by their consequences and chooses with a reason. DE-1: accepts or rejects an AI's choice with a reason.
- **Topics:** list versus tuple; sets; uniqueness; membership-performance awareness; mutability; hashability awareness; ordering guarantees at useful level; choosing representation; shallow/deep-copy judgment at practical depth; avoid choosing structures by habit alone
- **Prerequisites:** PY-1.2 to PY-1.4 | **Importance:** Core | **Integration link:** Cross-Link → Practical DSA: structure choice and complexity reasoning

#### PY-1.6 Specialised collections and the standard library

- **Objective:** Can use common specialized standard-library collection types when they simplify counting, grouped accumulation or queue-like processing.
- **The concept (Explain):** Python ships with tools for common jobs, and the documentation says how to use them.
- **Target skills:** BU-3 to Apply; DE-4 to Apply
- **Methods:** Explain → Build → Direct
- **Outcome (measured at unit end):** BU-3: replaces hand-rolled counting in a draft with `Counter`, found in the documentation. DE-4: checks an API detail in the official docs instead of trusting recall.
- **Topics:** `collections.Counter`; `collections.defaultdict`; `collections.deque`; counting patterns; grouped accumulation; FIFO/LIFO queue-like usage; when ordinary list/dict is clearer; avoid manually recreating standard collection behavior; how to look things up: `help()`, `dir()`, the official documentation (new); a tour of useful standard-library modules and when to use one instead of writing your own (new); `random` basics (new)
- **Prerequisites:** PY-1.4, PY-1.5 | **Importance:** Supporting | **Integration link:** Cross-Link → Practical DSA


### Stage 2

#### PY-2.1 Conditions

- **Objective:** Can construct and reason about conditional logic that correctly handles expected, missing and boundary conditions.
- **The concept (Explain):** A condition decides which path the program takes, and boundaries are where paths are most likely wrong.
- **Target skills:** VE-1 to Adapt; VE-6 to Adapt; SP-1 to Apply
- **Methods:** Explain → Specify → Debug & Validate → Build
- **Outcome (measured at unit end):** SP-1: lists the boundary questions before coding a rule. VE-1 and VE-6: write checks at the boundaries that catch a planted wrong version. Make (VE-6): a parcel-size checker that sorts a family into one of four parcel sizes by household size, including the boundary values, and refuses an empty or out-of-range answer with a clear message.
- **Topics:** boolean expressions; comparison operators; logical operators; truthiness/falsiness; chained comparisons; `if / elif / else`; membership; identity where appropriate; nested conditions; guard clauses; edge-condition reasoning; `match` statement (supporting); conditional expressions (new); writing a small program from a blank file (Make)
- **Prerequisites:** Stage 1 | **Importance:** Foundational | **Integration link:** Validation, filtering, control flow
- **Changed in v4:** SP-1 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-6 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-2.2 Iteration

- **Objective:** Can process collections through iteration while tracking state and controlling execution correctly.
- **The concept (Explain):** A loop repeats steps while a condition holds or while items remain, and carries state from one pass to the next.
- **Target skills:** VE-1 to Adapt; VE-2 to Adapt; VE-5 to Apply; CO-1 to Adapt
- **Methods:** Explain → Predict → Trace → Debug & Validate → Build
- **Outcome (measured at unit end):** Milestone 1 unit. Given an AI-written loop function with a planted bug, the learner writes checks (VE-1), finds the bug (VE-2) and proves the fix (VE-5). Make (VE-1): a morning-queue summary that counts families, totals parcels and flags any family over the parcel limit, with checks for an empty and a one-family queue. CO-1: predicts the output of a loop with `break` and `continue` before running it.
- **Topics:** `for`; `while`; `range`; iteration over lists/dicts/sets; `enumerate`; `zip`; accumulation; nested iteration; `break`; `continue`; loop `else` awareness; mutation-while-iterating pitfalls; `sorted`, `reversed`, `any`, `all` (new); writing a small program from a blank file (Make)
- **Prerequisites:** Stage 1 | **Importance:** Foundational | **Integration link:** Data processing; Cross-Link → Practical DSA
- **Changed in v4:** VE-5 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-1 (recommendation 1); CO-1 (Adapt) added: loop-output prediction (recommendation 7); Predict added (recommendation 7); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-2.5 Debugging basics

- **Objective:** Can reproduce a failure, read its traceback and find the cause by testing one idea at a time.
- **The concept (Explain):** Debugging is testing one guess about the cause at a time against evidence.
- **Target skills:** VE-3 to Apply; VE-4 to Apply
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-3: states a cause, tests one change, records whether it held. VE-4: names the line and likely cause of a common error before asking for help.
- **Topics:** reproduce the failure first; reading a traceback: type, message, line; print-based debugging; shrinking the failing input; one hypothesis, one change, record the result; `breakpoint()` and stepping, introduced; when to stop guessing and ask
- **Prerequisites:** PY-2.2 | **Importance:** Foundational | **Integration link:** Stage 4 exceptions; Stage 9 debugging (deepens this unit)

#### PY-2.3 Comprehensions

- **Objective:** Can express straightforward collection transformations using comprehensions when they improve clarity and avoid them when explicit control flow is clearer.
- **The concept (Explain):** A comprehension builds a new collection from an old one in a single expression.
- **Target skills:** BU-2 to Apply; BU-4 to Apply
- **Methods:** Explain → Modify → Evaluate → Build
- **Outcome (measured at unit end):** BU-2: refines an AI comprehension to meet a spec line by line. BU-4: replaces a nested one with a clear loop where that is simpler. Make (BU-2): writes a comprehension from a one-line spec (today's urgent requests from the queue), then brings it up to every line of the spec.
- **Topics:** list comprehensions; dictionary comprehensions; set comprehensions; filtering; expression transformation; nested-comprehension readability limits; generator-expression preview; assignment expressions `:=` (awareness only); writing a small program from a blank file (Make)
- **Prerequisites:** PY-2.1, PY-2.2 | **Importance:** Core | **Integration link:** Data transformation; Stage 7 lazy processing
- **Changed in v4:** Make step added as Build, credited to BU-2 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-2.4 Choosing control flow

- **Objective:** Can choose an appropriate control-flow form without unnecessary complexity.
- **The concept (Explain):** Several control-flow forms can do the same job; the clearest one wins.
- **Target skills:** DE-6 to Apply; BU-4 to Apply
- **Methods:** Explain → Evaluate → Modify → Build
- **Outcome (measured at unit end):** DE-6: compares two forms by readability and risk and chooses with a reason. BU-4: rewrites an over-clever AI solution in the simpler form, keeping behaviour. Make (BU-4): writes the simplest correct form (expression, branch, loop or comprehension) for three small pantry specs: a stock-reserve check, a queue count and a list of family names.
- **Topics:** expression versus branch; branch versus loop; comprehension versus loop; early return awareness; readability; simple versus clever implementation; writing a small program from a blank file (Make)
- **Prerequisites:** PY-2.1 to PY-2.3 | **Importance:** Core | **Integration link:** All subsequent coding
- **Changed in v4:** Make step added as Build, credited to BU-4 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)


### Stage 3

#### PY-3.1 Function calls and scope

- **Objective:** Can trace function calls, argument binding, local state, return values and scope through multi-function code.
- **The concept (Explain):** A call creates its own space for local names, and where a name is looked up decides which value it finds.
- **Target skills:** CO-2 to Adapt; CO-3 to Adapt; CO-6 to Adapt; BU-2 to Apply
- **Methods:** Explain → Trace → Build
- **Outcome (measured at unit end):** CO-2: traces multi-function code through argument binding, scope and implicit `None`. CO-3: explains AI code accurately, including the empty case. Make (BU-2): three small functions with parameters and return values (parcels for a household size, a family's label, a day's total), written from a short spec and refined until every spec line holds.
- **Topics:** `def`; parameters versus arguments; call frames conceptual model; local variables; return; implicit `None`; local/global/enclosing/builtin scope; LEGB mental model; `global`/`nonlocal` awareness; recursion awareness; docstrings; writing a small program from a blank file (Make)
- **Prerequisites:** Stages 1–2 | **Importance:** Foundational | **Integration link:** All structured programs
- **Changed in v4:** BU-2 (Apply) added: credits the Make step; Make step added as Build, credited to BU-2 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-3.6 Recursion

- **Objective:** Can write and trace a recursive function with a correct base case, and judge when a loop is clearer.
- **The concept (Explain):** A recursive function solves a smaller copy of the same problem and stops at a base case.
- **Target skills:** CO-2 to Apply; VE-2 to Apply
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-2: traces a recursive call stack. VE-2: finds the missing or wrong base case in an AI-written function.
- **Topics:** base case and recursive case; the call stack growing and unwinding; `RecursionError` and the depth limit; recursion over nested data; when a loop is clearer
- **Prerequisites:** PY-3.1 | **Importance:** Core | **Integration link:** Cross-Link → Practical DSA; nested data

#### PY-3.2 Function interfaces

- **Objective:** Can design and call Python functions using parameter forms appropriate to a clear and maintainable interface.
- **The concept (Explain):** A function's parameters are its promise to callers; changing them can break the callers.
- **Target skills:** BU-1 to Adapt; DE-1 to Adapt; VE-2 to Adapt
- **Methods:** Explain → Modify → Evaluate → Debug & Validate → Build
- **Outcome (measured at unit end):** DE-1: judges an AI function's parameter design. BU-1: adapts its interface without breaking callers. VE-2: finds the mutable-default bug. Make (BU-1): adds keyword-only options with safe defaults (dietary needs, pickup window) to their own allocation function, keeping old calls working.
- **Topics:** positional arguments; keyword arguments; defaults; mutable-default pitfall; keyword-only parameters; positional-only awareness; `*args`; `**kwargs`; argument unpacking; interface clarity; backwards-compatibility awareness; writing a small program from a blank file (Make)
- **Prerequisites:** PY-3.1 | **Importance:** Foundational | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering
- **Changed in v4:** Make step added as Build, credited to BU-1 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-3.3 Functions as values

- **Objective:** Can work with functions as values where callbacks or configurable behavior genuinely simplify a design.
- **The concept (Explain):** A function is an object, so it can be passed to and returned from other functions.
- **Target skills:** CO-3 to Apply; CO-4 to Apply; DE-1 to Apply
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-3: explains an AI callback or closure. CO-4: states in one sentence what it is for. DE-1: keeps or removes it with a reason.
- **Topics:** functions as objects; assigning/passing functions; callbacks; lambda expressions; `key=` style callbacks; nested functions; closures at practical depth; avoiding unnecessary functional cleverness; `sorted(key=)`, `min` and `max` with `key=` (new); `functools.partial` awareness (new); `map` and `filter`, and when a comprehension is clearer (new)
- **Prerequisites:** PY-3.1 | **Importance:** Core | **Integration link:** Decorators, event/callback patterns
- **Changed in v4:** `map` and `filter` added (recommendation 5)

#### PY-3.4 Coherent functions

- **Objective:** Can design and modify functions with coherent responsibilities, clear inputs and explicit outputs.
- **The concept (Explain):** A function should do one clear job with explicit inputs and outputs.
- **Target skills:** SP-1 to Adapt; SP-2 to Apply; SP-4 to Apply; VE-1 to Adapt
- **Methods:** Explain → Specify → Debug & Validate → Build
- **Outcome (measured at unit end):** SP-1: lists the open questions and assumptions before specifying. SP-2: writes a spec (inputs, outputs, 3–5 examples) before code. SP-4: names the missing detail in a prompt that produced wrong code. VE-1: turns the spec's examples into checks. Make (VE-1): a pure function written from a written contract (a household's parcel allowance), with checks that fail on a wrong version they have not seen.
- **Topics:** coherent function responsibility; input/output boundaries; pure-ish versus stateful functions; avoiding hidden state; side effects; naming; return contracts; small interfaces; distinction from formal SOLID responsibility principles; writing a small program from a blank file (Make)
- **Prerequisites:** PY-3.1, PY-3.2 | **Importance:** Foundational | **Integration link:** Cross-Link → Software Design / OOD / LLD
- **Changed in v4:** SP-2 goal lowered Adapt to Apply (first appearance); SP-4 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-1 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-3.5 Decomposing a requirement

- **Objective:** Can decompose a small engineering requirement into cooperating functions and explain its resulting data flow.
- **The concept (Explain):** A requirement becomes a set of small cooperating functions, each easy to check on its own.
- **Target skills:** SP-1 to Adapt; SP-3 to Apply; BU-2 to Adapt; DE-3 to Apply
- **Methods:** Explain → Specify → Decompose → Modify → Direct
- **Outcome (measured at unit end):** SP-1: asks the clarifying questions for a requirement. SP-3: splits it into functions with clear inputs and outputs. DE-3: decides which piece to delegate. BU-2: has an AI build one piece and refines it to spec.
- **Topics:** requirements → function responsibilities; step decomposition; transformation pipelines; function composition; data flow; failure-boundary preview; function-level decomposition boundary
- **Prerequisites:** PY-3.4 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering; System Architecture at larger decomposition levels
- **Changed in v4:** SP-3 goal lowered Adapt to Apply (first appearance); DE-3 goal lowered Adapt to Apply (was Understand in PY-0.3; one rung at a time)


### Stage 4

#### PY-4.1 Exception flow

- **Objective:** Can trace, raise and handle Python exceptions at appropriate boundaries without hiding programmer errors.
- **The concept (Explain):** An exception interrupts normal flow and travels up the calls until something handles it.
- **Target skills:** CO-2 to Adapt; VE-4 to Adapt; DE-1 to Adapt; DE-2 to Apply
- **Methods:** Explain → Trace → Debug & Validate → Evaluate → Direct
- **Outcome (measured at unit end):** CO-2 and VE-4: follow a multi-frame traceback through code they did not write. DE-2: asks a tool to explain it, then fixes it themself. DE-1: rejects an AI's broad `except` that hides a programmer error.
- **Topics:** exception hierarchy awareness; `try`; `except`; specific versus broad catching; `raise`; propagation; traceback; `else`; `finally`; reraising; exception context/chaining awareness
- **Prerequisites:** Stage 3 | **Importance:** Foundational | **Integration link:** Reliability/testing; Cross-Link → Backend Engineering and AI Engineering
- **Changed in v4:** DE-2 goal lowered Adapt to Apply (was Understand in PY-0.3; one rung at a time)

#### PY-4.2 Failure contracts

- **Objective:** Can design meaningful failure contracts for Python application code, including when custom exceptions are justified.
- **The concept (Explain):** A function promises both what it returns and which failures it raises.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-4 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Specify → Decompose → Debug & Validate → Build
- **Outcome (measured at unit end):** SP-1: lists the failures a function could meet. SP-2: specifies which it raises and why. SP-4: spots a failure case the spec leaves out. VE-1: writes checks that the right exception is raised. Make (VE-1): an allocation function that raises a custom exception for each documented failure (out of stock, duplicate claim), with `assert`-based checks for each.
- **Topics:** expected domain/application failure; programmer error versus runtime condition; custom exception classes; exception messages; preserving context; translation across Python boundaries; recoverable versus unrecoverable conditions; writing a small program from a blank file (Make)
- **Prerequisites:** PY-4.1 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering failure boundaries; AI Engineering provider/tool boundaries
- **Changed in v4:** Make step added as Build, credited to VE-1 (recommendation 1); Decompose added as a helper for SP-1 and SP-2 (recommendation 7); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-4.3 Validation

- **Objective:** Can validate inputs and state at appropriate Python boundaries before invalid data propagates.
- **The concept (Explain):** Bad data should be stopped at the boundary, before it travels further.
- **Target skills:** BU-1 to Adapt; VE-6 to Adapt; DE-5 to Apply
- **Methods:** Explain → Modify → Debug & Validate → Direct → Build
- **Outcome (measured at unit end):** BU-1: adds boundary validation to AI code. VE-6: writes hostile and malformed inputs that must be rejected. DE-5: treats all input as untrusted until checked. Make (VE-6): a validator for one family's intake record that returns clear error messages for missing, malformed (including text that is not a number) and out-of-range fields.
- **Topics:** preconditions; missing input; malformed data; range/value constraints; state invariants; validation versus exception handling; boundary validation; checking and converting user input (new); writing a small program from a blank file (Make)
- **Prerequisites:** Stages 2–3 | **Importance:** Core | **Integration link:** Configuration; Cross-Link → Backend Engineering input validation; AI Engineering input/tool boundaries
- **Changed in v4:** DE-5 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-6 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-4.4 Making failures explicit

- **Objective:** Can modify unreliable multi-function Python code so failures become explicit, diagnosable and testable.
- **The concept (Explain):** A failure that is silent is worse than one that is loud, because nobody can diagnose it.
- **Target skills:** VE-3 to Adapt; VE-5 to Adapt; BU-5 to Apply
- **Methods:** Explain → Debug & Validate → Modify
- **Outcome (measured at unit end):** VE-3: finds a silent failure by hypothesis. BU-5: fixes it one change at a time. VE-5: proves it with a failing-then-passing check.
- **Topics:** propagation; failure boundaries; useful errors; cleanup; preserving context; validation; avoiding silent failure
- **Prerequisites:** PY-4.1 to PY-4.3 | **Importance:** Core | **Integration link:** Reliable multi-function Python flow; Stage 9
- **Changed in v4:** BU-5 goal lowered Adapt to Apply (first appearance)


### Stage 5

#### PY-5.1 Modules and imports

- **Objective:** Can reason about Python module namespaces and import resolution sufficiently to diagnose common import failures.
- **The concept (Explain):** A module is a file with its own namespace, and an import runs it once and makes its names available.
- **Target skills:** VE-3 to Adapt; VE-4 to Adapt; CO-6 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-3 and VE-4: diagnose an import failure in an unfamiliar project by stating and testing one hypothesis at a time.
- **Topics:** modules; `import x`; `from x import y`; module namespace; import execution; import caching awareness; search path / `sys.path` conceptual awareness; name collisions; circular imports; import-time side effects
- **Prerequisites:** Stage 3 | **Importance:** Foundational | **Integration link:** Multi-file Python applications

#### PY-5.2 Splitting code across modules

- **Objective:** Can split Python responsibilities across modules while keeping imports and module interfaces understandable.
- **The concept (Explain):** Modules group code by responsibility so each file has one reason to change.
- **Target skills:** SP-3 to Adapt; BU-4 to Adapt; CO-4 to Adapt; BU-5 to Adapt
- **Methods:** Explain → Decompose → Modify → Evaluate → Build
- **Outcome (measured at unit end):** SP-3: splits an AI's kitchen-sink module by responsibility. CO-4: gives each new module a one-sentence purpose. BU-4: keeps module interfaces clear. BU-5: moves one responsibility at a time, with behaviour checked after each move. Make (BU-4): splits their own single-file pantry script into two modules (intake and allocation) with one clear public function, behaviour unchanged.
- **Topics:** Python module responsibility; public/internal functions; avoiding kitchen-sink modules; dependency direction at module/import level; import boundaries; cohesion; boundary between Python organization and general software design; writing a small program from a blank file (Make)
- **Prerequisites:** PY-3.5, PY-5.1 | **Importance:** Foundational | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering project structure
- **Changed in v4:** Make step added as Build, credited to BU-4 (recommendation 1); Make wording moved into the PantryFlow story (2026-11-04)

#### PY-5.3 Packages

- **Objective:** Can structure and use Python packages with intentional import boundaries.
- **The concept (Explain):** A package is a folder of modules whose import paths define its public surface.
- **Target skills:** CO-5 to Apply; VE-3 to Adapt
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-5: maps the import dependencies of a small package. VE-3: explains and fixes a circular import by hypothesis.
- **Topics:** package directories; `__init__.py`; absolute imports; relative imports; package API exposure; subpackages; circular dependencies
- **Prerequisites:** PY-5.1, PY-5.2 | **Importance:** Core | **Integration link:** Stage 12; Cross-Link → Backend Engineering
- **Changed in v4:** CO-5 goal lowered Adapt to Apply (first appearance)

#### PY-5.4 Entry points

- **Objective:** Can distinguish importing a module from executing it as program entry code and structure entry points accordingly.
- **The concept (Explain):** A file can be imported or run, and `__main__` tells it which.
- **Target skills:** CO-1 to Apply; BU-1 to Apply; DE-4 to Apply
- **Methods:** Explain → Predict → Modify → Direct → Build
- **Outcome (measured at unit end):** CO-1: predicts what runs on import versus on execution. BU-1: moves an AI script's import-time side effects behind `__main__`. DE-4: checks `argparse` behaviour in the official documentation. Make (BU-1): turns their own pantry script into a runnable module with a `main()` guard and a non-zero exit code on failure.
- **Topics:** module import versus execution; `__name__`; `__main__`; `if __name__ == "__main__"`; `python file.py`; `python -m package.module`; `__main__.py` awareness; keeping side effects out of imports; `sys.argv` and a first look at `argparse` (new); exit codes (new); writing a small program from a blank file (Make); program versus process; exit status as the process's result (from OS / Process)
- **Prerequisites:** PY-5.1 | **Importance:** Core | **Integration link:** Applications/CLI/service startup; Stage 10 packaging
- **Changed in v4:** Make step added as Build, credited to BU-1 (recommendation 1); OS / Process topic added; Make wording moved into the PantryFlow story (2026-11-04)

#### PY-0.2 Reading a small Python application

- **Objective:** Can identify the major responsibilities in a small Python application and explain where Python participates in larger software, backend and AI-enabled systems without confusing adjacent domains with Python itself.
- **The concept (Explain):** A small application has an entry point, logic, data handling and configuration, and each file has a job.
- **Target skills:** CO-4 to Apply; CO-5 to Apply
- **Methods:** Explain → Trace
- **Outcome (measured at unit end):** CO-4: writes a one-sentence purpose for each file of a small AI-generated app. CO-5: sketches how data moves between the files.
- **Topics:** entry point; application logic; data transformation; external services awareness; configuration; persistence awareness; libraries/dependencies; validation; observability awareness; interfaces/boundaries; Python versus adjacent technologies; application responsibility map
- **Prerequisites:** PY-5.1 to PY-5.4 | **Importance:** Foundational | **Integration link:** Cross-Link → Backend Engineering; Database / SQL; AI Engineering; System Architecture; Python Stages 5, 8, 12, 13


### Stage 6

#### PY-6.1 Classes, instances and state

- **Objective:** Can model a stateful responsibility with a class, explain how instances maintain state and behavior, and reason about state transitions over time.
- **The concept (Explain):** A class bundles state and the methods that change it; each instance has its own state.
- **Target skills:** CO-2 to Adapt; CO-6 to Adapt; BU-1 to Adapt
- **Methods:** Explain → Trace → Modify
- **Outcome (measured at unit end):** CO-2: traces an AI `Cart` object's attributes through a sequence of method calls. CO-6: explains class versus instance with an example and a non-example. BU-1: adapts one method so invalid input cannot corrupt state.
- **Topics:** class definitions; instances; `self`; attributes; methods; object identity; attribute access; instance namespace mental model; when a class is appropriate; state changes over time; methods as controlled state transitions; valid versus invalid state
- **Prerequisites:** Stage 3 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering component implementations

#### PY-6.2 Constructing objects

- **Objective:** Can construct objects correctly and distinguish instance state from shared class state.
- **The concept (Explain):** `__init__` builds each instance's own state; attributes on the class are shared by all instances.
- **Target skills:** VE-1 to Adapt; VE-2 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-2: finds the shared mutable class attribute in an AI class. VE-1: writes a two-instance check that fails on it, then moves the state into `__init__`.
- **Topics:** `__init__`; initialization; instance attributes; class attributes; shared mutable class-state risks; defaults; invariants during construction
- **Prerequisites:** PY-6.1 | **Importance:** Core | **Integration link:** Reliable object state

#### PY-6.3 Instance, class and static methods

- **Objective:** Can choose among instance, class and static methods according to the responsibility being modeled.
- **The concept (Explain):** Instance, class and static methods differ in what they receive and what they are for.
- **Target skills:** DE-6 to Apply; BU-4 to Apply
- **Methods:** Explain → Evaluate → Modify
- **Outcome (measured at unit end):** DE-6: for each method of an AI class, compares instance, class, static and module-level forms and chooses with a reason. BU-4: changes a method to the simpler form.
- **Topics:** instance methods; `self`; `@classmethod`; `cls`; alternate constructors; `@staticmethod`; when a module-level function is better; method binding mental model
- **Prerequisites:** PY-6.1, PY-6.2 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD

#### PY-6.4 Controlled object interfaces

- **Objective:** Can expose controlled Python object interfaces while protecting meaningful state invariants.
- **The concept (Explain):** Python protects invariants by convention and by properties, not by locks.
- **Target skills:** DE-1 to Adapt; BU-4 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Evaluate → Modify → Debug & Validate
- **Outcome (measured at unit end):** DE-1: rejects an AI's Java-style getters and setters. BU-4: uses `@property` only where an invariant needs it. VE-6: checks that an invalid assignment raises.
- **Topics:** encapsulation; Python conventions; public/private-by-convention; `_name`; double-underscore name mangling awareness; why name mangling is not true access control; property access; `@property`; setters where justified; invariants; avoiding Java-style accessor boilerplate
- **Prerequisites:** PY-6.2 | **Importance:** Core | **Integration link:** Data/config/domain objects; Cross-Link → Software Design / OOD / LLD

#### PY-6.8 Special methods

- **Objective:** Can implement selected Python special methods to make objects integrate predictably with normal language operations.
- **The concept (Explain):** Special methods let your objects behave like built-in ones in `==`, `len()` and `print()`.
- **Target skills:** CO-1 to Apply; DE-1 to Apply
- **Methods:** Explain → Predict → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts how `==`, `len()` and `print()` behave on an AI class before and after adding special methods. DE-1: rejects an unneeded `__add__`.
- **Topics:** `__repr__`; `__str__`; `__eq__`; ordering awareness; `__len__`; selected protocol methods as needed; operator/protocol behavior; avoid unnecessary operator overloading
- **Prerequisites:** PY-6.2 | **Importance:** Supporting | **Integration link:** Data models/debugging

#### PY-6.9 Data classes and named values

- **Objective:** Can use dataclasses and simple bounded named values when a responsibility is primarily structured data with lightweight behavior.
- **The concept (Explain):** A dataclass is a class whose job is to hold data, with the boilerplate written for you.
- **Target skills:** DE-6 to Adapt; BU-3 to Adapt
- **Methods:** Explain → Evaluate → Build
- **Outcome (measured at unit end):** BU-3: converts an AI's dict-based records to a dataclass with `field(default_factory=...)` and an `Enum`. DE-6: keeps the dict where it is clearer and states the trade-off.
- **Topics:** `@dataclass`; generated initializer; representation/equality behavior; defaults; `field`; mutable-default concerns; frozen awareness; dataclass versus ordinary class; dataclass versus dictionary; `Enum` awareness/use for bounded named values; when plain constants remain clearer
- **Prerequisites:** PY-6.2, PY-6.8 | **Importance:** Core | **Integration link:** Configuration/data/domain models; Cross-Link → Backend Engineering schemas/models

#### PY-6.5 Inheritance and resolution

- **Objective:** Can trace inherited and overridden behavior and explain how `super()` and method resolution determine which implementation runs.
- **The concept (Explain):** A subclass inherits and can override; `super()` and the method resolution order decide which version runs.
- **Target skills:** CO-1 to Adapt; CO-6 to Adapt; VE-2 to Adapt
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts which method runs in a three-class AI hierarchy from the MRO. CO-6: explains inheritance versus has-a with examples. VE-2: finds the override that skips `super().__init__()`.
- **Topics:** base/subclasses; inherited methods/attributes; overriding; `super()`; MRO; `isinstance`; `issubclass`; multiple inheritance awareness; cooperative inheritance awareness; common inheritance mistakes
- **Prerequisites:** PY-6.4, PY-6.9 | **Importance:** Core | **Integration link:** Framework/library code; Cross-Link → Software Design / OOD / LLD

#### PY-6.6 Polymorphism and shared contracts

- **Objective:** Can use subtype/polymorphic behavior when Python implementations can reasonably satisfy a shared behavioral contract.
- **The concept (Explain):** Different classes can be used interchangeably when they keep the same behavioural promise.
- **Target skills:** SP-2 to Adapt; DE-6 to Adapt; DE-1 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Specify → Evaluate → Debug & Validate
- **Outcome (measured at unit end):** SP-2: writes the behavioural contract two storage classes should share. DE-1: judges whether two AI-written classes really share it. DE-6: replaces inheritance-for-reuse with duck typing or an ABC by trade-off. VE-1: writes one check both must pass.
- **Topics:** polymorphism; duck typing; substitutability at Python implementation level; behavioral contracts; ABC awareness; `abc.ABC`; abstract methods where relevant; interface-like reasoning; avoiding inheritance merely for reuse; distinction from formal SOLID/LSP design analysis
- **Prerequisites:** PY-6.5 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering; AI Engineering interchangeable implementations

#### PY-6.7 Composition and object responsibility

- **Objective:** Can compose cooperating Python objects and choose composition, inheritance, functions, dataclasses or plain data structures based on implementation responsibility.
- **The concept (Explain):** Build bigger behaviour by combining small objects, and choose class, function or plain data by what the job needs.
- **Target skills:** SP-3 to Adapt; DE-6 to Adapt; BU-4 to Adapt; BU-5 to Adapt
- **Methods:** Explain → Decompose → Evaluate → Modify
- **Outcome (measured at unit end):** SP-3: splits an AI's inheritance-heavy notifier into cooperating parts. DE-6: compares composition, function and dataclass alternatives and chooses. BU-4 and BU-5: refactor to the choice in small steps with behaviour unchanged.
- **Topics:** composition; has-a versus is-a; dependency relationships; delegation; responsibility boundaries at Python object level; class-versus-function judgment; class-versus-dataclass judgment; plain-data-structure judgment; avoiding unnecessary OOP; distinction from full LLD/pattern/SOLID ownership
- **Prerequisites:** PY-6.5, PY-6.6, PY-6.9 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering


### Stage 7

#### PY-7.1 Iterables and iterators

- **Objective:** Can reason about iterable versus iterator behavior and diagnose consumption/state issues.
- **The concept (Explain):** An iterable can produce an iterator, and an iterator is used up as you go.
- **Target skills:** CO-1 to Apply; CO-6 to Apply; VE-2 to Apply
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts what happens when code loops over a `map` object twice. CO-6: explains iterable versus iterator. VE-2: finds why an AI function returns nothing on its second pass.
- **Topics:** iterable; iterator; `iter()`; `next()`; iterator exhaustion; single-pass behavior; iteration protocol concept; common iterable types; `itertools` basics (new)
- **Prerequisites:** Stage 2 | **Importance:** Core | **Integration link:** Streaming/data processing

#### PY-7.2 Generators

- **Objective:** Can implement and modify generators when lazy production or streaming is useful.
- **The concept (Explain):** A generator produces values one at a time and remembers where it stopped.
- **Target skills:** CO-2 to Adapt; CO-5 to Adapt; BU-2 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Trace → Modify → Evaluate
- **Outcome (measured at unit end):** CO-2: traces a generator's suspension and resumption. CO-5: sketches the data flow of a pipeline. BU-2: refines an AI function that builds a whole list into a generator that meets the spec. DE-6: judges where laziness is worth it.
- **Topics:** `yield`; generator functions; generator objects; generator expressions; lazy evaluation; memory/streaming motivation; state suspension; common exhaustion mistakes
- **Prerequisites:** PY-7.1, Stage 3 | **Importance:** Core | **Integration link:** Streaming/data pipelines; Cross-Link → Backend Engineering and AI Engineering

#### PY-7.3 Decorators

- **Objective:** Can read and modify straightforward decorators while preserving the wrapped callable's intended behavior.
- **The concept (Explain):** A decorator is a function that wraps another function to add behaviour.
- **Target skills:** CO-4 to Apply; BU-1 to Apply; VE-2 to Apply
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** CO-4: explains an AI retry decorator in one sentence. BU-1: fixes it to pass through arguments and return values with `functools.wraps`. VE-2: finds the swallowed exception.
- **Topics:** functions as values; nested functions/closures; wrapper function; decorator syntax; arguments; `functools.wraps`; parameterized-decorator awareness; common framework usage; when not to write decorators; `functools.lru_cache` (new)
- **Prerequisites:** PY-3.3 | **Importance:** Supporting | **Integration link:** Cross-Link → Backend Engineering/framework code

#### PY-7.4 Context managers

- **Objective:** Can use context managers to ensure reliable acquisition and cleanup of resources.
- **The concept (Explain):** A `with` block guarantees cleanup, even when the body fails.
- **Target skills:** CO-2 to Adapt; BU-3 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Trace → Build → Debug & Validate
- **Outcome (measured at unit end):** CO-2: traces `__enter__` and `__exit__` when the body raises. BU-3: rewrites AI code that leaks connections to use `with` or `contextlib`. VE-6: checks cleanup runs on error.
- **Topics:** `with`; `__enter__`; `__exit__`; exception interaction; file/resource cleanup; `contextlib` awareness; custom context-manager concept; file handles and resource leaks (from OS / Process)
- **Prerequisites:** Stage 4 | **Importance:** Core | **Integration link:** Files/network/resources; Cross-Link → Backend Engineering and Database / SQL resource lifecycles
- **Changed in v4:** OS / Process topic added

#### PY-7.5 Type annotations

- **Objective:** Can use Python type annotations to communicate common function and data contracts and interpret type-checker feedback appropriately.
- **The concept (Explain):** Type annotations state a contract that tools can check but Python does not enforce.
- **Target skills:** CO-3 to Adapt; DE-1 to Adapt; VE-4 to Adapt
- **Methods:** Explain → Evaluate → Debug & Validate
- **Outcome (measured at unit end):** CO-3: reads an AI module's annotations. DE-1: decides for each type-checker finding whether it is a real bug, a wrong annotation or a false positive. VE-4: reads each finding to its cause.
- **Topics:** annotations; runtime-versus-static distinction; built-in generic forms; unions; optional/`None`; return types; type aliases; callable types at useful depth; type narrowing awareness; type-checker role
- **Prerequisites:** Stage 3 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering; AI Engineering

#### PY-7.6 Interface-style type contracts

- **Objective:** Can express reusable interface-oriented type contracts when basic annotations are insufficient.
- **The concept (Explain):** A `Protocol` describes the behaviour a function needs, not the class it gets.
- **Target skills:** SP-2 to Apply; SP-4 to Apply; DE-6 to Apply
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-2: writes the `Protocol` that states what a function needs. SP-4: spots a behaviour the protocol leaves out. DE-6: replaces a union of concrete classes with it and rejects an over-complex generic signature for a simpler one.
- **Topics:** Protocol awareness/use; structural typing; generic type variables at practical depth; collections/interfaces; avoiding typing over-complexity; interaction with polymorphic design
- **Prerequisites:** PY-7.5, Stage 6 | **Importance:** Supporting | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering; AI Engineering


### Stage 8

#### PY-8.1 Files and paths

- **Objective:** Can read, write and navigate filesystem resources safely using Python's path and context-management facilities.
- **The concept (Explain):** Files live outside the program: they can be missing, locked or in a different encoding.
- **Target skills:** BU-3 to Adapt; VE-6 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Build → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-3: moves an AI script from string paths and bare `open()` to `pathlib` with context-managed files. VE-6: tries missing paths, wrong encodings and a directory. DE-5: keeps writes inside the intended folder.
- **Topics:** `pathlib.Path`; relative/absolute paths; existence; directories; file reading/writing; modes; context-managed files; text versus binary awareness; encoding awareness; missing paths; filesystem errors; bytes and text encodings (new); current working directory and why relative paths break (from OS / Process)
- **Prerequisites:** Stages 4, 7 | **Importance:** Core | **Integration link:** Configuration/ingestion; Cross-Link → AI Engineering ingestion workflows
- **Changed in v4:** OS / Process topic added

#### PY-8.2 Structured data

- **Objective:** Can parse, validate and serialize common structured application data while handling malformed input.
- **The concept (Explain):** Data entering or leaving the program must be parsed and checked, never trusted.
- **Target skills:** VE-1 to Adapt; VE-6 to Adapt; BU-3 to Adapt
- **Methods:** Explain → Debug & Validate → Build
- **Outcome (measured at unit end):** VE-1 and VE-6: write checks with malformed, truncated and wrong-type JSON that a parser must reject clearly. BU-3: reads and writes CSV through the `csv` module.
- **Topics:** JSON; Python ↔ JSON types; load/dump; malformed data; serialization boundaries; nested structures; data validation; CSV awareness if useful; unsafe serialization awareness (`pickle` caution, not mastery); the `csv` module (new)
- **Prerequisites:** Stage 1, Stage 4 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering; Database / SQL; AI Engineering

#### PY-8.6 Pattern matching in text

- **Objective:** Can read and write simple regular expressions for matching and extracting text, and judge when string methods are enough.
- **The concept (Explain):** A regular expression describes a text pattern so matching can be done by rule.
- **Target skills:** CO-3 to Apply; VE-1 to Apply
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** CO-3: explains an AI-written pattern in plain words. VE-1: writes matching and non-matching examples that catch a too-greedy or too-loose pattern.
- **Topics:** `re` module basics; `search`, `match`, `findall`, `sub`; groups; raw strings; common patterns; greedy versus lazy matching; when string methods are clearer; testing patterns on edge cases; catastrophic backtracking awareness
- **Prerequisites:** PY-1.7, PY-8.2 | **Importance:** Supporting | **Integration link:** Text processing; Cross-Link → AI Engineering text handling

#### PY-8.3 Configuration

- **Objective:** Can separate configuration from Python application logic and handle environment-dependent settings intentionally.
- **The concept (Explain):** Settings change between machines; the code should not.
- **Target skills:** SP-1 to Adapt; SP-2 to Adapt; SP-4 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Specify → Decompose → Direct
- **Outcome (measured at unit end):** SP-1 and SP-2: list required and optional settings and write the config spec. SP-4: spots a setting the spec leaves out. DE-5: moves hardcoded values and an API key into a validated config object that never prints the secret.
- **Topics:** environment variables; configuration files; defaults; required settings; type conversion/validation; config objects; secrets versus non-secret config; avoiding hardcoded environment-specific values; `.env` as an implementation option, not a roadmap requirement
- **Prerequisites:** PY-8.2, Stage 5 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering configuration; Infrastructure / Ops Depth for deployed secret handling
- **Changed in v4:** Decompose added as a helper for SP-1 and SP-2 (recommendation 7)

#### PY-8.7 Command-line programs and running other programs

- **Objective:** Can write a command-line program that takes arguments, reports success or failure through exit codes, and runs other programs safely.
- **The concept (Explain):** A command-line program talks to its caller through arguments, text streams and an exit code.
- **Target skills:** BU-3 to Apply; DE-5 to Apply; VE-4 to Apply
- **Methods:** Explain → Build → Direct → Debug & Validate
- **Outcome (measured at unit end):** BU-3: builds a small tool with `argparse` from the docs. DE-5: rejects an AI call that builds a shell command from user input. VE-4: reads a failing exit code and error stream to the cause.
- **Topics:** `argparse`: options, arguments, help; `sys.argv`; standard input, output and error; exit codes; `subprocess.run` with argument lists; avoiding shell injection; capturing output; timeouts; environment variables; parent and child processes (from OS / Process)
- **Prerequisites:** PY-5.4, PY-8.3 | **Importance:** Supporting | **Integration link:** Cross-Link → OS / Process Foundations; applications and CLI startup
- **Changed in v4:** OS / Process topic added

#### PY-8.4 Calling HTTP services

- **Objective:** Can call external HTTP services from Python and distinguish request, transport, protocol and application-level failures.
- **The concept (Explain):** A network call can fail in many ways, and the code must tell them apart.
- **Target skills:** BU-2 to Adapt; VE-2 to Adapt; VE-6 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-2: reviews an AI HTTP call with no timeout that treats any response as success. VE-6: classifies connection, timeout, status and malformed-body failures. DE-4: reads the library's documentation for the right options. BU-2: refines the call to meet the spec line by line.
- **Topics:** HTTP client library usage concept; URL/parameters/headers/body; status codes; JSON responses; timeout; connectivity; retry awareness; validation; failure boundaries; dependency/library documentation; HTTP client capability versus API-server design
- **Prerequisites:** Stage 4, PY-8.2 | **Importance:** Core | **Integration link:** Cross-Link → Networking / Web Foundations; Backend Engineering; AI Engineering

#### PY-8.5 Dates, times and timezones

- **Objective:** Can create, parse, compare and serialize application timestamps while correctly distinguishing naive and timezone-aware values and using UTC appropriately at external boundaries.
- **The concept (Explain):** A timestamp without a timezone is ambiguous.
- **Target skills:** VE-2 to Apply; VE-6 to Apply; DE-4 to Apply
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** DE-4: checks `fromisoformat()` in the docs rather than trusting recall. VE-2: finds the naive-time bug in an AI token-expiry check. VE-6: tests across a timezone and a daylight-saving boundary.
- **Topics:** `datetime`; `date`; `timedelta` at practical depth; naive versus timezone-aware datetime values; UTC; ISO 8601 awareness; `isoformat()`; `fromisoformat()`; timezone conversion awareness; `zoneinfo` where useful; timestamp comparison/arithmetic; external API/persistence boundary considerations
- **Prerequisites:** PY-1.2, PY-8.2 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering; Database / SQL; AI Engineering


### Stage 9

#### PY-9.1 Debugging

- **Objective:** Can reproduce, isolate and diagnose Python failures using tracebacks, program state and controlled experiments.
- **The concept (Explain):** Debugging finds the cause, not just a change that hides the symptom.
- **Target skills:** VE-3 to Adapt; VE-5 to Adapt; CO-2 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Debug & Validate → Trace → Direct
- **Outcome (measured at unit end):** VE-3: reproduces a failure in an unfamiliar AI module, shrinks it and narrows to the root cause one hypothesis at a time. CO-2: inspects state with the debugger. DE-2: asks an assistant for hypotheses, then tests each themself. VE-5: proves the fix.
- **Topics:** tracebacks; exception location; stack frames; reproduction; minimal failing case; print-versus-debugger judgment; breakpoint/debugger awareness; inspecting state; hypothesis testing; binary-search-style narrowing; root cause versus symptom
- **Prerequisites:** Stages 3–4 | **Importance:** Foundational | **Integration link:** Entire professional roadmap

#### PY-9.2 Logging and runtime evidence

- **Objective:** Can instrument a Python system with useful runtime evidence while keeping signal, severity and context meaningful.
- **The concept (Explain):** Logs are evidence you leave for the future, so they must be useful and safe.
- **Target skills:** VE-4 to Adapt; BU-4 to Adapt; DE-5 to Adapt
- **Methods:** Explain → Debug & Validate → Modify → Direct
- **Outcome (measured at unit end):** BU-4: replaces `print` debugging with named loggers at sensible levels. VE-4: adds context to error logs. DE-5: removes a log line that leaks a token.
- **Topics:** logging versus `print`; levels; named loggers; logger hierarchy awareness; handlers; formatting; structured/contextual information; exception logging; avoiding sensitive data; avoiding log noise; configuration awareness
- **Prerequisites:** PY-9.1, Stage 4 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering observability; AI Engineering observability; long-running Python applications

#### PY-9.3 Behavioural tests with pytest

- **Objective:** Can write focused pytest-style tests that establish expected behavior, edge conditions and failure contracts.
- **The concept (Explain):** A test is a repeatable check of one behaviour.
- **Target skills:** VE-1 to Adapt; VE-5 to Adapt; VE-6 to Adapt; DE-3 to Adapt
- **Methods:** Explain → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-1: writes parametrized pytest tests that fail on a wrong version not seen. VE-6: includes edge cases and `pytest.raises`. VE-5: adds a regression test for a fixed bug. DE-3: decides which tests to delegate to an AI and which to write themself.
- **Topics:** arrange-act-assert concept; pytest discovery/naming; test functions/cases; plain assertions; `pytest.raises`; happy path; edge cases; failure paths; deterministic tests; regression tests; `@pytest.mark.parametrize`; basic fixtures; basic fixture-scope awareness where useful; standard-library `unittest` awareness
- **Prerequisites:** Stage 4–5 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering testing; AI Engineering testing/evaluation

#### PY-9.4 Isolating code under test

- **Objective:** Can isolate code under test from unstable or external dependencies when isolation materially improves the test.
- **The concept (Explain):** Fakes replace slow or unstable dependencies only where that makes the test more trustworthy.
- **Target skills:** VE-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** DE-6: given an AI suite that mocks everything, decides what to fake and what to keep real. VE-1: rewrites one test so it still fails on a wrong version.
- **Topics:** dependencies; fakes/stubs/mocks conceptual distinctions; patching awareness; dependency injection as test aid; avoiding over-mocking; external network/service isolation; test boundaries
- **Prerequisites:** PY-9.3, Stage 6 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering service/API testing; AI Engineering external-provider testing

#### PY-9.5 When passing is not proof

- **Objective:** Can detect when an apparently successful implementation or test suite does not actually prove the requested behavior.
- **The concept (Explain):** A passing test suite proves only what its tests check.
- **Target skills:** VE-2 to Adapt; VE-6 to Adapt; DE-1 to Adapt; SP-4 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate → Specify
- **Outcome (measured at unit end):** VE-2: finds a wrong implementation that still passes an AI-generated suite. VE-6: adds the missing edge cases. SP-4: names the requirement detail no test covers. DE-1: rejects or strengthens the suite with a reason.
- **Topics:** false confidence; insufficient assertions; wrong test target; missing edge cases; happy-path-only testing; AI-generated tests; requirement-to-test alignment; validation evidence
- **Prerequisites:** PY-9.1–9.4 | **Importance:** Core | **Integration link:** AI-assisted engineering; entire evidence system

#### PY-9.6 Measuring runtime

- **Objective:** Can gather basic runtime measurements to determine whether a suspected performance problem exists and identify where further investigation should focus.
- **The concept (Explain):** Measure first: a guess about speed is often wrong.
- **Target skills:** VE-3 to Apply; CO-1 to Apply; DE-1 to Apply
- **Methods:** Explain → Predict → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts the hot path. VE-3: times an AI's optimisation against the original over repeated runs and profiles both. DE-1: decides whether the change is worth keeping.
- **Topics:** `time.perf_counter()`; basic timing; measurement variability awareness; repeat measurements enough to avoid obvious false conclusions; basic profiler awareness/use; hot-path identification; CPU-bound versus I/O-bound symptoms; measure-before-optimize principle; deciding when deeper investigation is justified; memory pressure as a runtime limit (awareness, from OS / Process)
- **Prerequisites:** PY-9.1, PY-2.2 | **Importance:** Supporting | **Integration link:** Cross-Link → Practical DSA; OS / Process Foundations; Backend Engineering; System Architecture
- **Changed in v4:** OS / Process topic added


### Stage 10

#### PY-10.1 Environments

- **Objective:** Can create and reason about isolated Python environments and diagnose interpreter/environment mismatches.
- **The concept (Explain):** An environment is a separate Python with its own packages, and every command must use the same one.
- **Target skills:** VE-3 to Adapt; VE-4 to Adapt; CO-6 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-3: diagnoses why `pip install` succeeded but the import fails by testing which interpreter each command uses. VE-4: reads the error to the cause. CO-6: explains the interpreter-environment link.
- **Topics:** interpreter; environment; `venv`; activation; installed packages; project-local environment; multiple Python versions awareness; environment mismatch; `python`/`pip` alignment; tool-specific environment managers as execution choices
- **Prerequisites:** Stage 5 | **Importance:** Core | **Integration link:** Project setup; Cross-Link → OS / Process Foundations

#### PY-10.2 Dependencies

- **Objective:** Can install, declare and update dependencies while reasoning about versioning and reproducibility.
- **The concept (Explain):** Every dependency you add is code you trust and must keep working.
- **Target skills:** DE-5 to Adapt; DE-6 to Adapt; BU-5 to Adapt
- **Methods:** Explain → Direct → Evaluate → Modify
- **Outcome (measured at unit end):** DE-5: rejects an AI-added package that is unneeded or unvetted. DE-6: pins the rest by a stated reproducibility trade-off. BU-5: upgrades one package at a time.
- **Topics:** `pip`; package-index awareness; package versions; dependency declarations; requirements-style files; dependency groups awareness; direct/transitive dependency concept; pinning/ranges at useful depth; reproducibility; upgrade risks; `uv`, Poetry, Conda or similar tools as implementation choices, not roadmap requirements
- **Prerequisites:** PY-10.1 | **Importance:** Core | **Integration link:** Application lifecycle

#### PY-10.3 Project metadata and packaging

- **Objective:** Can interpret and maintain practical Python project metadata and make a reusable project installable.
- **The concept (Explain):** `pyproject.toml` tells tools how to build, install and check the project.
- **Target skills:** CO-3 to Apply; CO-4 to Apply; CO-5 to Apply
- **Methods:** Explain → Trace
- **Outcome (measured at unit end):** CO-3: explains each section of an AI-generated `pyproject.toml`. CO-4: states what each section is for. CO-5: fixes a distribution-name versus import-name mismatch and installs the project in editable mode.
- **Topics:** `pyproject.toml`; `[build-system]`; `[project]`; dependencies; tool configuration awareness; package layout; build-backend concept; editable/local installation awareness; distribution package versus import package; basic build/distribution flow
- **Prerequisites:** Stage 5, PY-10.2 | **Importance:** Supporting | **Integration link:** Reusable/project packaging; Stage 5 execution boundaries

#### PY-10.4 Diagnosing install and environment failures

- **Objective:** Can diagnose common dependency, environment, import and installation failures across local project contexts.
- **The concept (Explain):** Most install failures come from a wrong interpreter, a missing or clashing dependency, or a wrong name.
- **Target skills:** VE-3 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Debug & Validate
- **Outcome (measured at unit end):** VE-3: diagnoses a project that works on the AI's machine but not theirs. VE-5: proves the fix by rebuilding the environment from scratch.
- **Topics:** wrong interpreter; missing dependency; incompatible versions; editable/local install issues; import package versus distribution-name mismatch; environment recreation; reproducibility checks; locating a failure: application, process, filesystem or environment (from OS / Process)
- **Prerequisites:** PY-10.1–10.3 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering and AI Engineering project setup
- **Changed in v4:** OS / Process topic added

#### PY-10.5 Quality gates

- **Objective:** Can configure and use automated formatting, linting and static checking as complementary quality gates and interpret their output appropriately.
- **The concept (Explain):** Formatters, linters and type checkers catch different problems, and none replaces tests.
- **Target skills:** BU-4 to Apply; VE-4 to Apply; DE-3 to Apply
- **Methods:** Explain → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** BU-4: fixes actionable findings on an AI module. VE-4: reads each finding to its cause. DE-3: decides which checks to hand to tools and justifies or removes each suppression.
- **Topics:** formatter role; linter role; type-checker role; tests as a distinct behavioral-evidence mechanism; tool configuration in project metadata; running checks locally; interpreting and fixing actionable findings; suppressing/ignoring findings only with justification; examples may include Ruff, Black, mypy, Pyright without requiring mastery of any one tool
- **Prerequisites:** PY-7.5, PY-10.3 | **Importance:** Core | **Integration link:** Stage 7 typing; Stage 9 testing; Stage 12 professional codebases; Cross-Link → Git / Version Control


### Stage 11

#### PY-11.1 Concurrency mental model

- **Objective:** Can explain blocking, concurrency and parallelism sufficiently to decide when asynchronous I/O is relevant in Python.
- **The concept (Explain):** Waiting and working are different, and the right tool depends on which one slows you down.
- **Target skills:** CO-6 to Understand; DE-6 to Understand
- **Methods:** Explain → Evaluate
- **Outcome (measured at unit end):** CO-6: explains blocking, concurrency and parallelism with examples. DE-6: for three tasks, decides whether each is CPU- or I/O-bound and judges an AI's proposal to make code async.
- **Topics:** blocking; synchronous execution; concurrency; parallelism distinction; CPU-bound versus I/O-bound; thread/process awareness; async I/O; when async adds complexity without value; distinction between Python mechanics and general OS/process theory
- **Prerequisites:** Stage 3 | **Importance:** Core | **Integration link:** Cross-Link → OS / Process Foundations; Backend Engineering; AI Engineering

#### PY-11.5 Threads and processes

- **Objective:** Can use threads and processes through `concurrent.futures` for simple jobs, and recognise races and the effect of the GIL.
- **The concept (Explain):** Threads share memory and processes do not, and the GIL limits what threads do in parallel.
- **Target skills:** BU-3 to Apply; VE-2 to Apply
- **Methods:** Explain → Build → Debug & Validate
- **Outcome (measured at unit end):** BU-3: runs a job over many files with `concurrent.futures` from the docs. VE-2: finds the race condition in an AI threaded counter.
- **Topics:** `threading` basics; `concurrent.futures`: thread and process pools; `multiprocessing` awareness; the GIL and what it means; shared state and race conditions; locks (awareness); choosing thread, process or async; passing data between processes; cost of starting workers
- **Prerequisites:** PY-11.1 | **Importance:** Supporting | **Integration link:** Cross-Link → OS / Process Foundations

#### PY-11.2 Tracing async code

- **Objective:** Can trace coroutine, `await`, task and event-loop behavior through a straightforward async Python program.
- **The concept (Explain):** An async program switches between tasks only at `await`.
- **Target skills:** CO-1 to Adapt; CO-2 to Adapt; DE-2 to Adapt
- **Methods:** Explain → Predict → Trace → Direct
- **Outcome (measured at unit end):** CO-1: predicts the print order of async code with sequential awaits and with gathered tasks. CO-2: traces the event loop to explain any mismatch. DE-2: asks an assistant to explain the event loop, then re-predicts without it.
- **Topics:** `async def`; coroutine objects; `await`; event-loop mental model; tasks; scheduling; sequential awaits versus concurrent tasks; gather-style coordination concept
- **Prerequisites:** PY-11.1 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering and AI Engineering external-I/O workflows

#### PY-11.3 Concurrent I/O

- **Objective:** Can implement and modify straightforward concurrent-I/O workflows without accidentally blocking the event loop.
- **The concept (Explain):** Async only helps if nothing inside it blocks.
- **Target skills:** BU-2 to Adapt; VE-2 to Adapt; VE-3 to Adapt; DE-4 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** VE-2: finds a blocking call hidden in an AI coroutine. DE-4: finds an async-compatible library in the documentation. BU-2: refines the code to make the calls concurrent and meet the spec. VE-3: measures time before and after.
- **Topics:** multiple concurrent calls; task creation; gathering results; blocking sync calls; async-compatible libraries; async context-manager awareness; async-iteration awareness
- **Prerequisites:** PY-11.2 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering; AI Engineering

#### PY-11.4 Async failures

- **Objective:** Can diagnose common async failures and decide when simpler synchronous code is preferable.
- **The concept (Explain):** Async failures are often silent: a task nobody awaits keeps its exception to itself.
- **Target skills:** VE-3 to Adapt; VE-5 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: diagnoses AI async code that leaks a task and drops its exception. VE-5: proves the fix. DE-6: decides by trade-off whether the workflow should have stayed synchronous.
- **Topics:** forgotten `await`; coroutine-not-awaited failures; blocking calls; task exceptions; timeout awareness; cancellation awareness; exception propagation; leaked tasks/resources; unnecessary async complexity; graceful versus abrupt shutdown (from OS / Process)
- **Prerequisites:** PY-11.2–11.3 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering; AI Engineering; OS / Process Foundations
- **Changed in v4:** OS / Process topic added


### Stage 12

#### PY-12.1 Navigating an unfamiliar codebase

- **Objective:** Can enter an unfamiliar Python codebase and locate entry points, important modules, Python responsibility boundaries and major data flows.
- **The concept (Explain):** Before changing a codebase, build a map of how it fits together.
- **Target skills:** CO-3 to Own; CO-4 to Own; CO-5 to Own; SP-3 to Own
- **Methods:** Explain → Trace → Decompose
- **Outcome (measured at unit end):** Enters an unfamiliar codebase and, before any edit, writes a one-page map of entry points, modules, data flows and likely change boundaries (CO-5, CO-4); explains unfamiliar code accurately (CO-3); names the safest change boundary (SP-3).
- **Topics:** directory/package inspection; entry points; imports; call-graph reasoning; configuration; recognition of service/domain layers without claiming their architectural ownership; tests as behavioral evidence; search/navigation tooling; identifying likely change boundaries
- **Prerequisites:** Stages 5–10; GIT-1.4 | **Importance:** Core | **Integration link:** Professional Python work; Cross-Link → Backend Engineering; Software Design / OOD / LLD

#### PY-12.2 Learning a library from its documentation

- **Objective:** Can learn an unfamiliar Python library or subsystem from authoritative documentation, interfaces and small experiments rather than requiring full prior knowledge.
- **The concept (Explain):** Documentation, small experiments and source are the authority; an assistant's explanation is a lead.
- **Target skills:** DE-2 to Adapt; DE-4 to Adapt; BU-3 to Adapt
- **Methods:** Explain → Direct → Build
- **Outcome (measured at unit end):** DE-4: learns an unfamiliar library from its version-specific docs and experiments. DE-2: uses an assistant to explain, then does the step themself. BU-3: checks an AI's use of the library against the docs and corrects the calls.
- **Topics:** API documentation; signatures; examples; source inspection where useful; minimal experiments; version-specific docs; assumptions; library conventions; AI-assisted documentation use; verifying generated library usage; distinguishing authoritative source material from assistant explanation
- **Prerequisites:** Stage 3+, Stage 9 | **Importance:** Core | **Integration link:** Third-party integrations; runtime Source-Grounded Learning system

#### PY-12.3 Organising a Python application

- **Objective:** Can organize Python application code into coherent packages, modules, Python interfaces, configuration boundaries and side-effect boundaries without taking ownership of broader backend/system architecture.
- **The concept (Explain):** Where code lives and which way imports point decide how easy change will be.
- **Target skills:** SP-3 to Adapt; DE-6 to Adapt; BU-4 to Adapt; CO-5 to Adapt
- **Methods:** Explain → Decompose → Evaluate → Modify
- **Outcome (measured at unit end):** DE-6: compares two layouts for an AI app with config reads and I/O scattered through its logic. SP-3: reorganises it into packages. BU-4 and CO-5: one-way imports and explicit interfaces, shown with a dependency map.
- **Topics:** Python responsibility boundaries; import/dependency direction; modules/packages; configuration boundaries; side-effect boundaries; avoiding circular coupling; appropriate Python abstraction; recognition of service-layer concepts; boundary between Python organization and Software Design / Backend ownership
- **Prerequisites:** Stages 5–8 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering

#### PY-12.4 Changing an existing subsystem safely

- **Objective:** Can modify an existing Python subsystem while preserving relevant behavior and proving that important contracts still hold.
- **The concept (Explain):** A change is safe only when the behaviour that must stay the same is proven to stay the same.
- **Target skills:** BU-1 to Own; BU-5 to Own; VE-1 to Own; VE-5 to Own
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** Changes a subsystem for a new requirement: writes regression tests first (VE-1), changes in small reversible steps (BU-5), keeps old cases passing (BU-1), and shows the proof (VE-5).
- **Topics:** change impact; existing tests; new regression tests; interface stability; refactoring versus behavior change; incremental changes; validation; dependency effects
- **Prerequisites:** PY-12.1, Stage 9; GIT-1.3 | **Importance:** Core | **Integration link:** Existing-codebase change; Cross-Link → Git / Version Control

#### PY-12.5 Refactoring

- **Objective:** Can improve duplicated, coupled or unclear Python code while preserving behavior and explaining implementation trade-offs rather than refactoring mechanically.
- **The concept (Explain):** Refactoring changes structure, not behaviour, and each step is proven.
- **Target skills:** BU-4 to Adapt; BU-5 to Adapt; VE-5 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Modify → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** BU-4: removes duplication and coupling by extraction. BU-5 and VE-5: tests stay green each step. DE-6: explains each trade-off and rejects a premature abstraction.
- **Topics:** duplication; cohesion; coupling; extraction; naming; Python interfaces; decomposition; avoiding premature abstractions; maintaining behavior; recognizing when a problem has moved beyond Python refactoring into broader design
- **Prerequisites:** PY-12.3–12.4 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Git / Version Control


### Stage 13

#### PY-13.1 Building a Python subsystem

- **Objective:** Can decompose and implement a Python subsystem that receives input, transforms data, interacts with an external dependency and returns validated output.
- **The concept (Explain):** A subsystem takes input, checks it, transforms it, calls something outside, and fails clearly.
- **Target skills:** SP-1 to Own; SP-3 to Own; BU-2 to Own; DE-3 to Own
- **Methods:** Explain → Specify → Decompose → Modify → Direct
- **Outcome (measured at unit end):** From a loose goal, asks the clarifying questions (SP-1), splits the pieces (SP-3), decides which to have an AI draft (DE-3) and refines them to spec (BU-2). Proves the pieces with checks as part of the work.
- **Topics:** input boundary; structured data; validation; transformation; functions/classes; external dependency/client; failure propagation; typing; configuration; tests
- **Prerequisites:** Stages 3–12 | **Importance:** Core | **Integration link:** Cross-Link → Projects / Capstones; Backend Engineering; AI Engineering

#### PY-13.2 Interchangeable components behind contracts

- **Objective:** Can integrate interchangeable Python components behind intentional contracts or interfaces and reason about failures across those boundaries.
- **The concept (Explain):** Parts that can be swapped need a contract that both sides keep.
- **Target skills:** SP-2 to Own; BU-3 to Own; DE-5 to Own; DE-6 to Own
- **Methods:** Explain → Specify → Build → Direct → Evaluate
- **Outcome (measured at unit end):** Puts a real and a fake source behind one interface they specified (SP-2), integrates both (BU-3), limits and validates what crosses the boundary (DE-5), and chooses the interface by trade-off (DE-6).
- **Topics:** contracts/interfaces; composition; polymorphism/protocols; dependency boundaries; validation; failure translation; testability; replacement/fakes; generic components rather than retriever/model/service-specific ownership
- **Prerequisites:** Stages 6, 7, 9, 12; SD-1.1 | **Importance:** Core | **Integration link:** Cross-Link → Software Design / OOD / LLD; Backend Engineering; AI Engineering; Projects / Capstones

#### PY-13.3 An integrated, reliable workflow

- **Objective:** Can combine configuration, typing, validation, exceptions, logging, testing and async where appropriate in one coherent and reliable Python workflow.
- **The concept (Explain):** Reliability comes from several small habits working together.
- **Target skills:** BU-2 to Own; VE-4 to Own; VE-6 to Own; DE-5 to Own
- **Methods:** Explain → Modify → Debug & Validate → Direct
- **Outcome (measured at unit end):** Builds one workflow with validated config, input checks, an external call (async only if justified), contextual logs and cleanup, refining AI-written parts to spec (BU-2). Shows failures are observable (VE-4), hostile input is handled (VE-6) and secrets stay safe (DE-5).
- **Topics:** configuration; boundary validation; typing; exceptions; structured/contextual logs; tests; external calls; async selection; cleanup; observable failure; explicit boundary: reliable Python workflow does not equal full production-system competence
- **Prerequisites:** Stages 7–11 | **Importance:** Core | **Integration link:** Cross-Link → Backend Engineering; AI Engineering; Projects / Capstones

#### PY-13.4 Owning AI-assisted Python work

- **Objective:** Can use AI coding tools to implement, inspect and refactor Python while independently retaining enough understanding to validate and own the resulting work.
- **The concept (Explain):** You can direct an AI tool and still own the understanding, the checking and the decisions.
- **Target skills:** SP-4 to Own; DE-1 to Own; DE-2 to Own; DE-3 to Own
- **Methods:** Explain → Specify → Direct → Evaluate
- **Outcome (measured at unit end):** Directs an AI tool with only the access the task needs through a change in a real codebase: decides what to delegate (DE-3), asks it to explain rather than do (DE-2), fixes the spec when output is wrong (SP-4), and accepts, changes or rejects its output with reasons (DE-1).
- **Topics:** prompt/requirement framing; code generation; code review; reasoning about generated dependencies; checking API/library assumptions; tracing generated code; debugging; generating/reviewing tests; rejecting inappropriate solutions; validating outcomes; identifying uncertainty; consulting authoritative documentation when generated claims are uncertain; future cross-cutting extraction candidate after multi-roadmap evidence
- **Prerequisites:** Entire roadmap; AAE-0.6, GIT-2.1 | **Importance:** Core | **Integration link:** Professional AI-era development across roadmap ecosystem

## Skill coverage (target skills, Python units)

79 Python units: 42 with a code-writing activity (Modify or Build), 24 with Build; in Stages 0 to 5, 18 of 32 write code and 16 have Build. Targets by level: Understand 10, Apply 76, Adapt 127, Own 24. Predict in 11 units, Decompose in 8. Checked by script on 2026-10-31: every unit passes the curriculum checks in `src/lms/core/curriculum_checks.py`, and no skill breaks the entry or one-rung rule anywhere in the path.

| Skill | Python units | Highest level |
| --- | --- | --- |
| BU-1 | 8 | Own |
| BU-2 | 8 | Own |
| BU-3 | 9 | Own |
| BU-4 | 10 | Adapt |
| BU-5 | 6 | Own |
| CO-1 | 11 | Adapt |
| CO-2 | 12 | Adapt |
| CO-3 | 7 | Own |
| CO-4 | 6 | Own |
| CO-5 | 6 | Own |
| CO-6 | 9 | Adapt |
| DE-1 | 11 | Own |
| DE-2 | 6 | Own |
| DE-3 | 6 | Own |
| DE-4 | 7 | Adapt |
| DE-5 | 8 | Own |
| DE-6 | 15 | Own |
| SP-1 | 6 | Own |
| SP-2 | 6 | Own |
| SP-3 | 6 | Own |
| SP-4 | 6 | Own |
| VE-1 | 12 | Own |
| VE-2 | 14 | Adapt |
| VE-3 | 10 | Adapt |
| VE-4 | 10 | Own |
| VE-5 | 8 | Own |
| VE-6 | 14 | Own |

## Changes from v3, by unit

| Unit | Change |
| --- | --- |
| PY-0.1 | topics thinned: call flow (PY-3.1), exceptions as altered control flow (PY-4.1) and modules, functions and objects as future layers removed |
| PY-1.2 | Make step added as Build, credited to VE-6 (recommendation 1); bitwise operators added as awareness (recommendation 5) |
| PY-1.7 | Make step added as Build, credited to VE-6 (recommendation 1) |
| PY-1.8 | Make step added as Build, credited to VE-1 (recommendation 1) |
| PY-1.3 | VE-2 goal lowered Adapt to Apply (first appearance); CO-2 goal kept at Apply here; Adapt moves to the new PY-1.9; split: copying, aliasing and nested data moved to the new PY-1.9 |
| PY-1.9 | new unit, split from PY-1.3 (recommendation 6) |
| PY-1.4 | CO-3 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to BU-1 (recommendation 1) |
| PY-2.1 | SP-1 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-6 (recommendation 1) |
| PY-2.2 | VE-5 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-1 (recommendation 1); CO-1 (Adapt) added: loop-output prediction (recommendation 7); Predict added (recommendation 7) |
| PY-2.3 | Make step added as Build, credited to BU-2 (recommendation 1) |
| PY-2.4 | Make step added as Build, credited to BU-4 (recommendation 1) |
| PY-3.1 | BU-2 (Apply) added: credits the Make step; Make step added as Build, credited to BU-2 (recommendation 1) |
| PY-3.2 | Make step added as Build, credited to BU-1 (recommendation 1) |
| PY-3.3 | `map` and `filter` added (recommendation 5) |
| PY-3.4 | SP-2 goal lowered Adapt to Apply (first appearance); SP-4 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-1 (recommendation 1) |
| PY-3.5 | SP-3 goal lowered Adapt to Apply (first appearance); DE-3 goal lowered Adapt to Apply (was Understand in PY-0.3; one rung at a time) |
| PY-4.1 | DE-2 goal lowered Adapt to Apply (was Understand in PY-0.3; one rung at a time) |
| PY-4.2 | Make step added as Build, credited to VE-1 (recommendation 1); Decompose added as a helper for SP-1 and SP-2 (recommendation 7) |
| PY-4.3 | DE-5 goal lowered Adapt to Apply (first appearance); Make step added as Build, credited to VE-6 (recommendation 1) |
| PY-4.4 | BU-5 goal lowered Adapt to Apply (first appearance) |
| PY-5.2 | Make step added as Build, credited to BU-4 (recommendation 1) |
| PY-5.3 | CO-5 goal lowered Adapt to Apply (first appearance) |
| PY-5.4 | Make step added as Build, credited to BU-1 (recommendation 1); OS / Process topic added |
| PY-7.4 | OS / Process topic added |
| PY-8.1 | OS / Process topic added |
| PY-8.3 | Decompose added as a helper for SP-1 and SP-2 (recommendation 7) |
| PY-8.7 | OS / Process topic added |
| PY-9.6 | OS / Process topic added |
| PY-10.4 | OS / Process topic added |
| PY-11.4 | OS / Process topic added |

## Decisions

1. **Approved by Asheesh 2026-10-31:** the seven review recommendations, the cuts to the supporting roadmaps, and slotting their units into this path.
2. **Carried from v3 (2026-10-17):** PY-0.2 at the end of Stage 5; four targets in some units; database access, web frameworks and data libraries left to other roadmaps.
3. **Still to review:** the Make tasks, PY-1.9, and the changed goal levels.
4. **App:** the loader still reads v3. Moving it to v4 and loading the supporting roadmaps is a code change for the build thread.
