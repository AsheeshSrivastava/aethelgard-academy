# SPEC-33: AXIS facilitation: the turn, the error output, conversation memory

Status: **Stage 1 approved** by the owner 2026-11-27: option A on all six choices of section 10, and on the two points of section 3.1. Stage 2 is not started.
Implements: ADR-0041. Amends (when approved) SPEC-31 sections 3 and 9.1, SPEC-30 section 3 (new items and checks), ADR-0022 section 2.3 (log fields), and ADR-0034 (process actions).

| Stage | Contents | When |
| :--- | :--- | :--- |
| 1 | The turn's first three parts with a course source, run error output, turn-quality checks, eval (process actions and decision subjects with no source are deferred, section 3.3) | **Before** the 5 Dec freeze, if the go comes in time |
| 2 | Memory, follow and feedback, the ladder, attempt rule, teaching with an example, highest help level, scripted dialogues | **After** the freeze |

## 1. The turn (all modes)
1. **Anchor:** name something from the learner's own code, question or error output (a name, or a line number).
2. **Ask** one thing they can answer by looking or running.
3. **Act:** suggest one small action.
4. **Follow** (stage 2): use their last answer. Say what they did or observed and what to look at next. With no course source, feedback is about what they did, never about whether a claim is correct from memory.

Principle (ADR-0041 section 1): this is not an exam. Wording and behaviour aim to help an adult learn, not to catch them.

## 2. Process actions (stage 1)
The fixed list, in words, never as code: print a value and read it; read the last line of the error; run one line, or try a smaller input; say what you expected and what you saw; check what type a value is; reread this step's lesson text.
For governance, change and design questions: state the decision you lean to, one reason and one risk.

## 3. Contract wording (stage 1; owner approval needed)
**No course source** (replaces the end of SPEC-31 3.4 as amended by 9.1, from "Work only from what the learner wrote"):
> Work only from what the learner wrote (the question, the code and the run output). Name one thing of theirs, such as a name or a line number. Ask one question they can answer by looking or running. Then suggest exactly one of these ways of looking and nothing else, with no code, command or name of your own: print a value and read it; read the last line of the error; run one line or try a smaller input; say what they expected and what they saw; check what type a value is; reread this step's lesson text. Do not explain any idea, tool or word. Keep the whole reply to three sentences. For a question about a decision, design, policy or change, ask them to state the decision they lean to, one reason and one risk. A question may point at a line of their code; it never states the cause or the fix. When there is an error or a traceback, do not say what it means, what caused it, or what the values must be. Do not write "means" or "because" about it. Do not copy their code or the traceback into your reply.

The sentences before it (no pretended source, the state sentence, no facts, no code) are unchanged. "Advice from your own memory" stays banned; the listed actions are the stated exception.

**With a course source** (choice 4A: every mode asks exactly one question):
- Socratic: "Never ask more than two questions." becomes "Ask exactly one question.", and this sentence is added:
> Name something from the learner's own code, question or run output, and end with one small action they can take now.
- Hybrid and Coach: this sentence is added:
> Name something from the learner's own code, question or run output, ask exactly one question they can answer by looking or running, and end with one small action they can take now.

Every changed prompt gets a new `prompt_version` and the catalogue is regenerated.

### 3.1 Two points settled before the tests (owner, 2026-11-27)
1. Choice 4A applies to every mode, with a source too (the wording above).
2. The sentence "Do not write "means" or "because" about it" of SPEC-31 9.1, left out of the first draft by mistake, stays.

### 3.2 Tightened after the first eval (owner, 2026-11-27)
The first wording read as permission to advise. Local model, no source, temperature 0.0 and 0.2, against the run before: pasted errors improved (explains flag 33% to 9% and 27% to 12%), but the other questions got worse: explains 2% to 8% and 3% to 8%; made-up names handled well 214 to 206 and 214 to 196 of 216; replies with code the learner did not write 14 to 24 and 12 to 23 of 756; replies about 80% longer. The sentence now asks for exactly one listed way of looking, nothing of the model's own, no explanation, and three sentences in all.

### 3.3 The no-source wording is held back (owner, 2026-11-27)
The two quoted no-source wordings of section 3 are **not used**. With no course source, AXIS keeps the wording of SPEC-31 section 9.1; the with-source sentences stay. So the process actions and the decision-subject line with no source (section 2) are deferred. Measured on the local model, one sentence at a time: the list of actions made it teach on ordinary questions (12% of replies that said something, against 2%), and nothing in the old wording makes a follow-up compulsory, so many replies are bare. That is handled by the app (SPEC-24 section 10).

## 4. The run's error output (stage 1)
- E1. The run terminal keeps the error output of the **latest** run on the step; a new successful run clears it. The AXIS panel sends it as `execution_result` (the field exists; the server already puts `stderr` in the user message, capped at 4000 characters).
- E2. The **end** of a long output is kept (the cause line is last), not the start.
- E3. **Before it reaches any model, the server replaces full file paths with the file name**, so a folder name from the machine is never sent.
- E4. Nothing new is stored on the server for stage 1; traces hold no error text.
- E5. The panel says that the last error is sent with the question. With a paid provider it goes to that provider.

