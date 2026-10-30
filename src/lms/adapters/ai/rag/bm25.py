"""In-memory BM25 Inverted Index for fast, zero-dependency lexical search.

Weights heading paths alongside passage text to match exact keywords,
function names, exception types, and CLI flags.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Set, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\.:]+")


class InvertedBM25Index:
    """Zero-dependency BM25 index over passages and heading paths."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.doc_count = 0
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length = 0.0
        self.inverted_index: Dict[str, Dict[str, int]] = {}  # term -> {doc_id: freq}
        self.doc_headings: Dict[str, List[str]] = {}

    def _tokenize(self, text: str) -> List[str]:
        return [t.lower() for t in TOKEN_RE.findall(text)]

    def add(self, passage_id: str, text: str, headings: List[str] | Tuple[str, ...]) -> None:
        """Indexes a passage, repeating headings with higher weight."""
        heading_text = " ".join(headings)
        # Give heading terms a 2x boost in the lexical bag of words
        full_text = f"{heading_text} {heading_text} {text}"
        tokens = self._tokenize(full_text)
        if not tokens:
            return

        doc_len = len(tokens)
        self.doc_lengths[passage_id] = doc_len
        self.doc_headings[passage_id] = list(headings)
        self.doc_count += 1

        total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / self.doc_count if self.doc_count else 0.0

        counts: Dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1

        for term, freq in counts.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = {}
            self.inverted_index[term][passage_id] = freq

    def search(self, query: str, top_k: int = 200) -> List[Tuple[str, float]]:
        """Scores all matching documents using standard BM25 formula."""
        query_terms = self._tokenize(query)
        if not query_terms or self.doc_count == 0:
            return []

        scores: Dict[str, float] = {}

        for term in set(query_terms):
            if term not in self.inverted_index:
                continue

            posting = self.inverted_index[term]
            df = len(posting)
            # Standard Lucene/Robertson IDF
            idf = math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))

            for doc_id, freq in posting.items():
                doc_len = self.doc_lengths.get(doc_id, self.avg_doc_length)
                denom = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_length or 1.0)))
                term_score = idf * (freq * (self.k1 + 1.0)) / (denom or 1.0)
                scores[doc_id] = scores.get(doc_id, 0.0) + term_score

        sorted_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_results[:top_k]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes index state for fast disk persistence."""
        return {
            "k1": self.k1,
            "b": self.b,
            "doc_count": self.doc_count,
            "doc_lengths": self.doc_lengths,
            "avg_doc_length": self.avg_doc_length,
            "doc_headings": self.doc_headings,
            "inverted_index": self.inverted_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InvertedBM25Index:
        """Reconstitutes index from a serialized dictionary."""
        idx = cls(k1=data.get("k1", 1.5), b=data.get("b", 0.75))
        idx.doc_count = data.get("doc_count", 0)
        idx.doc_lengths = data.get("doc_lengths", {})
        idx.avg_doc_length = data.get("avg_doc_length", 0.0)
        idx.doc_headings = data.get("doc_headings", {})
        idx.inverted_index = data.get("inverted_index", {})
        return idx

