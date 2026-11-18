"""SPEC-25 R7: the passages-per-source setting (default 1) of the keyword search.

Cap 1 must give exactly today's output; 2 and 3 return at most that many passages per file.
"""

from __future__ import annotations

import hashlib

import pytest

import retrieval_quality as rq
from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.adapters.ai.rag.startup import PASSAGES_PER_SOURCE_ENV, RetrievalConfigError, configured_passages_per_source
from lms.core.rag_contracts import Source, Span


def _source(source_id: str, text: str) -> Source:
    return Source(source_id, "v1", text, hashlib.sha256(text.encode()).hexdigest(), "t-1", "CC0-1.0", "declared")


def _engine() -> HybridRerankedRetriever:
    """big.md has three passages that all mention 'widget'; other.md has one."""
    engine = HybridRerankedRetriever()
    parts = [
        "widget widget widget parts list",
        "widget second part with more words here",
        "widget third part and some other words",
    ]
    text = "\n\n".join(parts)
    spans, pos = [], 0
    for p in parts:
        spans.append(Span(pos, pos + len(p)))
        pos += len(p) + 2
    engine.index_source(_source("big.md", text), spans)
    engine.index_source(_source("other.md", "widget single passage in another file"))
    return engine


def test_default_is_one_passage_per_file():
    hits, _ = _engine().keyword_search("widget")
    assert [h.passage.source_id for h in hits] == ["big.md", "other.md"]


@pytest.mark.parametrize("cap", [1, 2, 3])
def test_no_file_returns_more_than_the_cap(cap):
    hits, _ = _engine().keyword_search("widget", per_source=cap)
    per_file: dict[str, int] = {}
    for h in hits:
        per_file[h.passage.source_id] = per_file.get(h.passage.source_id, 0) + 1
    assert max(per_file.values()) <= cap
    assert per_file["big.md"] == cap  # the file really has three matching passages


def test_cap_one_is_the_same_as_the_default_byte_for_byte():
    engine = _engine()
    default, total_default = engine.keyword_search("widget parts")
    explicit, total_explicit = engine.keyword_search("widget parts", per_source=1)
    assert total_default == total_explicit
    assert repr(default) == repr(explicit)


def test_extra_passages_come_after_the_best_one_in_score_order():
    hits, _ = _engine().keyword_search("widget", per_source=3)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)
    big = [h.passage.start for h in hits if h.passage.source_id == "big.md"]
    assert len(big) == 3 and len(set(big)) == 3


def test_retriever_cap_one_matches_the_fixture_default():
    engine = rq.build_keyword_retriever()
    default = KeywordRetriever.from_hybrid(engine)
    explicit = KeywordRetriever.from_hybrid(engine, passages_per_source=1)
    for q in rq.load_questions():
        a, b = default.search(q["question"], top_k=5), explicit.search(q["question"], top_k=5)
        assert repr(a) == repr(b)


def test_retriever_with_cap_three_returns_several_passages_of_one_file():
    r = KeywordRetriever.from_hybrid(_engine(), min_matched_terms=1, passages_per_source=3)
    result = r.search("widget", top_k=5)
    ids = [p.source_id for p in result.passages]
    assert ids.count("big.md") == 3 and ids.count("other.md") == 1
    r1 = KeywordRetriever.from_hybrid(_engine(), min_matched_terms=1)
    assert [p.source_id for p in r1.search("widget", top_k=5).passages] == ["big.md", "other.md"]


def test_a_cap_below_one_is_refused():
    with pytest.raises(ValueError):
        KeywordRetriever.from_hybrid(_engine(), passages_per_source=0)


# --- the setting read at startup ----------------------------------------------------------------------


def test_setting_default_is_one():
    assert configured_passages_per_source({}) == 1
    assert configured_passages_per_source({PASSAGES_PER_SOURCE_ENV: ""}) == 1


def test_setting_accepts_one_to_five():
    assert configured_passages_per_source({PASSAGES_PER_SOURCE_ENV: "3"}) == 3


@pytest.mark.parametrize("bad", ["0", "6", "-1", "two", "1.5"])
def test_setting_refuses_values_outside_one_to_five(bad):
    with pytest.raises(RetrievalConfigError):
        configured_passages_per_source({PASSAGES_PER_SOURCE_ENV: bad})
