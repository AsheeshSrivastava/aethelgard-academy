# ADR 0026: AI Judgement of Written Explanations

- **Status:** Accepted (2026-11-08) by the owner ("I agree with the plan").
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-08
- **Governed by:** ADR-0009 (Socratic boundary), ADR-0016 (estimator; Cold Checks stay deterministic), ADR-0021 (answers private), ADR-0022 (interaction log), ADR-0024 (writing feedback), ADR-0025 (provider profiles)

---

## 1. Context & Problem Statement

A concept check asks the learner to explain an idea in their own words. It was graded by counting keywords in the answer (2 of a list), which matched parts of words ("int" inside "print") and could not tell understanding from luck. When a model was set, any failure (free-tier quota, timeout, unreadable reply) fell back to that keyword count without saying so, so the owner saw a "Shaky" that no model had judged (2026-11-08). The rubric and keywords also sat in the public `meta.json`. The same need comes later for README, ADR and spec feedback.

---

## 2. Decision

1. **AXIS judges, against private required ideas.** Each concept check has 2 or 3 required ideas, stored in the private answers folder (`<LMS_ANSWERS_DIR>/<course>/<unit>/concept_check.json`). The public `meta.json` keeps only the prompt. The model reports, for each idea, whether the explanation shows it, plus one feedback sentence, in a fixed JSON format. **Solid** means every required idea is met; otherwise **Shaky**. The rule is code, not the model's opinion.
2. **The status is always shown.** Either "Judged by <model>" or "Not judged", with the reason in plain words: AI is off, no rubric for this unit, the monthly cap is reached, the provider refused (quota, rate limit or key), the provider did not answer, or its reply could not be read. There is **no silent keyword fallback**. The keyword grader is removed.
3. **Not judged writes nothing** to the ledger. The learner can carry on and try again later; the Explain step stays open until a judgement exists.
4. **Judged verdicts write CO-6 evidence (owner option A)**, tagged with the model that judged them. This is one switch (`CONCEPT_CHECK_WRITES_EVIDENCE`); the owner may flip it to option C, where a verdict is feedback only.
5. **"AI can be wrong."** Every verdict says which model judged it and that AI can be wrong, with a "This seems wrong" button. A dispute is logged (ADR-0022) and does not change the verdict; it is data for choosing models.
6. **A separate judging model.** Settings has a "Judging model" apart from the AXIS chat model, so every learner is judged the same way. Unset, it uses the active chat profile.
7. **One shared AI-judgement piece.** The verdict shape (ideas met or missed, feedback, model, status, reason) and its screen component are shared; README, ADR and spec feedback reuse them later (ADR-0024).
8. **Cold Checks are unchanged:** they stay deterministic (ADR-0016). Only written explanations use AI judgement.

---

## 3. Consequences

### Positive
- Feedback names what was missing, not a generic sentence.
- A failed AI call is visible, never a fake verdict.
- The expected ideas are private, like other answer material.

### Negative / Trade-offs
- With AI off, concept checks cannot be judged; the Explain step waits. Tests and CI use the offline mock, which judges deterministically.
- Some providers ignore temperature (OpenAI's newer models); consistency comes from the fixed format and the per-idea rule.
- A judged verdict still moves the CO-6 estimate (option A); a wrong verdict can be disputed but is not reversed automatically.

### Future, not decided here
- One fixed cloud judging model for all learners, and paid access to AXIS for some learners. Both need accounts and billing (work sequence phase 6) and a later ADR.
- Older CO-6 entries from the keyword grader stay in the ledger (it is never edited); they can be told apart by their text ("Mental model evaluated as ...").
