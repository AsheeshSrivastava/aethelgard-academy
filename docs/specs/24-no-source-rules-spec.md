# SPEC-24: What AXIS says with no course source, and a visible "no index" status

Status: approved by the owner 2026-11-18 ("go", after the revision below). Owner on 2026-11-18: wording (section 3) OK, placement (section 4) OK, "RAG only in every mode" (R4 below) decided, Hybrid and mode stress testing moved to a separate task (section 8).
Implements: ADR-0034 section 2.3 (the answer rule: "not in the course yet", "no index" said in plain words), as amended by this step: **no mode may answer from the model's own memory** (the Coach "Not from the course" exception is removed; ADR-0034 gets an amendment in the same PR). Also ADR-0035 section 2.3 ("no index" gives a clear message, never `None`). Plan step 4 (ADR-0035 section 5.1). The same PR corrects ADR-0035 section 5.1 (plan order, docs only) and updates its Done list.
Governed by: ADR-0009 (Socratic boundary, unchanged), SPEC-17 section 3.1 (shared rules live once, provider-neutral, in `axis_rules`), SPEC-21 (statuses), SPEC-22 (fenced passages, labels), SPEC-23 (`not_found` rule).

## 1. What is wrong today (read from main at 90c7f66)
1. **One notice for four different situations.** `axis_rules._not_found_notice` says "NO CURRICULUM PASSAGE WAS FOUND" whether the status is `not_found` (a weak match), `no_index` (nothing loaded) or `unavailable` (the search broke). The learner cannot tell "this is not taught here" from "the course reference is switched off".
2. **The notice lives only in the system prompt.** If the model ignores it, the learner gets a fluent answer with nothing to show it was not grounded. Nothing outside the model's words tells the learner.
3. **The browser never learns the status.** The stream `done` event carries only `assistance_level` and `cited_concepts`. The consult reply has no status field. The status is only in the server log.
4. **No status on the AXIS panel.** On a fresh clone with no `data/index`, the panel says "AXIS can see this step and your code" and nothing else. That is the silent failure ADR-0034 and ADR-0035 2.3 forbid.
5. **Modes differ on memory use.** ADR-0034 let Coach explain from general knowledge, labelled, and was silent on Hybrid. The owner has decided that no mode answers from the model's memory (R4).

## 2. Requirements: prompt rules (backend, no UI)
- R1. `axis_rules._not_found_notice(mode)` becomes `no_source_notice(mode, status)`. It stays in `axis_rules` only (SPEC-17 3.1), takes the mode and the retrieval status (`not_found`, `no_index`, `unavailable`), and is used only when no passage reaches the prompt.
- R2. Every no-source notice, in every mode and state, tells the model: no course source was used; do not write source labels such as [1]; do not name a document, page or book as the source; say the state sentence from R3 once, at the start of the reply, in the model's own plain words.
- R3. The state sentence the reply must carry (wording in section 3):
  - `not_found`: "This is not in the course yet."
  - `no_index`: says the course reference is not loaded, so the answer was not checked against the course.
  - `unavailable`: says the course search is not working right now, so the answer was not checked against the course.
- R4. **One rule for all three modes (owner decision 2026-11-18): with no course source, AXIS gives no facts, syntax, error explanations or advice from the model's own memory.** After the state sentence it may only work from what the learner wrote (their question, code and run output):
  - restate what the learner seems to be asking, in the learner's own terms;
  - ask one or two guiding questions about the learner's own code or data (this is the whole of Socratic's reply, and Coach and Hybrid may do the same);
  - suggest they rephrase, or look at the step's lesson text.
  No mode may write a "Not from the course:" part. The Socratic no-code invariant (ADR-0009) is unchanged and still applies on top. With no source the mode stance is replaced by the neutral header; the tone differences apply with a source (SPEC-31 R3). *(Amended 2026-11-26, SPEC-31 section 4.)*
- R4a. The same rule, with a source: the stance text for each mode says answers come from the numbered course passages only; anything the passages do not say is "not in the course yet". (The grounded notice is a one-line addition to the existing reference-passages instruction.)
- R4b. **Not in scope of R4: Concept Check judging and README feedback.** Those two jobs compare the learner's text with data we supply (the authored idea list, SPEC-18; the measured checklist points, SPEC-15 section 10.2) and must not add facts. They keep their current prompts. A test pins that they are untouched.
- R5. When a passage reaches the prompt, none of this text is added. The grounded path is unchanged (SPEC-22 R1 to R7).
- R6. A concept-store rescue still counts as grounded: if the retriever has no passage but the concept store supplies one, R1 does not apply.
- R7. Unknown or invented labels in a no-source reply are removed, as SPEC-22 R5 already does (no labels are valid when no passage was given).

## 3. Proposed wording (for the owner's approval; learner-facing)
These are the exact strings the prompt asks for and the panel shows. They live in one place per layer: `axis_rules.py` (what the model is told) and `frontend/src/lesson/axisNotices.ts` (what the panel shows).

