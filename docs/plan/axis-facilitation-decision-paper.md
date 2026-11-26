# AXIS facilitation: what a good turn is, conversation memory, and how we judge it

Status: **Decided** by the owner 2026-11-27: yes to D1 to D5 and additions A1 to A7, plus "ask for an attempt before giving more help". Recorded in [ADR-0041](../adr/0041-axis-facilitation.md); the build is described in SPEC-33 (draft).

**The owner's principle:** this LMS is not an exam. Cold Checks give some resistance to cheating, but learners are adults responsible for their own learning, and we provide the platform. Facilitating learning, feedback and guiding questions matter more than policing.
Labels: **CONFIRMED** (seen in code or eval), **INFERRED** (reasoning), **UNKNOWN**.

## 1. The problem
CONFIRMED from the SPEC-31 Amendment A eval (18 error-message questions, no course source):
- Local model (Qwythos-9B): the explains flag is on for 33% (temperature 0.0) and 27% (0.2) of replies; the true rate is higher. It often states the cause from memory, then asks a question.
- OpenAI (`gpt-6-luna`, one run): 0 of 162 replies state a cause or fix, on one reader's check. 14 of 162 ask a question that leans towards the answer. 145 of 162 are one shape: "What did you expect to happen, and what have you checked so far?" No reply suggests anything to try.
- The eval measures whether the model keeps the rules, not whether a learner learns.

CONFIRMED by code check:
- AXIS has **no memory** of the conversation. On both routes (`/api/v1/axis/stream` and `/api/v1/axis/consult`; there is no other chat route) no earlier turn reaches the model: it gets one system prompt and one user message.
- AXIS **does not see the learner's run**. The panel never sends `execution_result`, so AXIS sees an error only if the learner pastes it.

So today there are two failures: one model breaks the rule; the other keeps it and helps very little (one move, repeated), and no model can follow up without memory.

## 2. Principles (INFERRED)
Basis: the DFELE handout and references (Knowles, scaffolding, guided discussion, Gagne). They cover human-led training only, so applying them to a tutor is inference, not a finding.
1. The learner has real experience and a real problem (their own script and error). Start from their line, not from a general explanation.
2. A guiding question works only if the learner already holds the concept. A question they cannot answer is a wall. After two stuck turns on one point, support must step up, not repeat.
3. Support is scaffolding: light first, fading as the learner shows they can do it. It is not a fixed mode.
4. Feedback is specific, close in time and tied to the learner's goal.
5. Adults want to act. A small action ("print this value", "run only line 2", "reread step 3 of the lesson") keeps them moving and teaches the habit of checking.

## 3. What a good turn is
Four parts, in any mode. The mode changes how much it gives, not the shape.
1. **Anchor:** name the learner's own line, value or error word.
2. **Narrow:** ask one thing they can answer by looking or running it.
3. **Act:** suggest one small next action that is a process move, not a fact.
4. **Follow:** use what they answered last turn.

Step-up ladder when stuck on the same point:
- Turn 1: anchor + question.
- Turn 2 (still stuck): anchor + a narrower question + one action.
- Turn 3 (still stuck): point at the lesson step that covers it; with a course source, quote it with its label.
- Never, with no source: state the cause or fix, or any fact from memory. The strict rule stays.
- Never, in Socratic: code.

**Decision D1.** Today the no-source rule bans facts, syntax, error explanations and advice from the model's memory. It does allow suggesting a rephrase or rereading this step's lesson text. Proposal: a fact from memory stays banned; a process move that needs no knowledge ("print the value", "run line 2 alone", "reread this step") becomes allowed. This is a loosening and is the owner's to decide.

## 4. Conversation memory
- **M0, none (today).** Part 4 above is impossible. Rejected as the end state.
- **M1, the last few turns** of this learner on this step. **Recommended:** last 4 exchanges, reset when the step changes, in a new fenced block, each earlier turn marked as untrusted data like the learner's code, inside the length caps.
- **M2, a model-written summary.** Not recommended now: model-made state, hard to test, can drift.

