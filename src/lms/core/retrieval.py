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


@dataclass(frozen=True)
class RetrievalTrace:
    """What one answer's retrieval did; written to the interaction log (ADR-0022)."""

    index_version: str
    mode: str
    status: str
    latency_ms: int

    def as_log_fields(self) -> Dict[str, object]:
        return {
            "index_version": self.index_version,
            "retrieval_mode": self.mode,
            "retrieval_status": self.status,
            "latency_ms": self.latency_ms,
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


def clamp_top_k(top_k: int) -> int:
    return max(MIN_TOP_K, min(MAX_TOP_K, int(top_k)))


def compute_index_version(sources: Iterable[SourceRecord], loader_version: str) -> str:
    """sha256 over the sorted (source_id, raw_sha256) pairs plus the loader version (R4)."""
    digest = hashlib.sha256()
    for source_id, raw_sha256 in sorted((s.source_id, s.raw_sha256) for s in sources):
        digest.update(f"{source_id}\0{raw_sha256}\n".encode("utf-8"))
    digest.update(f"loader\0{loader_version}".encode("utf-8"))
    return digest.hexdigest()
