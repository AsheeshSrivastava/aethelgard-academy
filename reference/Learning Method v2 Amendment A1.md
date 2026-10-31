---
title: Learning Method v2 Amendment A1
created-date: 2026-10-31
status: approved
approved-date: 2026-10-31
version: "2.1"
amends: "Learning Method v2"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-10-31 at Asheesh's direction. **Asheesh approved on 2026-10-31 the seven recommendations of the Python roadmap review and applying them across all roadmaps.** This file states them as rules. Asheesh accepted the wording on 2026-10-31 and chose Cold Check at unit end plus a stage review (A1.5). Learning Method v2 is unchanged, including its skill-to-activity table, which the app reads.

# Learning Method v2 Amendment A1

## Purpose

The Python roadmap review (2026-10-31) found that the path asked learners to judge and adapt code long before they had written enough of it, that some skills started above the first rung, and that practice volume and review were not stated anywhere. This amendment adds six rules to Learning Method v2. It does not change the ten activities, the unit rule, the concept check or the skill-to-activity table.

## A1.1 Entry rule

No skill enters the learning path above **Apply**. The first unit in path order that targets a skill sets it to Understand or Apply.

## A1.2 One-rung rule

No skill rises more than one level from one unit to the next unit that targets it, in path order. Understand → Adapt or Apply → Own is not allowed.

Path order is the order of the whole learning path, with supporting units slotted in (Python Subject Roadmap v4 and Backend Engineering Roadmap v3, Table 1). Both rules are checked by script over the whole path.

## A1.3 Make step

A **Make** step is a Build activity in which the learner writes a small program **from a blank file**, graded by hidden tests in the sandbox.

- Every unit in Stages 1 to 5 of Python that teaches a code construct ends with a Make step, unless none of its target skills fits.
- A Make step credits one of the unit's own target skills, named in the unit's outcome line. It does not add a skill. This keeps the seed rule (a seed's skill must be a target of the unit, and its activity must be in the unit's Methods).
- Make is graded deterministically, like every Build.
- The framework has no write-from-scratch skill. Make evidence counts toward the credited skill only. Whether the framework should gain such a skill is an open question for the owner.

## A1.4 Awareness topics

A topic marked **(awareness)** in a roadmap is explained in Explain and may appear in examples. It is never tested in Cold Check and never needed to pass an exercise.

## A1.5 Cold Check and spaced review

Decided by Asheesh on 2026-10-31: Cold Check runs at two points, plus rechecks.

- **Unit Cold Check.** 3 to 5 items, 24 hours after the unit is completed, AXIS off, graded deterministically. It covers only that unit's target skills and finds a gap before later units build on it.
- **Stage review.** When every unit of the stage has passed its unit Cold Check, a stage review opens: a mixed set of items from all the stage's units, AXIS off, graded deterministically. Passing it unlocks the stage build.
- **Rechecks.** Each skill is rechecked **7 days** and **30 days** after the learner first passes it in a stage review. A failed recheck lowers the estimate as any failed evidence does; it does not reset the unit or the stage.
- All three use curator-approved Cold Check variants only, and none repeats an item the learner has already seen in an earlier check.

How the app schedules this is decided in ADR-0019.

## A1.6 Practice volume

| Where | Graded items per unit | Of which Make |
| --- | --- | --- |
| Python Stages 0 to 5 | 15 to 20 | at least 3 (where the unit has a Make step) |
| Later stages and other roadmaps | 8 to 12 | as the unit needs |

Items include exercises, Regenerate variants, unit Cold Check items and the unit's share of the stage review. Regenerated exercises count as evidence. The targets set how many variants each seed pool needs (ADR-0017).

## Boundaries

This amendment owns the six rules above. Projects, course projects and capstones follow the Projects & Capstones Integration Layer v1, and how the app uses them is in ADR-0018. Evidence strength and progression decisions stay with the Proficiency & Progression System.
