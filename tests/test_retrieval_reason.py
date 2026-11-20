"""SPEC-29 R17: a structured retrieval reason, so a busy search can be told from a timeout.

Written before the code. Offline: the engine is the same fake the SPEC-27 tests use.
Names under test: RetrievalResult.reason, RetrievalTrace.reason, the `retrieval_reason` span attribute.
"""

import threading
import time

import pytest

from test_ragcore_retriever import GOOD, FakeEngine, make

from lms.core.retrieval import RetrievalResult, RetrievalStatus

REASONS = {"busy", "timeout", "stalled", "start_failed", "model_fault"}


def test_a_normal_result_has_no_reason():
    result = make(FakeEngine(GOOD)).search("pytest fixtures")

    assert result.reason == "" and not result.downgraded


def test_busy_search_has_reason_busy():
    slow = FakeEngine(GOOD, delay=0.5)
    r = make(slow, concurrency=1, timeout_s=2.0)
    first = threading.Thread(target=lambda: r.search("pytest fixtures"))
    first.start()
    time.sleep(0.15)

    second = r.search("pytest fixtures")
    first.join()

    assert second.status is RetrievalStatus.UNAVAILABLE and second.reason == "busy"


def test_timeout_has_reason_timeout_and_still_downgrades():
    result = make(FakeEngine(GOOD, delay=1.0), timeout_s=0.1).search("pytest fixtures")

    assert result.downgraded and result.reason == "timeout"


def test_stalled_start_failed_and_model_fault_reasons():
    slow = FakeEngine(GOOD, delay=0.4)
    r = make(slow, concurrency=1, timeout_s=0.05)
    assert r.search("pytest fixtures").reason == "timeout"
    assert r.search("pytest fixtures").reason == "stalled"          # the one slot is held by the timed-out search

    broken = make(FakeEngine(GOOD))
    broken._pool.shutdown()
    assert broken.search("pytest fixtures").reason == "start_failed"

    assert make(FakeEngine(error=RuntimeError("cuda lost"))).search("pytest fixtures").reason == "model_fault"


@pytest.mark.parametrize("build, reason", [
    (lambda: make(FakeEngine(GOOD, delay=1.0), timeout_s=0.1), "timeout"),
    (lambda: make(FakeEngine(error=RuntimeError("x"))), "model_fault"),
])
def test_reason_does_not_change_status_message_or_label(build, reason):
    result = build().search("pytest fixtures")

    assert result.reason == reason
    assert result.downgraded is True and result.status is RetrievalStatus.OK  # exactly what SPEC-27 R6 already says
    assert result.passages[0].source_id == "docs/kw.md"


def test_the_reason_is_not_in_the_interaction_log_fields():
    from lms.core.retrieval import RetrievalTrace

    fields = RetrievalTrace("v1", "keyword_only", "ok", 5, reason="timeout").as_log_fields()

    assert "reason" not in fields and "retrieval_reason" not in fields  # logged payloads stay exactly as they are


def test_retrieve_span_carries_retrieval_reason_from_the_fixed_set(tmp_path):
    import lms.core.tracing as tracing
    from fake_retriever import FakeRetriever, passage
    from lms.adapters.ai.providers import axis_rules
    from lms.adapters.observability.local_tracer import LocalTracer
    from lms.core.retrieval import RetrievalMode

    class Reasoned(FakeRetriever):
        def search(self, query, *, top_k=3, source_prefixes=()):
            base = super().search(query, top_k=top_k, source_prefixes=source_prefixes)
            return RetrievalResult(base.status, RetrievalMode.HYBRID_RERANK, base.index_version, base.passages, base.message,
                                   downgraded=True, reason="timeout")

    tracing.set_tracer(LocalTracer(tmp_path))
    try:
        axis_rules.ground_with_trace(Reasoned((passage("how-to/a", "some text here"),), index_version="ab12cd34ef56"), None, "PY-0.1", "text")
    finally:
        tracing.set_tracer(tracing.NoopTracer())

    import json

    spans = [json.loads(line) for line in (tmp_path / "axis-trace.jsonl").read_text(encoding="utf-8").splitlines()]
    retrieve = next(s for s in spans if s["name"] == "retrieve")
    assert retrieve["attributes"]["retrieval_reason"] == "timeout"
    assert retrieve["attributes"].get("dropped_attributes", 0) == 0


@pytest.mark.parametrize("value", ["", "something else", "the provider said no", "BUSY", None, 7])
def test_retrieval_reason_outside_the_set_is_dropped(value):
    from lms.core.tracing import sanitise_attributes

    clean, dropped = sanitise_attributes({"retrieval_reason": value})

    assert clean == {} and dropped == 1


@pytest.mark.parametrize("value", sorted(REASONS))
def test_every_reason_in_the_set_is_accepted(value):
    from lms.core.tracing import sanitise_attributes

    assert sanitise_attributes({"retrieval_reason": value}) == ({"retrieval_reason": value}, 0)


def test_existing_retrieval_and_span_tests_unchanged():
    # The SPEC-27 adapter suite and the SPEC-28 tracing suites keep passing as written (checked by the full run);
    # this guard fails only if RetrievalResult stops accepting its old positional fields.
    result = RetrievalResult(RetrievalStatus.OK, __import__("lms.core.retrieval", fromlist=["RetrievalMode"]).RetrievalMode.KEYWORD_ONLY, "v1")

    assert result.reason == "" and result.downgraded is False
