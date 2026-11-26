# ADR-0039: AXIS mode contracts, one no-source contract, and a record of every prompt

- **Status:** Accepted by the owner 2026-11-26 (the decisions are listed in section 5). No test or code is written yet.
- **Decider:** Platform Architect & Owner (Asheesh Ranjan Srivastava)
- **Number:** 0038 is reserved for the LangSmith adapter named in ADR-0037, so this is 0039.
- **Builds on:** ADR-0009 (Socratic boundary), ADR-0034 as amended 2026-11-18 and SPEC-24 R4 (no answer from memory), ADR-0022 (interaction log), ADR-0037 (tracing and evals), SPEC-30 (no-source eval).
- **Already decided by the owner (2026-11-26):** one tutor with a contract per mode, not three agents; the starting mode is suggested by the activity and the learner can override; builds stay Socratic; with no source a question may point at a line but never states the cause.

## 1. Context

- The mode text in `axis_rules.py` is one or two sentences per mode. Coach is told to "Explain ... error messages" and the no-source notice, placed after it, takes that back. In the first eval runs Coach and Hybrid still explained from memory (SPEC-30, runs `5d5fbd74-…` and `rules-b-temps-*`).
- Modes are defined by tone, so they cannot be tested. Only the no-source rules have checks; **nothing measures the quality of a reply that uses a course source**.
- The activity (`Explain`, `Predict`, ...) is sent in the user message and never used to choose or shape the mode. The panel defaults to Socratic.
- No place records the prompt, a prompt version or a hash (interaction log, traces, eval results). A reply cannot be tied to the exact prompt that produced it.

## 2. Decision

### 2.1 One tutor, composed prompt
One AXIS companion. The system prompt is composed in this order: base rules, **mode contract**, **source contract** (grounded or no-source). A mode is a contract (tasks, output shape, constraints), not an agent. No router model: the learner picks the mode. A second model call is out of scope; a checking agent would be an LLM judge (ADR-0037 2.9).

### 2.2 Mode contracts (apply when a course source was found)
| | Socratic ("you work it out") | Hybrid ("plan before code") | Coach ("explain, then you do it") |
|---|---|---|---|
| Tasks | Draw out what the learner already thinks; one question at a time; follow up; close with a short check of what they concluded | Restate the goal; split it; have the learner state inputs, outputs and success criteria; compare their plan with that | Explain from the passages; give one example from the source; set a small task |
| Output shape | One sentence restating, then one question (never more than two) | Goal in one line; two or three sub-steps phrased as gaps the learner fills; one next action | Short explanation with `[n]`; one example from the source; one task; about 150 words |
| Constraints | No code, not even inside a sentence. No facts the passages do not give | No implementation code. Does not write the plan or the contract for the learner | Never the exercise's solution. Only the passages, each claim cited |
| After repeated stalls | Offer Hybrid or Coach (needs turn history: later step) | Offer Coach (later) | |

### 2.3 The no-source contract (all modes, a second axis)
State sentence (SPEC-24), restate the question in the learner's words, ask what they already know or tried, point to the lesson text or a rephrase. No facts, no syntax, no error explanation, no advice from memory, no guessing what an unfamiliar name is or does, no code. A question may point at a line of the learner's own code; it never states the cause. This keeps the 2026-11-18 rule.

### 2.4 The Coach contradiction
The "Explain ... error messages" sentence belongs **only to the grounded Coach contract**. With no source the mode contract is replaced by the no-source contract, so no instruction to explain is ever present to be overridden. This changes SPEC-24 R4's sentence that tone differences stay in the stance text; the spec amendment states it.

### 2.5 Starting mode suggested by activity
The panel preselects a mode from the step's activity; the learner can change it; builds stay Socratic (forced today).

| Activity | Suggested | Status |
|---|---|---|
| Explain (also the video step) | Coach | owner accepted |
| Specify, Decompose | Hybrid | owner accepted |
| Predict, Trace, Debug & Validate | Socratic | owner accepted |
| Modify (also the playground), Evaluate, Direct | Hybrid | owner accepted 2026-11-26 |
| Build | Socratic (forced) | existing |

### 2.6 Every prompt is recorded
1. **Catalogue:** `docs/prompts/prompt-catalogue.md` holds the full text of every prompt the app sends to a model. A script generates it from the code and a test fails when the two differ. The 2026-11-26 file is a hand-run draft, not yet drift-checked.
2. **Version:** each call gets a `prompt_version`: a short SHA-256 of the **static** text (the system prompt with passages and any learner text replaced by placeholders), so it changes only when the wording changes.
3. **Where it is written:** a new allow-listed trace attribute on the model-call span (amends ADR-0037 and SPEC-28), a field on the interaction-log events that follow a model call (ADR-0022), and `results.json` of every eval run (SPEC-30). Never learner text, never the assembled prompt.