What the code holds today (CONFIRMED):
- The interaction log keeps, per answered turn: learner, unit, activity, exercise id, time, the **full question and answer text** (capped at 64 KiB each), mode, assistance level, retrieval status and `prompt_version`.
- It does **not** keep the learner's code, the error output, the step or a session. A failed or abandoned stream is not logged.
- So history can be read from the log, but **not strictly per step** (the video and Explain steps share one activity). A spec needs a step or session key.
- The question, the code and the error output are each capped at 4000 characters when sent to the model.

Points for the spec: where history comes from; privacy (history sends more learner text to a paid provider; state it in the ADR); prompt injection (earlier turns are untrusted, fenced and capped); assistance accounting (history lets us count turns on one point); `prompt_version` covers static text only, history is variable text and is not hashed; traces keep holding no learner text.

## 5. How we would judge it
Four layers. Only the last speaks to learning.
1. **Rules (exists):** the obedience eval. Keep it.
2. **Turn quality**, deterministic where possible (no model judge, ADR-0037 2.9): anchored (the reply contains a word from the learner's code or error), one question, one process action, no leaked cause (existing flag). The owner scores a small sample by hand with a five-line rubric.
3. **Scripted dialogues:** about 10 made-up scenarios of 3 turns with scripted learner replies, including a stuck learner. Checks: turn 2 uses a word from the learner's turn 1 answer; support steps up after two stuck turns; the strict rules hold on every turn. Made-up content only.
4. **Learning (the real test): judged by what the learner can do without AXIS,** with Cold Checks on the same skill, later, as the nearest signal. This is for knowing whether the help works, not for catching anyone. Doing well while AXIS is available is not evidence of learning (see Evidence). Supporting signals only: after a hint, does the learner fix it without more help; hints per item; does the next attempt pass; thumbs. Needs real learners; with a demo target only a very small pilot. Do not claim learning before it is measured.

## 6. Decisions (accepted 2026-11-27, as recommended in brackets)
- **D1:** allow process moves in the no-source rule (yes).
- **D2:** memory M1, last 4 exchanges on the same step (yes).
- **D3:** the five-point turn rubric and scripted dialogues as the quality bar (yes).
- **D4:** the fixed reply for error turns with no source: hold it back, build D1 to D3 first, measure on the local model and OpenAI, keep the fixed reply only as a safety net if the local model still leaks (yes).
- **D5:** the with-source reply eval (tracker item 5c) uses the same rubric.

## 7. Additions (accepted 2026-11-27, with "attempt before more help")
- **A1:** send AXIS the run's error output.
- **A2:** the server builds the history from the log; it is never accepted from the browser.
- **A3:** history is cleared while a Cold Check round is open.
- **A4:** a conversation records the highest level of help it reached.
- **A5:** with a course source, a stuck beginner is taught with an example, not only given a quote.
- **A6:** memory is not attempted before the 5 Dec 2026 freeze.
- **A7:** for governance, change and design topics, the small action is stating a decision, its reason and a risk.

## 8. Evidence
A quick desk review, mostly from abstracts and summaries: [axis-facilitation-evidence-review.md](axis-facilitation-evidence-review.md).

- Help that keeps the learner doing the thinking did better than help that does it for them. A guardrail removed harm in one large study without showing a gain.
- Doing better with the tool can go with doing worse without it, including for adults learning a Python library.
- No randomised trial of a guard-railed tutor for adults learning programming was found.

| Item | Evidence |
| :--- | :--- |
| D1, D4, A1, A4 | supports, indirectly or weakly |
| A5 | supports (secondary source) |
| D2, D3, D5, A7 | leaves open |
| A2, A3, A6 | not evidence questions (security, integrity, time) |
| Weakened by the evidence | none |

The review also suggests asking for an attempt before the ladder steps up.

## 9. Limits
- The turn contracts are inference from human-led training sources.
- One run, error questions with no course source, one cloud model. With-source replies are untested.
- A pattern- and word-based check cannot prove a reply is good.
