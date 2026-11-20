"""The rag-core adapter (SPEC-27, ADR-0035 2.1 to 2.9): mode hybrid_rerank behind the IRetriever port.

This is the only LMS file that talks to `ragcore`, and it imports it inside functions, so importing
`lms` never loads torch or ragcore. The engine is anything with `search(query, k, max_per_file)`
returning objects with passage_id, source_id, text and score (ragcore.Retriever in production, a
fake in tests). When the ranking models fail, are missing or are too slow, the answer comes from the
keyword adapter and says so (`downgraded=True`, ADR-0035 2.7).
"""

from __future__ import annotations

import hashlib
import logging
import math
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import replace
from typing import Any, Iterable, Mapping, Optional, Tuple

from lms.core.query import clean_query_words, count_matched_terms
from lms.core.retrieval import (
    IRetriever,
    RetrievalMode,
    RetrievalResult,
    RetrievalStatus,
    RetrievedPassage,
    clamp_top_k,
)

logger = logging.getLogger(__name__)

RERANK_DEPTH = 30  # ragcore reranks the first 30; a prefix filter after ranking needs all of them
DEFAULT_TIMEOUT_S = 10.0
DEFAULT_CONCURRENCY = 2

_SETUP_FIELDS = (
    "embedder_id", "embedder_revision", "chunker", "chunker_version",
    "chunk_config", "llama_index_version", "reranker_id", "reranker_revision",
)


def _source_name(source_id: str) -> str:
    return source_id.rsplit("/", 1)[-1]


def compute_ragcore_index_version(setup: Mapping[str, str], sources: Iterable[Tuple[str, str]]) -> str:
    """sha256 over the index setup (model pins, chunker) and the sorted (source_id, content_sha256) pairs (R8)."""
    digest = hashlib.sha256()
    for name in _SETUP_FIELDS:
        digest.update(f"{name}\0{setup.get(name, '')}\n".encode("utf-8"))
    for source_id, content_sha256 in sorted(sources):
        digest.update(f"{source_id}\0{content_sha256}\n".encode("utf-8"))
    return digest.hexdigest()


class DowngradedRetriever(IRetriever):
    """Keyword search wearing the "Keyword search only" label: used when the ranking models cannot be used."""

    def __init__(self, fallback: IRetriever, reason: str) -> None:
        self._fallback = fallback
        self.reason = reason

    def index_status(self) -> RetrievalStatus:
        return self._fallback.index_status()

    def search(self, query: str, *, top_k: int = 3, source_prefixes: Tuple[str, ...] = ()) -> RetrievalResult:
        return replace(self._fallback.search(query, top_k=top_k, source_prefixes=source_prefixes), downgraded=True)


