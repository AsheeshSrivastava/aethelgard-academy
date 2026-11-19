"""SPEC-27: the rag-core adapter (mode hybrid_rerank), downgrade, timeout, concurrency, not-found rule.

Implements: ADR-0035 sections 2.2, 2.3, 2.4, 2.7, 2.9 and plan step 7. Test numbers match SPEC-27 section 5.
No model and no ragcore is loaded here: the engine is a fake with the same `search` shape.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from typing import List

import pytest

from fake_retriever import FakeRetriever, passage
from lms.adapters.ai.rag.ragcore_retriever import (
    DowngradedRetriever,
    RagcoreRetriever,
    compute_ragcore_index_version,
)
from lms.adapters.ai.rag.startup import (
    RetrievalConfigError,
    configured_hr_min_score,
    configured_mode,
    configured_rerank_concurrency,
    configured_timeout_s,
)
from lms.core.retrieval import (
    RetrievalMode,
    RetrievalResult,
    RetrievalStatus,
    RetrievalTrace,
)


def hit(source_id: str, text: str, score: float, n: int = 1) -> SimpleNamespace:
    return SimpleNamespace(passage_id=f"{source_id}#{n}", source_id=source_id, text=text, score=score)


class FakeEngine:
    """The shape of ragcore.Retriever.search. Scripted results; can sleep or raise."""

    def __init__(self, results: List[SimpleNamespace] | None = None, delay: float = 0.0, error: Exception | None = None):
        self.results = results or []
        self.delay = delay
        self.error = error
        self.calls: list = []

    def search(self, query: str, k: int = 5, max_per_file: int | None = None):
        self.calls.append((query, k, max_per_file))
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise self.error
        return list(self.results)[:k]


FALLBACK = FakeRetriever((passage("docs/kw.md", "keyword text"),), index_version="kw-1")


def make(engine, **kw) -> RagcoreRetriever:
    kw.setdefault("timeout_s", 2.0)
    kw.setdefault("min_matched_terms", 1)
    return RagcoreRetriever(engine, "hr-1", FALLBACK, **kw)


GOOD = [hit("pytest/fixtures.md", "pytest fixtures share setup code", 3.2), hit("pytest/marks.md", "marks tag tests", 1.0)]


# 1. Port contract ----------------------------------------------------------------------------------

def test_ok_result_has_our_types_and_hybrid_mode():
    r = make(FakeEngine(GOOD)).search("how do pytest fixtures work", top_k=3)
    assert r.status is RetrievalStatus.OK and r.mode is RetrievalMode.HYBRID_RERANK
    assert r.index_version == "hr-1" and not r.downgraded
    assert r.passages[0].passage_id == "pytest/fixtures.md#1"


def test_nothing_found_is_not_found():
    r = make(FakeEngine([])).search("pytest fixtures", top_k=3)
    assert r.status is RetrievalStatus.NOT_FOUND


def test_engine_error_is_unavailable_or_downgraded_never_raised():
    r = make(FakeEngine(error=RuntimeError("boom"))).search("pytest fixtures")
    assert isinstance(r, RetrievalResult)


def test_index_status_ok():
    assert make(FakeEngine(GOOD)).index_status() is RetrievalStatus.OK


# 2. Mapping and order ----------------------------------------------------------------------------

def test_mapping_fields_and_source_name_and_order():
    results = [hit("a/b/low.md", "pytest low", 0.5), hit("a/b/high.md", "pytest high", 4.0)]
    r = make(FakeEngine(results)).search("pytest", top_k=3)
    assert [p.source_name for p in r.passages] == ["high.md", "low.md"]  # best score first
    assert r.passages[0].text == "pytest high" and r.passages[0].score == 4.0


def test_ties_break_by_source_then_passage_id():
    results = [hit("b.md", "pytest x", 1.0), hit("a.md", "pytest x", 1.0)]
    r = make(FakeEngine(results)).search("pytest", top_k=3)
    assert [p.source_id for p in r.passages] == ["a.md", "b.md"]


# 3. top_k, passages per source, prefixes ---------------------------------------------------------

def test_top_k_is_clamped_and_passages_per_source_is_passed():
    engine = FakeEngine(GOOD)
    r = make(engine, passages_per_source=2)
    r.search("pytest", top_k=0)
    r.search("pytest", top_k=1000)
    assert engine.calls[0][1] == 1 and engine.calls[1][1] == 10
    assert engine.calls[0][2] == 2


def test_prefix_filters_after_ranking_and_may_leave_fewer():
    engine = FakeEngine(GOOD)
    r = make(engine).search("pytest", top_k=3, source_prefixes=("pytest/fix",))
    assert [p.source_id for p in r.passages] == ["pytest/fixtures.md"]
    assert engine.calls[0][1] >= 30  # asked for the reranker's whole depth so the filter has material
    none = make(FakeEngine(GOOD)).search("pytest", top_k=3, source_prefixes=("nope/",))
    assert none.status is RetrievalStatus.NOT_FOUND


def test_empty_and_whitespace_and_function_word_queries():
    engine = FakeEngine(GOOD)
    r = make(engine)
    assert r.search("   ").status is RetrievalStatus.NOT_FOUND
    assert r.search("how do the a").status is RetrievalStatus.NOT_FOUND
    assert engine.calls == []  # nothing to search; the model is not called


def test_very_long_query_does_not_raise():
    assert isinstance(make(FakeEngine(GOOD)).search("pytest " * 3000), RetrievalResult)


# 4/5. Downgrade ------------------------------------------------------------------------------------

def test_downgraded_retriever_labels_every_result():
    d = DowngradedRetriever(FALLBACK, "models missing")
    r = d.search("anything")
    assert r.downgraded and r.mode is RetrievalMode.KEYWORD_ONLY and r.status is RetrievalStatus.OK
    assert d.index_status() is RetrievalStatus.OK


# 6. Timeout ----------------------------------------------------------------------------------------

def test_timeout_answers_from_keyword_labelled_and_in_time():
    slow = FakeEngine(GOOD, delay=1.0)
    r = make(slow, timeout_s=0.1)
    started = time.perf_counter()
    result = r.search("pytest fixtures")
    assert time.perf_counter() - started < 0.6
    assert result.downgraded and result.mode is RetrievalMode.KEYWORD_ONLY
    assert result.passages[0].source_id == "docs/kw.md"


def test_runtime_model_error_is_downgraded_not_raised():
    result = make(FakeEngine(error=RuntimeError("cuda lost"))).search("pytest fixtures")
    assert result.downgraded and result.status is RetrievalStatus.OK


# 7. Concurrency ------------------------------------------------------------------------------------

def test_over_the_concurrency_limit_is_busy_at_once():
    slow = FakeEngine(GOOD, delay=0.5)
    r = make(slow, concurrency=2, timeout_s=2.0)
    out: list = []
    threads = [threading.Thread(target=lambda: out.append(r.search("pytest fixtures"))) for _ in range(2)]
    for t in threads:
        t.start()
    time.sleep(0.15)
    started = time.perf_counter()
    third = r.search("pytest fixtures")
    assert time.perf_counter() - started < 0.2
    assert third.status is RetrievalStatus.UNAVAILABLE and "busy" in third.message
    assert third.mode is RetrievalMode.HYBRID_RERANK and not third.downgraded
    for t in threads:
        t.join()
    assert all(x.status is RetrievalStatus.OK for x in out)


def test_slot_is_released_after_a_timeout_only_when_the_engine_finishes():
    slow = FakeEngine(GOOD, delay=0.4)
    r = make(slow, concurrency=1, timeout_s=0.05)
    assert r.search("pytest fixtures").downgraded
    assert r.search("pytest fixtures").status is RetrievalStatus.UNAVAILABLE  # late search still running
    time.sleep(0.5)
    assert r.search("pytest fixtures").downgraded  # slot is free again (timeout again, not busy)


# 8. Import hygiene ---------------------------------------------------------------------------------

def test_importing_the_adapter_does_not_import_ragcore_or_torch():
    code = (
        "import sys, lms.adapters.ai.rag.ragcore_retriever, lms.adapters.ai.rag.startup;"
        "bad=[m for m in ('ragcore','torch','transformers') if m in sys.modules];"
        "sys.exit(1 if bad else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


# 9. Configuration ----------------------------------------------------------------------------------

def test_hybrid_rerank_mode_is_accepted_and_unknown_still_fails():
    assert configured_mode({"LMS_RETRIEVAL_MODE": "hybrid_rerank"}) is RetrievalMode.HYBRID_RERANK
    with pytest.raises(RetrievalConfigError, match="Unknown"):
        configured_mode({"LMS_RETRIEVAL_MODE": "magic"})


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "301"])
def test_timeout_rejects_bad_values(raw):
    with pytest.raises(RetrievalConfigError, match="LMS_RETRIEVAL_TIMEOUT_S"):
        configured_timeout_s({"LMS_RETRIEVAL_TIMEOUT_S": raw})


def test_timeout_default_is_ten_seconds():
    assert configured_timeout_s({}) == 10.0 and configured_timeout_s({"LMS_RETRIEVAL_TIMEOUT_S": "7"}) == 7.0


@pytest.mark.parametrize("raw", ["0", "9", "x"])
def test_concurrency_rejects_bad_values(raw):
    with pytest.raises(RetrievalConfigError, match="LMS_RERANK_CONCURRENCY"):
        configured_rerank_concurrency({"LMS_RERANK_CONCURRENCY": raw})
    assert configured_rerank_concurrency({}) == 2


def test_min_score_empty_means_off_and_bad_value_fails():
    assert configured_hr_min_score({}) is None and configured_hr_min_score({"LMS_HR_MIN_SCORE": " "}) is None
    assert configured_hr_min_score({"LMS_HR_MIN_SCORE": "-2.5"}) == -2.5
    with pytest.raises(RetrievalConfigError, match="LMS_HR_MIN_SCORE"):
        configured_hr_min_score({"LMS_HR_MIN_SCORE": "nan"})
    with pytest.raises(RetrievalConfigError, match="LMS_HR_MIN_SCORE"):
        configured_hr_min_score({"LMS_HR_MIN_SCORE": "abc"})


# 10. index_version ---------------------------------------------------------------------------------

SETUP = {"embedder_id": "e", "embedder_revision": "r1", "chunker": "c", "chunker_version": "1",
         "chunk_config": "1500/6000", "llama_index_version": "0.14", "reranker_id": "rr", "reranker_revision": "r2"}
SOURCES = [("a.md", "h1"), ("b.md", "h2")]


def test_index_version_is_stable_and_changes_with_pins_and_sources():
    base = compute_ragcore_index_version(SETUP, SOURCES)
    assert base == compute_ragcore_index_version(SETUP, list(reversed(SOURCES)))
    assert base != compute_ragcore_index_version({**SETUP, "reranker_revision": "x"}, SOURCES)
    assert base != compute_ragcore_index_version({**SETUP, "embedder_revision": "x"}, SOURCES)
    assert base != compute_ragcore_index_version(SETUP, [("a.md", "h1"), ("b.md", "CHANGED")])


# 11. Not-found rule for HR ---------------------------------------------------------------------

def test_floor_refuses_a_low_top_score_and_empty_floor_means_off():
    low = [hit("a.md", "pytest fixtures setup", -3.0)]
    refused = make(FakeEngine(low), min_score=-1.0).search("pytest fixtures")
    assert refused.status is RetrievalStatus.NOT_FOUND and "score" in refused.message
    assert make(FakeEngine(low), min_score=None).search("pytest fixtures").status is RetrievalStatus.OK
    assert make(FakeEngine(low), min_score=-5.0).search("pytest fixtures").status is RetrievalStatus.OK


def test_term_rule_still_applies_and_trace_numbers_are_reported():
    text = [hit("a.md", "pytest fixtures", 2.0)]
    r = make(FakeEngine(text), min_matched_terms=3).search("pytest fixtures scope session")
    assert r.status is RetrievalStatus.NOT_FOUND
    assert (r.terms_matched, r.terms_total) == (2, 4)
    ok = make(FakeEngine(text), min_matched_terms=2).search("pytest fixtures scope session")
    assert ok.status is RetrievalStatus.OK and (ok.terms_matched, ok.terms_total) == (2, 4)


def test_term_rule_can_be_switched_off_for_the_floor_only_variant():
    text = [hit("a.md", "unrelated words", 2.0)]
    r = make(FakeEngine(text), min_matched_terms=0).search("pytest fixtures scope")
    assert r.status is RetrievalStatus.OK


# 12. Log field ---------------------------------------------------------------------------------

def test_trace_logs_downgraded():
    t = RetrievalTrace("v", "keyword_only", "ok", 5, downgraded=True)
    assert t.as_log_fields()["downgraded"] is True


# 12b. The downgrade reaches the learner (SPEC-27 R6, D2) -------------------------------------------

def test_downgrade_reaches_consult_and_stream_and_is_absent_otherwise():
    from lms.adapters.ai import passage_safety as ps
    from lms.adapters.ai.axis_stream import stream_axis
    from lms.adapters.ai.providers import axis_rules
    from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
    from lms.core.interfaces import AxisMode

    class Axis:
        def __init__(self, grounding):
            self.g = grounding

        def stream(self, _q):
            return iter(["ok"]), self.g

    from test_no_source_rules import query

    q = query(AxisMode.COACH)
    for downgraded in (True, False):
        trace = RetrievalTrace("v", "keyword_only", "ok", 1, downgraded=downgraded)
        g = ps.build_grounding([("a#1", "A", "alpha beta gamma delta epsilon")], trace)
        reply = axis_rules.finish_reply("ok", q, g, SocraticGuardrail(), AssistanceClassifier())
        done = [d for e, d in stream_axis(Axis(g), q, SocraticGuardrail(), AssistanceClassifier()) if e == "done"][0]
        assert reply.retrieval_downgraded is downgraded
        assert done.get("retrieval_downgraded", False) is downgraded
