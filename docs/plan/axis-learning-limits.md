# AXIS: what it does not do yet, and what could be done

Recorded 2026-11-27 at the owner's request. **AXIS does not yet improve learning in any way we can show.** Labels: **CONFIRMED** (measured or read in the code), **INFERRED** (reasoning), **UNKNOWN**.

## 1. Questions the course does not answer (what the AXIS evals measure)
These evals force "no course source". Local model Qwythos-9B, temperature 0.0 and 0.2; OpenAI `gpt-6-luna`, one run.

| | Local | OpenAI | Label |
| :--- | :--- | :--- | :--- |
| States the cause of a pasted error (stricter word count) | about 48% to 64% | none found in 324 | CONFIRMED (flags and a word search; OpenAI hits read, not every reply) |
| Explains from memory, other questions | 3% to 4% | none found | CONFIRMED, same method |
| Replies with no question | about 20% | none | CONFIRMED. The app adds a question (SPEC-24 section 10, PR #84) |
| Made-up names handled well, of 216 | 213 to 216 | 216 | CONFIRMED |
| Suggests something to try | rarely | 0% to 5% | CONFIRMED |

Run-to-run differences of up to about 9 points are normal for the local model, so small changes mean nothing.

Wording changes tried on the local model (Amendment A, stage 1, a tighter stage 1) each improved one number and worsened another. CONFIRMED.

**Why these replies teach little.**
- The rule is strict: no facts, causes or fixes from memory. CONFIRMED (SPEC-24).
- The replies are one move repeated: "what did you expect, what have you tried?" (96% to 100% of OpenAI's). CONFIRMED.
- No conversation memory: AXIS cannot follow the learner's answer. CONFIRMED.
- A question cannot draw out knowledge the learner does not have yet. INFERRED.

## 2. Questions the course does answer
**The reply itself has never been measured.** The prompt wording for each mode is tested as text only. UNKNOWN: whether replies are correct, whether the cited passage supports them, whether they help.

What is measured is the search, on 240 questions written to be answerable from the upstream docs (SPEC-25, SPEC-27, 2026-11-18 and 19). CONFIRMED:

| | Keyword search (default) | Hybrid with reranker |
| :--- | :--- | :--- |
| The expected file is among the 3 passages | 57% | 75% |
| Same, for paraphrased questions | 30% | 67% |
| Wrongly told "not in the course" | 6% | 6% |
| Out-of-course questions correctly refused (60 questions) | 43% | 42% |

What follows (INFERRED from these figures):
- A noticeable share of answerable questions get passages that are not the expected ones (very roughly 37% keyword, 19% hybrid). The expected-file measure can understate success, since another file may also answer.
- **More than half of the out-of-course questions still get passages**, so they take the "with source" path, not the careful one. Everything in section 1 applies only when the search finds nothing.
- What a wrong or irrelevant passage does to a reply is UNKNOWN.

Other facts. CONFIRMED:
- The search uses **only the words of the question**, not the learner's code or run error.
- "The course" is **upstream documentation** (ADR-0034), not lesson notes: 1371 files, of which only 28 are Python documentation.
- There is no usage data: the interaction log on the owner's machine holds 6 test AXIS turns, none with a search result.

## 3. Not measured at all
Whether anyone learns; reply quality with a source; real learner errors (only 18 invented ones); a second local model; a second OpenAI run; the with-source sentences added in SPEC-33 stage 1.

## 4. What could be done later, in this order
1. **With-source reply quality eval** (tracker 5c): the most common case is unmeasured.
2. **See what real use looks like:** how often a question finds a source (the log records it once real use exists).
3. **Search quality:** hybrid search for daily use; revisit the "not found" threshold; include the error text in the search.
4. **More course notes,** especially Python, so fewer questions have no source and Coach has something to teach from.
5. **Teaching with a source:** an example, then a small task, when the learner is stuck (ADR-0041 A5).
6. **Conversation memory and the support ladder** (SPEC-33 stage 2).
7. **Process actions added by the app,** not asked of the model (the list in the prompt made the local model teach).
8. **Try another local model.**
9. **A small pilot with an outcome measure:** what the learner can do afterwards without AXIS (Cold Checks).

None of this is approved by this page.
