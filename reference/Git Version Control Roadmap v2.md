---
title: Git / Version Control Roadmap v2
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "2.0"
supersedes: "Git / Version Control Supporting Track v1 (30 units, Competency Model codes)"
governed-by: "AI-Era Programming Skills Framework v1 (27 skills); Learning Method v2 with Amendment A1 (2026-10-31)"
roadmap-role: "Supporting roadmap, slotted into the Python and Backend path"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **The scope (which units are kept, merged or dropped) and their place in the path were approved by Asheesh on 2026-10-31.** Target skills, goal levels, Methods, concept lines and outcome lines are new AI-drafted wording, checked by script against the Framework and Learning Method v2, and not yet reviewed by Asheesh. Detailed teaching tasks per unit are still to be written. The v1 file stays in `reference/` until it is moved to history.

# Git / Version Control Roadmap v2

**Purpose.** The version-control capability needed to work safely in real codebases, collaborate, recover from mistakes, and keep ownership of the repository when coding agents change it.

## What changed from v1

- **Converted to the AI-Era Programming Skills Framework.** Each unit has one to three target skills from the 27, each with a goal level, a one-line concept for Explain and the CO-6 check, a Methods list (Explain first, then the main activity of each target skill) and an outcome line that can be graded without AI. The old five competencies are gone.
- **9 units replace 23 v1 units.** Small v1 units were merged into units the size of a Python unit; each unit lists the v1 units it replaces. Dropped: GIT-4.3 (reflog, now an awareness topic in GIT-1.3), GIT-5.2 and 5.4 (rebase and history reshaping), GIT-6.2 and 6.3 (blame and bisect, now awareness topics in GIT-1.4), GIT-7.1 and 7.2 (tags and releases).
- **Entry rule (Learning Method Amendment A1).** No skill enters the learning path above Apply, and no skill rises more than one level from one unit to the next. Levels here are set for where these units sit in the path, after the Python units that precede them.
- **Slotted into the path.** Units are taught where the path first needs them, not as a separate course run after Python (see "Place in the path").
- **New unit IDs.** IDs restart at `GIT-0.1`. The "Replaces (v1)" field maps each one to the old IDs.

## Place in the path

| Stage | Title | Taught | Units |
| --- | --- | --- | --- |
| 0 | Local Git | after Python Stage 4, before Stage 5 (code starts to span several files) | 4 |
| 1 | Collaboration and recovery | after Python Stage 11, before Stage 12 (existing codebases) | 4 |
| 2 | Git with coding agents | after Python Stage 12, with AI-Assisted Engineering Stage 0 | 1 |

**Course project.** No separate project: every stage build from Python Stage 5 onward is committed with Git, and the commit history becomes evidence for BU-5.

## Table 1: sequence, target skills and methods

| # | Unit | Stage | Targets (goal level) | Methods |
| --- | --- | --- | --- | --- |
| 1 | GIT-0.1 Repository state: working tree, staging and history | 0 | CO-2 (Apply), CO-6 (Apply) | Explain → Trace |
| 2 | GIT-0.2 Diffs, staging and meaningful commits | 0 | CO-3 (Apply), BU-5 (Apply) | Explain → Trace → Modify |
| 3 | GIT-0.3 Branches, HEAD and merging | 0 | CO-1 (Apply), CO-2 (Apply) | Explain → Predict → Trace |
| 4 | GIT-0.4 Resolving merge conflicts | 0 | BU-1 (Adapt), VE-5 (Apply) | Explain → Modify → Debug & Validate |
| 5 | GIT-1.1 Remotes: fetch, pull, push and divergence | 1 | CO-1 (Adapt), VE-3 (Adapt) | Explain → Predict → Debug & Validate |
| 6 | GIT-1.2 The pull-request workflow | 1 | SP-4 (Adapt), DE-1 (Adapt) | Explain → Specify → Evaluate |
| 7 | GIT-1.3 Undo and recovery | 1 | VE-3 (Adapt), DE-6 (Adapt) | Explain → Debug & Validate → Evaluate |
| 8 | GIT-1.4 Reading history for context | 1 | CO-3 (Adapt), CO-4 (Adapt) | Explain → Trace |
| 9 | GIT-2.1 Git as the safety net for agent work | 2 | BU-5 (Adapt), DE-5 (Adapt), VE-5 (Adapt) | Explain → Modify → Direct → Debug & Validate |

The CO-6 concept check runs in every unit as part of Explain and is a target only where listed.

## Table 2: stage, unit and topics

