# ADR 0029: Explain in parts, step diagrams and quick checks

- **Status:** Accepted (2026-11-09) by the owner: the lesson layout "like you showed in the sample layout" (owner-approved mock `Lesson`), with options D1a (a steps block in `lesson.md`, drawn as boxes) and D2a (quick-check keys in the private answers repo, the server checks the choice), "1a + 2a", 2026-11-09.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-09
- **Governed by:** ADR-0008 (lesson packages), ADR-0021 (private answer material, seed amendment), ADR-0026 (AI judgement of the concept check), ADR-0027 (learner term "Module")
- **Spec:** SPEC-19

---

## 1. Context & Problem Statement

The Explain step shows a unit's whole `lesson.md` as one long page, then the concept check. The approved lesson mock splits Explain into a few short parts the learner moves through one at a time: a reason to care, the idea drawn as a small diagram of steps, the everyday tools with a quick check, and "Say it back". Two of those pieces are new kinds of lesson content:

- **A step diagram** (for example Take in → Clean up → Send out, each with code, a result and a note).
- **A quick check** (a short multiple-choice question inside a part, marked "Not graded. Just for you"). Its right answer is answer material, so under ADR-0021 it cannot sit in this repository.

## 2. Decision

1. **Parts come from the headings already in `lesson.md`.** Each `## ` section is one part, in file order, named by its heading. Sections shown by other steps (Video Walkthrough, Local Editor Instructions) are left out, as today. A lesson with no `## ` section is one part. No lesson needs rewriting to get parts.
2. **"Say it back" is always the last part.** It is the unit's existing concept check (CO-6), judged as ADR-0026 says, against the private required ideas. A Shaky answer gives feedback and never blocks (the soft gate).
3. **Step diagrams (D1a).** A fenced block with the language `steps` holds two to five steps. Each step has a `title`, and may have `code`, `result` and `note`; the block may have one `caption`. The app draws it as numbered boxes with arrows; a screen reader reads it as an ordered list. A malformed block is shown as plain text and reported by a curriculum check.
4. **Quick checks (D2a).** A fenced block with the language `quickcheck` holds an `id`, a `question` and two to four options (`A:` to `D:`). It never holds the answer. The key (`answer`, `why`) lives in the private answers repo, mirroring the unit's folder: `<LMS_ANSWERS_DIR>/<course>/<unit folder>/quick_checks.json`. The server checks a learner's choice and returns whether it is right, and the "why" only when it is right, so a wrong try does not reveal the answer.
5. **Quick checks are not evidence.** They are practice "just for you": no ledger entry, no effect on decisions or proficiency.
6. **Guards, as for seeds (ADR-0021 amendment).** A `quickcheck` block that holds `answer` or `why` is reported as `quickcheck-answers-public` and a test scans every `lesson.md` for it. A quick check with no private key is reported as `quickcheck-answers-missing`, and the app says it cannot mark that check here, rather than guessing.
7. **No invented numbers.** Parts show no minutes or durations unless the content states them.

## 3. Consequences

- Every lesson gets parts at once from its headings; only the diagrams and quick checks need authoring. PY-0.4 is converted first, as the pilot.
- The quick check needs a small API addition (SPEC-19 section 4).
- Offline development and CI still work: with no answers folder, quick checks load, and marking them answers "not available here".
- Authors write two new fenced block types; the format is in SPEC-19 so other units can follow.

## 4. Not covered

- Recording quick-check answers in the interaction log (ADR-0022). Not needed for "just for you"; can be added later.
- Images in parts. Markdown images already work; no new format is added.
