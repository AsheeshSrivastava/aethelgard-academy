# ADR 0028: AI-drafted documents, learner review as evidence

- **Status:** Accepted (2026-11-09) by the owner (rule approved 2026-11-08 in the Technical Writing scope; "go" for this step 2026-11-09).
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-09
- **Governed by:** Learning Method v2 Amendment A2; ADR-0009 (Socratic boundary, assistance accounting); ADR-0024 (writing feedback); ADR-0026 (AI judgement); ADR-0027 (learner term "Module")
- **Supersedes in part:** ADR-0024 sections 2.2 and 2.4
- **Amends:** ADR-0009 (a scoped exception for documents)

---

## 1. Context & Problem Statement

The Stage 0 build asks for a README that no unit teaches, and AXIS could only answer with questions (ADR-0024 section 2.2). The owner's stance (2026-11-08): AI is central to how engineers write documents. AI drafts READMEs, ADRs and specs; the engineer directs, reviews and customises them. The Technical Writing Roadmap v1 now teaches this review, starting in TW Module 0.

Two rules block it. ADR-0024 keeps AXIS Socratic on build documents, now and later for ADRs and specs. ADR-0009 tags reasoning AI supplies as `SUPPLIED_REASONING`, which routes the learner to Strengthen, so a learner who used an AI draft, as intended, would be marked down.

## 2. Decision

1. **Documents follow Amendment A2.** For READMEs, ADRs and specs, AI drafting is expected and the learner's review is the evidence: the reviewed document passes its checklist, and a review note says what changed and why.
2. **ADR-0024 section 2.1 stays and is extended** with exact checks, set per build in `build.json`: required headings present, the run command names the real entry file, and the sample run reproduces when the command is run.
3. **ADR-0024 section 2.3 stays:** every AXIS interaction on a document is logged (ADR-0022).
4. **ADR-0024 section 2.2 is superseded.** AXIS feedback on a build document is data-based: each checklist point met or missing, with one sentence on how to fix it. No Socratic questions on documents. Where a point cannot be checked exactly, AXIS judges it using the shared AI-judgement piece (ADR-0026), with the status always shown.
5. **ADR-0024 section 2.4 is superseded.** ADRs and specs follow this ADR, not the Socratic pattern.
6. **Scoped exception to ADR-0009.** A draft of a document that the learner asks for through the build's "Draft my README" (and later the ADR and spec drafts) is recorded as a **document draft**, not `SUPPLIED_REASONING`, and does not lower the evidence. The exact field is set in the spec for the build change (work sequence 2d.4). Everything else in ADR-0009 is unchanged: AXIS stays Socratic on code, and AI help on code is accounted for as before.
7. **Cold Checks are unchanged.** They run with AXIS off and are graded by exact keys (Amendment A1.5).

## 3. Options considered

| Option | For | Against |
|---|---|---|
| A. Keep Socratic-only on documents (ADR-0024 as written) | No change; AI never writes for the learner | Teaches a habit engineers no longer use; learners stall on a README nothing taught |
| B. AI drafts everything, code included | Fastest output | Learners stop building code ownership; breaks ADR-0009 and the platform's purpose |
| **C. AI drafts documents only (chosen)** | Matches real practice; review becomes the skill and the evidence; code ownership stays | Two rules (documents versus code) that the app and learners must keep apart |

## 4. Consequences

- The build page gains "Draft my README", a checklist panel and a review note (work sequence 2d.4), and data-based AXIS feedback (2d.5).
- A document draft must never be confused with help on code. The draft is requested through its own button and recorded with its own marker, so the code in the same build keeps ADR-0009 accounting.
- Structure checks plus a review note can still be met with a weak review; the checklist judgement (ADR-0026) and the owner's later look at the logs (ADR-0022) cover part of that.
- With `MOCK_AI=true`, the draft and the feedback are canned, so tests stay offline.
- Learners read "Module" on screen (ADR-0027); this ADR keeps "stage" for the code and data.
