# ADR 0034: Upstream docs stay the primary source for AXIS answers until the concept notes are ready

- **Status:** Proposed (owner decision 2026-11-14 in principle; ADR text awaits owner review)
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-14
- **Extends:** ADR-0003 (section 4, temporary exception for upstream citations)
- **Governed by:** AGENTS.md (Provenance Firewall, Zero-Cost Local Development), ADR-0035 (retrieval strategy)
- **Findings behind it:** `lms-backlog/2d7-axis-answers-vs-rag.md` (read-only check of main fc0bf71)

---

## 1. Context & Problem Statement

ADR-0003 section 4 lets AXIS cite upstream documentation (Python, FastAPI, pytest) from `data/index`, as a temporary exception to Stage 3. A check of main on 2026-11-14 shows the exception is not working honestly:

1. The prompt never says "answer only from these passages", "cite what you use" or "say so if nothing fits".
2. When nothing is retrieved, the grounding block is left out and the learner is not told.
3. `DEFAULT_CITATION` shows a source the answer did not use. The concept-store fallback can show an unrelated passage.
4. The curriculum and concept notes are never searched (`build_default_router` passes no `ConceptStore`).
5. On a fresh clone there is no `data/index`, no retriever, and no message.

The curriculum notes are not ready (10 approved, many to write), so AXIS cannot move to Stage 3 yet. The ADR-0003 review ("before anyone other than the owner learns on the platform") is the pilot, so the exception has to become a rule that is safe to run, not an accident.

## 2. Decision

1. **Upstream docs remain the primary source** for AXIS answers until the concept notes are ready. The ADR-0003 section 4 review stays open. Stage 3 stays the target.
2. **Curriculum comes first, upstream second.** Lessons and approved concept notes are searched as a source beside upstream docs (this is the A7 wiring). When both match, curriculum passages rank first for terminology.
3. **The answer rule:**
   - Answers are built from retrieved, verified passages.
   - The prompt says: use the passages, cite only passages you used, and if none fit, say so.
   - A citation chip shows only a passage that was retrieved, verified and used. No default citation, no fallback to an unrelated passage.
   - No passage found: AXIS says "This is not in the course yet" (or "not in the docs"), shows no chip. In Coach mode only, it may explain syntax or an error message from general knowledge, labelled "Not from the course". Socratic mode stays Socratic (ADR-0009).
   - No index loaded (fresh clone, mock mode): AXIS says so in plain words. It never answers as if grounded.
4. **Licence care.** Upstream text is quoted in short passages with a readable source name, never at length and never as a raw passage id.
5. **Exit condition.** When the concept notes and lessons cover the corpus well enough (measured by ADR-0035's question set: curriculum answers a set share of the questions), the owner decides whether upstream moves to "second source" or is removed.

## 3. Consequences

- AXIS stops claiming sources it did not use. The learner can tell grounded from not grounded.
- Upstream stays a recorded exception with a visible exit, not a silent one.
- Costs: some questions now end in "not in the course yet" where the model used to guess. That is the intended trade (honest evidence over fluent guesses, per the owner's quality bar).
- ADR-0003 section 4 gets a one-line pointer to this ADR. Its text is not rewritten.
- Work this implies, one PR each, tests first: remove default and unrelated citations (1); prompt rules (2); wire the `ConceptStore` (3); retrieval upgrade per ADR-0035 (4 onward).
