# Work Sequence

One list of what comes next, in order. One step at a time. Agreed with the owner on 2026-11-04.

**Current step:** 2.2 Multi-file builds.
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
- [x] 1.1 Entry and one-rung check: no skill enters above Apply, no jump of more than one level (Learning Method v2 A1.1, A1.2). Done 2026-11-04: no entry breaks, 9 rung breaks found (step 1.4).
- [x] 1.2 Volume warning below 15 practice items per unit in Stages 0 to 5 (A1.6, ADR-0019). Done 2026-11-04: all 5 units with content warn, as expected.
- [x] 1.3 Awareness topics never in a Cold Check: each seed names its `topic`, and the check compares it with the roadmap's awareness topics (A1.4). Done 2026-11-04: all 37 seeds have a topic; none tests an awareness topic.
- [x] 1.4 The 9 skills that rise two levels at once in the roadmaps (PY-11.4, PY-12.1, PY-12.4 twice, PY-13.3, NET-0.2, BE-15.1, BE-17.2, AI-17.4). Decided 2026-11-04: option C, left as they are for now and always flagged as errors; `test_the_nine_known_jumps_in_the_roadmaps_stay_flagged` fails if the check stops reporting them. Revisit when content reaches Stage 11.
- [x] 1.5 Flaky frontend tests. Done 2026-11-04: the one fixed 600 ms sleep now waits for the page's re-check; condition waits may take up to 5 s on a busy machine.

## Phase 2: Build maturity and stage builds

- [x] 2.1 Builds carry `maturity` (P0 to P4) and `kind`, and the map shows them (ADR-0018). Stage builds are P1. (APPROVE the Stage 0 build's label) Done 2026-11-04 with option A; label approved by the owner: `maturity` only, the type of work follows from the level (ADR-0018 amendment). The map shows "P1 · Stage build".
- [ ] 2.2 Multi-file builds, needed from Python Stage 5. (NOTHING)
- [x] 2.3 When to write the other stage builds. Decided: with each stage's content (ADR-0018 amendment).

## Phase 2b: README feedback on the Stage 0 build (ADR-0024, owner option C)

Runs after phase 2's build-page work is committed, because it changes the same files.

- [ ] 2b.1 Plain-Python README checks: headings kept, words in each section, run command under "How to run it", "What I checked myself" names something tried. (NOTHING, then APPROVE the updated Stage 0 build)
- [ ] 2b.2 AXIS comment on the README: Socratic, ungraded, logged. (NOTHING)
- [ ] 2b.3 The editor colours only `.py` files; README and other files show as plain text. (NOTHING)

## Phase 2c: Model providers and a Settings page (ADR-0025, separate thread)

Decided 2026-11-04: keys stay in `.env` for now; Gemini gets its own adapter (Google's SDK), not the OpenAI-compatible address; check which Gemini model answers on the free API when this is built.

- [ ] 2c.1 Provider profiles behind `IAXISCompanion`: local (OpenAI-compatible), OpenAI, Gemini. (DECIDE which first)
- [ ] 2c.2 Settings page: active profile, "key set: yes/no", test connection showing the model that answered. (NOTHING)
- [ ] 2c.3 Cost estimate and a monthly cap for paid providers. (DECIDE the cap)

## Phase 3: Two decisions before more testing

- [x] 3.1 Does work done in test mode count toward your own progress? Decided 2026-11-04: yes, as today.
- [x] 3.2 The 4 playground practice-check files (`test_solution.py`). Decided 2026-11-04 ("move private"): moved to the private answers repo; `lms pull` reads them from there.

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
