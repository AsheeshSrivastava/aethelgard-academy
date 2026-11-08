# ADR 0027: Learner-facing term: Module (code keeps stage)

- **Status:** Accepted (2026-11-08) by the owner.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-08
- **Governed by:** ADR-0020 (stage ids and labels), ADR-0014 (frontend)

---

## 1. Context & Problem Statement

The roadmaps, the curriculum data, the API and the code group units into **stages** ("Stage 0", "DSA 0"). Learners do not use that word. Most of them know **module** from other courses. The owner wants the screen to say "Module" in every course.

Renaming "stage" everywhere would collide with Python's own "module" (imports, `.py` files, unit PY-5.1 "Modules and imports"). It would also churn routes, JSON keys, database columns, ADRs and tests weeks before the 5 Dec feature freeze.

## 2. Decision

1. **On screen the word is "Module".** Anything a learner reads says "Module" / "module": page titles, course and unit maps, build and review pages, rechecks, My progress, empty states, aria-labels, error messages the API returns to the learner, starter files a learner opens.
2. **Inside, the word stays "stage".** Code identifiers, API routes and fields (`stage`, `stage_label`, `/stages/{stage}/...`), JSON keys, curriculum files (`stages.json`, `builds/stage-0/`), database columns, evidence-ledger data, roadmaps in `reference/` and earlier ADRs keep "stage". Change labels only, never identifiers.
3. **One place makes the label.** `stage_label()` in `src/lms/core/models.py` builds the learner label ("Module 4"); slotted roadmaps keep their own names ("DSA 0", ADR-0020). The frontend shows that label as given and writes its own fixed copy with "module".
4. **A guard keeps it.** A component test renders the learner pages (course map, unit map, lesson, build, review, progress) and fails if the word "Stage" appears.

## 3. Options considered

| Option | For | Against |
|---|---|---|
| **A. "Module" on screen only (chosen)** | Learners see a familiar word; no code churn; no clash in code with Python modules | Two words for one thing; contributors must know the mapping |
| B. Rename to "module" everywhere | One word | Collides with Python modules in code and docs; touches routes, data, DB, ADRs; high risk before the freeze |
| C. Keep "Stage" | No work | Learners find it unfamiliar; the owner's call is to change it |

## 4. Consequences

- **Wording clash on screen.** Python stage 5 reads "Module 5 · Modules, packages and project structure", and unit PY-5.1 is "Modules and imports". Accepted: the label and the title are visibly different parts. Copy that teaches Python modules says "Python module" where it could be misread.
- **Glossary and AGENTS.md** carry the rule: stage (code, data, roadmaps, ADRs) = Module (anything a learner reads).
- **Curator-facing output** (curriculum check messages) uses `stage_label()` too, so it also says "Module"; the check codes (`stage-review-short`) stay.
- **Stored data is not rewritten.** Ledger entries keep their `demonstration_context` ("Stage build ..."); it is not shown to learners.
- **`/legacy`** (the old shell) is not changed; it is being retired.
- Existing specs keep "stage" for the concept; specs that define learner copy point here.
