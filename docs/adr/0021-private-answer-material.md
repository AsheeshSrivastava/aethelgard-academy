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
