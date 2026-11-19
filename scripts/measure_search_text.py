"""SPEC-26: measure the search-only text recipes V0..V4 on the six Gemini sets and the SPEC-20 fixture. Local only, not CI.

Offline, no key, no model, no paid call. Reads data/index (git-ignored) and eval/gemini-sets/. Writes
docs/measurements/<date>-search-only-text.txt (and .json). Run from the repo root:

    uv run --no-sync python scripts/measure_search_text.py

One search per question and recipe is run with min_matched_terms=1; the shipped rule (needed = min(m, terms in query),
SPEC-23) is then applied for m = 2, 3, 4 from terms_matched, which is exactly what KeywordRetriever does for a given m.
V0 must reproduce the SPEC-25 baseline (checked at the end of the run). Numbers carry no timestamps and no timings (R8).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import measure_gemini as mg  # noqa: E402
import measure_lib as ml  # noqa: E402

RECIPES = ("none", "path", "title", "path_title", "path_title_x2")
NAMES = {"none": "V0", "path": "V1", "title": "V2", "path_title": "V3", "path_title_x2": "V4"}
MINS = (2, 3, 4)
SHIPPED_MIN = 3
FIXTURE_MIN = 2


class Cached:
    """One real search per query (min 1); the shipped not-found rule is applied for any m."""

    def __init__(self, retriever) -> None:
        self.retriever = retriever
        self.cache: dict[str, object] = {}

    def result(self, query: str):
        if query not in self.cache:
            self.cache[query] = self.retriever.search(query, top_k=5)
        return self.cache[query]

    def searcher(self, m: int):
        def search(query: str) -> dict:
            r = self.result(query)
            ok = r.status.value == "ok" and r.terms_matched >= min(m, r.terms_total)
            ids = [p.source_id for p in r.passages] if ok else []
            return {"status": "ok" if ok else "not_found", "ids": ids, "passages": r.passages if ok else (),
                    "score": r.passages[0].score if ok and r.passages else None}
        return search


def fixture_numbers(recipe: str, m: int) -> dict:
    import retrieval_quality as rq
    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever

    adapter = KeywordRetriever.from_hybrid(rq.build_keyword_retriever(search_recipe=recipe), min_matched_terms=m)
    qs = rq.load_questions()
    ans = [q for q in qs if q["expected_source"]]
    no = [q for q in qs if not q["expected_source"]]
    first = top3 = lost = 0
    for q in ans:
        res = adapter.search(q["question"], top_k=3)
        ids = [p.source_id for p in res.passages]
        first += bool(ids) and ids[0] == q["expected_source"]
        top3 += q["expected_source"] in ids
        lost += res.status.value == "not_found"
    refused = sum(adapter.search(q["question"], top_k=3).status.value == "not_found" for q in no)
    return {"answerable": len(ans), "first_hit": first, "top3": top3, "false_refusal": lost / len(ans),
            "correct_refusal": refused / len(no), "no_answer": len(no)}


def summary(agg: dict, ref: dict) -> dict:
    o = agg["overall"]
    return {"hit1": o["hit@1"], "hit3": o["hit@3"], "hit5": o["hit@5"], "mrr": o["mrr"], "ndcg3": o["ndcg@3"],
            "para3": agg["by_kind"]["paraphrase"]["hit@3"], "false_refusal": ref["false_refusal"],
            "correct_refusal": ref["correct_refusal"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-dir", default=str(ROOT / "data" / "index"))
    ap.add_argument("--date", default="2026-11-19")
    ap.add_argument("--out-dir", default=str(ROOT / "docs" / "measurements"))
    ap.add_argument("--recipes", default=",".join(RECIPES))
    args = ap.parse_args()
    index_dir, out_dir = Path(args.index_dir), Path(args.out_dir)
    recipes = [r.strip() for r in args.recipes.split(",") if r.strip()]

    import retrieval_quality as rq
    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
    from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
    from lms.core.search_text import SEARCH_TEXT_VERSION

    version = ml.set_version()
    sets = ml.load_gemini_sets()
    rows_src = [json.loads(ln) for ln in (index_dir / "sources.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    corpus_ids = [r["source_id"] for r in rows_src]
    items = [(n, sets[n]["prefix"], sets[n]["questions"]) for n in sorted(sets)]
    no_answer = [q for n in sorted(sets) for q in sets[n]["out_of_scope"]]
    floor = rq.load_floor()
    baseline = json.loads((ROOT / "docs" / "measurements" / "2026-11-18-gemini-baseline.json").read_text(encoding="utf-8"))

    out = mg.Out()
    out.p("SPEC-26 measurement: search-only text recipes on the six Gemini sets and the SPEC-20 fixture")
    out.p(f"set_version {version}")
    out.p(f"SEARCH_TEXT_VERSION {SEARCH_TEXT_VERSION}; date {args.date}; offline, no model, no paid call; scores are rounded, no timings (R8)")
    out.p("Mode lms (keyword_only): cleaned query, BM25, one passage per file (cap 1), min_matched_terms 3 on the real corpus, 2 on the fixture.")
    out.p("Metrics are over answerable questions only (240 answerable, 60 out-of-scope). Baseline: docs/measurements/2026-11-18-gemini-baseline.txt.")
    out.p("V0 none | V1 path | V2 title | V3 path_title | V4 path_title_x2 (SPEC-26 R5).\n")
    out.data.update({"set_version": version, "search_text_version": SEARCH_TEXT_VERSION, "date": args.date})

    results: dict[str, dict] = {}
    for recipe in recipes:
        name = NAMES[recipe]
        engine = HybridRerankedRetriever.load(index_dir, search_recipe=recipe)
        adapter = KeywordRetriever.from_hybrid(engine, min_matched_terms=1)
        index_version = adapter.manifest.index_version
        cached = Cached(adapter)
        out.p("=" * 100)
        out.p(f"{name} recipe={recipe}  index_version {index_version}  ({len(engine.sources)} files, {len(engine.passages)} passages)")
        out.p("=" * 100)
        per_min: dict[int, dict] = {}
        for m in MINS:
            rows, a, o, sc = mg.evaluate(cached.searcher(m), items, no_answer, corpus_ids)
            ref = ml.refusal_rates(a, o)
            agg = ml.aggregate(rows)
            per_min[m] = {"rows": rows, "agg": agg, "ref": ref, "summary": summary(agg, ref)}
        main_m = per_min[SHIPPED_MIN]
        stamp = f"set_version={version[:12]} index_version={index_version[:12]} mode=lms recipe={recipe} ({name}) min_matched_terms={SHIPPED_MIN} date={args.date}"
        mg.report_mode(out, f"gemini/{recipe}", stamp, main_m["rows"], [r["status"] for r in main_m["rows"]],
                       [cached.searcher(SHIPPED_MIN)(q["q"])["status"] for q in no_answer],
                       [None] * len(no_answer), refusal=True)
        out.p("  min_matched_terms sweep (Gemini sets): " + "; ".join(
            f"m={m}: Hit@3 {mg.pct(per_min[m]['summary']['hit3'])} false-refusal {mg.pct(per_min[m]['summary']['false_refusal'])} "
            f"correct-refusal {mg.pct(per_min[m]['summary']['correct_refusal'])}" for m in MINS))
        fx = {m: fixture_numbers(recipe, m) for m in MINS}
        out.p("  fixture (SPEC-20, 41 answerable, 9 no-answer): " + "; ".join(
            f"m={m}: first {fx[m]['first_hit']}/41 top3 {fx[m]['top3']}/41 false-refusal {mg.pct(fx[m]['false_refusal'])} "
            f"correct-refusal {mg.pct(fx[m]['correct_refusal'])}" for m in MINS))
        mg.miss_analysis(out, f"gemini/{recipe}", main_m["rows"], engine, corpus_ids, examples=False)
        results[recipe] = {"index_version": index_version, "per_min": {m: {"summary": v["summary"]} for m, v in per_min.items()},
                           "fixture": fx, "misses": out.data["misses"][f"gemini/{recipe}"],
                           "hit3_flags": [any(r["flags"][:3]) for r in main_m["rows"]],
                           "by_kind": {k: s for k, s in main_m["agg"]["by_kind"].items()}, "agg": main_m["agg"]["overall"]}
        del engine, adapter, cached, per_min

    # --- comparison and the R7 verdict ---------------------------------------------------------------
    out.p("=" * 100)
    out.p("COMPARISON at min_matched_terms 3 (fixture at 2). Hit values in percent.")
    out.p("=" * 100)
    out.p("  variant            hit@1  hit@3  hit@5   MRR  nDCG@3  para@3 false-ref corr-ref | fixture first top3 | misses (wording/vague/multi/other)")
    for recipe in recipes:
        r = results[recipe]
        s = r["per_min"][SHIPPED_MIN]["summary"]
        f = r["fixture"][FIXTURE_MIN]
        mi = r["misses"]
        out.p(f"  {NAMES[recipe]} {recipe:<14} {mg.pct(s['hit1'])}  {mg.pct(s['hit3'])}  {mg.pct(s['hit5'])}  {s['mrr']:.3f}  {s['ndcg3']:.3f}  {mg.pct(s['para3'])}   "
              f"{mg.pct(s['false_refusal'])}    {mg.pct(s['correct_refusal'])}  | {f['first_hit']:>5} {f['top3']:>4}      | "
              f"{mi['total_misses']} ({mi['wording']}/{mi['vague chunk']}/{mi['multi-page']}/{mi['other']})")
    out.p()

    verdict = {}
    if "none" in results:
        v0 = results["none"]["per_min"][SHIPPED_MIN]["summary"]
        f0 = results["none"]["fixture"][FIXTURE_MIN]
        out.p("R7 adoption rule: against V0, Hit@3 gain >= 2.0 points; false-refusal and correct-refusal each no more than 1.0 point worse;")
        out.p(f"fixture top-3 not below floor.json ({floor['top3']} of {floor['answerable']}), fixture refusal rates within 1 point of V0's.")
        ok_names = []
        for recipe in recipes:
            if recipe == "none":
                continue
            s = results[recipe]["per_min"][SHIPPED_MIN]["summary"]
            f = results[recipe]["fixture"][FIXTURE_MIN]
            gain = s["hit3"] - v0["hit3"]
            checks = {
                "hit3_gain>=2": gain >= mg.BAR_GAIN - 1e-9,
                "false_refusal<=+1": s["false_refusal"] - v0["false_refusal"] <= mg.BAR_WORSE + 1e-9,
                "correct_refusal>=-1": v0["correct_refusal"] - s["correct_refusal"] <= mg.BAR_WORSE + 1e-9,
                "fixture_top3>=floor": f["top3"] >= floor["top3"],
                "fixture_first>=floor": f["first_hit"] >= floor["first_hit"],
                "fixture_false_refusal<=+1": f["false_refusal"] - f0["false_refusal"] <= mg.BAR_WORSE + 1e-9,
                "fixture_correct_refusal>=-1": f0["correct_refusal"] - f["correct_refusal"] <= mg.BAR_WORSE + 1e-9,
            }
            met = all(checks.values())
            base_flags, flags = results["none"]["hit3_flags"], results[recipe]["hit3_flags"]
            gained = sum(1 for x, y in zip(base_flags, flags) if y and not x)
            lost = sum(1 for x, y in zip(base_flags, flags) if x and not y)
            verdict[recipe] = {"gain_points": round(gain * 100, 2), "gained": gained, "lost": lost, "checks": checks, "met": met}
            failed = [k for k, v in checks.items() if not v]
            out.p(f"  {NAMES[recipe]} {recipe:<14} Hit@3 {gain * 100:+.1f} pts ({round(gain * 240):+d} questions: {gained} gained, {lost} lost) -> bar "
                  + ("MET" if met else "not met (" + ", ".join(failed) + ")"))
            if met:
                ok_names.append((recipe, gain))
        adopted = "none"
        if ok_names:
            best = max(g for _, g in ok_names)
            # the simplest qualifying variant within 2 points of the best (V4 is not taken over V3 on a thin edge)
            adopted = next(r for r in RECIPES if any(r == n and g >= best - 0.02 + 1e-9 for n, g in ok_names))
        out.p(f"\n  Adopted by R7: {NAMES[adopted]} ({adopted}). " + (
            "No variant meets the bar, so V0 (today's index) stays and the default remains LMS_SEARCH_TEXT=none." if adopted == "none"
            else "A variant meets the bar; the owner decides whether to make it the default (the code keeps it behind LMS_SEARCH_TEXT)."))
        out.data["verdict"] = verdict | {"adopted": adopted}

        # V0 reproduces the SPEC-25 baseline?
        b = baseline["metrics"]["gemini/lms"] if "metrics" in baseline else baseline["gemini/lms"]["metrics"]
        b_hit3 = b["overall"]["hit@3"]
        out.p(f"\n  Baseline check: SPEC-25 file says lms Hit@3 {mg.pct(b_hit3)}; this run's V0 says {mg.pct(v0['hit3'])} "
              f"-> {'reproduced' if abs(b_hit3 - v0['hit3']) < 5e-5 else 'DIFFERS: investigate before trusting this file'}")
    out.data["results"] = {k: {"index_version": v["index_version"], "per_min": v["per_min"], "fixture": v["fixture"], "misses": v["misses"]} for k, v in results.items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.date}-search-only-text.txt").write_text("\n".join(out.lines) + "\n", encoding="utf-8", newline="\n")
    (out_dir / f"{args.date}-search-only-text.json").write_text(
        json.dumps(mg.rnd(out.data), indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
