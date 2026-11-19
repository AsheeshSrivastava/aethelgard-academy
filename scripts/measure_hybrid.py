"""SPEC-27 R9 and R11: measure the rag-core adapter (hybrid_rerank) on the six Gemini sets. Local only, not CI.

Offline after the models are cached, no key, no paid call. It needs the retrieval extra, the keyword index
(data/index) and the rag-core index built by scripts/build_ragcore_index.py:

    uv sync --extra retrieval
    uv run python scripts/build_ragcore_index.py        # once, or after the sources change
    $env:HF_HUB_OFFLINE="1"; uv run python scripts/measure_hybrid.py

It searches every question ONCE through the real adapter with both refusal rules switched off, then works out
every candidate not-found rule from those saved numbers (no second model pass). It prints:
  1. Parity (R11): the adapter's hit@1/3/5 against the direct rag-core HR numbers in the 2026-11-18 baseline.
  2. The paraphrase gap, so you can decide on step 6b.
  3. Not-found candidates (R9): the term rule, a score floor, and both; read on fastapi, httpx and pydantic,
     checked untouched on pytest, python and uv; with the bar from SPEC-27 R9 applied.
It writes docs/measurements/<date>-hybrid-adapter.txt (no timings, so it repeats). Timings go to the screen only.
It never changes a setting: you decide the value, then set LMS_HR_MIN_SCORE / LMS_HR_MIN_TERMS.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import measure_lib as ml  # noqa: E402

READ_SETS = ("fastapi-docs", "httpx-docs", "pydantic-docs")  # as in SPEC-23: read here, check on the rest
# SPEC-27 R9 bar: today's keyword numbers on these sets (baseline 2026-11-18, lms mode).
TODAY_FALSE_REFUSAL = 15 / 240
TODAY_CORRECT_REFUSAL = 26 / 60
BASELINE_JSON = ROOT / "docs" / "measurements" / "2026-11-18-gemini-baseline.json"
PARITY_TOLERANCE = 0.005  # half a percentage point, "within rounding"
MIN_TERMS_GRID = (0, 2, 3, 4)  # 0 = term rule off


def pct(x) -> str:
    return "  -  " if x is None else f"{x * 100:5.1f}"


def collect(adapter, sets: dict) -> tuple[list[dict], list[dict], list[float]]:
    """One search per question. -> answerable records, out-of-scope records, latencies (seconds)."""
    ans, oos, times = [], [], []
    for name in sorted(sets):
        for q in sets[name]["questions"]:
            t0 = time.perf_counter()
            r = adapter.search(q["q"], top_k=5)
            times.append(time.perf_counter() - t0)
            ids = [p.source_id for p in r.passages]
            ans.append({"set": name, "kind": q.get("kind", "?"), "ids": ids, "prefix": sets[name]["prefix"],
                        "expect": q["expect"], "status": r.status.value, "score": r.passages[0].score if r.passages else None,
                        "matched": r.terms_matched, "total": r.terms_total, "downgraded": r.downgraded})
        for q in sets[name]["out_of_scope"]:
            t0 = time.perf_counter()
            r = adapter.search(q["q"], top_k=5)
            times.append(time.perf_counter() - t0)
            oos.append({"set": name, "status": r.status.value, "score": r.passages[0].score if r.passages else None,
                        "matched": r.terms_matched, "total": r.terms_total, "downgraded": r.downgraded})
    return ans, oos, times


def refuses(rec: dict, min_terms: int, floor: float | None) -> bool:
    """Would this rule refuse the record? A search that found nothing is refused by every rule."""
    if rec["score"] is None:
        return True
    if min_terms and rec["matched"] < min(min_terms, rec["total"]):
        return True
    return floor is not None and rec["score"] < floor


def rates(ans: list[dict], oos: list[dict], min_terms: int, floor: float | None) -> tuple[float, float]:
    false = sum(refuses(r, min_terms, floor) for r in ans) / len(ans) if ans else 0.0
    correct = sum(refuses(r, min_terms, floor) for r in oos) / len(oos) if oos else 0.0
    return false, correct


def candidate_grid(ans: list[dict]) -> list[tuple[int, float | None]]:
    scores = sorted(r["score"] for r in ans if r["score"] is not None)
    floors: list[float | None] = [None]
    for p in range(1, 41):  # floors at the 1st..40th percentile of answerable top scores, rounded
        floors.append(round(scores[min(len(scores) - 1, len(scores) * p // 100)], 2))
    seen, grid = set(), []
    for m in MIN_TERMS_GRID:
        for f in floors:
            if (m, f) not in seen and (m, f) != (0, None):
                seen.add((m, f))
                grid.append((m, f))
    return grid


def label(m: int, f: float | None) -> str:
    if m and f is None:
        return f"term rule only: M={m}"
    if not m:
        return f"floor only: {f:g}"
    return f"both: M={m} and floor {f:g}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--index-dir", default=str(ROOT / "data" / "index"))
    ap.add_argument("--ragcore-index", default=str(ROOT / "data" / "ragcore" / "index.db"))
    ap.add_argument("--embedder", default="jina-v2-base-en")
    ap.add_argument("--reranker", default="bge-reranker-v2-m3")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--out-dir", default=str(ROOT / "docs" / "measurements"))
    args = ap.parse_args()

    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
    from lms.adapters.ai.rag.ragcore_retriever import RagcoreRetriever, open_ragcore_retriever

    keyword = KeywordRetriever.from_index_dir(args.index_dir)
    if keyword.manifest is None:
        print(f"No keyword index at {args.index_dir}: {keyword.no_index_reason}")
        return 2
    # Both rules off: every search keeps its top passage and its numbers, so candidates can be judged offline.
    adapter = open_ragcore_retriever(args.ragcore_index, keyword, embedder_id=args.embedder, reranker_id=args.reranker,
                                     min_matched_terms=0, min_score=None, timeout_s=300.0)
    if not isinstance(adapter, RagcoreRetriever):
        print("The hybrid adapter did not start, so there is nothing to measure. See the log line above.")
        print("Check: the retrieval extra is installed, the index file exists, the Jina code folder is in place.")
        return 2

    version = ml.set_version()
    sets = ml.load_gemini_sets()
    ans, oos, times = collect(adapter, sets)
    if any(r["downgraded"] for r in ans + oos):
        print("Some searches were answered by keyword search (downgrade). Numbers would be mixed; stopping.")
        return 2
    corpus_ids = [json.loads(ln)["source_id"] for ln in (Path(args.index_dir) / "sources.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]

    lines: list[str] = []

    def p(text: str = "") -> None:
        lines.append(text)
        print(text)

    p("SPEC-27 measurement: the rag-core adapter (hybrid_rerank) on the six Gemini sets")
    p(f"set_version {version}")
    p(f"adapter index_version {adapter._index_version}")  # noqa: SLF001 - this is a measurement script
    p(f"date {args.date}; {len(ans)} answerable, {len(oos)} out-of-scope; offline, no paid call; no timings in this file")
    p()

    # 1. Parity -----------------------------------------------------------------------------------------------------
    rows = [{"set": r["set"], "kind": r["kind"], "flags": ml.flags_for(r["ids"], r["prefix"], r["expect"]),
             "n_expect": len(r["expect"]),
             "n_relevant": sum(1 for i in corpus_ids if ml.is_right(i, r["prefix"], r["expect"]))} for r in ans]
    agg = ml.aggregate(rows)
    p("=" * 100)
    p("R11. PARITY with direct rag-core HR (2026-11-18 baseline)")
    p("=" * 100)
    overall = agg["overall"]
    p(f"  adapter  hit@1 {pct(overall['hit@1'])}  hit@3 {pct(overall['hit@3'])}  hit@5 {pct(overall['hit@5'])}  MRR {overall['mrr']:.3f}")
    parity_ok = None
    if BASELINE_JSON.exists():
        base = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))["gemini/HR"]["metrics"]["overall"]
        p(f"  direct   hit@1 {pct(base['hit@1'])}  hit@3 {pct(base['hit@3'])}  hit@5 {pct(base['hit@5'])}  MRR {base['mrr']:.3f}")
        parity_ok = all(abs(overall[k] - base[k]) <= PARITY_TOLERANCE for k in ("hit@1", "hit@3", "hit@5"))
        p(f"  parity within half a point: {'PASS' if parity_ok else 'FAIL (stop here and look before tuning)'}")
    else:
        p("  baseline file not found; parity not checked")
    p()

    # 2. Paraphrase gap -----------------------------------------------------------------------------------------------
    p("=" * 100)
    p("PARAPHRASE GAP (for the step 6b decision): hit@3 by kind")
    p("=" * 100)
    for kind, s in agg["by_kind"].items():
        p(f"  {kind:<12} n={s['n']:<3} hit@1 {pct(s['hit@1'])}  hit@3 {pct(s['hit@3'])}  hit@5 {pct(s['hit@5'])}")
    p("  For comparison (2026-11-18 baseline): paraphrase hit@3 was 30.0 (lms keyword), 31.7 (rag-core L), 66.7 (HR direct).")
    p()

    # 3. Not-found tuning -------------------------------------------------------------------------------------------------
    p("=" * 100)
    p("R9. NOT-FOUND RULE for hybrid search")
    p("=" * 100)
    p(f"  Bar: false refusal no worse than today's {TODAY_FALSE_REFUSAL * 100:.1f}% and correct refusal at least today's "
      f"{TODAY_CORRECT_REFUSAL * 100:.1f}%; among those, lowest false refusal, then highest correct refusal.")
    read_a = [r for r in ans if r["set"] in READ_SETS]
    read_o = [r for r in oos if r["set"] in READ_SETS]
    chk_a = [r for r in ans if r["set"] not in READ_SETS]
    chk_o = [r for r in oos if r["set"] not in READ_SETS]
    p(f"  Read on {', '.join(READ_SETS)} ({len(read_a)} answerable, {len(read_o)} out-of-scope); "
      f"checked untouched on the other {len(chk_a)} and {len(chk_o)}.")
    top_ans = sorted(r["score"] for r in ans if r["score"] is not None)
    top_oos = sorted(r["score"] for r in oos if r["score"] is not None)
    mid = lambda xs: f"{xs[len(xs) // 2]:.2f}" if xs else "-"  # noqa: E731
    p(f"  Top reranker score, median: answerable {mid(top_ans)}, out-of-scope {mid(top_oos)}.")
    p()
    p(f"  {'rule':<34} {'read: false/correct':>20} {'check: false/correct':>22} {'all six: false/correct':>24}  bar")
    scored = []
    for m, f in candidate_grid(read_a):
        rf, rc = rates(read_a, read_o, m, f)
        cf, cc = rates(chk_a, chk_o, m, f)
        af, ac = rates(ans, oos, m, f)
        meets = rf <= TODAY_FALSE_REFUSAL and rc >= TODAY_CORRECT_REFUSAL
        scored.append((m, f, rf, rc, cf, cc, af, ac, meets))
    meeting = sorted((s for s in scored if s[8]), key=lambda s: (s[2], -s[3]))
    shown = meeting[:8] + [s for s in scored if s[0] == 3 and s[1] is None]  # best eight, plus today's rule for reference
    for m, f, rf, rc, cf, cc, af, ac, meets in shown:
        p(f"  {label(m, f):<34} {pct(rf):>9}/{pct(rc):<9} {pct(cf):>11}/{pct(cc):<9} {pct(af):>12}/{pct(ac):<9}  {'meets' if meets else 'no'}")
    p()
    if meeting:
        m, f, rf, rc, cf, cc, af, ac, _ = meeting[0]
        agrees = cf <= TODAY_FALSE_REFUSAL + 0.03 and cc >= TODAY_CORRECT_REFUSAL - 0.10
        p(f"  Best on the read sets: {label(m, f)}. On the untouched check sets: false {pct(cf)}%, correct {pct(cc)}% "
          f"({'agrees within a few points' if agrees else 'DOES NOT AGREE: do not adopt without a look'}).")
        p("  To use it: set " + (f"LMS_HR_MIN_SCORE={f:g} " if f is not None else "LMS_HR_MIN_SCORE empty ")
          + f"and LMS_HR_MIN_TERMS={m} (0 = term rule off).")
    else:
        p("  No candidate meets the bar on the read sets. Per SPEC-27 R9, keep the term rule as it is (M=3, no floor) and record why.")
    p()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.date}-hybrid-adapter.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    # Timing goes to the screen only (not in the file), as a first look for the 10 s timeout setting.
    times.sort()
    print(f"[screen only] {len(times)} searches: median {statistics.median(times) * 1000:.0f} ms, "
          f"p95 {times[int(len(times) * 0.95) - 1] * 1000:.0f} ms, max {times[-1] * 1000:.0f} ms")
    return 0 if parity_ok is not False else 1


if __name__ == "__main__":
    sys.exit(main())
