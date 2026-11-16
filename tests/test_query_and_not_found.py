"""Query cleanup, the "not found" rule and keyword ranking (SPEC-23).

Implements: SPEC-23 sections 3 and 4; ADR-0035 sections 2.4, 2.8 and work step 4b.
Test numbers in the comments are SPEC-23 section 4.
"""

from __future__ import annotations

import hashlib
import re

import pytest

import retrieval_quality as rq
from fake_retriever import FakeRetriever
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.rag.bm25 import TOKEN_RE
from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.adapters.ai.rag.startup import MIN_TERMS_ENV, RetrievalConfigError, build_retriever, configured_min_terms
from lms.core.query import FUNCTION_WORDS, clean_query
from lms.core.rag_contracts import Source, normalize_text
from lms.core.retrieval import RetrievalStatus

FIXTURE_MIN_TERMS = 2  # the SPEC-20 fixture has 12 short docs; section 1 item 6 of SPEC-23


def engine_from(docs: dict) -> HybridRerankedRetriever:
    engine = HybridRerankedRetriever()
    for name, text in docs.items():
        text = normalize_text(text)
        engine.index_source(
            Source(name, "v1", text, hashlib.sha256(text.encode()).hexdigest(), "t-1", "CC0-1.0", "declared")
        )
    return engine


def adapter(docs: dict, minimum: int = 3) -> KeywordRetriever:
    return KeywordRetriever.from_hybrid(engine_from(docs), min_matched_terms=minimum)


DOCS = {
    "a.md": "# Alpha\n\nalpha beta gamma delta epsilon are letters used in this made up page.",
    "b.md": "# Other\n\nomega sigma tau are different letters used in another page.",
}


# --- 1. clean_query (R1) ---------------------------------------------------------------------


def test_function_words_go_and_negations_stay():
    assert clean_query("How do I get the last item of a list?") == "get last item list"
    assert clean_query("why did it not raise an error") == "not raise error"
    assert "no" in clean_query("there is no output").split()


def test_order_is_kept_and_repeats_removed():
    assert clean_query("sort the list then sort the list again") == "sort list again"
    assert clean_query("List list LIST") == "List"


@pytest.mark.parametrize("keep", ["--locked", "exclude_unset", "pytest.mark.slow", "KeyError", "uv.lock", "ValueError:"])
def test_error_names_flags_and_dotted_names_survive(keep):
    assert keep in clean_query(f"why does {keep} happen in the build").split()


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_input_gives_empty_output(text):
    assert clean_query(text) == ""


def test_a_huge_input_is_handled_and_a_query_of_only_function_words_is_empty():
    assert clean_query("the " * 5000) == ""
    assert len(clean_query(" ".join(f"w{i}" for i in range(10000))).split()) == 10000


def test_the_token_rule_equals_the_bm25_index_rule():
    """clean_query must split text exactly as the index does (SPEC-23 R1)."""
    sample = "a.b.c: --flag foo_bar 3.14 C:\\x\\y.py:3 KeyError, 'quoted'"
    from lms.core import query as core_query

    assert re.findall(core_query.TOKEN_PATTERN, sample) == TOKEN_RE.findall(sample)


def test_the_function_word_list_never_contains_negations():
    assert not ({"not", "no"} & FUNCTION_WORDS)


# --- 2. nothing left after cleaning (R2) -------------------------------------------------------


def test_only_function_words_is_not_found_and_does_not_fall_back_to_the_raw_text():
    result = adapter(DOCS).search("what is the", top_k=3)
    assert result.status is RetrievalStatus.NOT_FOUND
    assert result.passages == ()
    assert "no searchable words" in result.message


# --- 3. the unit id is no longer in the search text (R3) -----------------------------------------


def test_ground_with_trace_sends_the_learner_text_only():
    fake = FakeRetriever(())
    axis_rules.ground_with_trace(fake, None, "PY-0.1", "Why is my list empty?")
    assert fake.calls[0][0] == "Why is my list empty?"


# --- 4. pasted blocks go through R1 only (R4) ------------------------------------------------------


def test_a_pasted_block_is_kept_as_typed_after_cleaning():
    pasted = "why does this fail??\nE   AssertionError: assert 'hello' in ''\ndef test_audit(caplog):\n    assert 'hello' in caplog.text"
    words = clean_query(pasted).split()
    assert {"AssertionError:", "caplog.text", "test_audit", "caplog"} <= set(words)
    assert "why" not in words


# --- 5. ranking is BM25 alone (R5) -----------------------------------------------------------------


def test_the_order_is_the_bm25_order_best_passage_per_source():
    docs = {
        "one.md": "# One\n\nalpha alpha alpha alpha beta gamma",
        "two.md": "# Two\n\nalpha beta gamma delta",
        "three.md": "# Three\n\nalpha only",
    }
    kw = adapter(docs, minimum=1)
    result = kw.search("alpha beta gamma", top_k=3)
    engine = engine_from(docs)
    expected = []
    for pid, _ in engine.bm25.search("alpha beta gamma", top_k=200):
        src = engine.passages[pid].source_id
        if src not in expected:
            expected.append(src)
    assert [p.source_id for p in result.passages] == expected[:3]
    assert len({p.source_id for p in result.passages}) == len(result.passages)


def test_a_question_that_fusion_ranked_by_luck_now_ranks_by_bm25():
    """The word-overlap list and the +1 bonus are gone: scores are BM25 scores, not RRF plus one."""
    result = adapter(DOCS, minimum=1).search("alpha beta gamma")
    assert result.passages[0].source_id == "a.md"
    assert result.passages[0].score > 2.0  # an RRF score is below 0.1; a bonus makes it at least 1.0


