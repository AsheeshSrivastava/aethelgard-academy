---
title: Practical DSA Roadmap v3
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "3.0"
supersedes: "Practical DSA Roadmap v2 (26 units, Competency Model codes)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Supporting roadmap, slotted into the Python and Backend path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **The scope (which units are kept, merged or dropped) and their place in the path were approved by Asheesh on 2026-10-31.** Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2, and not yet reviewed by Asheesh. Detailed teaching tasks per unit are still to be written. The v1 file stays in `reference/` until it is moved to history.

# Practical DSA Roadmap v3

**Purpose.** Practical reasoning about cost, ordering, search and structure choice in everyday Python, backend and AI-engineering code. Not competitive programming.

## What changed from v1

- **Converted to the AI-Era Programming Skills Framework.** Each unit has one to three target skills from the 27, each with a goal level, a one-line concept for Explain and the CO-6 check, a Methods list (Explain first, then the main activity of each target skill) and an outcome line that can be graded without AI. The old five competencies are gone.
- **8 units replace 17 v1 units.** Small v1 units were merged into units the size of a Python unit; each unit lists the v1 units it replaces. Dropped: DSA-0.2 (scope note), DSA-1.4 (amortised cost), DSA-2.1 to 2.3 (lists, hashmaps, sets: already PY-1.5 and PY-1.6), DSA-2.5 (linked structures), DSA-4.2 (balanced trees, now an awareness topic in DSA-1.2), DSA-4.6 (shortest paths, now an awareness topic in DSA-1.3), DSA-5.5 (becomes the course project).
- **Entry rule (Learning Method Amendment A1).** No skill enters the learning path above Apply, and no skill rises more than one level from one unit to the next. Levels here are set for where these units sit in the path, after the Python units that precede them.
- **Slotted into the path.** Units are taught where the path first needs them, not as a separate course run after Python (see "Place in the path").
- **New unit IDs.** IDs restart at `DSA-0.1`. The "Replaces (v1)" field maps each one to the old IDs.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | Cost, sorting and search | after Python Stage 3 (functions), before Stage 4 | 4 |
| 1 | Ordering, hierarchy and graphs | after Python Stage 8 (files, data and services), before Stage 9 | 4 |

**Course project.** DSA v2 Stage 5 integration (DSA-5.5) becomes a course project at maturity P1: improve the structure of an existing relief-centre report and prove the gain with complexity and runtime evidence.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | DSA-0.1 Growth and the cost of common operations | 0 | CO-1 (Apply), DE-6 (Apply) | Explain → Predict → Evaluate |
| 2 | DSA-0.2 Finding repeated and nested work | 0 | CO-3 (Apply), BU-1 (Adapt) | Explain → Trace → Modify |
| 3 | DSA-0.3 Theory versus measured runtime | 0 | VE-3 (Apply), DE-1 (Apply) | Explain → Debug & Validate → Evaluate |
| 4 | DSA-0.4 Sorting and binary search | 0 | CO-2 (Adapt), VE-1 (Adapt) | Explain → Trace → Debug & Validate |
| 5 | DSA-1.1 Stacks, queues and priority queues | 1 | DE-6 (Adapt), BU-3 (Apply) | Explain → Evaluate → Build |
| 6 | DSA-1.2 Trees and hierarchical data | 1 | CO-2 (Adapt), VE-2 (Adapt) | Explain → Trace → Debug & Validate |
| 7 | DSA-1.3 Graphs, BFS, DFS and dependency order | 1 | CO-2 (Adapt), SP-3 (Adapt) | Explain → Trace → Decompose |
| 8 | DSA-1.4 Choosing under changing constraints | 1 | DE-6 (Adapt), DE-1 (Adapt), VE-6 (Adapt) | Explain → Evaluate → Debug & Validate |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | DSA-0.1 Growth and the cost of common operations | the operations a program actually needs; constant, logarithmic, linear, n log n and quadratic growth; the cost of common list, dict and set operations; time versus memory; Big-O as a quick sketch, not a proof |
|  | DSA-0.2 Finding repeated and nested work | nested loops; `in` on a list inside a loop; repeated sorting or searching; precomputing a dict or set once; counting with a dict in one pass; when the simple version is fast enough |
|  | DSA-0.3 Theory versus measured runtime | `time.perf_counter()` basics; repeating a measurement; input sizes that show growth; noise and warm-up (awareness); when the measurement disagrees with the estimate; PY-9.6 builds on this with profilers |
|  | DSA-0.4 Sorting and binary search | `sorted` and `list.sort` with `key=`; stability (awareness); the cost of sorting; binary search by hand; `bisect` module; the loop invariant; off-by-one errors; sort once, search many times |
| 1 | DSA-1.1 Stacks, queues and priority queues | LIFO, FIFO and priority order; `list` as a stack; `collections.deque` as a queue; `heapq`; ties and stable priority; what happens when the queue is empty |
|  | DSA-1.2 Trees and hierarchical data | parent and child; nested dicts and lists as trees; recursive and iterative walks; depth; leaves; JSON documents as trees; search trees and balancing (awareness) |
|  | DSA-1.3 Graphs, BFS, DFS and dependency order | nodes and edges; adjacency dicts; directed and undirected; BFS with a queue; DFS with a stack or recursion; visited sets; dependency graphs and topological order; cycles; shortest paths (awareness) |
|  | DSA-1.4 Choosing under changing constraints | reading the new operations from a changed requirement; diagnosing an inefficient structure in existing code; trade-offs between memory, speed and simplicity; checking the change at scale |