| Stage | Unit | Topics |
| --- | --- | --- |
| 0 | GIT-0.1 Repository state: working tree, staging and history | `git init` and `git clone`; working tree; staging area; commits; `git status`; `git log --oneline`; checking state before any command |
|  | GIT-0.2 Diffs, staging and meaningful commits | `git diff`, `git diff --staged`; reading hunks; `git add -p`; commit messages; one change per commit; `.gitignore` for environments, secrets and build output |
|  | GIT-0.3 Branches, HEAD and merging | `git switch` and `git branch`; HEAD; short-lived feature branches; fast-forward and merge commits; `git log --graph` |
|  | GIT-0.4 Resolving merge conflicts | conflict markers; ours and theirs; reading both sides' intent; aborting a merge; re-running checks after resolving |
| 1 | GIT-1.1 Remotes: fetch, pull, push and divergence | remotes; `origin`; remote-tracking branches; `git fetch` versus `git pull`; `git push`; upstream; ahead and behind; rejected pushes |
|  | GIT-1.2 The pull-request workflow | branch, push, open; description: what, why, how checked; small pull requests; review comments; responding to review; merging |
|  | GIT-1.3 Undo and recovery | `git restore`; `git restore --staged`; `git revert`; `git reset` (soft, mixed, hard) and its risk; merge versus rebase at practical depth; never rewrite shared history; `git reflog` (awareness) |
|  | GIT-1.4 Reading history for context | `git log -p`; `git log -- <path>`; `git show`; searching history; blame and bisect (awareness) |
| 2 | GIT-2.1 Git as the safety net for agent work | clean baseline; agent work on a branch; reviewing agent diffs hunk by hunk; small recoverable commits; rolling back an agent change; never letting an agent force-push |

## Unit details

### Stage 0: Local Git

#### GIT-0.1 Repository state: working tree, staging and history

- **Objective:** Can say where any change currently lives (working tree, staging area or commit history) and check it before acting.
- **The concept (Explain):** Git keeps three places for your work: what you are editing, what you have staged, and what you have committed.
- **Target skills:** CO-2 to Apply; CO-6 to Apply
- **Methods:** Explain → Trace
- **Outcome (measured at unit end):** CO-2: fills in a table of working tree, staged and committed contents after a sequence of edits, adds and commits, then checks it with `git status`. CO-6: explains staging in their own words with an example and a non-example.
- **Topics:** `git init` and `git clone`; working tree; staging area; commits; `git status`; `git log --oneline`; checking state before any command
- **Prerequisites:** PY-0.4 | **Importance:** Foundational | **Replaces (v1):** GIT-0.1, GIT-0.2

#### GIT-0.2 Diffs, staging and meaningful commits

- **Objective:** Can read a diff, stage only the intended change, and write a commit that says what changed and why.
- **The concept (Explain):** A commit is one intended change with a reason, not a snapshot of everything you touched.
- **Target skills:** CO-3 to Apply; BU-5 to Apply
- **Methods:** Explain → Trace → Modify
- **Outcome (measured at unit end):** CO-3: reads a diff and names the unrelated change mixed into it. BU-5: stages only the intended lines (`git add -p`) and writes a message that says why.
- **Topics:** `git diff`, `git diff --staged`; reading hunks; `git add -p`; commit messages; one change per commit; `.gitignore` for environments, secrets and build output
- **Prerequisites:** GIT-0.1 | **Importance:** Core | **Replaces (v1):** GIT-1.1, GIT-1.2, GIT-1.3, GIT-1.4

#### GIT-0.3 Branches, HEAD and merging

- **Objective:** Can work on a short-lived branch, predict what a merge will produce, and read the result.
- **The concept (Explain):** A branch is a movable name for a commit; HEAD is where you are now.
- **Target skills:** CO-1 to Apply; CO-2 to Apply
- **Methods:** Explain → Predict → Trace
- **Outcome (measured at unit end):** CO-1: predicts the commit graph after two branches change and one is merged, then checks with `git log --graph`. CO-2: traces where HEAD and each branch name point after each step.
- **Topics:** `git switch` and `git branch`; HEAD; short-lived feature branches; fast-forward and merge commits; `git log --graph`
- **Prerequisites:** GIT-0.2 | **Importance:** Core | **Replaces (v1):** GIT-2.1, GIT-2.2, GIT-2.3

#### GIT-0.4 Resolving merge conflicts

- **Objective:** Can resolve a merge conflict so that both intended changes survive, and prove it.
- **The concept (Explain):** A conflict means two changes touched the same lines; resolving it means keeping both intents, not picking a side.
- **Target skills:** BU-1 to Adapt; VE-5 to Apply
- **Methods:** Explain → Modify → Debug & Validate
- **Outcome (measured at unit end):** BU-1: resolves a conflict between two features in the same function so both behaviours remain. VE-5: runs checks that failed or were missing before and pass after, for both features.
- **Topics:** conflict markers; ours and theirs; reading both sides' intent; aborting a merge; re-running checks after resolving
- **Prerequisites:** GIT-0.3 | **Importance:** Core | **Replaces (v1):** GIT-2.4

### Stage 1: Collaboration and recovery

#### GIT-1.1 Remotes: fetch, pull, push and divergence

