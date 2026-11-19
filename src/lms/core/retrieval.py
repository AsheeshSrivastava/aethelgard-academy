"""The retrieval port and its own result type (SPEC-21, ADR-0035 sections 2.2 and 2.3).

Pure standard library. No adapter type (SQLite, ragcore, BM25 internals) appears here, so an
adapter can be swapped without touching the companions.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Tuple

from lms.core.search_text import DEFAULT_RECIPE, SEARCH_TEXT_VERSION

MIN_TOP_K = 1
MAX_TOP_K = 10


class RetrievalStatus(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    NO_INDEX = "no_index"
    UNAVAILABLE = "unavailable"


class RetrievalMode(str, Enum):
    HYBRID_RERANK = "hybrid_rerank"
    KEYWORD_ONLY = "keyword_only"


@dataclass(frozen=True)
class RetrievedPassage:
    passage_id: str
    source_id: str
    source_name: str  # readable name for the learner
    text: str
    score: float


@dataclass(frozen=True)
class RetrievalResult:
    status: RetrievalStatus
    mode: RetrievalMode
    index_version: str  # empty string when there is no index
    passages: Tuple[RetrievedPassage, ...] = ()  # empty unless status is OK
    message: str = ""  # short, for logs
    terms_matched: int = 0  # query terms found in the best passage (SPEC-23 R6); 0 when not measured
    terms_total: int = 0  # distinct cleaned query terms
    downgraded: bool = False  # ranking models were not used for this answer; shown as "Keyword search only" (SPEC-27 R6)


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    licence: str
    licence_basis: str
    raw_sha256: str


@dataclass(frozen=True)
class IndexManifest:
    index_version: str
    built_at: str
    loader_version: str
    sources: Tuple[SourceRecord, ...]


@dataclass
class RetrievalTrace:
    """What one answer's retrieval did; written to the interaction log (ADR-0022).

    passages_cited is filled in once the reply is checked against the passages (SPEC-22 R8).
    """

    index_version: str
    mode: str
    status: str
    latency_ms: int
    passages_retrieved: int = 0
    passages_cited: int = 0
    terms_matched: int = 0
    terms_total: int = 0
    downgraded: bool = False

    def as_log_fields(self) -> Dict[str, object]:
        return {
            "index_version": self.index_version,
            "retrieval_mode": self.mode,
            "retrieval_status": self.status,
            "latency_ms": self.latency_ms,
            "passages_retrieved": self.passages_retrieved,
            "passages_cited": self.passages_cited,
            "terms_matched": self.terms_matched,
            "terms_total": self.terms_total,
            "downgraded": self.downgraded,
        }


class IRetriever(ABC):
    """Port: search the curriculum index. Never raises for an expected condition (R1)."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        source_prefixes: Tuple[str, ...] = (),
    ) -> RetrievalResult:
        """Missing or unreadable index: NO_INDEX. Adapter fault: UNAVAILABLE. Nothing found: NOT_FOUND."""

    @abstractmethod
    def index_status(self) -> RetrievalStatus:
        """Is the index usable right now? OK, NO_INDEX or UNAVAILABLE. Never searches and never raises (SPEC-24 R8)."""


def clamp_top_k(top_k: int) -> int:
    return max(MIN_TOP_K, min(MAX_TOP_K, int(top_k)))


def compute_index_version(sources: Iterable[SourceRecord], loader_version: str, search_recipe: str = DEFAULT_RECIPE) -> str:
    """sha256 over the sorted (source_id, raw_sha256) pairs plus the loader version (R4).

    A search-text recipe other than "none" is mixed in with SEARCH_TEXT_VERSION (SPEC-26 R6); "none" adds
    nothing, so an index built without search-only text keeps its old version byte for byte.
    """
    digest = hashlib.sha256()
    for source_id, raw_sha256 in sorted((s.source_id, s.raw_sha256) for s in sources):
        digest.update(f"{source_id}\0{raw_sha256}\n".encode("utf-8"))
    digest.update(f"loader\0{loader_version}".encode("utf-8"))
    if search_recipe != DEFAULT_RECIPE:
        digest.update(f"\nsearch_text\0{SEARCH_TEXT_VERSION}\0{search_recipe}".encode("utf-8"))
    return digest.hexdigest()
