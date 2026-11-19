"""Helpers for the retrieval quality set (SPEC-20, ADR-0035 2.6).

Used by the CI gate test and by scripts/measure_retrieval.py. Keyword-only:
no embedder, no reranker, no network.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.core.rag_contracts import Source, normalize_text

SET_DIR = Path(__file__).parent / "fixtures" / "retrieval"


def load_questions(set_dir: Path = SET_DIR) -> List[Dict]:
    data = json.loads((set_dir / "questions.json").read_text(encoding="utf-8"))
    return data["questions"]


def dangling_sources(set_dir: Path = SET_DIR) -> List[str]:
    """Ids of questions whose expected_source is not a doc in set_dir (SPEC-20 3.3)."""
    docs = {p.name for p in (set_dir / "docs").glob("*.md")}
    return [
        q["id"]
        for q in load_questions(set_dir)
        if q["expected_source"] is not None and q["expected_source"] not in docs
    ]


def load_floor(set_dir: Path = SET_DIR) -> Dict:
    return json.loads((set_dir / "floor.json").read_text(encoding="utf-8"))


def build_keyword_retriever(set_dir: Path = SET_DIR, search_recipe: str = "none") -> HybridRerankedRetriever:
    retriever = HybridRerankedRetriever(search_recipe=search_recipe)
    for path in sorted((set_dir / "docs").glob("*.md")):
        text = normalize_text(path.read_text(encoding="utf-8"))
        retriever.index_source(
            Source(
                source_id=path.name,
                version="fixture-1",
                text=text,
                raw_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                loader_version="markdown-fixture-1",
                licence="CC0-1.0",
                licence_basis="declared",
            )
        )
    return retriever


@dataclass(frozen=True)
class Score:
    answerable: int
    first_hit: int
    top3: int

    @property
    def first_hit_rate(self) -> float:
        return self.first_hit / self.answerable

    @property
    def top3_rate(self) -> float:
        return self.top3 / self.answerable


def score(
    search: Callable[[str], List[str]], questions: Optional[List[Dict]] = None
) -> Score:
    """Score a search function (query -> ranked source ids) on the answerable questions."""
    questions = load_questions() if questions is None else questions
    answerable = [q for q in questions if q["expected_source"] is not None]
    first = top3 = 0
    for q in answerable:
        ids = search(q["question"])[:3]
        first += bool(ids) and ids[0] == q["expected_source"]
        top3 += q["expected_source"] in ids
    return Score(len(answerable), first, top3)
