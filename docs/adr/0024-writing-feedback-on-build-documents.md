# ADR 0024: Writing Feedback on Build Documents

- **Status:** Proposed (2026-11-04). **Superseded in part by ADR-0028 (sections 2.2, 2.4)**, 2026-11-09; sections 2.1 and 2.3 stay.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-04
- **Governed by:** ADR-0009 (Socratic boundary, assistance accounting), ADR-0016 (deterministic grading), SPEC-15 (stage build), ADR-0018 (build maturity)

---

## 1. Context & Problem Statement

A stage build asks for a README. Its only check looks for the run command anywhere in the file, so an empty README with one command passes, and the learner gets no help with writing. Writing a README is the first of the documents a learner will write later (ADRs, specs), so the owner wants real feedback on it. The owner's own Stage 0 build showed this on 2026-11-04.

---

## 2. Decision (owner, option C)

1. **Plain-Python checks grade the README.** They give the same answer every time and need no AI:
   - the starter's headings are still there;
   - each section has at least a few words;
   - the run command sits under the "How to run it" heading;
   - "What I checked myself" names something the learner tried (an input or a case).
   The exact headings, word counts and run commands are set per build in `build.json`, as public requirements: they say what is wanted, not an answer.
2. **AXIS may comment on the writing, never grade it.** On the build page the learner can ask AXIS for feedback on the README. AXIS reads the README and the build brief and asks questions or points at unclear parts, in Socratic mode (ADR-0009). Its comment never changes a requirement, never passes or fails the build, and writes no evidence.
3. **The comment is logged** like every interaction (ADR-0022), so the owner can later see how feedback was used.
4. **The same pattern applies later** to ADRs and specs a learner writes: deterministic structure checks graded, AXIS comments ungraded.

---

## 3. Consequences

### Positive
- The learner gets feedback on writing from the first build, without AI deciding a pass.
- Each new build states its document rules in data, not code.

### Negative / Trade-offs
- Structure checks can be met with weak text. Quality is left to AXIS comments and the learner's own judgement.
- AXIS feedback needs a working model; with `MOCK_AI=true` the comment is a canned prompt.
