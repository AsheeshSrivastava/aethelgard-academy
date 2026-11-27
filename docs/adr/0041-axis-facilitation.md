# ADR-0041: AXIS facilitates: the shape of a turn, conversation memory, and how it is judged

- **Status:** **Accepted** by the owner 2026-11-27 for the decisions of sections 1 to 6. The choices left open are in SPEC-33 section 10. No test or code is written.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Basis:** the [decision paper](../plan/axis-facilitation-decision-paper.md) (D1 to D5, A1 to A7) and its [evidence review](../plan/axis-facilitation-evidence-review.md), a quick scan, not a literature review.
- **Relates to:** ADR-0009, ADR-0022, ADR-0034 (amended), ADR-0039 (amended), ADR-0040.

## 1. Principle
**This LMS is not an exam.** Cold Checks give some resistance to cheating, but learners are adults responsible for their own learning, and we provide the platform. So facilitating learning, giving feedback and asking guiding questions matter more than policing.

What follows from it here: AXIS is judged first on whether it helps; guards stay as reasonable resistance, not as something to be made perfect. What does **not** change: AXIS states no fact from memory (that is about being truthful, not about cheating), writes no code in Socratic, and evidence stays honest (ADR-0009). Cold Check rules (ADR-0040, SPEC-32) are unchanged.

## 2. Context
AXIS has no memory, never receives the learner's run output, and with no course source mostly repeats one question (cloud model) or states the cause from memory (local model). Details and figures are in the decision paper section 1.

## 3. Decisions
1. **A turn has four parts:** anchor on the learner's own line, value or error; ask one thing they can answer by looking or running; suggest one small action; follow from what they answered, with feedback on it.
2. **Support steps up** when the learner is stuck on the same point: question; narrower question and an action; then the lesson step, and with a course source an example from it (A5).
3. **Attempt before more help.** AXIS asks for an attempt before it steps up.
4. **Process actions are allowed with no course source** (D1): ways of looking that need no knowledge. Facts, causes and fixes from memory stay banned. **Deferred 2026-11-27** (SPEC-33 3.3): putting the list in the prompt made the local model teach from memory, so the wording with no source is unchanged for now.
5. **Memory** (D2, A2, A3): the last 4 exchanges of this learner on this step, built **by the server** from the interaction log, never accepted from the browser; fenced as untrusted data and capped; cleared on a new step and while a Cold Check round is open.
6. **AXIS receives the run's error output** (A1). **A conversation records the highest level of help** it reached (A4). For decision subjects (governance, change, design) the small action is **stating a decision, its reason and a risk** (A7).

## 4. Judging
Four layers: the obedience eval; turn quality (deterministic checks plus the owner's hand score on a five-line rubric); about 10 scripted dialogues; and learning, judged by what the learner can do without AXIS, with Cold Checks as the nearest signal (D3). No model grades another model. The with-source eval (plan step 5c) uses the same rubric (D5).

## 5. The fixed reply
The server-side fixed reply for error turns (SPEC-31 9.6, choice 1(b)) is **held back** (D4). It is kept only as a safety net if the local model still states causes after stage 1.

## 6. Order
Stage 1, the one-turn change and its eval, comes first. Stage 2, memory and everything that needs it, comes **after the 5 Dec 2026 freeze** (A6). SPEC-33 gives both.

## 7. Consequences
- Easier: a conversation becomes possible; help can be judged, not only withheld.
- Harder: more text is sent to the model, and with a cloud model more of the learner's words and error output leave the machine; more state to test.
- Unknown: whether the local model can follow the longer contract; whether any of this improves learning. Only use will show that.
