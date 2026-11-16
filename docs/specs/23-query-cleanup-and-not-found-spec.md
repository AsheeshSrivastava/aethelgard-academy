# SPEC-23: Query cleanup, the "not found" rule, and keyword ranking

Status: approved by the owner 2026-11-16 ("go with your recommendation": R5 BM25 alone, M=3 on the real corpus).
Implements: ADR-0035 section 2.4 ("not found" threshold), section 2.8 (query transformation, step one) and section 4 step 4b (F8). No new ADR is needed; the same PR updates the ADR-0035 Done list. Open point 1 may need a one-line ADR-0035 amendment.
Measured with: `scripts/measure_not_found.py` (output in `docs/measurements/2026-11-16-not-found-rules.txt`), `scripts/measure_retrieval.py` for the fixture set. Local only, offline, no key.

## 1. What the measurements say (real corpus, 1,371 sources)
Sets: the six Gemini question files, validated first (every expected file exists in the corpus). 240 answerable questions (plain, error, paraphrase, pasted; 60 each) and 60 out-of-scope questions. Thresholds were read on three sets (fastapi, httpx, pydantic) and checked, untouched, on the other three (pytest, python, uv); both halves agreed within a few points.

1. **Today's `keyword_only` ranking is the weakest part.** It fuses BM25 with a word-overlap list that stands in for embeddings, then adds +1 to almost every passage. On the cleaned query it gets 48 first-hit / 87 top-3 of 240. BM25 alone gets 70 / 142. Giving BM25 more weight in the fusion helps but never catches up (weight 3: 54/117, weight 10: 62/132). So weighted fusion is not worth adopting here; dropping the stand-in list is.
2. **Query cleanup is a small win.** Dropping function words (a, the, how, do, is...) while keeping "not" and "no": 70 / 142 against 72 / 137 for the raw question. Top-3 +5, first-hit -2, so it is roughly neutral by itself; its real value is that the "not found" signal below needs a clean term count.
3. **Extracting error types and identifiers from pasted blocks made things worse** (pasted questions: 17/35 with plain cleanup, 14/25 extracted). The pasted text already carries those words and the message wording matters. Not adopted. Stripping Windows paths and URLs changed nothing that matters (69 / 144 against 70 / 142), so not adopted either.
4. **No score floor separates the groups well.** BM25 score of the top hit: separation (AUC) 0.77; the score of answerable questions overlaps the out-of-scope ones. This matches the earlier real-corpus result.
5. **The count of query terms found in the top passage separates best** (AUC 0.83; gap between 1st and 2nd score 0.49, a coin flip; share of terms matched 0.57). Rule "refuse when fewer than M distinct cleaned query terms appear in the best passage":

| M | false refusal (answerable question refused) | correct refusal (out-of-scope question refused) |
|---|---|---|
| 2 | 0 of 240 (0%) | 2 of 60 (3%) |
| 3 | 15 of 240 (6%) | 26 of 60 (43%) |
| 4 | 45 of 240 (19%) | 45 of 60 (75%) |

   Honest reading: the rule is a trade, not a clean split. M=3 refuses roughly 4 in 10 labelled out-of-scope questions and wrongly refuses about 6% of good ones. The correct-refusal number understates the truth: the sets were written against one doc set, and several "out-of-scope" questions have a fair answer elsewhere in the 1,371-source corpus (for example an httpx question answered in the fastapi docs). The remaining misses are mostly path-only pastes ("why is this failing??" plus a file path) and questions about neighbouring tools.
6. **The number does not transfer between corpora.** On the small SPEC-20 fixture (12 short docs) M=3 loses 10 of 41 answerable questions (and refuses all 9 no-answer); M=2 loses 2 and refuses 8 of 9 no-answer questions. So M is a per-index setting that must be tuned and recorded (ADR-0035 2.4 says exactly this), not a constant in code.
7. **Fixture gate.** BM25 alone on the cleaned query scores 36 first-hit / 40 top-3 of 41 on the SPEC-20 fixture, against 31 / 36 today. With the refusal rule at the fixture's minimum of 2 it scores 36 / 39 and refuses 8 of the 9 no-answer questions. The floor goes up to that. It cannot go down.
8. **Limit of all this.** These are keyword-only numbers. Keyword search finds the right file first for only 30% of real-corpus questions (rag-core measured about 80% for HR on its sets). `keyword_only` is the development and CI mode; HR will need its own tuning of the rule in step 6.

## 2. Scope
In this step:
- A pure `clean_query` in `core/` and callers that use it; the unit id is no longer part of the search text.
- `keyword_only` ranks by BM25 alone (best passage per source), without the word-overlap list and the +1 bonus.
- A "not found" rule on the number of query terms found in the best passage, with the minimum stored in configuration.
- The measurement script, its output, and the fixture floor raised to what the gate now shows.

Not in this step: the `hybrid_rerank` adapter and its own threshold (ADR step 6); LLM query rewriting (ADR 2.8, only if measured to help); changes to prompt wording (ADR-0034, step 5).

