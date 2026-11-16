"""Measure query cleanup, "not found" rules and fusion weights on the real LMS corpus (SPEC-23).

Local only, not CI. Offline, no models, no network, no key. Reads:
  data/index/                         the real index (1,371 sources)
  data/gemini-runs/result/*.yaml      six learner-style question sets (git-ignored; validated first)

    uv run --no-sync python scripts/measure_not_found.py > docs/measurements/2026-11-16-not-found-rules.txt

Search used for ranking: the keyword engine's own BM25, best passage per source (what keyword_only returns).
A search is right when a returned source id starts with the set's prefix and contains an `expect` piece.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

from lms.adapters.ai.rag.bm25 import TOKEN_RE  # noqa: E402
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever  # noqa: E402
from lms.core.query import clean_query  # noqa: E402  (the shipped cleanup, so measured = shipped)

SETS_DIR = ROOT / "data" / "gemini-runs" / "result"
TUNE = ("fastapi-docs", "httpx-docs", "pydantic-docs")   # thresholds are picked on these three
CHECK = ("pytest-docs", "python-docs", "uv-docs")        # and read, untouched, on these three

class Ranker:
    """BM25 over the real index, best passage per source, with the signals a rule can use."""

    def __init__(self, engine: HybridRerankedRetriever) -> None:
        self.e, self.bm = engine, engine.bm25

    def terms(self, query: str) -> list[str]:
        return sorted(set(t.lower() for t in TOKEN_RE.findall(query)))

    def idf(self, term: str) -> float:
        df = len(self.bm.inverted_index.get(term, ()))
        return math.log(1.0 + (self.bm.doc_count - df + 0.5) / (df + 0.5))

    def rank(self, query: str):
        """-> rows (source_id, score, matched_terms, matched_idf) best-first, and the query terms."""
        qt = self.terms(query)
        hits = self.bm.search(query, top_k=200)
        best: dict[str, tuple[float, str]] = {}
        for pid, s in hits:
            src = self.e.passages[pid].source_id
            if src not in best or s > best[src][0]:
                best[src] = (s, pid)
        rows = []
        for src, (s, pid) in best.items():
            m = [t for t in qt if pid in self.bm.inverted_index.get(t, ())]
            rows.append((src, s, len(m), sum(self.idf(t) for t in m)))
        rows.sort(key=lambda r: (-r[1], r[0]))
        return rows, qt


def right(src: str, prefix: str, expect: list[str]) -> bool:
    return src.startswith(prefix) and any(p in src for p in expect)


def load_sets():
    sets = {}
    ids = {json.loads(row)["source_id"] for row in (ROOT / "data/index/sources.jsonl").read_text("utf-8").splitlines() if row.strip()}
    for f in sorted(SETS_DIR.glob("*.yaml")):
        d = yaml.safe_load(f.read_text("utf-8"))
        prefix = f.stem + "/"
        for q in d["questions"]:
            assert any(i.startswith(prefix) and any(p in i for p in q["expect"]) for i in ids), (f.name, q["q"][:50])
        sets[f.stem] = d
    return sets


def pct(a: int, b: int) -> str:
    return f"{a:>3}/{b:<3} {a / b:>4.0%}" if b else "  -"


def main() -> int:
    sets = load_sets()
    ranker = Ranker(HybridRerankedRetriever.load(ROOT / "data" / "index"))
    ans = [(s, q) for s, d in sets.items() for q in d["questions"]]
    oos = [(s, q) for s, d in sets.items() for q in d["out_of_scope"]]
    print(f"sets validated: {len(sets)} files, {len(ans)} answerable, {len(oos)} out-of-scope\n")

    # ---- 1. query cleanup ablation ---------------------------------------------------------------
    variants = {
        "raw question (today, without unit id)": lambda t: t,
        "function words out (SPEC-23 cleanup)": clean_query,
    }
    print("== 1. query cleanup (first hit / top 3, answerable questions, by kind)")
    kinds = ["plain", "error", "paraphrase", "pasted"]
    print(f"{'variant':<68}" + "".join(f"{k:>14}" for k in kinds) + f"{'ALL':>14}")
    for name, fn in variants.items():
        cells, tf, t3, tn = [], 0, 0, 0
        for k in kinds:
            f1 = f3 = n = 0
            for s, q in ans:
                if q["kind"] != k:
                    continue
                rows, _ = ranker.rank(fn(q["q"]))
                ids = [r[0] for r in rows][:3]
                n += 1
                f1 += bool(ids) and right(ids[0], s + "/", q["expect"])
                f3 += any(right(i, s + "/", q["expect"]) for i in ids)
            cells.append(f"{f1}/{f3} of {n}")
            tf, t3, tn = tf + f1, t3 + f3, tn + n
        print(f"{name:<68}" + "".join(f"{c:>14}" for c in cells) + f"{f'{tf}/{t3} of {tn}':>14}")

    # ---- 2. not_found rules --------------------------------------------------------------------
    cleaned = {}
    for s, q in ans + oos:
        cleaned[(s, q["q"])] = ranker.rank(clean_query(q["q"]))

    def signals(key):
        rows, qt = cleaned[key]
        if not rows:
            return dict(score=0.0, matched=0, frac=0.0, idf_frac=0.0, gap=0.0)
        _, s1, m1, mi1 = rows[0]
        s2 = next((r[1] for r in rows[1:]), 0.0)
        tot = sum(ranker.idf(t) for t in qt) or 1.0
        return dict(score=s1, matched=m1, frac=m1 / max(len(qt), 1), idf_frac=mi1 / tot, gap=(s1 - s2) / s1 if s1 else 0.0)

    sig = {k: signals(k) for k in cleaned}
    print("\n== 2. 'not found' rules. A rule refuses when the signal is BELOW the threshold.")
    print("   false refusal = answerable question refused (bad). correct refusal = out-of-scope question refused (good).")
    print("   thresholds are read on the tune sets (fastapi, httpx, pydantic) and then on the check sets (pytest, python, uv).")
    a_tune = [(s, q) for s, q in ans if s in TUNE]
    a_chk = [(s, q) for s, q in ans if s in CHECK]
    o_tune = [(s, q) for s, q in oos if s in TUNE]
    o_chk = [(s, q) for s, q in oos if s in CHECK]
    grids = {
        "score": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        "matched": [1, 2, 3, 4],
        "frac": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        "idf_frac": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        "gap": [0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3],
    }
    for name, grid in grids.items():
        print(f"\n  rule: {name}")
        print(f"  {'thr':>6} | tune: false-refusal  correct-refusal | check: false-refusal  correct-refusal")
        for thr in grid:
            def rate(pool):
                return sum(sig[(s, q["q"])][name] < thr for s, q in pool)
            print(f"  {thr:>6} |       {pct(rate(a_tune), len(a_tune)):<15} {pct(rate(o_tune), len(o_tune)):<16} |        {pct(rate(a_chk), len(a_chk)):<15} {pct(rate(o_chk), len(o_chk))}")

    print("\n  combined: refuse when matched < M OR score < S")
    for M in (2, 3):
        for S in (6, 8, 10, 12):
            def rr(pool):
                return sum(sig[(s, q["q"])]["matched"] < M or sig[(s, q["q"])]["score"] < S for s, q in pool)
            print(f"  M={M} S={S:>2} | tune {pct(rr(a_tune), len(a_tune)):<14}{pct(rr(o_tune), len(o_tune)):<14}| check {pct(rr(a_chk), len(a_chk)):<14}{pct(rr(o_chk), len(o_chk))}")

    # ---- 3. what the out-of-scope questions actually retrieve ----------------------------------
    print("\n== 3. top-1 signal by question group")
    by_kind: dict[str, list] = {}
    for s, q in oos:
        by_kind.setdefault(q["kind"], []).append(sig[(s, q["q"])])
    for k, v in by_kind.items():
        sc = sorted(x["score"] for x in v)
        mt = sorted(x["matched"] for x in v)
        print(f"  oos {k:<14} n={len(v):<3} score median {sc[len(sc) // 2]:.1f} max {sc[-1]:.1f}; matched median {mt[len(mt) // 2]} max {mt[-1]}")
    sc = sorted(sig[(s, q["q"])]["score"] for s, q in ans)
    mt = sorted(sig[(s, q["q"])]["matched"] for s, q in ans)
    print(f"  answerable           n={len(sc):<3} score p10 {sc[len(sc) // 10]:.1f} median {sc[len(sc) // 2]:.1f}; matched p10 {mt[len(mt) // 10]} median {mt[len(mt) // 2]}")
    # ---- 4. how well does each signal separate the two groups? (AUC: 0.5 = coin flip, 1.0 = perfect)
    print("\n== 4. separation of answerable from out-of-scope, by signal (AUC)")
    for name in ("score", "matched", "frac", "idf_frac", "gap"):
        good = [sig[(s, q["q"])][name] for s, q in ans]
        bad = [sig[(s, q["q"])][name] for s, q in oos]
        wins = sum((g > b) + 0.5 * (g == b) for g in good for b in bad)
        print(f"  {name:<9} AUC {wins / (len(good) * len(bad)):.2f}")

    # ---- 5. out-of-scope questions that still get an answer: is it a real answer elsewhere in the corpus?
    print("\n== 5. sample of out-of-scope questions NOT refused by 'matched < 3' (question -> top source)")
    shown = 0
    for s, q in oos:
        if sig[(s, q["q"])]["matched"] >= 3 and shown < 12:
            rows, _ = cleaned[(s, q["q"])]
            print(f"  [{s}] {q['q'][:70]} -> {rows[0][0]}")
            shown += 1

    # ---- 6. fusion: today's keyword_only (word-overlap stand-in + BM25) against BM25 alone ----------
    print("\n== 6. ranking, answerable questions (first hit / top 3 of 240), cleaned query")
    cq = lambda t: clean_query(t)  # noqa: E731
    eng = ranker.e

    def fused(query: str, w_lex: float) -> list[str]:
        lex = [pid for pid, _ in eng.bm25.search(query, top_k=200)]
        dense = eng._dense_search(query, top_k=200)
        sc: dict[str, float] = {}
        for r, d in enumerate(dense, 1):
            sc[d] = sc.get(d, 0.0) + 1.0 / (60 + r)
        for r, d in enumerate(lex, 1):
            sc[d] = sc.get(d, 0.0) + w_lex / (60 + r)
        top = sorted(sc.items(), key=lambda kv: (-kv[1], kv[0]))[:30]
        ql = query.lower().split()
        cand = sorted(((pid, v + (1.0 if any(w in eng.passages[pid].text.lower() for w in ql) else 0.0)) for pid, v in top),
                      key=lambda x: -x[1])
        out: list[str] = []
        for pid, _ in cand:
            src = eng.passages[pid].source_id
            if src not in out:
                out.append(src)
            if len(out) == 3:
                break
        return out

    def score(search) -> tuple[int, int]:
        f1 = f3 = 0
        for s, q in ans:
            ids = search(cq(q["q"]))
            f1 += bool(ids) and right(ids[0], s + "/", q["expect"])
            f3 += any(right(i, s + "/", q["expect"]) for i in ids)
        return f1, f3

    print("  BM25 alone (best passage per source):  %d / %d" % score(lambda q: [r[0] for r in ranker.rank(q)[0]][:3]))
    for w in (1, 3, 10):
        print("  fused with word-overlap list, lexical weight %-2d: %d / %d" % ((w,) + score(lambda q, w=w: fused(q, w))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