def test_equal_scores_are_ordered_by_source_then_position():
    docs = {"y.md": "# T\n\nalpha beta", "x.md": "# T\n\nalpha beta"}
    result = adapter(docs, minimum=1).search("alpha beta", top_k=2)
    assert [p.source_id for p in result.passages] == ["x.md", "y.md"]


# --- 6. the "not found" rule (R6) -------------------------------------------------------------------


@pytest.mark.parametrize(
    "query,minimum,expected",
    [
        ("alpha beta zzz qqq", 3, RetrievalStatus.NOT_FOUND),  # 2 of 4 terms, needs 3
        ("alpha beta gamma qqq", 3, RetrievalStatus.OK),  # 3 of 4
        ("alpha beta", 3, RetrievalStatus.OK),  # 2-word query, both present: min(3, 2) = 2
        ("alpha zzz", 3, RetrievalStatus.NOT_FOUND),  # 2-word query, one missing
        ("alpha", 3, RetrievalStatus.OK),  # 1-word query that matches
        ("zzz", 3, RetrievalStatus.NOT_FOUND),  # matches nothing at all
        ("alpha beta zzz qqq", 2, RetrievalStatus.OK),  # a lower minimum lets it through
        ("alpha beta zzz qqq", 1, RetrievalStatus.OK),
        ("alpha beta zzz qqq", 10, RetrievalStatus.NOT_FOUND),
    ],
)
def test_minimum_matched_terms_decides_found_or_not(query, minimum, expected):
    assert adapter(DOCS, minimum).search(query).status is expected


def test_the_result_reports_how_many_terms_matched():
    refused = adapter(DOCS, 3).search("alpha beta zzz qqq")
    assert (refused.terms_matched, refused.terms_total) == (2, 4)
    found = adapter(DOCS, 3).search("alpha beta gamma qqq")
    assert (found.terms_matched, found.terms_total) == (3, 4)
    assert "terms_matched=2" in refused.message and "terms_total=4" in refused.message


def test_the_rule_counts_distinct_terms_not_repeats():
    assert adapter(DOCS, 3).search("alpha alpha alpha beta zzz").status is RetrievalStatus.NOT_FOUND


def test_a_prefix_filter_applies_before_the_rule():
    docs = {"x/a.md": "# A\n\nalpha beta gamma", "y/b.md": "# B\n\nalpha"}
    kw = adapter(docs, 3)
    assert kw.search("alpha beta gamma", source_prefixes=("y/",)).status is RetrievalStatus.NOT_FOUND
    assert kw.search("alpha beta gamma", source_prefixes=("x/",)).status is RetrievalStatus.OK


def test_m_larger_than_the_query_and_a_one_passage_index():
    kw = adapter({"only.md": "# Only\n\nalpha"}, 10)
    assert kw.search("alpha").status is RetrievalStatus.OK


# --- 7. the setting (R7) ------------------------------------------------------------------------------


def test_default_is_three_and_valid_values_are_accepted():
    assert configured_min_terms({}) == 3
    assert configured_min_terms({MIN_TERMS_ENV: "1"}) == 1
    assert configured_min_terms({MIN_TERMS_ENV: " 10 "}) == 10


@pytest.mark.parametrize("bad", ["0", "11", "-1", "abc", "2.5", ""])
def test_bad_values_fail_startup_with_a_clear_message(bad):
    if bad == "":
        assert configured_min_terms({MIN_TERMS_ENV: ""}) == 3  # unset and empty mean "use the default"
        return
    with pytest.raises(RetrievalConfigError) as err:
        configured_min_terms({MIN_TERMS_ENV: bad})
    assert MIN_TERMS_ENV in str(err.value) and "1 to 10" in str(err.value)


def test_build_retriever_reads_the_setting(tmp_path):
    rq.build_keyword_retriever().save(tmp_path / "index")
    kw = build_retriever({"LMS_INDEX_DIR": str(tmp_path / "index"), MIN_TERMS_ENV: "2"})
    assert kw.min_matched_terms == 2
    with pytest.raises(RetrievalConfigError):
        build_retriever({"LMS_INDEX_DIR": str(tmp_path / "index"), MIN_TERMS_ENV: "99"})


# --- 8. the CI gate with its own minimum (R8) -----------------------------------------------------------


def _fixture_adapter() -> KeywordRetriever:
    return KeywordRetriever.from_hybrid(rq.build_keyword_retriever(), min_matched_terms=FIXTURE_MIN_TERMS)


def test_the_fixture_meets_the_new_floor_through_the_shipped_adapter():
    floor = rq.load_floor()
    kw = _fixture_adapter()
    result = rq.score(lambda q: [p.source_id for p in kw.search(q, top_k=3).passages])
    assert result.first_hit >= floor["first_hit"], result
    assert result.top3 >= floor["top3"], result
    assert floor["first_hit"] >= 36 and floor["top3"] >= 39  # it can go up from 31/36, never down


def test_the_fixture_refuses_the_recorded_share_of_no_answer_questions():
    floor = rq.load_floor()
    kw = _fixture_adapter()
    no_answer = [q for q in rq.load_questions() if q["expected_source"] is None]
    refused = sum(kw.search(q["question"]).status is RetrievalStatus.NOT_FOUND for q in no_answer)
    assert refused >= floor["no_answer_refused"] >= 8
    assert len(no_answer) == floor["no_answer_total"]


# --- 9. the trace ---------------------------------------------------------------------------------------


def test_a_refusal_puts_the_term_counts_in_the_trace():
    kw = adapter(DOCS, 3)
    _grounding, trace = axis_rules.ground_with_trace(kw, None, "PY-0.1", "alpha beta zzz qqq")
    assert trace is not None and trace.status == "not_found"
    fields = trace.as_log_fields()
    assert (fields["terms_matched"], fields["terms_total"]) == (2, 4)
