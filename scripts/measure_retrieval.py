"""Local retrieval measurement on the SPEC-20 question set. Not run in CI.

    uv run --no-sync python scripts/measure_retrieval.py

Scores, offline and without models:
  current        the LMS keyword search as it is today (what the CI gate guards)
  keyword-tuned  the same BM25 index, query with stop words dropped, plus a score floor
                 so "not found" can fire. The floor is swept; pick one from the table.
The ragcore L and HR modes (ADR-0035 2.6) are a separate step: they need an index built
by ragcore from tests/fixtures/retrieval/docs and, for HR, the embedder and reranker.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import retrieval_quality as rq  # noqa: E402

STOP_WORDS = frozenset(
    "a an and are as at be but by can do does for from how i if in into is it its me my "
    "no not of on or so than that the then there this to up was what when where which who "
    "why will with would you your should could get got have has had am we they them our "
    "just also any some very".split()
)
WORD = re.compile(r"[A-Za-z0-9_\-\.:]+")


def drop_stop_words(query: str) -> str:
    kept = [w for w in WORD.findall(query) if w.lower() not in STOP_WORDS]
    return " ".join(kept) or query


def main() -> int:
    questions = rq.load_questions()
    answerable = [q for q in questions if q["expected_source"]]
    unanswerable = [q for q in questions if not q["expected_source"]]
    retriever = rq.build_keyword_retriever()

    start = time.perf_counter()
    current = rq.score(lambda q: [p.source_id for p in retriever.retrieve(q, 3)], questions)
    ms = (time.perf_counter() - start) / len(answerable) * 1000
    print(f"set {len(questions)} questions: {len(answerable)} answerable, {len(unanswerable)} no-answer")
    print(f"current        first {current.first_hit}/{current.answerable}  top3 {current.top3}/{current.answerable}  ({ms:.1f} ms/question)")

    # keyword-tuned: best BM25 score per source, query without stop words
    index = retriever.bm25
    passages = retriever.passages

    def ranked(query: str) -> list[tuple[str, float]]:
        best: dict[str, float] = {}
        for pid, s in index.search(drop_stop_words(query), top_k=200):
            src = passages[pid].source_id
            best[src] = max(best.get(src, 0.0), s)
        return sorted(best.items(), key=lambda kv: kv[1], reverse=True)

    plain = rq.score(lambda q: [s for s, _ in ranked(q)], questions)
    print(f"stop words out first {plain.first_hit}/{plain.answerable}  top3 {plain.top3}/{plain.answerable}")

    print("\nscore floor sweep (top hit must reach the floor, else 'not found')")
    print("floor  first  top3  answerable-lost  no-answer-correct")
    for floor in (0, 2, 3, 4, 5, 6, 7, 8, 10):
        def search(q: str, floor=floor) -> list[str]:
            r = ranked(q)
            return [s for s, _ in r] if r and r[0][1] >= floor else []
        sc = rq.score(search, questions)
        lost = sum(1 for q in answerable if not search(q["question"]))
        ok = sum(1 for q in unanswerable if not search(q["question"]))
        print(f"{floor:>5}  {sc.first_hit:>5}  {sc.top3:>4}  {lost:>15}  {ok:>3}/{len(unanswerable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
