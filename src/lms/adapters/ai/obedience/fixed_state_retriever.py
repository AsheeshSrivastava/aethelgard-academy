"""A retriever that always answers with one fixed no-source state (SPEC-30 R10).

The obedience eval must test the no-source rules, so every question is asked with no passage. This retriever returns
exactly one of `not_found`, `no_index` or `unavailable` and never a passage. The real `ground_with_trace` path then
builds the real no-source prompt from it, so the model is given exactly what it would be given in production.
"""

from __future__ import annotations

from typing import Tuple

from lms.core.retrieval import IRetriever, RetrievalMode, RetrievalResult, RetrievalStatus

FIXED_STATES = (RetrievalStatus.NOT_FOUND.value, RetrievalStatus.NO_INDEX.value, RetrievalStatus.UNAVAILABLE.value)


class FixedStateRetriever(IRetriever):
    def __init__(self, state: str) -> None:
        if state not in FIXED_STATES:
            raise ValueError(f"state must be one of {', '.join(FIXED_STATES)}")
        self.state = state

    def search(self, query: str, *, top_k: int = 3, source_prefixes: Tuple[str, ...] = ()) -> RetrievalResult:
        # The query is ignored on purpose: the state is fixed and no passage is ever returned.
        return RetrievalResult(
            status=RetrievalStatus(self.state), mode=RetrievalMode.KEYWORD_ONLY, index_version="", passages=(),
            message="fixed state for the obedience eval",
        )

    def index_status(self) -> RetrievalStatus:
        # "No match" is a healthy index that holds nothing relevant; the other two states describe the index itself.
        return RetrievalStatus.OK if self.state == RetrievalStatus.NOT_FOUND.value else RetrievalStatus(self.state)
