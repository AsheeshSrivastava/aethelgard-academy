"""Choose and load the retriever at app startup, never at import (SPEC-21 R5 to R8, ADR-0035 2.3 and 2.7)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Mapping, Optional

from lms.adapters.ai.rag.keyword_retriever import DEFAULT_MIN_MATCHED_TERMS, KeywordRetriever
from lms.core.retrieval import IRetriever, RetrievalMode

logger = logging.getLogger(__name__)

MODE_ENV = "LMS_RETRIEVAL_MODE"
INDEX_DIR_ENV = "LMS_INDEX_DIR"
DEFAULT_INDEX_DIR = "data/index"
MIN_TERMS_ENV = "LMS_MIN_MATCHED_TERMS"


class RetrievalConfigError(Exception):
    """The retrieval settings are wrong. Startup stops; the message says what to change."""


def configured_mode(environ: Optional[Mapping[str, str]] = None) -> RetrievalMode:
    """The mode named by LMS_RETRIEVAL_MODE. Unknown, or not built yet, fails loudly (R6)."""
    env = os.environ if environ is None else environ
    raw = (env.get(MODE_ENV) or RetrievalMode.KEYWORD_ONLY.value).strip()
    try:
        mode = RetrievalMode(raw)
    except ValueError:
        choices = ", ".join(m.value for m in RetrievalMode)
        raise RetrievalConfigError(f"Unknown {MODE_ENV} '{raw}'. Choose one of: {choices}.") from None
    if mode is RetrievalMode.HYBRID_RERANK:
        raise RetrievalConfigError(
            f"{MODE_ENV}=hybrid_rerank is not available in this build. Use {RetrievalMode.KEYWORD_ONLY.value}."
        )
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


def build_retriever(environ: Optional[Mapping[str, str]] = None) -> IRetriever:
    """Load the index once and say what was loaded. A missing folder gives NO_INDEX, not a crash (R7)."""
    env = os.environ if environ is None else environ
    mode = configured_mode(env)
    min_terms = configured_min_terms(env)
    index_dir = Path(env.get(INDEX_DIR_ENV) or DEFAULT_INDEX_DIR)
    retriever = KeywordRetriever.from_index_dir(index_dir, min_matched_terms=min_terms)
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
            "Retrieval ready: mode=%s index_version=%s sources=%d index_dir=%s min_matched_terms=%d",
            mode.value,
            manifest.index_version,
            len(manifest.sources),
            index_dir,
            min_terms,
        )
    return retriever