## 3. Requirements
- R1. `clean_query(text) -> str` lives in `core/` (pure standard library). It splits the text into the same tokens the BM25 index uses, drops a fixed list of function words (the list in `core/query.py`, which the measurement script imports: articles, auxiliaries, question words, pronouns, prepositions; **not** "not" or "no"), removes repeats (first occurrence wins, order kept), and joins with single spaces. It never raises.
- R2. If cleaning leaves no word, the search returns `not_found` (message "no searchable words"); it does not fall back to the raw text.
- R3. `axis_rules.ground_with_trace` stops prepending `unit_id`. The query is the learner's text only. `unit_id` is still used for the concept-store path.
- R4. No error-type or identifier extraction and no path stripping (section 1, items 3). The pasted block stays in the query as typed, after R1.
- R5. `KeywordRetriever` ranks passages by BM25 score, best passage per source, ties broken as in SPEC-21 R3. The word-overlap list, the fusion step and the +1 bonus are not used in `keyword_only`. `HybridRerankedRetriever` itself is not changed in this step, so the later HR adapter and its fusion stay open.
- R6. Not found. After ranking, the search is `not_found` when the best passage contains fewer than `min(M, n)` distinct cleaned query terms, where `n` is the number of distinct cleaned query terms and `M` is the configured minimum. (`min(M, n)` so a one- or two-word query is refused only when a term is missing, not always.) The adapter reports `terms_matched` and `terms_total` in the result message for the log.
- R7. `M` comes from `LMS_MIN_MATCHED_TERMS` (integer 1 to 10; default 3, tuned on the real corpus on 2026-11-16 with set version `gemini-6x50`). An invalid value fails startup with a clear message, as in SPEC-21 R6. The tuning value, date and set version are written next to the default in code and in `docs/measurements/`.
- R8. The SPEC-20 CI gate runs the fixture with its own `M` (2, per section 1 item 6) so the gate does not depend on the real-corpus setting. `floor.json` is raised to 36 first-hit and 39 top-3 (from 31 and 36) and records 8 of 9 no-answer questions refused; the date and set version are updated. The gate's no-answer check now also asserts the share of no-answer questions refused.
- R9. The interaction log keeps the SPEC-21/22 fields. A `not_found` caused by this rule logs `terms_matched` and `terms_total` through the trace, so the false-refusal rate can be watched on real traffic.
- R10. `source_prefixes`, `top_k`, `no_index` and `unavailable` behave as in SPEC-21. The SPEC-21 contract tests keep their assertions; their set-up changes only where R5 forces it (a fixture adapter built with minimum 2, test doubles that implement `keyword_search`), and the test that compared the new ranking with the old class is replaced by the floor test of R8.

## 4. Tests first (names, written before code)
1. `clean_query`: drops function words, keeps "not" and "no", keeps order, removes repeats, keeps error names, flags and dotted names such as `--locked`, `exclude_unset`, `pytest.mark.slow`; empty and whitespace input; a 10,000-character input (R1).
2. A query made only of function words returns `not_found` and does not fall back to the raw text (R2).
3. `ground_with_trace` calls the retriever with the question only; a unit id never appears in the search text (R3).
4. A pasted block (traceback plus config) is passed through R1 only; no extraction (R4).
5. Keyword ranking: order equals BM25 order, deterministic ties; a question that fusion used to rank by luck now ranks by BM25 (R5).
6. Not found: best passage with 2 of 4 terms and `M=3` gives `not_found`; 3 of 4 gives `ok`; a 2-term query with both terms present gives `ok`; with one missing gives `not_found`; a 1-term query that matches gives `ok` (R6).
7. `LMS_MIN_MATCHED_TERMS`: default 3, valid values accepted, `0`, `11` and `abc` fail startup with the message (R7).
8. Gate: fixture with `M=2` gives at least the new floor and refuses at least the recorded share of the 9 no-answer questions; the gate still fails if first-hit or top-3 drops (R8).
9. Trace carries `terms_matched` and `terms_total` on a refusal (R9).
10. Regression: SPEC-21 port contract tests pass unchanged against the fake and the keyword adapter (R10).

## 5. Edge cases for the later chaos check
Non-ASCII text, a query with only punctuation, tokens such as `a.b.c:` with trailing colons, a 10,000-character paste, a very long single token, a query of 3 distinct words repeated 100 times, uppercase and mixed case terms, `M` larger than the number of terms in the query, an index with one passage.

## 6. Traceability
ADR-0035 2.4 (threshold tuned on the set, stored with value, date and set version) -> R6, R7, R8. 2.8 (rule-based first step; drop the unit id) -> R1, R3, R4. 2.6 (CI floor) -> R8. SPEC-22 R4 (no fallback, so `not_found` can fire) -> R2, R6. SPEC-21 -> R10.

## 7. Open points for the owner
1. **Ranking change.** R5 changes what `keyword_only` returns and so changes SPEC-09's description of the keyword path (BM25 plus word-overlap fusion). The measurement says the extra list hurts. I recommend R5; the choice is yours because the dev mode will answer differently.
2. **M=3 or M=2 on the real corpus.** M=3 refuses about 43% of labelled out-of-scope questions and wrongly refuses about 6% of good ones; M=2 refuses almost nothing and loses nothing. A wrongly refused learner is sent to the "not in the course yet" path (Coach can still explain, labelled as not from the course); a wrongly answered one gets a weak citation. I recommend M=3, with the false-refusal rate watched through R9.
3. **Not adopted, on the evidence:** weighted fusion, error-type extraction, path stripping. Say so if you want any of them tried again with a better method.
4. **Re-tune later.** The same measurement must be repeated for `hybrid_rerank` in step 6; its scores are on a different scale.
