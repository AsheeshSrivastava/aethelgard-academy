# SPEC-26: Search-only text for keyword search (plan step 6a)

Status: Approved by the owner 2026-11-19 ("okay, 6a"), scope 6a only (all five variants V0 to V4). The model-written sentence (6b) is not in this spec; it gets its own spec after the 6a numbers.
Implements: ADR-0035 section 5.2 (contextual retrieval, search-only field), split into 6a (free, offline, this spec) and 6b (model-written sentence, later). Amends nothing in SPEC-22, SPEC-23 or SPEC-25. Governed by AGENTS.md (zero-cost development, provenance firewall), ADR-0035 2.5 (retrieved text is untrusted; the learner sees original text only).
Reuses: scripts/measure_gemini.py, scripts/measure_lib.py (SPEC-25), docs/measurements/2026-11-18-gemini-baseline.txt. Local only, offline, no key, no model call, no paid run.

## 1. Why
SPEC-25 baseline, Hit@3 on 240 answerable questions: keyword 57.1, HR 75.0. Of 103 keyword top-3 misses, 86 are labelled "wording"; paraphrase is the weakest kind (30.0). BM25 today sees the passage text plus the heading path (counted twice) but not the page title or the file path (for example `how-to/tmp_path`). Question Q15 (pytest default flags, `reference/customize`, a nearly empty chunk) can only be found by its path. Words the index already holds, put into the bag of words, cost nothing and need no model.

## 2. Requirements
- R1. `search_text(passage, recipe)` is a pure function in `core/` (no vendor import) that returns extra words for the BM25 bag of words, taken only from fields the index already holds: the source id (path), the page title, and the heading path. No new data, no model call. (Reading note 1: the heading path is already in the bag twice and is not added again.)
- R2. Path words: each path segment is kept whole (`tmp_path`) and also split on `-`, `_` and `.` (`tmp`, `path`); lower-cased; de-duplicated per passage; the set prefix (the first segment, for example `pytest-docs`) is dropped; the file extension is dropped. A source id with no `/` has no set prefix to drop.
- R3. The BM25 index adds the search-only words to a passage's bag of words. The weighting is the variant (R5).
- R4. Display, prompt, citation and the quote-overlap check use the original passage text and headings only. A returned passage has the same text and headings as before and lacks the extra words (a test proves it).
- R5. Variants (recipe names in brackets). One is adopted only by R7.
  - V0 today's index (`none`).
  - V1 V0 plus path words once (`path`).
  - V2 V0 plus page title words once (`title`).
  - V3 V0 plus path words and title words once (`path_title`).
  - V4 V3 counted twice (`path_title_x2`).
- R6. `index_version` changes whenever the recipe changes: a `SEARCH_TEXT_VERSION` string is mixed into `compute_index_version`. Recipe `none` keeps today's `index_version` byte for byte. `matched_terms` (SPEC-23) keeps counting distinct query terms found in the passage's index entry (Reading note 2). `min_matched_terms` (2, 3, 4) is re-measured for the adopted variant and changed only by the R7 rule.
- R7. Adoption rule. A variant is adopted only if, against V0, on the six Gemini sets: Hit@3 gains at least 2 points; false-refusal and correct-refusal are each no more than 1 point worse; and the SPEC-20 fixture top-3 is not below `floor.json` (and its refusal rates stay within 1 point). Otherwise V0 stays. Report Hit@1/3/5, MRR, nDCG, per kind, and the SPEC-25 R6 miss labels before and after.
- R8. Deterministic output (SPEC-25 R11): ties by row position, no timestamps in numbers. The baseline is read from `docs/measurements/2026-11-18-gemini-baseline.txt`; results go to `docs/measurements/<date>-search-only-text.txt`, stamped with SET_VERSION and the index versions.

## 3. Setting
`LMS_SEARCH_TEXT` (recipe name, default `none`), read at startup beside `LMS_MIN_MATCHED_TERMS`. Unknown names stop startup with a message that lists the choices. The default stays `none` unless R7 is met and the owner agrees.

## 4. Out of scope
Model-written context (6b), embeddings, the rag-core adapter, query rewriting, any paid or network call.

## 5. Tests (written first)
- R1, R2: made-up passages with exact expected word lists (path with `-`, `_`, `.`; empty title; source id with no `/`; whole and split forms; de-duplication; extension dropped).
- R3: a passage that matches only through a path word is returned with a recipe that includes the path, and is not returned with `none`.
- R4: the returned passage text and headings are byte-identical to the `none` run; the extra words are not in them.
- R6: `none` gives today's `index_version` byte for byte (fixed vector); any other recipe differs; the recipe is mixed in even when the sources are equal.
- Setting: default `none`, unknown name rejected.
- Fixture gate (SPEC-20) stays green with the default.

## 6. Risks
Path words can pull sibling pages (the SPEC-25 "multi-page" label). One question is 0.4 points, so the 2-point bar is about five questions: V4 is not adopted over V3 on a one-question edge. Only 24 of 240 questions were human-reviewed.

## 7. Reading notes (implementation choices, added while building)
These fill gaps in the text above; none changes a requirement.
1. The heading path is already indexed (twice) today, so `search_text` adds nothing for it. The "page title" is the outermost heading of the passage's heading path (the page's first heading in practice), or the file name without extension for a passage before any heading, so the function needs only the passage.
2. `matched_terms` is counted from the index entry, which now includes the search-only words. A query term found only in the path therefore counts as matched. The `min_matched_terms` sweep in the measurement file shows the effect.
3. The saved `bm25.json` records its recipe (only when it is not `none`, so the old file format is unchanged). Loading with a different recipe rebuilds the BM25 index from the stored passages; the original text is never touched.

## 8. Result (2026-11-19; docs/measurements/2026-11-19-search-only-text.txt)
Hit@3 on the six Gemini sets (240 answerable), min_matched_terms 3: V0 57.1, V1 57.5, V2 57.1, V3 58.3, V4 59.2. Against V0, V4 gains 5 questions (7 gained, 2 lost): +2.1 points, which is on the R7 bar (4 questions would be 1.7 and fail). Refusal rates are unchanged for V4 (false 6.2, correct 43.3), the SPEC-20 fixture is identical for every variant (first 36, top3 39 of 41), and V0 reproduces the SPEC-25 baseline. V1, V2 and V3 do not meet the bar.
R7 is met by V4 alone, so V4 is the only candidate. Because the margin is one question and only 24 of 240 questions were human-reviewed, the default stays `none` until the owner decides; `LMS_SEARCH_TEXT=path_title_x2` turns V4 on. Switching it on changes `index_version`, and the saved `data/index/bm25.json` is not rewritten (the index is rebuilt in memory at load, which is quick).
