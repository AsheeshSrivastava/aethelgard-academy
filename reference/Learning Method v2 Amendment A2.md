---
title: Learning Method v2 Amendment A2
created-date: 2026-11-09
status: approved
approved-date: 2026-11-08
version: "2.2"
amends: "Learning Method v2 (with Amendment A1)"
ai-involvement: collaborative
ai-provider: Claude
tags:
  - "#claude"
---

> [!info] Provenance
> AI-drafted with Claude on 2026-11-09 at Asheesh's direction. **Asheesh approved the rule on 2026-11-08** as part of the Technical Writing course scope (`docs/proposals/technical-writing-course-2026-11-08.md`). The wording below is new and not yet reviewed by Asheesh. Learning Method v2 and Amendment A1 are unchanged, including the skill-to-activity table, which the app reads. How the app applies this rule is decided in ADR-0028.

# Learning Method v2 Amendment A2

## Purpose

AI now drafts most engineering documents: READMEs, decision records (ADRs) and specs. The skill a working engineer needs is to direct that draft and review it: find what is missing or untrue, check it against the running code, and fix it. Learning Method v2 treated any reasoning AI supplied as help that weakens evidence. For documents that rule teaches the wrong habit. This amendment adds one rule for documents. It does not change how code is learned or checked.

## A2.1 Documents: AI drafts, the learner reviews

- **Documents** are READMEs, ADRs and specs a learner writes for their own work (the Technical Writing Roadmap v1 and the stage builds that use it).
- **AI drafting is the expected way of working.** A learner may ask AXIS to draft a document. Using the draft is not marked down.
- **The learner's review is the evidence.** Evidence for a document is:
  1. the reviewed document passing its checklist (for a README: what it does, what you need first, how to run it, a sample run, limits); and
  2. a short **review note**: what the learner changed in the draft, and why.
- **Checks are exact wherever possible.** Required headings, a run command that names the real file, and a sample run that reproduces are checked without AI. Where a point cannot be checked exactly, AXIS judges it against the checklist (ADR-0026), and the status is always shown.

## A2.2 Code is unchanged

- The learner still writes their own code.
- AXIS stays Socratic on code (ADR-0009). AI help on code is accounted for as before, and supplied reasoning still routes to Strengthen.

## A2.3 Cold Checks are unchanged

Cold Checks, module reviews and rechecks still run with AXIS off and are graded deterministically (A1.5). Document units use exact keys for their Cold Check items (for example, the planted mistakes in a draft).

## A2.4 AXIS feedback on build documents

On a build document, AXIS gives **data-based feedback**, not Socratic questions: each checklist point is marked **met** or **missing**, with one sentence on how to fix a missing point. The feedback never passes or fails the build on its own; the exact checks and the checklist do.

## Boundaries

This amendment owns the four rules above, for documents only. Code, the ten activities, the unit rule, the concept check and the skill-to-activity table stay with Learning Method v2 and Amendment A1. Evidence strength and progression decisions stay with the Proficiency & Progression System. How the app records a document draft is decided in ADR-0028.