| State | What AXIS is told to say first | Note under the answer in the panel |
| :--- | :--- | :--- |
| `not_found` | "This is not in the course yet." | "No course source matched this question." |
| `no_index` | "The course reference is not loaded, so I could not check this against the course." | "Course reference not loaded. This answer was not checked against the course." |
| `unavailable` | "The course search is not working right now, so I could not check this against the course." | "Course search unavailable. This answer was not checked against the course." |

Standing status line (section 4):
- Index not loaded: "Course reference not loaded. AXIS can still talk with you, but its answers are not checked against the course."
- Course search unavailable: "Course search is not working right now. AXIS answers are not checked against the course."
- Mock mode (development only): "Practice mode: AXIS replies are fixed examples, not checked against the course."
- Ready: no line.

## 4. Requirements: status to the browser and the panel
- R8. **Port.** `IRetriever` gets one method, `index_status() -> RetrievalStatus`, that never searches and never raises. It returns `OK` (index loaded), `NO_INDEX` or `UNAVAILABLE`. The keyword adapter and the test fake implement it. This amends SPEC-21 by one line.
- R9. **Per-answer source state.** A reply carries `source_state`: `course` (at least one passage was given to the model), `not_found`, `no_index` or `unavailable`. It is derived from the grounding built for that turn, so a concept-store rescue gives `course`. It is added as an optional field `source_state` on `AxisResponse` (consult) and on the stream `done` event. A missing field means "not applicable" (mock mode). With no retriever at all (nothing was searched), the state is `no_index`. The router is given the retriever so it can report its status (R10).
- R10. **Status endpoint.** `GET /api/v1/axis/status` returns `{"course_reference": "ready" | "not_loaded" | "unavailable" | "mock"}`. It holds no index path, version, reason text or error text. Mock mode wins when `MOCK_AI` is on. The router supplies it from the active companion's retriever.
- R11. **Panel, standing line.** The AXIS panel asks the status endpoint once when it opens. When the value is not `ready`, it shows the line from section 3 directly under the "AXIS" header row, in a `role="status"` element, in plain text (not colour alone). When `ready`, nothing shows. If the request fails, nothing shows (a down server already gives "AXIS is unavailable right now" on the first question).
- R12. **Panel, per-answer note.** When a reply's `source_state` is `not_found`, `no_index` or `unavailable`, the panel shows the matching note from section 3 as a small muted line under that reply, where source chips would be. `course` or a missing value shows no note. An unknown value shows the generic text "This answer was not checked against the course." and does not crash.
- R13. **Not model-dependent.** R11 and R12 are driven by server data, never by what the model wrote. The model can ignore R2 to R4; the learner still sees the note.
- R14. **Logging.** The interaction log keeps its SPEC-21 fields; `retrieval_status` already carries the state. No new log field.
- R15. **Unchanged.** Mock companion replies, source chips, Socratic-only behaviour on builds, the cold-check block, and the SPEC-22 grounded path.