### 2.7 New measurement: with-source reply quality (outline)
- **Questions:** the 240 answerable questions of `eval/gemini-sets/`, each in the three modes, with real retrieval. A reply whose retrieval found nothing is counted apart, not scored.
- **Automatic checks:** every `[n]` points at a passage that was given; at least one label when the reply states a fact; length caps; Socratic at most two questions and no code; Hybrid shape (goal line, gaps, next action, no code block); Coach ends with a task.
- **Not automatable:** whether a passage supports the claim. Use a hand-review sample plus a structural proxy (shared word runs with the cited passage, as SPEC-22 already does). **No LLM judge** (ADR-0037 2.9) unless the owner decides otherwise.
- **Harness:** reuse SPEC-30 (profiles, `--estimate`/`--paid-ok`, replay, report, review sample). Local model first; a paid run needs an estimate and the owner runs it.
- The first run reports only; no pass mark.

## 3. Basis in the DFELE material
**DOC** = stated in the owner's files; **inference** = our application to an AI tutor (none of the files discusses one). The files are on the owner's machine, not in the repo.

| Rule | Basis |
|---|---|
| Control matches prior knowledge and confidence, so the mode is a choice with a suggested start | DOC: COURSE CONTENT p102-103 (directive, guided discovery, exploratory); Adult Learning Principles p1-3. Inference: mapping to modes |
| Guided questioning assumes some prior knowledge; with little, give content in short parts | DOC: Handout P16 p1, P18 p1. Inference: Socratic is a risky default for a new topic |
| Learner attempts first, then a debrief | DOC: P20 p1; Make It Stick review p1-3 |
| Socratic: elicit the learner's model, one question, follow up | DOC: P16 p1; How People Learn p16-17. Inference: the two-question limit |
| Hybrid: split the task, outcome with performance, condition and criterion, critique against the goal | DOC: Learning Theories p14-15; Designing Learning p65; Designing the Conversation p7-8. Inference: the output shape |
| Coach: explain, example, practice, feedback | DOC: P15 p1, P11 p1. Inference: about 150 words |
| Start from the learner's problem and experience | DOC: Knowles p58-61 (four assumptions); Adult Learning Theories p1-2 (six) |

## 4. Consequences
- Easier: each mode can be tested; a reply is traceable to a prompt version; Coach no longer contradicts itself.
- Harder: three more checks to maintain; a catalogue that must be regenerated when wording changes; the grounded eval needs a running index and a model.
- Unchanged: retrieval, guardrails, the live temperature, grading.
- Follow-ups already known: the offer to switch modes after stalls needs turn history; the `core` to `adapters` import (SPEC-30 follow-up).

## 5. Decisions (owner, 2026-11-26)
1. **One tutor with a contract per mode**, not three agents.
2. **Starting mode suggested by activity**, the learner can override, builds stay Socratic. Modify (and the playground), Evaluate and Direct start in Hybrid.
3. **Strict no-source rule kept:** a question may point at a line, it never states the cause (the 2026-11-18 rule).
4. **Grading is not changed by this ADR.** A Coach explanation in words, with no code, is still not tagged `supplied_reasoning` (the classifier marks only code, `socratic_guardrail.py:127-158`), which is narrower than AGENTS.md. A **separate ADR with its own tests** decides whether worded explanations count.
5. **`prompt_version` is one per assembled static prompt** (not one per prompt file).
6. **No rename** of Hybrid for learners.

## 6. Found while checking (not decided here)
- `/api/v1/axis/consult` logs the requested mode, not the forced one on builds (`api/app.py:1276-1280`).
- `/api/v1/explain-error` (legacy page) has no cold-check block and writes no interaction or assistance log (`api/app.py:1411-1425`). This bears on evidence honesty (REVIEW.md item 2).
- The build-feedback summary prompt can carry a message from the private build checks (`core/builds.py:238-247`); the learner already sees it, but a paid provider would receive it.
- The chat user message does not strip closing tags typed into the question or code (`axis_rules.py:231-244`).

## 7. What happens after the go
Spec amendments (SPEC-24, SPEC-28, SPEC-30 or a new spec for the contracts and the grounded eval), tests first, then code, each as its own small PR.

## 8. Amendment A (**Accepted** by the owner 2026-11-27)
The first run of the new contracts (SPEC-31 section 7; local model, 756 replies at 0.0 and 0.2, no course source) cut memory explanations sharply, and showed two faults.

1. **A pasted error still draws out the cause.** The explains flag (g) was on in 27 of 54 error-message replies at 0.0 and 17 of 54 at 0.2, against 2 and 4 of 702 for other questions. There are only six error-message questions.
2. **The Socratic code guard replaces harmless replies** with "direct code solutions are withheld": 15 of 252 at 0.0 and 8 of 252 at 0.2. Of those 23: 6 because the word "return" and a bracket both appear; 5 because "class" is followed by a word in plain English ("a named class in Python"); 5 because the learner's own code is quoted in backticks; 7 because it is copied in a code block (one of them changed). The same detector feeds `AssistanceClassifier`, so a false hit in Coach or Hybrid can mark help as `supplied_reasoning` and count against the learner's evidence.

Decision: keep the strict rules of section 2; say them more exactly in the no-source contract; make the code detector match code and not English; and let a Socratic reply quote the learner's own code inline (refines how ADR-0009's boundary is checked: nothing new is given to the learner). Details, tests and open choices: SPEC-31 section 9.
