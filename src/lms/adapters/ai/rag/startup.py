"""Choose and load the retriever at app startup, never at import (SPEC-21 R5 to R8, ADR-0035 2.3 and 2.7)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Mapping, Optional

from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
from lms.core.retrieval import IRetriever, RetrievalMode

logger = logging.getLogger(__name__)

MODE_ENV = "LMS_RETRIEVAL_MODE"
INDEX_DIR_ENV = "LMS_INDEX_DIR"
DEFAULT_INDEX_DIR = "data/index"


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


def build_retriever(environ: Optional[Mapping[str, str]] = None) -> IRetriever:
    """Load the index once and say what was loaded. A missing folder gives NO_INDEX, not a crash (R7)."""
    env = os.environ if environ is None else environ
    mode = configured_mode(env)
    index_dir = Path(env.get(INDEX_DIR_ENV) or DEFAULT_INDEX_DIR)
    retriever = KeywordRetriever.from_index_dir(index_dir)
    manifest = retriever.manifest
    if manifest is None:
        logger.warning(
            "No retrieval index is loaded: %s. AXIS answers will say they are not grounded. (mode=%s)",
            index_dir,
            mode.value,
        )
    else:
        logger.info(
            "Retrieval ready: mode=%s index_version=%s sources=%d index_dir=%s",
            mode.value,
            manifest.index_version,
            len(manifest.sources),
            index_dir,
        )
    return retriever
