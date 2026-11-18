# SPEC-25: Measurement on the six Gemini question sets

Status: Approved by the owner 2026-11-18 (90% review bar kept).
Implements: ADR-0035 section 4 (measurement) and plan step 5 in section 5.1. Tunes values set in SPEC-22 (citation run, character caps) and SPEC-23 (minimum matched terms). No new ADR needed. A passage-cap change would add a short ADR note and a SPEC-22 amendment (R9).
Reuses: scripts/measure_retrieval.py, measure_real_corpus.py, measure_ragcore.py, measure_not_found.py. Local only, offline, no key, no paid run.

## 1. Why
Today we have first-hit and top-3 on a mixed set. We cannot say how often a learner gets the right page in the top 1, 3 or 5, how ranking order is judged, why misses happen, or whether 2 or 3 passages per file would help. The six Gemini sets (learner-style wording) can answer this. Nothing has tuned SPEC-22 and SPEC-23 on them yet.

## 2. Inputs
- Six files in data/gemini-runs/result/: pytest, fastapi, pydantic, httpx, python, uv-docs. Each has 40 answerable questions (10 each of plain, error, paraphrase, pasted) and 10 out-of-scope. Total 240 + 60. Fields: q, kind, expect (path pieces), why.
- Mechanically checked (parse, counts, no duplicates, every expected path exists) but not content-reviewed. R8 adds a human review sheet.
- The corpus (data/index/sources.jsonl, 1,371 files, 13,712 passages) stays local and git-ignored. Only the question files go into the repo.

## 3. Requirements
- R1. Question files in the repo: the six YAML files go to eval/gemini-sets/ (owner decision 2026-11-18). Questions and expected path pieces only: no corpus text, no answers. A SET_VERSION file records a hash of the six files. The existing answer-material guard is unchanged; a small test checks the files parse, have 40 + 10 questions each, and contain no field other than q, kind, expect, why.
- R2. One loader in scripts/ (shared by the measurement scripts) reads the sets and the old rag-core sets so old and new results are comparable. A question is right when a returned source id contains one of its expect pieces and starts with the set's source prefix (same rule as measure_real_corpus.py).
- R3. Metrics at K = 1, 3, 5, over answerable questions only. Gains are binary.
  - Hit@K: any matching source in the top K.
  - MRR: 1 / rank of first matching source (0 if none in top 5).
  - nDCG@K: DCG over top K with binary gain, divided by the best possible DCG for that question.
  - Precision@K: matching sources in top K divided by K. Reported only for questions with two or more expect pieces.
  Each reported overall, per kind, and per set.
- R4. Refusal metrics: false-refusal rate (answerable but not_found) and correct-refusal rate (out-of-scope and not_found). Out-of-scope questions are not counted in R3.
- R5. Baselines in one file docs/measurements/2026-11-18-gemini-baseline.txt (plus .json with the same numbers), each row stamped with SET_VERSION, corpus index version, mode and date:
  - lms: today's keyword search (SPEC-23: cleaned query, BM25, one passage per file);
  - rag-core L and rag-core HR, with the rag-core interpreter and cached models, offline (HF_HUB_OFFLINE=1). No network, no paid call.
  The old sets (SPEC-20 fixture and rag-core real-corpus sets) are re-run in the same file for before/after.
- R6. Miss analysis: every answerable question that misses at K=3 gets one failure label, by fixed order of tests. Labels are inferred by rule, not read by a human; the report says so and shows 10 examples per label.
  1. wording: fewer than half of the cleaned query terms occur in the best passage of the expected file.
  2. vague chunk: the expected file's best passage is under 200 characters, or only a heading, or has under 3 distinct content terms.
  3. multi-page: the file returned first is a sibling of the expected file (same directory or same parent heading), or expect lists several pieces and another matches.
  4. other.
