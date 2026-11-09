# Work Sequence

One list of what comes next, in order. One step at a time. Agreed with the owner on 2026-11-04.

**Current step:** Phase 1b is done. Next: the owner's second Stage 0 pass with fresh resets, then 4.1 Finish PY-1.2.
**Owner, in parallel:** 1.0 Walk Stage 0 yourself (TEST).

What each step needs from the owner:

- **NOTHING**: Claude builds, tests and commits it, then reports.
- **DECIDE**: one choice, given as options.
- **APPROVE**: read a draft, say yes or change it.
- **TEST**: use the app yourself.

Pushing to GitHub and Entire is always at the owner's word.

---

## Phase 1: Guards before more content

- [x] 1.0 Walk Stage 0 as a learner, with AXIS on the local model, and say what felt wrong. Runs alongside phase 1. (TEST) Done 2026-11-04; the owner plans a second pass after resetting units. Findings are steps 1b.1 to 1b.4.
- [x] 1.1 Entry and one-rung check: no skill enters above Apply, no jump of more than one level (Learning Method v2 A1.1, A1.2). Done 2026-11-04: no entry breaks, 9 rung breaks found (step 1.4).
- [x] 1.2 Volume warning below 15 practice items per unit in Stages 0 to 5 (A1.6, ADR-0019). Done 2026-11-04: all 5 units with content warn, as expected.
- [x] 1.3 Awareness topics never in a Cold Check: each seed names its `topic`, and the check compares it with the roadmap's awareness topics (A1.4). Done 2026-11-04: all 37 seeds have a topic; none tests an awareness topic.
- [x] 1.4 The 9 skills that rise two levels at once in the roadmaps (PY-11.4, PY-12.1, PY-12.4 twice, PY-13.3, NET-0.2, BE-15.1, BE-17.2, AI-17.4). Decided 2026-11-04: option C, left as they are for now and always flagged as errors; `test_the_nine_known_jumps_in_the_roadmaps_stay_flagged` fails if the check stops reporting them. Revisit when content reaches Stage 11.
- [x] 1.5 Flaky frontend tests. Done 2026-11-04: the one fixed 600 ms sleep now waits for the page's re-check; condition waits may take up to 5 s on a busy machine.

## Phase 1b: From the owner's Stage 0 walk-through (2026-11-04)

- [x] 1b.1 Reset clears a unit's progress, not only its timers: the ledger is never deleted; a reset marker makes the unit's decision count only evidence after it. Amends ADR-0016. (DECIDE, then NOTHING) Decided A (per unit). Done 2026-11-04.
- [x] 1b.2 A reset for the stage review too, the same way. (DECIDE, then NOTHING) Decided A ("Restart stage review" button). Done 2026-11-04.
- [x] 1b.3 A Skills tab next to My progress: every target skill, its level on the Understand to Own ladder, and plain meanings of the levels and of Progress, Accelerate, Strengthen, Rebuild and Undecided. (APPROVE the wording and layout) Redrafted and approved 2026-11-04 as "My skills": grouped by the 5 skill areas, lifetime evidence across all courses, "Practised in" list, not-started skills greyed out; level meanings on the page, label meanings on My progress. Built 2026-11-04 (SPEC-12 section 6.1).
- [x] 1b.4 Which units have a Make step: 15 units, all in Python Stages 1 to 5 (PY-1.2 to PY-5.4), because Amendment A1.3 puts Make only in units that teach a code construct there. Stage 0 has none; its stage build plays that role. Answered 2026-11-04.

## Phase 2: Build maturity and stage builds

