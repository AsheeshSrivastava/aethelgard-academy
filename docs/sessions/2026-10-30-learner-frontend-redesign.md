# Session log: learner frontend redesign (2026-10-30)

- **Participants:** Asheesh Ranjan Srivastava (owner), Claude (architect, cloud session)
- **Why this file exists:** this session ran in the cloud and wrote files into the repo, so Entire did not capture it as a checkpoint. This log records what was discussed and decided.
- **Outputs:** ADR-0014, ADR-0015, ADR-0016, ADR-0017, SPEC-12; design canvas https://claude.ai/artifact/M4NM7RpDooWVXwHR8QarW6; architecture proposal https://claude.ai/artifact/VENPVEwkVxHjuhyAWH16X4; code step 1 (proficiency estimator).

## Sequence of decisions

1. **Scope.** Study the backend in `D:\01-Project\lms` (not the `aethelgard-lms-v2` GitHub repo) and build a modern AI-led frontend in this repo, replacing `src/lms/web/`.
2. **Information architecture.** Front page → Courses (Python, Python for Backend/AI, AI Engineering) → course map → unit map → lesson. Every page has a back arrow.
3. **Lesson structure.** Video first, then Explain (every lesson); further activities vary per unit. Playground must be truly interactive (live stdin, run, verify).
4. **Unit controls.** Reset per unit (clears progress, never the ledger). Regenerate on every activity except Explain. A Build (script or mini-project) at the end of every stage.
5. **Evidence.** Regenerated exercises count as evidence at full strength. Progress shown on a "My progress" page (skill ladder, provisional vs supported, filterable ledger, next action).
6. **Backend first.** Backend contract gaps are addressed before the real frontend. Stack chosen: React 19 + TypeScript + Vite, built into `src/lms/web/dist/` (ADR-0014).
7. **Future features.** Content and scenarios are data, replaceable without code. Google Meet, forums and gamification arrive as feature modules behind flags; gamification only reads evidence events and never feeds progression (ADR-0014 §6, SPEC-12 §9).
8. **Sign-in deferred** until the app is ready; `local-single` mode with `/learners/me` routes now (ADR-0015). **No Temporal** needed; short tasks only.
9. **Thresholds approved** as starting values (ADR-0016): window 10 entries / 90 days; supported needs 2 entries from different exercises; 2 consecutive weak entries lower a level by one.
10. **Cold Check** (owner's idea): a per-unit check available 24 h after completing the unit; no AXIS help; unseen variant; Regenerate only after an attempt; fail → Strengthen and retry in 24 h; required for *supported*. Graded deterministically, never by AI.
11. **Builds:** one build per stage, unlocked when every unit in the stage has passed its Cold Check.
12. **Content ownership:** the curator decides each unit's activities, order and scaffolding in the unit package; backend reads and validates (SPEC-12 §3.1); frontend only renders. Not every unit has all 5–6 activity types, but each stage covers all.
13. **Exercise variants** (ADR-0017): curator writes 1–3 seeds per activity; a separate offline AI pipeline batch-generates variants; every variant is auto-verified in the sandbox plus deterministic checks; Regenerate serves from the pool with no LLM call at click time; Cold Check variants need curator approval.

## Code step 1 (committed and pushed by owner to Entire `origin`, main d7daa1c)

- `src/lms/core/proficiency.py`: whole-ledger estimator and decisions (ADR-0016).
- `src/lms/core/models.py`: `EvidenceEntry` gains optional `exercise_id`, `activity`, `cold_check`.
- `src/lms/core/progression.py`: `evaluate_progression()` delegates to the estimator.
- Tests: new `tests/test_proficiency.py`; `test_progression.py` and `test_socratic_guardrail.py` updated for the single-entry-is-provisional rule.

## Next

Step 2 (run via Remote Control on the owner's machine so Entire records it): persist the new evidence fields, a per-unit Cold Check timer, and `GET /api/v1/learners/me/proficiency`.