- R7. Passages per source test: run lms mode with 1, 2 and 3 passages kept per source file (today the engine keeps 1; retriever.py step 5). Report Hit@K and Hit@K-by-file at K = 1, 3, 5, the number of distinct files in the top 5, and mean characters passed to the model (SPEC-22 total cap still applies). The cap becomes a setting (default 1) so the test needs no code edit between runs.
- R8. Review sheet: docs/measurements/2026-11-18-gemini-review-sheet.md, one page, 24 questions, 4 per set (one each of plain, error, paraphrase, pasted), fixed seed. For each: the question, the expected page, and empty boxes "question is realistic?" and "expected page is right?". The owner fills it in. Below 90% on either box (under 22 of 24 yes) means the set is not used as a gate until fixed.
- R9. Tuning rule: a shipped value changes only if the data shows a gain of at least 2 percentage points on Hit@3 (or the gated number) with no more than 1 point worse correct-refusal and false-refusal, on the Gemini sets and on the SPEC-20 fixture. Values in scope: CITATION_MIN_RUN (3, 4, 5, 6 on supplied-text and answer-text samples), the character caps (1,200 and 3,600), min_matched_terms (2, 3, 4), and the passage cap (R7). If the bar is not met, the value stays and the report says so. A changed value goes through its own SPEC amendment in the same PR.
- R10. CI gate: floor.json for the SPEC-20 fixture must not drop. If a change would lower it, stop and report first. The Gemini sets are not a CI gate in this step.
- R11. Deterministic output: ties sorted by row position (as in measure_ragcore.py), fixed seed for the sample, no timestamps inside the numbers.

## 4. Out of scope
Contextual retrieval (step 6), wiring rag-core into the LMS (step 7), mode stress test (5b), any model-based or paid run. HR uses only models already cached on the machine. If an HR run would need a paid call, stop and print a cost estimate; the owner runs it.

## 5. Tests
R1: tests/test_gemini_sets_files.py (parse, 40 + 10 per file, allowed fields only, SET_VERSION matches). R2, R3: metric functions on a made-up ranking (hand-computed Hit/MRR/nDCG/P@K, ties, empty results, several expect pieces). R4: made-up run with known refusals. R6: one made-up case per label plus other. R7: cap 1 keeps today's output byte for byte; 2 and 3 return at most that many per file. R9, R10: existing fixture gate stays green.

## 6. Decisions
1. Question files live in eval/gemini-sets/. 2. rag-core HR may run on cached models (free, offline). 3. Keep the 90% review bar.

## 7. Reading notes (implementation choices, added while building)
These fill gaps in the text above; none changes a requirement.
- "Same parent heading" (R6.3) is judged at file level only: siblings share a directory. Heading-level checks need a passage-level expected answer, which the sets do not carry.
- "Another matches" (R6.3): the question lists two or more expect pieces and a matching file appears at rank 4 or 5 (found, but below the top 3).
- Content terms (R6.2) are the distinct non-function words of the passage (same function-word list as the query cleanup).
- Refusal (R4) is measured for the lms mode only. rag-core L and HR have no "not found" rule until plan step 7; their rows show top-1 score spread instead.
- SET_VERSION is the sha256 of the six files in name order, with line endings normalised to LF.
- R9 reading: the 2-point Hit@3 gain is judged on the Gemini sets. The SPEC-20 fixture (41 questions, 1 question is about 2.4 points) is held to "top3 not below floor.json, and false-refusal and correct-refusal each within 1 point of the shipped value". For CITATION_MIN_RUN the gated number is recall of lightly edited supplied text, with false citations no more than 1 point worse. For the character caps the gated number is the share of query terms still present in the text the model receives, and a gain there is weighed against prompt size.
- R2 loader: scripts/measure_lib.py loads the Gemini sets; the old rag-core sets are read with the existing `load_yaml` and set lists of measure_real_corpus.py, imported by measure_gemini.py, so there is still one rule for "right" (`measure_lib.is_right`).
- R7 setting: read from `LMS_PASSAGES_PER_SOURCE` (whole number 1 to 5, default 1), like `LMS_MIN_MATCHED_TERMS`. By-file Hit@K uses the first 10 passages.
- The rag-core sync report's timing line is not written into the baseline file (R11).
