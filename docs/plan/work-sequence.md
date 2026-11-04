# Work Sequence

One list of what comes next, in order. One step at a time. Agreed with the owner on 2026-11-04.

**Current step:** 1.1 Entry and one-rung check.
**Owner, in parallel:** 1.0 Walk Stage 0 yourself (TEST).

What each step needs from the owner:

- **NOTHING**: Claude builds, tests and commits it, then reports.
- **DECIDE**: one choice, given as options.
- **APPROVE**: read a draft, say yes or change it.
- **TEST**: use the app yourself.

Pushing to GitHub and Entire is always at the owner's word.

---

## Phase 1: Guards before more content

- [ ] 1.0 Walk Stage 0 as a learner, with AXIS on the local model, and say what felt wrong. Runs alongside phase 1. (TEST)
- [ ] 1.1 Entry and one-rung check: no skill enters above Apply, no jump of more than one level (Learning Method v2 A1.1, A1.2). (NOTHING)
- [ ] 1.2 Volume warning below 15 practice items per unit in Stages 0 to 5 (A1.6, ADR-0019). (NOTHING)
- [ ] 1.3 Awareness topics never in a Cold Check: each seed names its `topic`, and the check compares it with the roadmap's "(awareness)" topics (A1.4). Decided: option A, a topic field. (NOTHING)

## Phase 2: Build maturity and stage builds

- [ ] 2.1 Builds carry `maturity` (P0 to P4) and `kind`, and the map shows them (ADR-0018). Stage builds are P1. (APPROVE the Stage 0 build's label)
- [ ] 2.2 Multi-file builds, needed from Python Stage 5. (NOTHING)
- [x] 2.3 When to write the other stage builds. Decided: with each stage's content (ADR-0018 amendment).

## Phase 3: Two decisions before more testing

- [ ] 3.1 Does work done in test mode count toward your own progress? Today it does. (DECIDE)
- [ ] 3.2 The 4 playground practice-check files (`test_solution.py`): keep them public, or move them to the private answers? (DECIDE)

## Phase 4: Content, one unit at a time

Hidden parts always go to the private answers repo from the start (ADR-0021).

- [ ] 4.1 Finish PY-1.2: lesson, concept check, Predict, Debug & Validate and Cold Check items. (APPROVE)
- [ ] 4.2 The rest of Stage 1 in v4 order, then the Stage 1 build and stage review. (APPROVE each)
- [ ] 4.3 Top up Stage 0 to 15 practice items per unit. (APPROVE)

## Phase 5: Your run-through of Stage 1

- [ ] 5.1 Walk Stage 1 as a learner. (TEST)
- [ ] 5.2 Turn the real waits back on: 24 hours, 7 days, 30 days. (DECIDE when)

## Phase 6: Before anyone else learns

- [ ] 6.1 Docker sandbox on by default. (NOTHING)
- [ ] 6.2 Consent, data deletion and retention (ADR-0022 section 2.6). (NOTHING, then APPROVE the wording)
- [ ] 6.3 Close the AXIS upstream-citation exception (ADR-0003 section 4). (NOTHING)
- [ ] 6.4 Accept or revise the Proposed ADRs: 0015, 0016, 0018 to 0023. (APPROVE each)

---

## Done

- 2026-11-04: answers moved to the private repo, backed up to a private GitHub repo (ADR-0021 amendment).
- 2026-11-04: ADR audit; ADR-0023 written, ADR-0018 and ADR-0021 amended.
