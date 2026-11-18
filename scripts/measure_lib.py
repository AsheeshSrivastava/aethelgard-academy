"""Shared pieces of the retrieval measurement scripts (SPEC-25 R2, R3, R4, R6, R8, R11).

Question-set loader, the "is this result right" rule, rank metrics (Hit@K, MRR, nDCG@K, Precision@K),
refusal rates, rule-based failure labels for misses and the review-sheet sample. No model, no network.
Tests: tests/test_gemini_measure_metrics.py, tests/test_gemini_sets_files.py.
"""

from __future__ import annotations

import hashlib
import math
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import yaml

ROOT = Path(__file__).resolve().parent.parent
SETS_DIR = ROOT / "eval" / "gemini-sets"
KS = (1, 3, 5)
KINDS = ("plain", "error", "paraphrase", "pasted")
LABELS = ("wording", "vague chunk", "multi-page", "other")
MIN_PASSAGE_CHARS = 200  # R6.2
MIN_CONTENT_TERMS = 3  # R6.2

_TOKEN = re.compile(r"[A-Za-z0-9_\-\.:]+")  # same split as core.query and the BM25 index


# --- R1, R2: the question files -------------------------------------------------------------------------


def set_version(sets_dir: Path = SETS_DIR) -> str:
    """sha256 of the six files in name order, line endings read as LF (R1)."""
    digest = hashlib.sha256()
    for path in sorted(Path(sets_dir).glob("*.yaml")):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def load_gemini_sets(sets_dir: Path = SETS_DIR) -> Dict[str, dict]:
    """{set name: {"prefix": "<name>/", "questions": [...], "out_of_scope": [...]}} in name order."""
    sets = {}
    for path in sorted(Path(sets_dir).glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        sets[path.stem] = {
            "prefix": path.stem + "/",
            "questions": data["questions"],
            "out_of_scope": data.get("out_of_scope", []),
        }
    return sets


def is_right(source_id: str, prefix: str, expect: Sequence[str]) -> bool:
    """A source is right when it starts with the set's prefix and contains one expected path piece."""
    return source_id.startswith(prefix) and any(piece in source_id for piece in expect)


def flags_for(ranking: Sequence[str], prefix: str, expect: Sequence[str], k: int = 5) -> List[bool]:
    """One flag per rank, exactly k long (shorter rankings are padded with False)."""
    flags = [is_right(s, prefix, expect) for s in list(ranking)[:k]]
    return flags + [False] * (k - len(flags))


def dedupe_files(ranking: Sequence[str]) -> List[str]:
    """Source ids in first-appearance order, each once (the "by file" view of a passage ranking)."""
    seen, out = set(), []
    for s in ranking:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


# --- R3: rank metrics (binary gain) ----------------------------------------------------------------------


def hit_at_k(flags: Sequence[bool], k: int) -> int:
    return int(any(flags[:k]))


def reciprocal_rank(flags: Sequence[bool], limit: int = 5) -> float:
    for rank, ok in enumerate(flags[:limit], start=1):
        if ok:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(flags: Sequence[bool], k: int, n_relevant: int) -> float:
    """DCG of the top k over the best possible DCG; `n_relevant` = matching files that exist in the corpus."""
    if n_relevant <= 0:
        return 0.0
    dcg = sum(1.0 / math.log2(rank + 1) for rank, ok in enumerate(flags[:k], start=1) if ok)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k, n_relevant) + 1))
    return dcg / ideal


def precision_at_k(flags: Sequence[bool], k: int) -> float:
    return sum(flags[:k]) / k


def _mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _summarise(rows: List[dict]) -> dict:
    out: dict = {"n": len(rows)}
    for k in KS:
        out[f"hit@{k}"] = _mean([hit_at_k(r["flags"], k) for r in rows])
    out["mrr"] = _mean([reciprocal_rank(r["flags"]) for r in rows])
    for k in KS:
        out[f"ndcg@{k}"] = _mean([ndcg_at_k(r["flags"], k, r["n_relevant"]) for r in rows])
    multi = [r for r in rows if r["n_expect"] >= 2]  # P@K only for questions with two or more expect pieces
    out["p_n"] = len(multi)
    for k in KS:
        out[f"p@{k}"] = _mean([precision_at_k(r["flags"], k) for r in multi])
    return out


