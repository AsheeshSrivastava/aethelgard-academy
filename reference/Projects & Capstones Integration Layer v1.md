---
title: Projects & Capstones Integration Layer v1
type: projects-capstones-integration-layer
version: "1.0"
status: locked
created: 2026-09-18
last_updated: 2026-09-18
domain: programming-engineering
owner: Learning OS
scope: project and capstone classification, maturity, capability integration, evidence boundaries, review decisions, and readiness claims
---

# Projects & Capstones Integration Layer v1

## 1. Purpose and boundary

This is the canonical operating layer for technical projects and capstones in Learning OS. It decides what project work means: how it is selected, scoped, matured, connected to roadmap capabilities, reviewed, and used as bounded evidence.

It owns:

- the `PROJECT:P0–P4` maturity ladder;
- classification of exercise, build, project, portfolio project, and capstone;
- project selection, scope, capability targets, lifecycle, and review decisions;
- multi-roadmap integration and project evidence localization;
- readiness labels and the boundaries of portfolio and job-readiness claims.

It does **not** own subject terrain, unit sequencing, prerequisites, or proficiency criteria. Those remain with the relevant canonical subject roadmaps, their supporting tracks, and the Proficiency & Progression System. A project integrates capabilities; it does not make the project layer their owner.

This is not a subject roadmap. A separate “project roadmap” is not required: subject roadmaps own what to learn, this layer governs how selected capabilities are integrated in work, and the P0–P4 ladder supplies the project traversal structure.

---

## 2. Classification and maturity

Classification is based on the work actually attempted and evidenced, not its name, time spent, repository polish, or whether it runs.

| Classification | Minimum meaning | Maturity label |
| --- | --- | --- |
| Exercise | Narrow practice of one bounded capability; no meaningful integration is required. | Outside P0–P4 unless retained as P0 evidence. |
| Build | A bounded implementation used to apply one or a few capabilities; may become a P0 or P1 item. | P0 or P1 when it meets the criteria below. |
| Project | A coherent problem, constraints, and integrated capability targets with reviewable engineering decisions. | P1 or P2. |
| Portfolio project | A P2-or-higher project deliberately prepared to support a bounded public claim. | P3. |
| Capstone | A mature, evidence-rich integration project with meaningful architecture evolution and review. | P4. |

### P0 — Focused Capability Exercise

One intentionally bounded capability application or variation. It may have a small implementation, test, or note, but it does not claim broad integration, engineering readiness, or portfolio value. Relevant EV(s) are sufficient; a formal repository is optional.

### P1 — Small Integrated Build

A small, coherent build integrating at least two relevant capability targets or one capability with a real interface/constraint. It has a bounded objective, working validation, and an explicit scope limit. It may demonstrate early integration but is not yet an engineering or portfolio claim.

### P2 — Engineering Project

A coherent engineering problem with primary capability targets, deliberate boundaries, verification, and at least one reviewable technical decision or trade-off. It has enough substance to localize evidence to roadmap capabilities, but completion remains evidence of the artifact—not automatic proficiency.

### P3 — Portfolio Project

A P2 project promoted after review because it presents a credible, bounded engineering narrative: a clear problem and user/engineering context, understandable architecture, meaningful verification, known limitations, and supportable learner-ownership evidence. It must be reproducible or honestly disclose its constraints. P3 is a portfolio-candidate maturity, not an automatic employment claim.

### P4 — Capstone

A P3-or-higher project that deliberately integrates multiple substantial capabilities or roadmaps around a coherent problem. It must show meaningful architecture-quality reasoning, requirement or design evolution, debugging/failure learning, verification, limitations, and a reviewed multi-roadmap evidence map. Breadth alone, a large codebase, or AI-generated output does not make a capstone.

Maturity may be revised downward when the evidence, scope, ownership, or verification does not support the current label. `PROJECT:P0–P4` is an integration/maturity reference, never a proficiency level.

---

## 3. Selection and scoping