## 5. Tests first (names, written before code)
Backend:
1. `no_source_notice` for each of the 3 states x 3 modes (9) contains the R3 state sentence and the R2 rules.
2. All three modes' no-source notices forbid facts, syntax and error explanations from the model's own memory, allow only questions and restating the learner's own text, and none of them contains or permits "Not from the course" (R4).
   *(Amended 2026-11-26, SPEC-31 section 4: item 2's test no longer asserts "overrides any mode instruction"; it asserts that no mode instruction is present with no source.)*
2a. The grounded prompt tells every mode to answer only from the numbered passages (R4a). The Concept Check judge prompt and the README feedback prompt are byte-for-byte unchanged (R4b).
3. The Socratic system prompt with a no-source notice still contains the ADR-0009 no-code invariant, unchanged (R4, ADR-0009).
4. With a passage in the prompt, no notice is present (R5). With a concept-store rescue, no notice is present (R6).
5. Fake retrievers returning `not_found`, `no_index`, `unavailable` give the right prompt notice and the right `source_state` (R1, R9).
6. A model reply with an invented [1] under no-source has the label removed (R7).
7. `source_state` appears on the consult response and the stream `done` event, and is the same for both (R9).
8. `index_status()` on the keyword adapter: loaded gives `OK`; a missing folder gives `NO_INDEX`; the fake can be set to `UNAVAILABLE` (R8). The SPEC-21 port contract tests still pass with the new method.
9. `GET /api/v1/axis/status`: `ready`, `not_loaded`, `unavailable`, `mock`; the body holds no path, version or reason text; `MOCK_AI` wins (R10).

Frontend:
10. The standing line shows for `not_loaded`, `unavailable` and `mock` with the section 3 text, in a `role="status"` element, and is absent for `ready` and when the request fails (R11).
11. The per-answer note shows for each of the 3 states with the section 3 text, not for `course` or a missing value, and an unknown value shows the generic text (R12).
12. Source chips and the existing panel tests are unchanged (R15).

Regression: SPEC-22 injection test (test 11 there) and the SPEC-20 gate numbers are unchanged. Run the end-to-end suite (`LMS_ANSWERS_DIR` set) before the merge, because the AXIS panel changes.

## 6. Edge cases for the later chaos check
`source_state` with an unexpected string; status request that times out or returns non-JSON; a learner who types "This is not in the course yet." in their question; mode switched mid-stream; index folder deleted after startup; retriever whose `index_status()` raises (must give `unavailable`, never a 500); a very long question in `no_index`; Socratic mode asked directly for code with no source; Coach asked "what does this error mean" with no source (must not explain it from memory); Hybrid asked for a design with no source.

## 7. Traceability
ADR-0034 2.3 "not in the course yet", no chip -> R2, R3, R12. "Coach only, labelled Not from the course" -> removed by the owner on 2026-11-18, replaced by R4 (ADR-0034 amendment). "Socratic stays Socratic" -> R4, test 3. "No index loaded: say so in plain words" -> R3, R10, R11. ADR-0035 2.3 "clear message, not None" -> R8, R10, R11. SPEC-17 3.1 (rules once, provider-neutral) -> R1. SPEC-22 R5 labels -> R7. SPEC-21 -> R8.

## 8. Open points for the owner
1. **Wording** in section 3, exact strings. I kept them short and in the first person for the model, third person for the panel.
2. **Placement:** a standing line under the AXIS header, and a small muted note under the reply where chips would be. The alternative is one banner above the messages for both. I chose two places because the standing line explains the cause before a question is asked, and the note tells the learner which answers to trust.
3. **Decided 2026-11-18:** the same memory rule for all modes (R4); Hybrid's own behaviour and a proper stress test of all three modes become a separate task (section 9).
4. **Port change (R8):** one new method on `IRetriever`. The alternative, reading the loaded state from the adapter's internals, would leak adapter details past the port.
5. **Model compliance is not guaranteed.** The prompt rules are tested as text only; offline we cannot prove a model obeys them. R13 is the guarantee: the panel note does not depend on the model. Measuring compliance on a real model belongs to the tracing and evals step (plan step 8).
6. **Mock mode line** names "Practice mode". Learners never see mock mode in a real deployment; the wording is for development.

## 9. Separate task, not in this step (owner 2026-11-18)
- **Stress test Socratic, Hybrid and Coach** against real questions: does each keep its stance, does Socratic ever give code, does any mode answer from memory when no source exists, does Hybrid add anything the other two lack. This step only fixes the shared memory rule; it does not judge the modes.
- **Mode usage count.** The interaction log already records `mode` on every AXIS answer, so "how often is each mode used" is a count over existing data. The task adds a small report (per mode, per unit, per week), not a new log field. It belongs with the tracing and evals step (plan step 8) or earlier if the owner wants.
- **Note for the tracing and evals step (plan step 8), owner 2026-11-18:** measure how often a real model obeys the SPEC-24 prompt rules. SPEC-24 tests the prompt text only. The eval should ask real questions with no source (and with a source), per mode, and count answers that give facts, syntax or error explanations from the model's memory, name a source that was not given, or skip the state sentence. The server-side note on the panel (R13) shows either way.

## 10. Never a bare reply (amendment 2026-11-27; ADR-0041 section 1)
Evidence: on the local model, 19% of no-source questions without an error got only the state sentence ("This is not in the course yet."), after SPEC-31 Amendment A. A prompt cannot guarantee a follow-up; the app can.

- R16. **Where.** Chat replies (consult and stream) whose `source_state` is `not_found`, `no_index` or `unavailable`, in every mode. Not with a course source, not for the mock companion, not for the concept check, drafts or build feedback.
- R17. **When.** Only when the reply the learner would see, after the guard and the label clean-up, holds no question. A question is a "?" outside fenced and inline code; a block opens only at the start of a line. A reply cut off inside a block has it closed before the line. A reply from the mock, including the fallback when the local server fails, gets no line.
- R18. **Exact wording**, added after a blank line (or alone if the reply is empty):
> Start from your own code, error or question: what have you tried so far, and what did you see?

  It states no cause or fact, holds no code, names nothing, and reads sensibly with no code or error.
- R19. In Socratic mode it takes the place of the general reflection question for no-source replies. With a course source, Socratic keeps that question.
- R20. **Stream.** It is sent as one last piece of text, after the model's reply.
- R21. **Help level** is judged on the reply before the line is added, so a fixed question never raises it.
- R22. **Record.** The interaction log's answer holds what the learner saw, the line included. No new log field; nothing new in traces.
- R23. The line is text the app adds, not a prompt: it changes no `prompt_version` and is not in the prompt catalogue.