def aggregate(rows: List[dict]) -> dict:
    """rows: {"set", "kind", "flags" (5), "n_expect", "n_relevant"} -> overall, by kind, by set (R3)."""
    present = {r["kind"] for r in rows}
    kinds = [k for k in KINDS if k in present] + sorted(present - set(KINDS))  # the old sets carry kind "old"
    sets = sorted({r["set"] for r in rows})
    return {
        "overall": _summarise(rows),
        "by_kind": {k: _summarise([r for r in rows if r["kind"] == k]) for k in kinds},
        "by_set": {s: _summarise([r for r in rows if r["set"] == s]) for s in sets},
    }


# --- R4: refusal ------------------------------------------------------------------------------------------


def refusal_rates(answerable_statuses: Sequence[str], out_of_scope_statuses: Sequence[str]) -> dict:
    """False refusal = answerable but not_found. Correct refusal = out of scope and not_found."""
    refused = lambda statuses: sum(s == "not_found" for s in statuses)  # noqa: E731
    a, o = len(answerable_statuses), len(out_of_scope_statuses)
    return {
        "answerable_n": a,
        "out_of_scope_n": o,
        "false_refusal": refused(answerable_statuses) / a if a else None,
        "correct_refusal": refused(out_of_scope_statuses) / o if o else None,
    }


# --- R6: failure labels (inferred by rule, not read by a human) -------------------------------------------


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN.findall(text or "")]


def _heading_only(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return bool(lines) and all(ln.lstrip().startswith("#") for ln in lines)


def classify_miss(
    terms: Sequence[str],
    best_passage: str,
    returned: Sequence[str],
    expected_files: Sequence[str],
    expect: Sequence[str],
    prefix: str,
) -> str:
    """One label for a question that missed at K=3, by the fixed order of tests in SPEC-25 R6.

    terms           cleaned query words
    best_passage    text of the expected file's best passage ('' if the file has no matching passage)
    returned        ranked source ids (top 5)
    expected_files  corpus files that count as right for this question
    """
    from lms.core.query import FUNCTION_WORDS  # the same function-word list as the query cleanup

    # 1. wording: fewer than half of the cleaned query terms occur in the best passage
    passage_tokens = set(_tokens(best_passage))
    present = sum(1 for t in terms if t.lower() in passage_tokens)
    if present * 2 < len(terms):
        return "wording"
    # 2. vague chunk: under 200 characters, only headings, or under 3 distinct content terms
    content = {t for t in passage_tokens if t not in FUNCTION_WORDS}
    if len(best_passage) < MIN_PASSAGE_CHARS or _heading_only(best_passage) or len(content) < MIN_CONTENT_TERMS:
        return "vague chunk"
    # 3. multi-page: first result is a sibling of the expected file, or another expected piece shows up at rank 4-5
    if returned:
        first = returned[0]
        dirs = {e.rsplit("/", 1)[0] for e in expected_files if "/" in e}
        if first not in expected_files and "/" in first and first.rsplit("/", 1)[0] in dirs:
            return "multi-page"
    if len(expect) >= 2 and any(is_right(s, prefix, expect) for s in list(returned)[3:5]):
        return "multi-page"
    return "other"


# --- R8: review sample ------------------------------------------------------------------------------------


def review_sample(sets: Dict[str, dict], seed: int = 25) -> List[dict]:
    """Four questions per set, one of each kind, fixed by the seed (R8)."""
    rng = random.Random(seed)
    sample = []
    for name in sorted(sets):
        for kind in KINDS:
            pool = [q for q in sets[name]["questions"] if q["kind"] == kind]
            q = pool[rng.randrange(len(pool))]
            sample.append({"set": name, "kind": kind, "q": q["q"], "expect": list(q["expect"])})
    return sample