Select project work when it is the smallest coherent way to address an active integration, transfer, engineering-practice, portfolio, or capstone need. Do not create projects merely to make learning feel productive or to avoid a prerequisite gap.

Before starting P1–P4 work, record a minimal project brief containing:

- problem/use context and the bounded outcome;
- intended maturity level and explicit non-goals;
- one or more **primary** roadmap capability targets;
- any **secondary** capability targets and why they are included;
- prerequisite risks, constraints, and validation approach;
- the next review gate and a stop/park condition.

Primary targets are the capabilities the project is deliberately meant to exercise or assess. They determine whether the project is worth doing now and must remain few enough for meaningful evidence. Secondary targets are enabling, incidental, or opportunistic capabilities. They can yield evidence only if independently observed and mapped; they do not quietly expand project scope or create broad claims.

Use the Technical Roadmap Cross-Link Registry to identify legitimate inter-roadmap relationships. Check the owning roadmap for its prerequisites and capability meaning. Pull only the smallest missing prerequisite when blocked, then return to the project objective.

Scope to the next defensible decision. A project may start P1 and later be promoted; it must not begin as a P4 claim because it has ambitious features. Reduce scope, split a project, or park it when breadth compromises learner ownership, validation, or the primary target.

---

## 4. Capability integration and evidence localization

A project is a context in which roadmap capabilities may be applied; it is not a substitute for the capability definitions or their evidence standards.

For each material project claim, maintain a capability map that identifies:

| Field | Required meaning |
| --- | --- |
| Project reference | Stable project/capstone ID and maturity label. |
| Capability reference | Owning roadmap/track and exact unit or capability ID. |
| Role | Primary or secondary. |
| Observable work | The specific design, implementation, debugging, explanation, or validation performed. |
| Evidence reference | Relevant `EV-####` and, when warranted, `LR-####`. |
| Assistance/limits | Material AI, documentation, collaborator, template, or reuse effects; unresolved limits. |
| Claim status | Supported, provisional, insufficient, or contradicted. |

GitHub repositories, commits, pull requests, demos, tests, deployment records, architecture notes, and project documentation are artifact evidence. They can corroborate what was built or changed. They do not alone establish that the learner understood, chose, debugged, or can transfer the underlying capability.

Evidence is localized: an artifact observation is attached to the exact capability it bears on, with its context and limits. One feature must not be used to claim every technology present in the repository. A project-level maturity label likewise cannot be converted into capability proficiency.

Create or update an Evidence Event when project work produces a meaningful learner-performance observation. Link it to the project and the owning capability. Create a Learning Record only when the work has durable value—for example a validated project milestone, a durable architectural decision, a meaningful transfer outcome, or a materially changed capability interpretation. Do not create EVs or LRs merely because a commit, file, or session exists.

---

## 5. Learner ownership and AI assistance

Professional tools, official documentation, tests, IDEs, search, and AI are permitted. The record must distinguish tool-assisted production from learner-owned capability.

For any material assistance, retain enough information to assess:

- what the learner selected, constrained, explained, implemented, tested, or changed;
- what an AI, collaborator, template, tutorial, or existing code supplied;
- whether the learner could explain the relevant design and diagnose or modify it under variation;
- what verification the learner performed rather than merely accepted.

AI-generated code or documentation may support project progress and artifact quality. It cannot by itself support claims of independent design, implementation, debugging, or proficiency. When assistance supplies reasoning central to the target capability, downgrade the claim to tool-assisted or insufficient until learner-owned evidence is available. Do not erase assistance history to improve a project label.

---

## 6. Lifecycle and review gates

Projects move through these states: **proposed → active → review → promoted / continued / strengthened / parked / archived**. A state is a current operational decision, not a measure of learner worth or skill.

### Gate A — Admit

Approve only when the project has a bounded brief, primary targets, feasible validation, and no known prerequisite gap that makes the objective unreliable. Otherwise use an exercise, narrow the scope, or learn the missing prerequisite first.

### Gate B — Milestone review

At a meaningful milestone, inspect the observable work, validation, assistance, scope drift, and evidence map. Decide:

- **Continue** when scope and evidence trajectory remain sound.
- **Strengthen** when the core project is valid but needs targeted verification, ownership evidence, documentation, or a missing primary capability demonstration.
- **Park** when it is currently valuable but blocked, superseded, or should wait for a prerequisite; preserve the exact resume condition.
- **Archive** when it no longer has a justified learning, portfolio, or capstone role; retain relevant evidence without implying unfinished work is a failure.

### Gate C — Maturity or public-claim review

Promotion requires the actual criteria for the proposed level, the minimum documentation required by the downstream documentation specification, and no material unsupported claim. Review independently of enthusiasm, visual polish, repository activity, or completion pressure.

### Gate D — Portfolio/capstone review

Audit the problem narrative, capability map, verification, limitations, ownership/assistance disclosure, and the truthfulness of any public or job-readiness claim. A project can remain P2 or P3 even if it is not publicly shown.

---

## 7. Readiness labels and claim boundaries

Use labels precisely:

- **Active project:** currently approved work with a bounded objective.
- **Review-ready:** enough implementation and evidence exist for the relevant gate; not yet a maturity or proficiency conclusion.
- **Portfolio candidate:** a P2+ project with a plausible public narrative, pending portfolio review.
- **Portfolio-ready:** a reviewed P3/P4 project whose public documentation, verification, limitations, and ownership disclosures support its specific portfolio claims.
- **Capstone candidate:** a P3+ project with a credible plan to meet P4 criteria; not a capstone yet.
- **Capstone-ready:** a reviewed P4 project meeting the P4 criteria and documentation requirements.

Portfolio-ready means the project can support the claims actually made about that project. It does not mean the learner is job-ready. Job readiness remains an evidence-based, cross-capability judgment: projects contribute credible integration evidence alongside roadmap evidence, learner-owned reasoning, validation, transfer, and other relevant engineering evidence. The learner may apply while learning continues once the available evidence supports the roles and claims pursued.

---

## 8. Documentation and ecosystem relationships

This layer owns project-system decisions. `Project & Capstone Documentation Specification v1` is the downstream owner of how those decisions are documented: file types, templates, repository/private boundaries, folder structure, ADRs, verification records, status/review documents, and minimum documentation at each P0–P4 level. Use that specification when creating or updating documentation; do not duplicate its formats here.

`Technical Roadmap Cross-Link Registry v1.1` owns inter-roadmap capability relationships. Its `PROJECT:P0–P4` references are integration gateways, not proficiency claims. Use the registry to route relationships; use this layer to decide project maturity, evidence mapping, lifecycle, and claims.

The Runtime MOC owns navigation and the Runtime Context Manifest owns context-loading policy. This layer supplies the project/capstone rules they point to; it does not replace them.

---

## 9. Runtime use

Load only the smallest relevant section of this layer when:

- selecting, scoping, classifying, promoting, pausing, or reviewing a project/capstone;
- mapping project work to one or more roadmap capabilities or EVs/LRs;
- deciding a portfolio, capstone, or job-readiness-related project claim;
- evaluating how AI or other assistance affects learner ownership.

For normal project work, load the current Learning State and Session Handoff, the relevant primary roadmap unit(s), the project’s capability map or brief, and the narrow section needed here. Add the Cross-Link Registry, documentation specification, repository artifacts, or prior evidence only when the current decision requires them. Do not load the full project history, all roadmaps, or this entire layer by default.

At a meaningful stop, preserve the current project state, the next action, material assistance/carryover, evidence-worthy observations, and the next review or resume condition in the appropriate Learning OS artifacts. Project records preserve project truth; Learning State remains current operational truth; EVs preserve learner-performance evidence; LRs preserve durable learning history.

---

## 10. Governing invariants

```text
project maturity ≠ roadmap proficiency
artifact completion ≠ learner capability
portfolio-ready project ≠ job-ready learner
AI-assisted output ≠ learner-owned evidence
project integration ≠ ownership of subject terrain
```

**Projects & Capstones Integration Layer v1 — LOCKED**