- **Objective:** Can reason about local and remote branches, predict what fetch, pull and push will do, and fix divergence without force.
- **The concept (Explain):** Your copy and the remote copy are separate histories that you bring together on purpose.
- **Target skills:** CO-1 to Adapt; VE-3 to Adapt
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts what `git pull` will do when local and remote have diverged. VE-3: diagnoses a rejected push from `git status` and `git log`, forms one hypothesis, and fixes it without `--force`.
- **Topics:** remotes; `origin`; remote-tracking branches; `git fetch` versus `git pull`; `git push`; upstream; ahead and behind; rejected pushes
- **Prerequisites:** GIT-0.4 | **Importance:** Core | **Replaces (v1):** GIT-3.1, GIT-3.2, GIT-3.3

#### GIT-1.2 The pull-request workflow

- **Objective:** Can propose a change as a pull request with a clear description, and review someone else's.
- **The concept (Explain):** A pull request asks others to check a change before it joins shared history.
- **Target skills:** SP-4 to Adapt; DE-1 to Adapt
- **Methods:** Explain → Specify → Evaluate
- **Outcome (measured at unit end):** SP-4: writes a description saying what, why and how it was checked, and names what a sample pull request leaves out. DE-1: reviews a small pull request and accepts, asks for a change, or rejects, with reasons.
- **Topics:** branch, push, open; description: what, why, how checked; small pull requests; review comments; responding to review; merging
- **Prerequisites:** GIT-1.1 | **Importance:** Core | **Replaces (v1):** GIT-3.4

#### GIT-1.3 Undo and recovery

- **Objective:** Can recover from common mistakes by choosing the safe undo for where the change lives, and avoid rewriting shared history.
- **The concept (Explain):** Every undo works on one place (working tree, staging or history); shared history is undone with a new commit, not erased.
- **Target skills:** VE-3 to Adapt; DE-6 to Adapt
- **Methods:** Explain → Debug & Validate → Evaluate
- **Outcome (measured at unit end):** VE-3: recovers from three broken states (a wrong file staged, a bad commit already pushed, local work that seems lost) by checking state first. DE-6: explains why `revert`, not `reset`, for a pushed commit.
- **Topics:** `git restore`; `git restore --staged`; `git revert`; `git reset` (soft, mixed, hard) and its risk; merge versus rebase at practical depth; never rewrite shared history; `git reflog` (awareness)
- **Prerequisites:** GIT-1.1 | **Importance:** Core | **Replaces (v1):** GIT-4.1, GIT-4.2, GIT-5.1, GIT-5.3

#### GIT-1.4 Reading history for context

- **Objective:** Can use commit history to explain why code is the way it is before changing it.
- **The concept (Explain):** History records why code changed, not only what changed.
- **Target skills:** CO-3 to Adapt; CO-4 to Adapt
- **Methods:** Explain → Trace
- **Outcome (measured at unit end):** CO-3 and CO-4: using `git log -p` and messages, explains in one sentence why a function changed and which commit introduced a behaviour.
- **Topics:** `git log -p`; `git log -- <path>`; `git show`; searching history; blame and bisect (awareness)
- **Prerequisites:** GIT-0.2 | **Importance:** Core | **Replaces (v1):** GIT-6.1

### Stage 2: Git with coding agents

#### GIT-2.1 Git as the safety net for agent work

- **Objective:** Can use Git to keep an AI agent's changes reviewable, small and recoverable.
- **The concept (Explain):** A clean commit before an agent starts, and small commits after, mean any agent change can be inspected or undone.
- **Target skills:** BU-5 to Adapt; DE-5 to Adapt; VE-5 to Adapt
- **Methods:** Explain → Modify → Direct → Debug & Validate
- **Outcome (measured at unit end):** BU-5: starts from a clean commit, lets an agent change code on a branch, and keeps only reviewed hunks in small commits. DE-5: limits what the agent may commit or push. VE-5: proves the result with checks, or rolls back to the baseline.
- **Topics:** clean baseline; agent work on a branch; reviewing agent diffs hunk by hunk; small recoverable commits; rolling back an agent change; never letting an agent force-push
- **Prerequisites:** GIT-1.3 | **Importance:** Core | **Replaces (v1):** GIT-8.1, GIT-8.2, GIT-8.3, GIT-8.4

## Skill coverage (target skills, this roadmap)

9 units carry 19 targets: Apply 7, Adapt 12. Skills not listed are trained in the Python, Backend and AI Engineering roadmaps.

| Skill | Units | Highest level |
| --- | --- | --- |
| CO-1 | 2 | Adapt |
| CO-2 | 2 | Apply |
| CO-3 | 2 | Adapt |
| CO-4 | 1 | Adapt |
| CO-6 | 1 | Apply |
| SP-4 | 1 | Adapt |
| BU-1 | 1 | Adapt |
| BU-5 | 2 | Adapt |
| VE-3 | 2 | Adapt |
| VE-5 | 2 | Adapt |
| DE-1 | 1 | Adapt |
| DE-5 | 1 | Adapt |
| DE-6 | 1 | Adapt |

## Decisions

1. **Scope, cuts and placement** approved by Asheesh on 2026-10-31 (review "New roadmaps: framework fit and scope").
2. **Wording still to review:** target skills, levels, concept and outcome lines.
3. **Stage builds:** every stage needs one build (owner rule). Not yet written for this roadmap.
