"""Hybrid Reranked Retriever (HR) coordinating BM25, Dense Embeddings, RRF, and Cross-Encoder Reranking.

Governed by:
- ADR-0011: RAG Chunking, Hybrid Retrieval, and Cross-Encoder Reranking
- SPEC-09: RAG Indexing & Hybrid Reranked Retriever
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Set, Tuple

from lms.adapters.ai.rag.bm25 import InvertedBM25Index
from lms.adapters.ai.rag.chunker import HeadingSentenceSplitter
from lms.adapters.ai.rag.fusion import reciprocal_rank_fusion
from lms.core.rag_contracts import Passage, Source, Span, make_passages


class HybridRerankedRetriever:
    """Production-grade hybrid retriever combining sparse BM25, dense embeddings,
    Reciprocal Rank Fusion, and cross-encoder reranking with 1-per-source deduplication.
    """

    def __init__(
        self,
        splitter: Optional[HeadingSentenceSplitter] = None,
        embedder: Optional[Callable[[str], List[float]]] = None,
        reranker: Optional[Callable[[str, List[str]], List[float]]] = None,
        chunker_version: str = "llamaindex-sentence-v1",
    ) -> None:
        self.splitter = splitter or HeadingSentenceSplitter()
        self.embedder = embedder
        self.reranker = reranker
        self.chunker_version = chunker_version

        self.bm25 = InvertedBM25Index()
        self.passages: Dict[str, Passage] = {}
        self.sources: Dict[str, Source] = {}
        self.dense_vectors: Dict[str, List[float]] = {}

    def index_source(self, source: Source, spans: Optional[List[Span]] = None) -> List[Passage]:
        """Indexes all passages of a source into lexical and dense representations."""
        self.sources[source.source_id] = source
        if spans is None:
            spans = self.splitter.split(source.text)

        passages = make_passages(source, spans, chunker_version=self.chunker_version)
        for p in passages:
            self.passages[p.passage_id] = p
            self.bm25.add(p.passage_id, p.text, p.headings)

            if self.embedder is not None:
                self.dense_vectors[p.passage_id] = self.embedder(p.text)

        return passages

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot / (norm1 * norm2)

    def _dense_search(self, query: str, top_k: int = 200) -> List[str]:
        if not self.passages:
            return []

        if self.embedder is not None and self.dense_vectors:
            q_vec = self.embedder(query)
            scores = [
                (pid, self._cosine_similarity(q_vec, vec))
                for pid, vec in self.dense_vectors.items()
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            return [pid for pid, _ in scores[:top_k]]

        # Mock / Fallback Dense Search (Token Jaccard similarity for offline testability)
        q_tokens = set(query.lower().split())
        scored: List[Tuple[str, float]] = []
        for pid, p in self.passages.items():
            p_tokens = set(p.text.lower().split())
            if not p_tokens or not q_tokens:
                continue
            inter = len(q_tokens & p_tokens)
            score = inter / float(len(q_tokens | p_tokens))
            if score > 0:
                scored.append((pid, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored[:top_k]]

    def retrieve(self, query: str, top_k: int = 3) -> List[Passage]:
        """Executes Hybrid (Dense + BM25) -> RRF (k=60) -> Rerank -> Source Dedup."""
        if not self.passages:
            return []

        # 1. Lexical BM25 (top 200)
        lexical_hits = self.bm25.search(query, top_k=200)
        lexical_ranks = [pid for pid, _ in lexical_hits]

        # 2. Dense Embeddings (top 200)
        dense_ranks = self._dense_search(query, top_k=200)

        # 3. Reciprocal Rank Fusion (k=60, top 30)
        fused = reciprocal_rank_fusion(dense_ranks, lexical_ranks, k=60, top_n=30)
        candidate_ids = [pid for pid, _ in fused]

        if not candidate_ids:
            # Fallback to any remaining lexical or all passages
            candidate_ids = list(self.passages.keys())[:30]

        # 4. Cross-Encoder Reranking
        scored_candidates: List[Tuple[str, float]] = []
        if self.reranker is not None:
            candidate_texts = [self.passages[pid].text for pid in candidate_ids]
            reranker_scores = self.reranker(query, candidate_texts)
            scored_candidates = list(zip(candidate_ids, reranker_scores))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
        else:
            # Preserve RRF score order, with lexical boost for exact token matches
            q_lower = query.lower()
            for pid, score in fused:
                p_text = self.passages[pid].text.lower()
                bonus = 1.0 if any(word in p_text for word in q_lower.split()) else 0.0
                scored_candidates.append((pid, score + bonus))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 5. Source File Deduplication (1 passage per source file)
        deduped: List[Passage] = []
        seen_sources: Set[str] = set()

        for pid, _score in scored_candidates:
            passage = self.passages.get(pid)
            if passage is None:
                continue
            if passage.source_id not in seen_sources:
                seen_sources.add(passage.source_id)
                deduped.append(passage)
                if len(deduped) == top_k:
                    break

        return deduped
