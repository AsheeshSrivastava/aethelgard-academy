# Brief: backend step 2 (persistence, Cold Check timer, proficiency API)

Work in D:\01-Project\lms. Read AGENTS.md and follow it strictly: test-first, commit locally only, NEVER push, never print or read .env/keys, plain simple words with the owner.

Read first: docs/adr/0016-proficiency-estimation-and-progression-decisions.md, docs/specs/12-learner-experience-api-spec.md (sections 4.1, 6, 10), docs/adr/0015-learner-identity-and-sessions.md (local-single mode only; sign-in deferred), docs/sessions/2026-10-30-learner-frontend-redesign.md. Step 1 already added src/lms/core/proficiency.py and the optional EvidenceEntry fields exercise_id, activity, cold_check.

Do, test-first, in small commits:

0. Commit docs/sessions/ (check git status first).
1. SQLiteLearnerRepository: persist and read back exercise_id, activity, cold_check in evidence_ledger. Existing databases must keep working: add the columns with an idempotent ALTER TABLE migration in initialize(); old rows read back as None/None/False. The ledger stays append-only.
2. Cold Check timer per learner x unit (ADR-0016 2.6, SPEC-12 4.1): store when a unit's non-Cold-Check activities were completed and the last Cold Check attempt and result; compute ColdCheckStatus (not_ready | waiting | available | passed | failed_waiting; available_at = completion + 24h; a fail sets a new available_at 24h after the attempt). Use an injectable clock so tests never sleep. Resetting a unit must not touch the evidence ledger.
3. GET /api/v1/learners/me/proficiency?course_id=&stage= returning ProficiencyView per SPEC-12 section 6, using lms.core.proficiency (decide_skill / decide_unit) and unit target skills from the curriculum loader. In local-single mode "me" resolves to the existing default learner. Also GET /api/v1/learners/me/units/{unit_id}/cold-check returning ColdCheckStatus.

Run `uv run pytest -q` after each change; the full suite must stay green (367 tests before this step). Commit locally after each green change. Do not push. At the end report: what changed, test count, commit hashes, and anything in the spec you had to interpret.
