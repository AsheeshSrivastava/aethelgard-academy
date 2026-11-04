# ADR 0021: Private Answer Material

- **Status:** Proposed (2026-11-03)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-03
- **Governed by:** SPEC-15 (Stage Build), ADR-0016 (Own needs a build), the 10-week plan, Step 1 "New hidden checks"

---

## 1. Context & Problem Statement

The `github` remote (`aethelgard-academy`) is public. SPEC-15 put a build's hidden checks (`checks.py`) and reference solution (`solution.py`) beside its `build.json`, so the Stage 0 answers are readable by anyone, now and in Git history. The browser test `frontend/e2e/stage-build.spec.ts` also held a full passing script.

A build is the only place a learner can show Own. If its checks are public, a learner can fit a script to them, and an Own claim means little.

Exercise seeds hold hidden fields too (`hidden_checks`, `reference_solution`, choice answers, rubrics). They are out of scope here and are named in section 4.

---

## 2. Decision

1. **Answer material lives outside the public tree.** A private folder, kept in its own private Git repository, mirrors the curriculum layout:

   ```text
   <LMS_ANSWERS_DIR>/python/builds/stage-0/
     checks.py      hidden behaviour checks
     solution.py    reference solution
   ```

2. **One environment variable.** `LMS_ANSWERS_DIR` names that folder. The loader reads a build's `checks.py` from there. Nothing else in the app knows the path.
3. **New hidden checks.** The checks that were public are retired as hidden checks. The new ones keep the same function names, so `build.json` does not change, and use different inputs.
4. **The old checks become practice checks.** They stay public as `practice_checks.py` beside `build.json`. A learner may read and run them. They are never what grades a build when `LMS_ANSWERS_DIR` is set.
5. **Offline still works.** With `LMS_ANSWERS_DIR` unset, a build loads with its practice checks and the loader reports a `build-practice-checks` warning, so development and CI run with no private folder (AGENTS.md section 5). A deployment that grades for real must set the variable; the warning says so on every start.
6. **A set variable is never quietly ignored.** If `LMS_ANSWERS_DIR` is set and a build's `checks.py` is missing there, the build is skipped with a `build-invalid` error. It does not fall back to practice checks.
7. **The public tree is guarded.** `.gitignore` refuses `checks.py` and `solution.py` under `curriculum/*/builds/`, and a curriculum check reports `build-answers-public` if either file is found there.
8. **Tests that need answers read them from the private folder** and are skipped when it is not set. No public test holds a passing script.
9. **Git history is not rewritten** by this decision. That needs the owner's word.

---

## 3. Consequences

- **Good:** the answers that grade a build are no longer published. A script fitted to the practice checks still has to pass checks it cannot see.
- **Good:** the folder is a plain path, so it can be a private repository today and a mounted secret volume in a container later.
- **Cost:** CI without the private folder no longer proves that a correct script passes the hidden checks. Those tests run on the owner's machine.
- **Risk:** the old `solution.py` is still in public Git history, and it passes the new checks too, because the task is the same. New inputs stop fitting to the old checks; they do not hide the method. Removing it from history, or changing the Stage 0 task, are the two ways to close that, and both are the owner's call.

---

## 4. Not covered yet

Exercise seeds under `curriculum/python/*/exercises/` keep their hidden fields in the public tree. Moving them follows the same pattern and is a separate step.

---

## Amendment 2026-11-04: exercise seeds (section 4 closed)

Decided by the owner on 2026-11-04 ("remove them from public eye").

1. **Every seed is split in two.** The public file under `curriculum/<course>/<unit>/exercises/<stem>.json` keeps the prompt, the visible block fields (options, code, starter, tasks, `make`), the hint and the seed id. The hidden fields of its block (SPEC-13 section 4, plus `line_states`) live in `<LMS_ANSWERS_DIR>/<course>/<unit>/exercises/<stem>.json` as `{"seed_id": ..., "<item_type>": {hidden fields}}`. Seed ids do not change, so the ledger still links.
2. **Where the answers are.** `LMS_ANSWERS_DIR` if it is set; otherwise the sibling folder `../lms-answers` next to the repository, if it exists. The same rule now applies to builds.
3. **Missing answers fail loudly, per item.** A seed whose private half is missing is skipped with a `seed-answers-missing` error naming it, and is never served ungraded. The app still starts.
4. **The public tree is guarded.** A public seed file that holds a hidden field is skipped with a `seed-answers-public` error, and a test scans every public seed file for hidden fields.
5. **Unchanged:** approved hints stay public (they never give the answer). Worked answers are read from the private half and shown only after a pass (ADR-0022). Playground `test_solution.py` files stay public: they are ungraded practice and the local CLI (`lms pull`) copies them.
6. **History is not rewritten.** Answers pushed before 2026-11-04 stay in public Git history; the owner accepted this (it is a learning platform, not an exam).
7. **Standing rule: answers stay private.** Every new content step writes its hidden part (answer keys, hidden checks, Make tests, reference and wrong solutions, worked answers, build checks) to the private answers repo from the start, never to this repository. Review docs that hold answers stay git-ignored. The guard test must stay.