- [x] 2.1 Builds carry `maturity` (P0 to P4) and `kind`, and the map shows them (ADR-0018). Stage builds are P1. (APPROVE the Stage 0 build's label) Done 2026-11-04 with option A; label approved by the owner: `maturity` only, the type of work follows from the level (ADR-0018 amendment). The map shows "P1 · Stage build".
- [x] 2.2 Multi-file builds, needed from Python Stage 5. (NOTHING) Done 2026-11-04 (SPEC-15 section 2.4): behaviour checks and the build page's Run use every `.py` file the build declares; other `.py` names must be importable; editing any `.py` file clears Verify.
- [x] 2.3 When to write the other stage builds. Decided: with each stage's content (ADR-0018 amendment).

## Phase 2b: README feedback on the Stage 0 build (ADR-0024, owner option C)

Runs after phase 2's build-page work is committed, because it changes the same files.

- [x] 2b.1 Plain-Python README checks: headings kept, words in each section, run command under "How to run it", "What I checked myself" names something tried. (NOTHING, then APPROVE the updated Stage 0 build) Done 2026-11-04: three README requirements (what it does, how to run it, what you checked); the Stage 0 build now has 9 requirements.
- [x] 2b.2 AXIS comment on the README: Socratic, ungraded, logged. (NOTHING) Done 2026-11-04: "Ask AXIS about my README" button; sent without the build's id, so it never counts as help on the build.
- [x] 2b.3 The editor colours only `.py` files; README and other files show as plain text. (NOTHING) Done 2026-11-04.

## Phase 2c: Model providers and a Settings page (ADR-0025, separate thread)

Decided 2026-11-04: keys stay in `.env` for now; Gemini gets its own adapter (Google's SDK), not the OpenAI-compatible address; check which Gemini model answers on the free API when this is built.

- [x] 2c.1 Provider profiles behind `IAXISCompanion`: local (OpenAI-compatible), OpenAI, Gemini. (DECIDE which first) Done 2026-11-04 (commit f63bb03).
- [x] 2c.2 Settings page: active profile, "key set: yes/no", test connection showing the model that answered. (NOTHING) Done 2026-11-04 (commit f63bb03).
- [x] 2c.3 Cost estimate and a monthly cap for paid providers. (DECIDE the cap) Done 2026-11-04 (commit f63bb03).

## Phase 2d: Technical Writing, the README work (owner, 2026-11-08)

Scope approved 2026-11-08: `docs/proposals/technical-writing-course-2026-11-08.md`.

- [x] 2d.1 Roadmap file `reference/Technical Writing Roadmap v1.md`, slotted into the Python path (TW 0, 1, 2). (NOTHING, then APPROVE the wording) Done 2026-11-08.
- [x] 2d.2 Learning Method Amendment A2 and its ADR: for documents, AI drafting is expected and the review is the evidence. Settle ADR-0024 sections 2.2 and 2.4 here. (APPROVE) Done 2026-11-09: `reference/Learning Method v2 Amendment A2.md`, ADR-0028 (supersedes ADR-0024 sections 2.2 and 2.4, amends ADR-0009).
- [ ] 2d.3 TW-0.1 and TW-0.2 content; keys in the private answers repo. (APPROVE) Drafted 2026-11-09: 21 seeds, all Draft (`curator_approved: false`) until the owner approves; keys in lms-answers.
- [ ] 2d.4 Stage 0 build change: "Learn it in TW Module 0" button, "Draft my README", checklist panel, review note, stronger Verify. (NOTHING, then TEST)
- [ ] 2d.5 AXIS data-based build feedback, point by point, no Socratic questions. (NOTHING, then TEST)
- [ ] 2d.6 AXIS answers vs RAG (owner, 2026-11-08; placed right after the README work, 2d.1 to 2d.5, by the owner): when a learner asks AXIS a question (not when AI judges), is the answer built only from retrieved passages, or from the model's own knowledge, and are the citations real sources for what was said? Decide the purpose of RAG at question time. Expected direction: answers are constructed from retrieved curriculum, since a direct answer is often not in one passage; say so when nothing relevant is found. Check first: what the prompt allows, whether citations match the text used, and the upstream exception in 6.3, which may close here too. (DECIDE, then NOTHING)

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

- 2026-11-08: AI judgement of concept checks (ADR-0026, SPEC-18): private required ideas, status always shown, no keyword fallback, "AI can be wrong" + dispute, separate judging model.
