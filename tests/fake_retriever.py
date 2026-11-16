"""A fake retriever for tests (SPEC-21 section 1). It speaks the IRetriever port and nothing else."""

from __future__ import annotations

from typing import Tuple

from lms.core.retrieval import (
    IRetriever,
    RetrievalMode,
    RetrievalResult,
    RetrievalStatus,
    RetrievedPassage,
    clamp_top_k,
)


class FakeRetriever(IRetriever):
    """Returns what it was given. For `ok` it applies the same top_k and prefix rules as a real adapter."""

    def __init__(
        self,
        passages: Tuple[RetrievedPassage, ...] = (),
        status: RetrievalStatus = RetrievalStatus.OK,
        mode: RetrievalMode = RetrievalMode.KEYWORD_ONLY,
        index_version: str = "fake-index-1",
    ) -> None:
        self.passages = tuple(passages)
        self.status = status
        self.mode = mode
        self.index_version = index_version
        self.calls: list = []

    def search(self, query: str, *, top_k: int = 3, source_prefixes: Tuple[str, ...] = ()) -> RetrievalResult:
        self.calls.append((query, top_k, source_prefixes))
        if self.status is not RetrievalStatus.OK:
            version = "" if self.status is RetrievalStatus.NO_INDEX else self.index_version
            return RetrievalResult(self.status, self.mode, version, (), message=f"fake {self.status.value}")
        chosen = [
            p for p in self.passages
            if not source_prefixes or any(p.source_id.startswith(x) for x in source_prefixes)
        ]
        chosen = chosen[: clamp_top_k(top_k)]
        if not chosen:
            return RetrievalResult(RetrievalStatus.NOT_FOUND, self.mode, self.index_version, (), "fake empty")
        return RetrievalResult(RetrievalStatus.OK, self.mode, self.index_version, tuple(chosen), "")


def passage(source_id: str, text: str = "some text", score: float = 1.0, pid: str = "") -> RetrievedPassage:
    return RetrievedPassage(
        passage_id=pid or f"{source_id}#1",
        source_id=source_id,
        source_name=source_id,
        text=text,
        score=score,
    )