## Unit details

### Stage 0: Cost, sorting and search

#### DSA-0.1 Growth and the cost of common operations

- **Objective:** Can estimate how the work of a piece of code grows with its input and compare two approaches by that cost.
- **The concept (Explain):** The cost of code is how its work grows as the input grows.
- **Target skills:** CO-1 to Apply; DE-6 to Apply
- **Methods:** Explain → Predict → Evaluate
- **Outcome (measured at unit end):** CO-1: predicts which of two functions slows down more when the input grows tenfold, before timing them. DE-6: chooses between a list scan and a dict lookup for a stated workload, with the reason.
- **Topics:** the operations a program actually needs; constant, logarithmic, linear, n log n and quadratic growth; the cost of common list, dict and set operations; time versus memory; Big-O as a quick sketch, not a proof
- **Prerequisites:** PY-3.5, PY-1.5 | **Importance:** Foundational | **Replaces (v1):** DSA-0.1, DSA-1.1, DSA-1.2

#### DSA-0.2 Finding repeated and nested work

- **Objective:** Can spot hidden repeated or nested work in code and replace it with indexed or precomputed access.
- **The concept (Explain):** A loop inside a loop, or a search inside a loop, multiplies the work.
- **Target skills:** CO-3 to Apply; BU-1 to Adapt
- **Methods:** Explain → Trace → Modify
- **Outcome (measured at unit end):** CO-3: finds the hidden quadratic in AI-written code that checks `in` on a list inside a loop. BU-1: rewrites it with a set or dict, and the old checks still pass.
- **Topics:** nested loops; `in` on a list inside a loop; repeated sorting or searching; precomputing a dict or set once; counting with a dict in one pass; when the simple version is fast enough
- **Prerequisites:** DSA-0.1 | **Importance:** Core | **Replaces (v1):** DSA-1.3, DSA-5.2

#### DSA-0.3 Theory versus measured runtime

- **Objective:** Can test a cost prediction with simple, repeated timing and say whether the evidence supports it.
- **The concept (Explain):** A cost estimate is a prediction; timing at several input sizes is the check.
- **Target skills:** VE-3 to Apply; DE-1 to Apply
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: states a prediction, times both versions with `time.perf_counter()` at three input sizes, repeats each run, and says whether the data supports the prediction. DE-1: accepts or rejects an AI's "this is faster" claim using those measurements.
- **Topics:** `time.perf_counter()` basics; repeating a measurement; input sizes that show growth; noise and warm-up (awareness); when the measurement disagrees with the estimate; PY-9.6 builds on this with profilers
- **Prerequisites:** DSA-0.1 | **Importance:** Core | **Replaces (v1):** DSA-1.5, DSA-5.4

#### DSA-0.4 Sorting and binary search

- **Objective:** Can use sorting as an operation with a cost and a key, and reason about binary search on sorted data, including its edge cases.
- **The concept (Explain):** Sorted data lets you find a value by halving the search each step.
- **Target skills:** CO-2 to Adapt; VE-1 to Adapt
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-2: traces `lo`, `hi` and `mid` through a binary search for a found and a not-found value. VE-1: writes checks (empty, one item, first, last, missing) that fail on an off-by-one version they have not seen.
- **Topics:** `sorted` and `list.sort` with `key=`; stability (awareness); the cost of sorting; binary search by hand; `bisect` module; the loop invariant; off-by-one errors; sort once, search many times
- **Prerequisites:** DSA-0.1, PY-3.3 | **Importance:** Core | **Replaces (v1):** DSA-3.1, DSA-3.2

### Stage 1: Ordering, hierarchy and graphs