class RagcoreRetriever(IRetriever):
    """mode = hybrid_rerank. Build it with `open_ragcore_retriever` (the app) or directly (tests)."""

    mode = RetrievalMode.HYBRID_RERANK

    def __init__(
        self,
        engine: Any,
        index_version: str,
        fallback: IRetriever,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        concurrency: int = DEFAULT_CONCURRENCY,
        min_matched_terms: int = 3,
        min_score: Optional[float] = None,
        passages_per_source: int = 1,
    ) -> None:
        if concurrency < 1 or timeout_s <= 0 or passages_per_source < 1:
            raise ValueError("concurrency, timeout and passages_per_source must be positive")
        self._engine = engine
        self._index_version = index_version
        self._fallback = fallback
        self._timeout_s = timeout_s
        self._min_terms = min_matched_terms  # 0 switches the term rule off (floor-only variant)
        self._min_score = min_score
        self._per_source = passages_per_source
        self._slots = threading.BoundedSemaphore(concurrency)
        self._pool = ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="ragcore-search")
        self._concurrency = concurrency
        self._timed_out: list = []  # searches the caller gave up on that are still running
        self._lock = threading.Lock()

    def index_status(self) -> RetrievalStatus:
        return RetrievalStatus.OK

    def _result(self, status: RetrievalStatus, passages: Tuple[RetrievedPassage, ...] = (), message: str = "",
                matched: int = 0, total: int = 0) -> RetrievalResult:
        return RetrievalResult(status, self.mode, self._index_version, passages, message, matched, total)

    def _run(self, query: str, k: int):
        try:
            return self._engine.search(query, k=k, max_per_file=self._per_source)
        finally:
            self._slots.release()  # held until the engine really finishes, even after a timeout

    def _downgrade(self, query: str, top_k: int, prefixes: Tuple[str, ...], log_text: str, reason: str) -> RetrievalResult:
        """`log_text` is prose for the log line; `reason` is the fixed code the trace records (SPEC-29 R17)."""
        logger.warning("Hybrid search not used for this answer (%s); answering from keyword search.", log_text)
        return replace(self._fallback.search(query, top_k=top_k, source_prefixes=prefixes), downgraded=True, reason=reason)

    def search(self, query: str, *, top_k: int = 3, source_prefixes: Tuple[str, ...] = ()) -> RetrievalResult:
        words = clean_query_words(query or "")
        if not words:
            return self._result(RetrievalStatus.NOT_FOUND,
                                message="empty query" if not (query or "").strip() else "no searchable words")
        k = clamp_top_k(top_k)
        prefixes = tuple(p for p in source_prefixes if p)
        with self._lock:
            self._timed_out = [f for f in self._timed_out if not f.done()]
            stalled = len(self._timed_out) >= self._concurrency
        if stalled:  # every slot is held by a search that already timed out: the models are stuck, not busy
            return self._downgrade(query, top_k, prefixes, "the ranking models are stalled", "stalled")
        if not self._slots.acquire(blocking=False):
            return replace(self._result(RetrievalStatus.UNAVAILABLE, message="busy: too many searches at once"), reason="busy")
        try:
            future = self._pool.submit(self._run, query, RERANK_DEPTH if prefixes else k)
        except Exception as exc:  # pool shut down: give the slot back
            self._slots.release()
            return self._downgrade(query, top_k, prefixes, f"could not start ({type(exc).__name__})", "start_failed")
        try:
            hits = future.result(timeout=self._timeout_s)
        except FutureTimeout:
            with self._lock:
                self._timed_out.append(future)
            return self._downgrade(query, top_k, prefixes, f"timed out after {self._timeout_s:g}s", "timeout")
        except Exception as exc:
            return self._downgrade(query, top_k, prefixes, f"model fault ({type(exc).__name__})", "model_fault")

        if prefixes:
            hits = [h for h in hits if h.source_id.startswith(prefixes)]
        hits = sorted(hits, key=lambda h: (-h.score, h.source_id, h.passage_id))
        if not hits:
            return self._result(RetrievalStatus.NOT_FOUND, message="nothing matched", total=len(words))
        best = hits[0]
        matched = count_matched_terms(words, best.text)
        total = len({w.lower() for w in words})
        needed = min(self._min_terms, total)
        if self._min_score is not None and best.score < self._min_score:
            return self._result(RetrievalStatus.NOT_FOUND, matched=matched, total=total,
                                message=f"top score {best.score:.2f} is below the floor {self._min_score:g}")
        if matched < needed:
            return self._result(
                RetrievalStatus.NOT_FOUND, matched=matched, total=total,
                message=f"too few query terms found: terms_matched={matched} terms_total={total} needed={needed}",
            )
        passages = tuple(
            RetrievedPassage(h.passage_id, h.source_id, _source_name(h.source_id), h.text, float(h.score))
            for h in hits[:k]
        )
        return self._result(RetrievalStatus.OK, passages, matched=matched, total=total)


def _self_check(engine: Any, timeout_s: float) -> None:
    """One real search warms the embedder and reranker and proves both answer. Raises on any fault or timeout."""
    pool = ThreadPoolExecutor(max_workers=1)
    try:  # no `with`: leaving it would wait for a stuck search and the timeout would never reach the caller
        results = pool.submit(engine.search, "python function", 1, None).result(timeout=timeout_s * 6)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    for r in results:
        if not math.isfinite(float(r.score)):
            raise ValueError("reranker returned a non-finite score")


def open_ragcore_retriever(
    index_path: Any,
    fallback: IRetriever,
    *,
    embedder_id: str,
    reranker_id: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    concurrency: int = DEFAULT_CONCURRENCY,
    min_matched_terms: int = 3,
    min_score: Optional[float] = None,
    passages_per_source: int = 1,
) -> IRetriever:
    """Open the rag-core index and models. Any failure returns the labelled keyword downgrade (R3, R4), never raises."""
    try:
        from ragcore import Retriever, load_models  # needs the `retrieval` extra (ragcore[embed])

        embedder, reranker, setup = load_models(embedder_id, reranker_id)
        engine = Retriever.open(index_path, setup, embedder=embedder, reranker=reranker, variant="HR")
        version = compute_ragcore_index_version(
            {name: getattr(setup, name, "") for name in _SETUP_FIELDS},
            [(s.source_id, s.content_sha256) for s in engine.store.sources().values()],
        )
        _self_check(engine, timeout_s)
    except Exception as exc:
        logger.error("Hybrid search is not available (%s: %s). Running keyword search only, labelled.",
                     type(exc).__name__, exc)
        return DowngradedRetriever(fallback, f"{type(exc).__name__}")
    return RagcoreRetriever(
        engine, version, fallback, timeout_s=timeout_s, concurrency=concurrency,
        min_matched_terms=min_matched_terms, min_score=min_score, passages_per_source=passages_per_source,
    )
