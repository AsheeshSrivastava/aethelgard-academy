"""The existing LMS keyword search, wrapped as the first IRetriever adapter (SPEC-21, mode keyword_only).

The search itself is HybridRerankedRetriever with no embedder and no reranker; this file only
adds the port's rules: statuses instead of exceptions, a capped top_k, a prefix filter, a stable
order, and the manifest with index_version.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.core.retrieval import (
    IndexManifest,
    IRetriever,
    RetrievalMode,
    RetrievalResult,
    RetrievalStatus,
    RetrievedPassage,
    SourceRecord,
    clamp_top_k,
    compute_index_version,
)

logger = logging.getLogger(__name__)

SOURCES_FILE = "sources.jsonl"
PASSAGES_FILE = "passages.jsonl"


def _manifest_from_records(records: List[SourceRecord], loader_versions: List[str], built_at: str) -> IndexManifest:
    loader_version = ",".join(sorted(set(loader_versions)))
    return IndexManifest(
        index_version=compute_index_version(records, loader_version),
        built_at=built_at,
        loader_version=loader_version,
        sources=tuple(sorted(records, key=lambda s: s.source_id)),
    )


def read_manifest(index_dir: Path | str) -> IndexManifest:
    """Build the manifest from sources.jsonl (R4). Raises on a missing or corrupt file."""
    path = Path(index_dir) / SOURCES_FILE
    records: List[SourceRecord] = []
    loaders: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            records.append(
                SourceRecord(
                    source_id=row["source_id"],
                    licence=row["licence"],
                    licence_basis=row["licence_basis"],
                    raw_sha256=row["raw_sha256"],
                )
            )
            loaders.append(row["loader_version"])
    built_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return _manifest_from_records(records, loaders, built_at)


def _source_name(source_id: str) -> str:
    return source_id.rsplit("/", 1)[-1]


class KeywordRetriever(IRetriever):
    """mode = keyword_only. Build it with from_index_dir (the app) or from_hybrid (tests, fixture sets)."""

    mode = RetrievalMode.KEYWORD_ONLY

    def __init__(
        self,
        engine: Optional[HybridRerankedRetriever],
        manifest: Optional[IndexManifest],
        no_index_reason: str = "",
    ) -> None:
        self._engine = engine
        self._manifest = manifest
        self._no_index_reason = no_index_reason

    # --- construction ---------------------------------------------------------------------------

    @classmethod
    def from_index_dir(cls, index_dir: Path | str) -> "KeywordRetriever":
        """Never raises: a missing or unreadable folder gives an adapter that answers NO_INDEX (R1, R7)."""
        folder = Path(index_dir)
        if not (folder / PASSAGES_FILE).exists() or not (folder / SOURCES_FILE).exists():
            return cls(None, None, f"{folder} has no index files")
        try:
            manifest = read_manifest(folder)
            engine = HybridRerankedRetriever.load(folder)
        except Exception as exc:  # corrupt JSON, missing key, unreadable file
            return cls(None, None, f"{folder} could not be read ({type(exc).__name__})")
        if not engine.passages:
            return cls(None, None, f"{folder} holds no passages")
        return cls(engine, manifest)

    @classmethod
    def from_hybrid(cls, engine: HybridRerankedRetriever) -> "KeywordRetriever":
        """Wrap an in-memory engine (the SPEC-20 fixture set, or a test double)."""
        if not engine.passages:
            return cls(None, None, "the engine holds no passages")
        records = [
            SourceRecord(s.source_id, s.licence, s.licence_basis, s.raw_sha256) for s in engine.sources.values()
        ]
        manifest = _manifest_from_records(records, [s.loader_version for s in engine.sources.values()], "in-memory")
        return cls(engine, manifest)

    # --- port -----------------------------------------------------------------------------------

    @property
    def manifest(self) -> Optional[IndexManifest]:
        return self._manifest

    def _result(self, status: RetrievalStatus, passages: Tuple[RetrievedPassage, ...] = (), message: str = "") -> RetrievalResult:
        version = self._manifest.index_version if self._manifest else ""
        return RetrievalResult(status, self.mode, version, passages, message)

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        source_prefixes: Tuple[str, ...] = (),
    ) -> RetrievalResult:
        if self._engine is None or self._manifest is None:
            return self._result(RetrievalStatus.NO_INDEX, message=self._no_index_reason or "no index")
        if not query or not query.strip():
            return self._result(RetrievalStatus.NOT_FOUND, message="empty query")
        k = clamp_top_k(top_k)
        prefixes = tuple(p for p in source_prefixes if p)
        try:
            # With a prefix filter the engine must rank every source first, so the filter cannot starve the result.
            asked = max(len(self._engine.sources), k) if prefixes else k
            scored = self._engine.retrieve_scored(query, top_k=asked)
        except Exception as exc:  # an adapter fault is a status, not a crash
            logger.warning("Keyword retrieval failed: %s", type(exc).__name__)
            return self._result(RetrievalStatus.UNAVAILABLE, message=f"adapter fault ({type(exc).__name__})")
        if prefixes:
            scored = [(p, s) for p, s in scored if p.source_id.startswith(prefixes)]
        # Highest score first; equal scores by source, then position, so the order never wobbles (R3).
        scored.sort(key=lambda item: (-item[1], item[0].source_id, item[0].start))
        passages = tuple(
            RetrievedPassage(
                passage_id=p.passage_id,
                source_id=p.source_id,
                source_name=_source_name(p.source_id),
                text=p.text,
                score=s,
            )
            for p, s in scored[:k]
        )
        if not passages:
            return self._result(RetrievalStatus.NOT_FOUND, message="nothing matched")
        return self._result(RetrievalStatus.OK, passages)