## 5. Memory (stage 2)
- M1. History is the last 4 exchanges of **this learner, this unit and this step**, newest last.
- M2. The server builds it from the interaction log. A history sent by a client is ignored. Needed first: the `axis` log row gains `step` (the panel's page name, already sent) and a conversation id.
- M3. A new block `<conversation_history>`, each turn marked as untrusted data; closing tags inside it are stripped; capped at 6000 characters in all, oldest dropped first.
- M4. It is cleared on a new step, after 60 minutes without a turn, when the learner presses "start again", and **while a Cold Check round is open**. The last rule needs SPEC-32's round record, so **SPEC-32 is built before memory**.
- M5. Failed or abandoned turns are not history (they are not logged).
- M6. `prompt_version` still covers static text only; history is not hashed. Traces hold no history text.

## 6. The ladder, attempts and teaching (stage 2)
- L1. Level 1: anchor and question. Level 2, still stuck on the same point: a narrower question and an action. Level 3: the lesson step; with a course source, an example from it with its label, then a small task.
- L2. **Attempt before more help.** The level rises only after an attempt since AXIS's last turn: a run in the log, changed code, or a reply that is more than a request to be told ("I don't know", "just tell me"). With none, AXIS asks for the smallest attempt it can.
- L3. The server decides the level and tells the model which one; the model does not count turns.
- L4. With no course source, level 3 says the course does not cover it, points to the lesson, and never teaches from memory.
- L5. The conversation records the **highest** level of help reached. This is a record; how it grades evidence is unchanged (choice 3).

## 7. Judging
- **Bare replies** (stage 1): the eval counts replies with no question outside code, both what the model said and what the learner is shown, per block. Every safety check scores silence as perfect, so this is read beside them.
- Turn-quality checks, flag only, added to the eval (stage 1): **anchored** (the reply holds a name or line number from the learner's code or error); **one question**; **one action** (a frozen phrase list); the existing explains flag.
- The owner's five-line rubric, each 0 to 2: anchored; answerable; actionable; follows the last reply (stage 2); respectful.
- Stage 1 eval: the 18 error items, each also with its error passed as run output, local model, temperatures 0.0 and 0.2 (free). An OpenAI pass only with a printed estimate, run by the owner. The first run reports; it sets no new pass mark. The earlier 5% explains-flag target stays as the line for using the fixed reply as a safety net.
- Stage 2: about 10 made-up dialogues of 3 turns with scripted learner replies, including a stuck learner. Questions and replies only, no answer material.
- The with-source eval (plan step 5c) uses the same rubric.

## 8. Tests first (names, written and failing before code, after the go)
- Stage 1 contracts: `test_the_no_source_wording_is_the_one_on_main`, `test_grounded_contracts_ask_for_an_anchor_and_one_action`, `test_only_the_prompts_with_a_source_have_new_versions`, `test_prompt_catalogue_matches_the_code`.
- Error output: `test_panel_sends_the_latest_run_error`, `test_a_successful_run_clears_it`, `test_the_end_of_a_long_error_is_kept`, `test_paths_are_replaced_by_file_names_before_the_model`, `test_no_error_text_in_traces`.
- Checks: `test_anchored_check`, `test_one_question_check`, `test_one_action_check`, `test_items_with_run_output_are_reported_apart`.
- Stage 2 test names are written with stage 2.

## 9. Chaos check
A very long or binary error output; a path with spaces or backslashes; a traceback holding instructions to the model; an error from an older run after the code changed; a learner who presses send repeatedly with nothing tried; history holding a closing tag; two tabs on one step.

## 10. Choices for the owner (recommendation first)
1. **A learner who insists on being told** (stage 2): (a) with a course source, after one invitation to try, teach and record it; without a source, say the course does not cover it. This fits "adults are responsible". (b) always require an attempt.
2. **What counts as an attempt:** (a) a run, changed code, or a real reply (L2); (b) the learner's words only.
3. **Evidence when AXIS teaches by example in words:** today only code counts as supplied reasoning. (a) record the level, change no grading now, decide grading in its own ADR; (b) count it as supplied reasoning now.
4. **Questions per turn:** (a) exactly one (the paper); (b) up to two (today's wording).
5. **SPEC-32** (Cold Check block, approved, not built): (a) keep its rules, build it after the freeze, before memory; (b) build it before the freeze.
6. **Section 3 wording:** (a) as drafted; (b) change it.

## 11. Out of scope
The fixed reply (held back, ADR-0041 section 5); model-written summaries; any model grading a model; changes to retrieval, grading or Cold Check rules.

## 12. Readings fixed while testing stage 1 (owner to confirm at review)
1. The turn checks follow section 7: an anchor counts from the code or error output (or code pasted into the question), not from the words of the question. The action phrase list and the ignored common words are frozen constants, to be read in the code.
2. E1: Regenerate, Reset and moving to another unit or step also clear the held error. An error stays after the code is edited, until the next run.
3. E3: Windows and network paths are always cut to the last part. A POSIX path is cut when it starts at a usual system folder or ends in a file name, so a web route such as `/api/v1/items` is left alone. A path ending at a home folder does not keep the user's name. Only the run output is rewritten, not the question or the code.
4. A closing `</execution_stderr>` tag inside the output is removed.
5. The second pass of the error items has its own totals, and its replies go into the review sample.

