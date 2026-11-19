"""Choose and load the retriever at app startup, never at import (SPEC-21 R5 to R8, ADR-0035 2.3 and 2.7)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Mapping, Optional

from lms.adapters.ai.rag.keyword_retriever import (
    DEFAULT_MIN_MATCHED_TERMS,
    DEFAULT_PASSAGES_PER_SOURCE,
    KeywordRetriever,
)
from lms.adapters.ai.rag.ragcore_retriever import (
    DEFAULT_CONCURRENCY,
    DEFAULT_TIMEOUT_S,
    DowngradedRetriever,
    open_ragcore_retriever,
)
from lms.core.retrieval import IRetriever, RetrievalMode
import math

logger = logging.getLogger(__name__)

MODE_ENV = "LMS_RETRIEVAL_MODE"
INDEX_DIR_ENV = "LMS_INDEX_DIR"
DEFAULT_INDEX_DIR = "data/index"
MIN_TERMS_ENV = "LMS_MIN_MATCHED_TERMS"
PASSAGES_PER_SOURCE_ENV = "LMS_PASSAGES_PER_SOURCE"
TIMEOUT_ENV = "LMS_RETRIEVAL_TIMEOUT_S"
CONCURRENCY_ENV = "LMS_RERANK_CONCURRENCY"
HR_MIN_SCORE_ENV = "LMS_HR_MIN_SCORE"
RAGCORE_INDEX_ENV = "LMS_RAGCORE_INDEX"
DEFAULT_RAGCORE_INDEX = "data/ragcore/index.db"
EMBEDDER_ENV = "LMS_EMBEDDER"
RERANKER_ENV = "LMS_RERANKER"
DEFAULT_EMBEDDER = "jina-v2-base-en"
DEFAULT_RERANKER = "bge-reranker-v2-m3"


class RetrievalConfigError(Exception):
    """The retrieval settings are wrong. Startup stops; the message says what to change."""


def configured_mode(environ: Optional[Mapping[str, str]] = None) -> RetrievalMode:
    """The mode named by LMS_RETRIEVAL_MODE. An unknown value fails loudly (SPEC-21 R6, SPEC-27 R4)."""
    env = os.environ if environ is None else environ
    raw = (env.get(MODE_ENV) or RetrievalMode.KEYWORD_ONLY.value).strip()
    try:
        mode = RetrievalMode(raw)
    except ValueError:
        choices = ", ".join(m.value for m in RetrievalMode)
        raise RetrievalConfigError(f"Unknown {MODE_ENV} '{raw}'. Choose one of: {choices}.") from None
    return mode


def configured_min_terms(environ: Optional[Mapping[str, str]] = None) -> int:
    """LMS_MIN_MATCHED_TERMS: whole number 1 to 10; unset or empty means the default (SPEC-23 R7)."""
    env = os.environ if environ is None else environ
    raw = (env.get(MIN_TERMS_ENV) or "").strip()
    if not raw:
        return DEFAULT_MIN_MATCHED_TERMS
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if not 1 <= value <= 10:
        raise RetrievalConfigError(f"{MIN_TERMS_ENV}='{raw}' is not allowed. Use a whole number from 1 to 10.")
    return value


def configured_passages_per_source(environ: Optional[Mapping[str, str]] = None) -> int:
    """LMS_PASSAGES_PER_SOURCE: whole number 1 to 5; unset or empty means 1 (SPEC-25 R7)."""
    env = os.environ if environ is None else environ
    raw = (env.get(PASSAGES_PER_SOURCE_ENV) or "").strip()
    if not raw:
        return DEFAULT_PASSAGES_PER_SOURCE
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if not 1 <= value <= 5:
        raise RetrievalConfigError(f"{PASSAGES_PER_SOURCE_ENV}='{raw}' is not allowed. Use a whole number from 1 to 5.")
    return value


def configured_timeout_s(environ: Optional[Mapping[str, str]] = None) -> float:
    """LMS_RETRIEVAL_TIMEOUT_S: seconds per hybrid search, above 0 and at most 300; unset means 10 (SPEC-27 D3)."""
    env = os.environ if environ is None else environ
    raw = (env.get(TIMEOUT_ENV) or "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_S
    try:
        value = float(raw)
    except ValueError:
        value = 0.0
    if not (0 < value <= 300) or math.isnan(value):
        raise RetrievalConfigError(f"{TIMEOUT_ENV}='{raw}' is not allowed. Use a number of seconds above 0 and up to 300.")
    return value


def configured_rerank_concurrency(environ: Optional[Mapping[str, str]] = None) -> int:
    """LMS_RERANK_CONCURRENCY: whole number 1 to 8; unset means 2 (SPEC-27 D3)."""
    env = os.environ if environ is None else environ
    raw = (env.get(CONCURRENCY_ENV) or "").strip()
    if not raw:
        return DEFAULT_CONCURRENCY
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if not 1 <= value <= 8:
        raise RetrievalConfigError(f"{CONCURRENCY_ENV}='{raw}' is not allowed. Use a whole number from 1 to 8.")
    return value


def configured_hr_min_score(environ: Optional[Mapping[str, str]] = None) -> Optional[float]:
    """LMS_HR_MIN_SCORE: floor on the top reranker score; unset or empty means no floor (SPEC-27 R9)."""
    env = os.environ if environ is None else environ
    raw = (env.get(HR_MIN_SCORE_ENV) or "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        value = math.nan
    if not math.isfinite(value):
        raise RetrievalConfigError(f"{HR_MIN_SCORE_ENV}='{raw}' is not allowed. Use a number, or leave it empty for no floor.")
    return value


def build_retriever(environ: Optional[Mapping[str, str]] = None) -> IRetriever:
    """Load the index once and say what was loaded. A missing folder gives NO_INDEX, not a crash (R7)."""
    env = os.environ if environ is None else environ
    mode = configured_mode(env)
    min_terms = configured_min_terms(env)
    per_source = configured_passages_per_source(env)
    index_dir = Path(env.get(INDEX_DIR_ENV) or DEFAULT_INDEX_DIR)
    retriever = KeywordRetriever.from_index_dir(index_dir, min_matched_terms=min_terms, passages_per_source=per_source)
    manifest = retriever.manifest
    if manifest is None:
        logger.warning(
            "No retrieval index is loaded: %s (%s). AXIS answers will say they are not grounded. (mode=%s)",
            index_dir,
            retriever.no_index_reason,
            mode.value,
        )
    else:
        logger.info(
            "Retrieval ready: mode=%s index_version=%s sources=%d index_dir=%s min_matched_terms=%d passages_per_source=%d",
            mode.value,
            manifest.index_version,
            len(manifest.sources),
            index_dir,
            min_terms,
            per_source,
        )
    if mode is not RetrievalMode.HYBRID_RERANK:
        return retriever
    timeout_s = configured_timeout_s(env)
    concurrency = configured_rerank_concurrency(env)
    min_score = configured_hr_min_score(env)
    ragcore_index = Path(env.get(RAGCORE_INDEX_ENV) or DEFAULT_RAGCORE_INDEX)
    if manifest is None:
        return retriever  # no keyword index to fall back on: the plain NO_INDEX answer is the honest one
    hybrid = open_ragcore_retriever(
        ragcore_index, retriever,
        embedder_id=env.get(EMBEDDER_ENV) or DEFAULT_EMBEDDER,
        reranker_id=env.get(RERANKER_ENV) or DEFAULT_RERANKER,
        timeout_s=timeout_s, concurrency=concurrency, min_matched_terms=min_terms,
        min_score=min_score, passages_per_source=per_source,
    )
    if isinstance(hybrid, DowngradedRetriever):
        logger.warning("Retrieval mode: keyword_only (labelled downgrade) because hybrid_rerank failed: %s", hybrid.reason)
    else:
        logger.info("Retrieval mode: hybrid_rerank index=%s timeout_s=%g concurrency=%d min_score=%s",
                    ragcore_index, timeout_s, concurrency, min_score)
    return hybrid