#### DSA-1.1 Stacks, queues and priority queues

- **Objective:** Can choose stack, queue or priority-queue behaviour from an ordering rule and build it with the standard library.
- **The concept (Explain):** The order things leave a collection (last in, first in, or most urgent) decides the structure.
- **Target skills:** DE-6 to Adapt; BU-3 to Apply
- **Methods:** Explain → Evaluate → Build
- **Outcome (measured at unit end):** DE-6: chooses stack, queue or priority queue for three intake scenarios and names the ordering rule that decides. BU-3: builds a triage queue with `heapq` from its documentation, tested on ties and an empty queue.
- **Topics:** LIFO, FIFO and priority order; `list` as a stack; `collections.deque` as a queue; `heapq`; ties and stable priority; what happens when the queue is empty
- **Prerequisites:** DSA-0.1, PY-1.6 | **Importance:** Core | **Replaces (v1):** DSA-2.4, DSA-3.3

#### DSA-1.2 Trees and hierarchical data

- **Objective:** Can represent and walk hierarchical data as a tree, and debug a recursive walk.
- **The concept (Explain):** A tree is data where each item has one parent and any number of children.
- **Target skills:** CO-2 to Adapt; VE-2 to Adapt
- **Methods:** Explain → Trace → Debug & Validate
- **Outcome (measured at unit end):** CO-2: traces a recursive walk over a nested department tree. VE-2: finds why an AI-written tree total misses leaf nodes and names the input that shows it.
- **Topics:** parent and child; nested dicts and lists as trees; recursive and iterative walks; depth; leaves; JSON documents as trees; search trees and balancing (awareness)
- **Prerequisites:** DSA-0.1, PY-3.6 | **Importance:** Core | **Replaces (v1):** DSA-4.1

#### DSA-1.3 Graphs, BFS, DFS and dependency order

- **Objective:** Can model relationships as a graph, reason about breadth-first and depth-first traversal, and order dependencies.
- **The concept (Explain):** A graph is a set of things and the links between them; traversal order decides what you reach first.
- **Target skills:** CO-2 to Adapt; SP-3 to Adapt
- **Methods:** Explain → Trace → Decompose
- **Outcome (measured at unit end):** CO-2: traces the visit order of BFS and DFS on a small referral graph. SP-3: orders a set of task dependencies so each runs after what it needs, and explains what a cycle means.
- **Topics:** nodes and edges; adjacency dicts; directed and undirected; BFS with a queue; DFS with a stack or recursion; visited sets; dependency graphs and topological order; cycles; shortest paths (awareness)
- **Prerequisites:** DSA-1.1, DSA-1.2 | **Importance:** Core | **Replaces (v1):** DSA-4.3, DSA-4.4, DSA-4.5

#### DSA-1.4 Choosing under changing constraints

- **Objective:** Can re-choose a structure or algorithm when the requirement changes, and justify the choice with cost and evidence.
- **The concept (Explain):** The right structure is the one that fits today's operations; when they change, the choice is reopened.
- **Target skills:** DE-6 to Adapt; DE-1 to Adapt; VE-6 to Adapt
- **Methods:** Explain → Evaluate → Debug & Validate
- **Outcome (measured at unit end):** DE-6: re-chooses a structure when "list all cases" becomes "top 10 by priority, updated live". DE-1: accepts, changes or rejects an AI's structural suggestion with a cost reason. VE-6: tests the new version on empty and very large input.
- **Topics:** reading the new operations from a changed requirement; diagnosing an inefficient structure in existing code; trade-offs between memory, speed and simplicity; checking the change at scale
- **Prerequisites:** DSA-1.1, DSA-1.3, DSA-0.3 | **Importance:** Core | **Replaces (v1):** DSA-5.1, DSA-5.3

## Skill coverage (target skills, this roadmap)

8 units carry 17 targets: Apply 6, Adapt 11. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-1 | 1 | Apply |
| CO-2 | 3 | Adapt |
| CO-3 | 1 | Apply |
| SP-3 | 1 | Adapt |
| BU-1 | 1 | Adapt |
| BU-3 | 1 | Apply |
| VE-1 | 1 | Adapt |
| VE-2 | 1 | Adapt |
| VE-3 | 1 | Apply |
| VE-6 | 1 | Adapt |
| DE-1 | 2 | Adapt |
| DE-6 | 3 | Adapt |

## Decisions

1. **Scope, cuts and placement** approved by Asheesh on 2026-10-31 (review "New roadmaps: framework fit and scope").
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Stage builds:** every stage needs one build (owner rule). Not yet written for this roadmap.
