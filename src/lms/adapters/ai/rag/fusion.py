"""Reciprocal Rank Fusion (RRF) for combining dense vector and sparse lexical ranks.

Governed by:
- ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking
- SPEC-09: RAG Indexing & Hybrid Reranked Retriever
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def reciprocal_rank_fusion(
    dense_ranks: List[str],
    lexical_ranks: List[str],
    k: int = 60,
    top_n: int = 30,
) -> List[Tuple[str, float]]:
    """Merges dense and lexical candidate lists using parameter-free RRF scoring.

    Formula:
        RRF_Score(d) = sum_{list L} 1.0 / (k + rank_L(d))
    where rank_L(d) is 1-based.
    """
    scores: Dict[str, float] = {}

    for rank, doc_id in enumerate(dense_ranks, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    for rank, doc_id in enumerate(lexical_ranks, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Sort descending by score; if tied, sort deterministically by doc_id
    sorted_items = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return sorted_items[:top_n]
