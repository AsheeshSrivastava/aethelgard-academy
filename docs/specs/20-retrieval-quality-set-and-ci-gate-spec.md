# Specification 20: Retrieval Quality Set and CI Gate

- **Status:** Draft (awaits owner review of the question list, then owner go)
- **Governed By:** `ADR-0035` sections 2.6 and 4 step 1; extends `SPEC-09`
- **Domain:** Offline regression gate for keyword-only retrieval; local comparison with HR
- **Date:** 2026-11-15

---

## 1. Scope

1. A small fixture corpus and a question set live in `tests/fixtures/retrieval/`:
   - `docs/*.md`: 12 short, made-up documents (written for this repo; no upstream text, so no licence issue), 48 passages in total.
   - `questions.json`: 50 learner-style questions, 41 with an expected source file and 9 with `expected_source: null` (the docs hold no answer).
   - `floor.json`: the recorded floor (section 3), with value, date and `set_version`.
2. The set holds no answer keys. The private-answers rule is unaffected.
3. Question kinds: `plain` (direct wording), `error` (the learner pastes an error line), `paraphrase` (the learner does not use the docs' words). The set is deliberately not saturated: today's keyword search must miss some questions, so a regression can be seen.

## 2. Measures (same as rag-core)

- **first-hit:** the top result's source file equals `expected_source`.
- **top-3:** `expected_source` is among the three returned source files (one passage per source).
- Both are counted over the 41 answerable questions only.
- **Not-found pass rate** (the 9 no-answer questions) is reported by the local measurement only. It is not gated in this step, because the minimum score that lets "not found" fire does not exist yet (ADR-0035 step 4).

## 3. CI gate

1. The test indexes `docs/` with the keyword-only retriever (no embedder, no reranker, no torch, no network) and scores the answerable questions.
2. It fails if first-hit or top-3 is below `floor.json`. The floor is set from the first measured run on this corpus and only raised by a reviewed change, never lowered silently; lowering needs a note in the PR.
3. The test also guards the set itself: 30 to 50 questions in total; every `expected_source` names an existing file; ids are unique; at least 8 questions have no answer.

## 4. Local measurement (not in CI)

A script `scripts/measure_retrieval.py` scores, on the same set, offline and without models: (a) the current LMS keyword search and (b) keyword-only with stop words dropped, plus a sweep of score floors showing first-hit, top-3, answerable questions lost and no-answer questions correctly refused. `scripts/measure_ragcore.py` scores (c) ragcore `variant="L"` and (d) HR on the same set. It builds a throwaway index from `docs/` in a temp folder and must run with the rag-core checkout's interpreter (torch and the pinned, cached models live there); it imports nothing from `lms`. `scripts/measure_real_corpus.py` repeats the comparison, plus the current LMS retriever, on the real corpus (`data/index/sources.jsonl`, 1,371 sources) with rag-core's python-docs, uv and ruff question sets (kept only where an expected file is in the LMS corpus) and two kinds of no-answer questions (foreign: MCP spec and OpenTelemetry; file-missing: the expected file is not in the LMS corpus). Its output, with (a) and (b), decides whether the models are adopted (ADR-0035 2.6 decision (a)).

## 5. Acceptance criteria

1. The gate test passes on a fresh clone with no models.
2. Dropping a document, or breaking the tokenizer so that scores fall below the floor, makes the gate fail (checked once by hand and recorded in the PR).
3. The guard checks in 3.3 pass, and fail on a deliberately broken copy of the set.
4. No `ragcore` import is needed by the CI gate; ragcore is imported only by the local script.

## 6. Recorded results (2026-11-15, local run, RTX 5070 Ti, models from the local cache)

Raw output: `docs/measurements/2026-11-15-fixture-set.txt` and `docs/measurements/2026-11-15-real-corpus.txt`.

**Fixture set (41 answerable, 9 no-answer; 48 passages).** Easy corpus; it guards regressions and does not prove quality.

| Mode | First-hit | Top-3 | No-answer refused at best floor |
|---|---|---|---|
| Current LMS keyword search | 31/41 | 36/41 | no score floor |
| LMS keyword, stop words dropped, floor 6 | 37/41 | 40/41 | 8/9, 3 answerable lost |
| ragcore L, floor about 7 | 38/41 | 40/41 | 8/9, 1 lost |
| ragcore HR | 41/41 | 41/41 | 9/9, 0 lost (margin about 0.15) |

**Real LMS corpus (1,371 sources, 13,256 ragcore passages).** 101 answerable questions (rag-core's python-docs, uv and ruff sets, kept only where an expected file is in the corpus); 192 foreign no-answer questions (MCP spec, OpenTelemetry) and 45 whose answer file is missing from the corpus.

| Mode | First-hit | Top-3 | Time per question |
|---|---|---|---|
| Current LMS keyword search | 20/101 | 34/101 | 160 ms |
| ragcore L | 64/101 | 80/101 | 1 ms |
| ragcore HR | 82/101 | 91/101 | 146 ms |

"Not found": HR scores for in-scope and no-answer questions overlap. At a floor that loses 7% of answerable questions, HR refuses 73% of foreign and 53% of file-missing questions; at 27% lost, 92% and 80%. One score floor does not give a clean "not found" path.

**Limits.** The questions are machine-written and quote-level (rag-core's own sets), not learner-style with pasted errors; several expected pages per question can hide valid alternatives; rag-core's own numbers came from the same sets. Learner-style questions with pasted errors need query transformation (ADR-0035 2.8), and judging generated answers needs an agentic evaluation. Both come after the retrieval port; this record is the baseline they are compared against.
