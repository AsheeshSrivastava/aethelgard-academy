"""SPEC-25: measure retrieval on the six Gemini question sets (and re-run the old sets). Local only, not CI.

Offline, no key, no paid call. Reads data/index (git-ignored, 1,371 files) and eval/gemini-sets/ (in the repo).
Writes docs/measurements/<date>-gemini-baseline.txt and .json, and the review sheet. Run with the rag-core
interpreter so the L and HR modes can load their cached models (HF_HUB_OFFLINE=1 keeps it off the network):

    $env:PYTHONPATH="D:\\01-Project\\lms\\src"; $env:HF_HUB_OFFLINE="1"
    D:\\01-Project\\rag-core\\.venv\\Scripts\\python.exe scripts/measure_gemini.py --ragcore-root D:\\01-Project\\rag-core

`--modes lms` runs without rag-core (uv run --no-sync python scripts/measure_gemini.py --modes lms).
Sections: baseline (R5), misses (R6), passages (R7), tuning (R9), sheet (R8). Default: all.
Reuses the old-set lists from measure_real_corpus.py. Numbers carry no timestamps and no timings (R11).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import tempfile
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import measure_lib as ml  # noqa: E402
from measure_real_corpus import IN_SCOPE, OUT_OF_SCOPE, load_yaml  # noqa: E402

SEED = 25
CHAR_CAP_PAIRS = ((800, 2400), (1200, 3600), (1600, 4800), (2000, 6000))
RUNS = (3, 4, 5, 6)
MIN_TERMS = (2, 3, 4)
BAR_GAIN = 0.02  # R9: at least 2 percentage points
BAR_WORSE = 0.01  # R9: no more than 1 point worse refusal


class Out:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.data: dict = {}

    def p(self, text: str = "") -> None:
        self.lines.append(text)
        print(text)


def pct(x) -> str:
    return "  -  " if x is None else f"{x * 100:5.1f}"


def metric_line(label: str, s: dict) -> str:
    return (f"  {label:<26} n={s['n']:<4} hit@1 {pct(s['hit@1'])}  hit@3 {pct(s['hit@3'])}  hit@5 {pct(s['hit@5'])}"
            f"  MRR {s['mrr']:.3f}  nDCG@1/3/5 {s['ndcg@1']:.3f}/{s['ndcg@3']:.3f}/{s['ndcg@5']:.3f}"
            f"  P@1/3/5 {pct(s['p@1'])}/{pct(s['p@3'])}/{pct(s['p@5'])} (n={s['p_n']})"
            if s["n"] else f"  {label:<26} n=0")


def rnd(obj):
    """Round floats to 4 places so the JSON is stable (R11)."""
    if isinstance(obj, float):
        return round(obj, 4)
    if isinstance(obj, dict):
        return {k: rnd(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rnd(v) for v in obj]
    return obj


# --- searchers -------------------------------------------------------------------------------------------


def lms_searcher(retriever, top_k: int = 5):
    def search(query: str) -> dict:
        res = retriever.search(query, top_k=top_k)
        return {"status": res.status.value, "ids": [p.source_id for p in res.passages],
                "passages": res.passages, "score": res.passages[0].score if res.passages else None}
    return search


def ragcore_searchers(rc_root: Path, rows: list[dict], index_dir: Path, modes: list[str], embedder_name: str,
                      reranker_name: str, log) -> tuple[dict, list, str]:
    """rag-core L / HR over `rows` (source dicts). Same setup as measure_real_corpus.py. -> searchers, closers, setup note."""
    from ragcore import IndexSetup, Retriever, open_index
    from ragcore.chunking import ChunkConfig
    from ragcore.contracts import Source
    from ragcore.embed.base import load_model_specs
    from ragcore.index_sync import sync
    from ragcore.llamaindex_chunker import LlamaIndexChunker, llamaindex_version
    from ragcore.rerank import load_reranker_specs
    from ragcore.stage import make_embedder
    from ragcore.stage3 import make_reranker

    config = ChunkConfig()
    models, rerankers = rc_root / "configs" / "models.yaml", rc_root / "configs" / "rerankers.yaml"
    model = load_model_specs(models)[embedder_name]
    rspec = load_reranker_specs(rerankers)[reranker_name]
    revision = model.revision + (f"+{model.code_revision}" if model.code_revision else "")
    setup = IndexSetup(model.id, revision, "llamaindex", llamaindex_version(config),
                       f"{config.max_chars}/{config.hard_limit}", metadata.version("llama-index-core"),
                       rspec.id, rspec.revision)
    embedder = make_embedder(embedder_name, models)
    index = index_dir / "index.db"
    index.parent.mkdir(parents=True, exist_ok=True)
    sources = [Source(r["source_id"], r["version"], r["text"], r["raw_sha256"], r["loader_version"],
                      r["licence"], r["licence_basis"]) for r in rows]
    chunker = LlamaIndexChunker()
    with open_index(index, setup) as store:
        report = sync(sources, store, lambda s: chunker(s, config), embedder)
    log(report.render())
    reranker = make_reranker(reranker_name, rerankers)[0] if "HR" in modes else None
    searchers, closers = {}, []
    for mode in ("L", "HR"):
        if mode not in modes:
            continue
        kw = dict(embedder=embedder, reranker=reranker) if mode == "HR" else {}
        r = Retriever.open(index, setup, variant=mode, **kw)
        closers.append(r)

        def search(query: str, r=r) -> dict:
            res = r.search(query, k=5, max_per_file=1)
            return {"status": "ok" if res else "no_results", "ids": [x.source_id for x in res],
                    "score": res[0].score if res else None}
        searchers[mode] = search
    note = f"embedder={model.id}@{revision}; reranker={rspec.id}@{rspec.revision}; chunker=llamaindex/{config.max_chars}/{config.hard_limit}"
    return searchers, closers, note


# --- evaluation --------------------------------------------------------------------------------------------


def evaluate(search, items, no_answer, corpus_ids):
    """items: [(set name, prefix, answerable questions)]; no_answer: [question dicts]. -> rows, answerable statuses, no-answer statuses."""
    rows, ans_status, oos_status, oos_scores = [], [], [], []
    for name, prefix, qs in items:
        for q in qs:
            r = search(q["q"])
            expect = q["expect"]
            rows.append({
                "set": name, "kind": q.get("kind", "old"), "q": q["q"], "expect": expect, "prefix": prefix,
                "ids": r["ids"], "flags": ml.flags_for(r["ids"], prefix, expect), "n_expect": len(expect),
                "n_relevant": sum(1 for i in corpus_ids if ml.is_right(i, prefix, expect)),
                "status": r["status"], "score": r.get("score"),
            })
            ans_status.append(r["status"])
    for q in no_answer:
        r = search(q["q"])
        oos_status.append(r["status"])
        oos_scores.append(r.get("score"))
    return rows, ans_status, oos_status, oos_scores


def old_sets(rc_root: Path, corpus_ids: list[str]):
    """The rag-core real-corpus sets (SPEC-20 era). Answerable = expected file exists in this corpus; rest are no-answer."""
    items, missing = [], []
    for fname, prefix in IN_SCOPE:
        qs = load_yaml(rc_root / "eval" / "questions" / fname)
        have = [q for q in qs if any(i.startswith(prefix) and any(p in i for p in q["expect"]) for i in corpus_ids)]
        missing += [q for q in qs if q not in have]
        items.append((fname, prefix, have))
    foreign = []
    for fname in OUT_OF_SCOPE:
        foreign += load_yaml(rc_root / "eval" / "questions" / fname)
    return items, foreign + missing


def report_mode(out: Out, key: str, stamp: str, rows, ans_status, oos_status, oos_scores, refusal: bool, by_set=True):
    agg = ml.aggregate(rows)
    out.p(f"[{stamp}]")
    out.p(metric_line("ALL answerable", agg["overall"]))
    for kind, s in agg["by_kind"].items():
        out.p(metric_line(f"  kind {kind}", s))
    if by_set:
        for name, s in agg["by_set"].items():
            out.p(metric_line(f"  set {name}", s))
    ref = ml.refusal_rates(ans_status, oos_status) if refusal else None
    if ref:
        out.p(f"  refusal: false-refusal {pct(ref['false_refusal'])}% of {ref['answerable_n']} answerable; "
              f"correct-refusal {pct(ref['correct_refusal'])}% of {ref['out_of_scope_n']} out-of-scope")
    else:
        sc = sorted(s for s in oos_scores if s is not None)
        out.p(f"  refusal: not measured (no not_found rule in this mode until plan step 7); "
              f"top-1 score of {len(sc)} no-answer questions: median {sc[len(sc) // 2]:.2f}" if sc else
              "  refusal: not measured (no not_found rule in this mode)")
    out.p()
    out.data[key] = {"stamp": stamp, "metrics": agg, "refusal": ref}
    return agg


# --- R6 -------------------------------------------------------------------------------------------------------


def miss_analysis(out: Out, key: str, rows, engine, corpus_ids, examples: bool):
    from lms.core.query import clean_query, clean_query_words

    misses = [r for r in rows if not any(r["flags"][:3])]
    labelled: dict[str, list[dict]] = {lab: [] for lab in ml.LABELS}
    for r in misses:
        expected = [i for i in corpus_ids if ml.is_right(i, r["prefix"], r["expect"])]
        hits, _ = engine.keyword_search(clean_query(r["q"]))
        best = next((h.passage.text for h in hits if h.passage.source_id in expected), "")
        terms = [t.lower() for t in clean_query_words(r["q"])]
        label = ml.classify_miss(terms, best, r["ids"], expected, r["expect"], r["prefix"])
        labelled[label].append({**r, "expected_files": expected[:3]})
    out.p(f"  {key}: {len(misses)} of {len(rows)} answerable questions miss at K=3 "
          + ", ".join(f"{lab} {len(v)}" for lab, v in labelled.items()))
    out.data.setdefault("misses", {})[key] = {lab: len(v) for lab, v in labelled.items()} | {"total_misses": len(misses)}
    if examples:
        rng = random.Random(SEED)
        for lab, v in labelled.items():
            out.p(f"\n  Label '{lab}': {len(v)} questions. 10 examples (fixed seed {SEED}; labels are inferred by rule, not read by a human)")
            for r in (rng.sample(v, min(10, len(v))) if v else []):
                q = " ".join(r["q"].split())
                q = q[:110] + ("..." if len(q) > 110 else "")
                out.p(f"   - [{r['set']} / {r['kind']}] {q}")
                out.p(f"       expected {r['expect']}   got {r['ids'][:2]}")
    out.p()


# --- R7 ---------------------------------------------------------------------------------------------------------


def passages_test(out: Out, index_dir: Path, sets):
    from lms.adapters.ai.passage_safety import build_grounding
    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever

    out.p("R7. Passages kept per source file (lms keyword mode, SPEC-23 cleaned query, min 3 matched terms)")
    out.p("   Hit@K = expected file among the top K passages. By-file@K = among the first K distinct files of the top 10 passages.")
    out.p("   'chars' = mean characters of source text passed to the model for the top 3 passages after the SPEC-22 caps.\n")
    res = {}
    for cap in (1, 2, 3):
        r10 = KeywordRetriever.from_index_dir(index_dir, passages_per_source=cap)
        hits_p = {1: [], 3: [], 5: []}
        hits_f = {1: [], 3: [], 5: []}
        distinct, chars, ans_s, oos_s = [], [], [], []
        for name in sorted(sets):
            prefix = sets[name]["prefix"]
            for q in sets[name]["questions"]:
                res10 = r10.search(q["q"], top_k=10)
                ids10 = [p.source_id for p in res10.passages]
                ans_s.append(res10.status.value)
                for k in (1, 3, 5):
                    hits_p[k].append(any(ml.flags_for(ids10, prefix, q["expect"], k=k)))
                    hits_f[k].append(any(ml.flags_for(ml.dedupe_files(ids10), prefix, q["expect"], k=k)))
                distinct.append(len(set(ids10[:5])))
                top3 = res10.passages[:3]
                g = build_grounding([(p.passage_id, p.source_name, p.text) for p in top3])
                chars.append(sum(len(e.text) for e in g.entries))
            for q in sets[name]["out_of_scope"]:
                oos_s.append(r10.search(q["q"], top_k=10).status.value)
        n = len(ans_s)
        ref = ml.refusal_rates(ans_s, oos_s)
        row = {"hit_passages": {k: sum(v) / n for k, v in hits_p.items()},
               "hit_by_file": {k: sum(v) / n for k, v in hits_f.items()},
               "distinct_files_top5": sum(distinct) / n, "mean_chars_top3": sum(chars) / n,
               "false_refusal": ref["false_refusal"], "correct_refusal": ref["correct_refusal"]}
        res[cap] = row
        out.p(f"   cap {cap}: Hit@1/3/5 {pct(row['hit_passages'][1])}/{pct(row['hit_passages'][3])}/{pct(row['hit_passages'][5])}"
              f"   by-file@1/3/5 {pct(row['hit_by_file'][1])}/{pct(row['hit_by_file'][3])}/{pct(row['hit_by_file'][5])}"
              f"   distinct files in top 5 {row['distinct_files_top5']:.2f}   chars {row['mean_chars_top3']:.0f}"
              f"   false-refusal {pct(row['false_refusal'])}  correct-refusal {pct(row['correct_refusal'])}")
    out.data["passages_per_source"] = res
    base, best = res[1], max(res[2]["hit_passages"][3], res[3]["hit_passages"][3])
    gain = best - base["hit_passages"][3]
    gain_f = max(res[2]["hit_by_file"][3], res[3]["hit_by_file"][3]) - base["hit_by_file"][3]
    out.p(f"\n   Verdict (R9): best gain over cap 1 is {gain * 100:+.1f} points on passage-level Hit@3 and {gain_f * 100:+.1f} points on by-file Hit@3 "
          "(bar: at least +2.0 on both; refusals are unchanged by the cap). "
          + ("Bar met; check the distinct-file line before changing the default." if gain >= BAR_GAIN and gain_f >= BAR_GAIN
             else "Bar not met; the default stays 1."))
    out.p("   By-file uses the first 10 passages, so at cap 3 fewer than 5 distinct files may be available, which limits by-file@5 for higher caps.")
    out.p("   Note: cap 2 and 3 fill the top K with passages of the same file, so passage-level Hit@K can rise while the "
          "number of distinct files falls. By-file Hit@K is the fair comparison for 'does the learner see the right page'.\n")


# --- R9 ---------------------------------------------------------------------------------------------------------


def _fixture_numbers(min_terms: int):
    import retrieval_quality as rq
    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever

    adapter = KeywordRetriever.from_hybrid(rq.build_keyword_retriever(), min_matched_terms=min_terms)
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


def tuning(out: Out, index_dir: Path, sets):
    import retrieval_quality as rq
    from lms.adapters.ai import passage_safety as ps
    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
    from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
    from lms.core.query import clean_query_words

    out.p("R9. Tuning sweeps. A shipped value changes only with a gain of at least 2 points on Hit@3 (or the gated number)")
    out.p("    and no more than 1 point worse false-refusal and correct-refusal, on the Gemini sets AND the SPEC-20 fixture.")
    out.p("    Reading of the rule used here: Hit@3 gain is judged on the Gemini sets; the fixture (41 questions) must not")
    out.p("    drop in top3 (floor, R10) and both refusal rates must stay within 1 point on both data sets.\n")
    engine = HybridRerankedRetriever.load(index_dir)
    floor = rq.load_floor()
    out.p(f"    CI floor (floor.json): first_hit {floor['first_hit']}, top3 {floor['top3']} of {floor['answerable']}\n")

    # (a) min_matched_terms
    out.p("(a) min_matched_terms (shipped 3 for the real corpus; the fixture uses 2)")
    results = {}
    for m in MIN_TERMS:
        r = KeywordRetriever.from_hybrid(engine, min_matched_terms=m)
        ans_s, oos_s, hit3 = [], [], []
        for name in sorted(sets):
            prefix = sets[name]["prefix"]
            for q in sets[name]["questions"]:
                res = r.search(q["q"], top_k=3)
                ans_s.append(res.status.value)
                hit3.append(any(ml.is_right(p.source_id, prefix, q["expect"]) for p in res.passages))
            oos_s += [r.search(q["q"], top_k=3).status.value for q in sets[name]["out_of_scope"]]
        ref = ml.refusal_rates(ans_s, oos_s)
        fx = _fixture_numbers(m)
        results[m] = {"hit3": sum(hit3) / len(hit3), "false_refusal": ref["false_refusal"],
                      "correct_refusal": ref["correct_refusal"], "fixture": fx}
        out.p(f"    min {m}: Gemini Hit@3 {pct(results[m]['hit3'])}  false-refusal {pct(ref['false_refusal'])}  "
              f"correct-refusal {pct(ref['correct_refusal'])}  | fixture first {fx['first_hit']}/{fx['answerable']} top3 {fx['top3']}/{fx['answerable']} "
              f"false-refusal {pct(fx['false_refusal'])} correct-refusal {pct(fx['correct_refusal'])} ({fx['correct_refusal'] * fx['no_answer']:.0f}/{fx['no_answer']})")
    out.data["min_matched_terms"] = results
    cur, fx_cur = results[3], results[2]["fixture"]  # shipped: 3 on the real corpus, 2 on the fixture
    for m in (2, 4):
        c = results[m]
        fx = c["fixture"]
        ok = (c["hit3"] - cur["hit3"] >= BAR_GAIN
              and c["false_refusal"] - cur["false_refusal"] <= BAR_WORSE
              and cur["correct_refusal"] - c["correct_refusal"] <= BAR_WORSE
              and fx["top3"] >= floor["top3"]
              and fx["false_refusal"] - fx_cur["false_refusal"] <= BAR_WORSE
              and fx_cur["correct_refusal"] - fx["correct_refusal"] <= BAR_WORSE)
        out.p(f"    min {m} vs shipped 3: Hit@3 {((c['hit3'] - cur['hit3']) * 100):+.1f} pts, false-refusal {((c['false_refusal'] - cur['false_refusal']) * 100):+.1f} pts, "
              f"correct-refusal {((c['correct_refusal'] - cur['correct_refusal']) * 100):+.1f} pts -> bar {'MET' if ok else 'not met'}")
    out.p()

    # samples for (b) and (c): top-3 grounding of every answerable question
    retriever = KeywordRetriever.from_hybrid(engine)
    rng = random.Random(SEED)
    all_pids = sorted(engine.passages)
    cases = []
    for name in sorted(sets):
        for q in sets[name]["questions"]:
            res = retriever.search(q["q"], top_k=3)
            if res.passages:
                cases.append((q["q"], res.passages))

    # (b) CITATION_MIN_RUN
    out.p("(b) CITATION_MIN_RUN (shipped 4). Supplied text should be recognised as quoting the passage; answer text should not.")
    out.p("    exact = 12 words copied from the top passage; edited = 20 words with every 6th dropped (runs of 5);")
    out.p("    other = 12 words of a passage from a different file; echo = the learner's own question as the reply.")
    samples = []
    for qtext, passages in cases:
        g = ps.build_grounding([(p.passage_id, p.source_name, p.text) for p in passages])
        if not g.entries:
            continue
        words = g.entries[0].text.split()
        if len(words) < 20:
            continue
        start = len(words) // 4
        window = words[start:start + 20]
        other = ""
        for _ in range(50):
            pid = all_pids[rng.randrange(len(all_pids))]
            cand = engine.passages[pid]
            w = cand.text.split()
            if cand.source_id not in {p.source_id for p in passages} and len(w) >= 20:
                other = " ".join(w[len(w) // 4: len(w) // 4 + 12])
                break
        samples.append((g, " ".join(window[:12]), " ".join(x for i, x in enumerate(window) if (i + 1) % 6), other, qtext))
    out.p(f"    {len(samples)} questions with a usable top passage (of {len(cases)} answered)")
    shipped = ps.CITATION_MIN_RUN
    cit = {}
    try:
        for n in RUNS:
            ps.CITATION_MIN_RUN = n
            ex = ed = fo = fe = 0
            for g, exact, edited, other, echo in samples:
                pid = g.entries[0].passage_id
                ex += pid in g.cited_for(exact)
                ed += pid in g.cited_for(edited)
                fo += bool(g.cited_for(other))
                fe += bool(g.cited_for(echo))
            t = len(samples)
            cit[n] = {"recall_exact": ex / t, "recall_edited": ed / t, "false_other": fo / t, "false_echo": fe / t}
            out.p(f"    run {n}: recall exact {pct(ex / t)}  recall edited {pct(ed / t)}  false-cite other-file text {pct(fo / t)}  false-cite echoed question {pct(fe / t)}")
    finally:
        ps.CITATION_MIN_RUN = shipped
    out.data["citation_min_run"] = cit
    for n in (3, 5, 6):
        d_rec = cit[n]["recall_edited"] - cit[4]["recall_edited"]
        d_fo = cit[n]["false_other"] - cit[4]["false_other"]
        d_fe = cit[n]["false_echo"] - cit[4]["false_echo"]
        ok = d_rec >= BAR_GAIN and d_fo <= BAR_WORSE and d_fe <= BAR_WORSE
        out.p(f"    run {n} vs shipped 4: edited recall {d_rec * 100:+.1f} pts, false-cite {d_fo * 100:+.1f}/{d_fe * 100:+.1f} pts -> bar {'MET' if ok else 'not met'} "
              "(gated number = recall of edited supplied text)")
    out.p()

    # (c) character caps
    out.p("(c) Character caps (shipped 1,200 per passage, 3,600 in total). The caps do not change which files are found, so Hit@K cannot")
    out.p("    move. Gated number used here: share of the learner's cleaned query terms still present in the text the model gets.")
    caps = {}
    sh = (ps.MAX_PASSAGE_CHARS, ps.MAX_PASSAGES_TOTAL_CHARS)
    try:
        for per, total in CHAR_CAP_PAIRS:
            ps.MAX_PASSAGE_CHARS, ps.MAX_PASSAGES_TOTAL_CHARS = per, total
            ret, chars, cut, dropped = [], [], 0, 0
            npass = 0
            for qtext, passages in cases:
                g = ps.build_grounding([(p.passage_id, p.source_name, p.text) for p in passages])
                terms = [t.lower() for t in clean_query_words(qtext)]
                have = set(ml.tokens(" ".join(e.text for e in g.entries)))
                if terms:
                    ret.append(sum(t in have for t in terms) / len(terms))
                chars.append(sum(len(e.text) for e in g.entries))
                npass += len(passages)
                cut += sum(len(ps.clean_text(p.text).strip()) > per for p in passages)
                dropped += len(passages) - len(g.entries)
            caps[f"{per}/{total}"] = {"term_retention": sum(ret) / len(ret), "mean_chars": sum(chars) / len(chars),
                                      "passages_cut_share": cut / npass, "passages_dropped_share": dropped / npass}
            c = caps[f"{per}/{total}"]
            out.p(f"    {per:>5}/{total:<5}: term retention {pct(c['term_retention'])}%  mean chars {c['mean_chars']:.0f}  "
                  f"passages over the per-passage cap {pct(c['passages_cut_share'])}%  dropped by the total cap {pct(c['passages_dropped_share'])}%")
    finally:
        ps.MAX_PASSAGE_CHARS, ps.MAX_PASSAGES_TOTAL_CHARS = sh
    out.data["char_caps"] = caps
    cur = caps["1200/3600"]
    for key, c in caps.items():
        if key == "1200/3600":
            continue
        gain = c["term_retention"] - cur["term_retention"]
        cost = c["mean_chars"] / cur["mean_chars"] - 1
        out.p(f"    {key} vs shipped: term retention {gain * 100:+.1f} pts, prompt size {cost * 100:+.0f}% -> "
              f"{'bar met on retention (but weigh the prompt-size cost)' if gain >= BAR_GAIN else 'bar not met'}")
    out.p()


# --- R8 -----------------------------------------------------------------------------------------------------------


def write_sheet(path: Path, sets, version: str):
    sample = ml.review_sample(sets, seed=SEED)
    lines = [
        "# Review sheet: 24 questions from the six Gemini sets (SPEC-25 R8)",
        "",
        f"SET_VERSION `{version[:16]}`. Seed {SEED}. Four questions per set, one of each kind. Fill the two boxes for each question:",
        "put `y` or `n`. The bar is 22 of 24 `y` on **each** box (90%). Below that, the sets are not used as a gate until fixed.",
        "",
        "- *Realistic?* Would a learner plausibly type or paste this?",
        "- *Page right?* Is the expected page really the best place in the docs to answer it? (The expected path is the folder or page name.)",
        "",
        "| # | Set / kind | Question | Expected page | Realistic? | Page right? |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, item in enumerate(sample, start=1):
        q = " ".join(item["q"].split())
        q = (q[:160] + "...") if len(q) > 160 else q
        q = q.replace("|", "\\|")
        lines.append(f"| {i} | {item['set']} / {item['kind']} | {q} | `{', '.join(item['expect'])}` | [ ] | [ ] |")
    lines += ["", "Totals: realistic ___ / 24, page right ___ / 24.", ""]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


# --- main --------------------------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ragcore-root", default="")
    ap.add_argument("--index-dir", default=str(ROOT / "data" / "index"))
    ap.add_argument("--ragcore-index-dir", default=str(Path.home() / ".ragcore" / "lms-measure"))
    ap.add_argument("--modes", default="lms,L,HR")
    ap.add_argument("--sections", default="baseline,misses,passages,tuning,sheet")
    ap.add_argument("--date", default="2026-11-18")
    ap.add_argument("--embedder", default="jina-v2-base-en")
    ap.add_argument("--reranker", default="bge-reranker-v2-m3")
    ap.add_argument("--out-dir", default=str(ROOT / "docs" / "measurements"))
    args = ap.parse_args()
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    sections = {s.strip() for s in args.sections.split(",")}
    index_dir = Path(args.index_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    version = ml.set_version()
    sets = ml.load_gemini_sets()

    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
    from lms.adapters.ai.rag.retriever import HybridRerankedRetriever

    keyword = KeywordRetriever.from_index_dir(index_dir)
    if keyword.manifest is None:
        print(f"No index at {index_dir}: {keyword.no_index_reason}")
        return 2
    index_version = keyword.manifest.index_version
    rows_src = [json.loads(ln) for ln in (index_dir / "sources.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    corpus_ids = [r["source_id"] for r in rows_src]
    engine = HybridRerankedRetriever.load(index_dir)

    out = Out()
    out.p("SPEC-25 measurement on the six Gemini sets")
    out.p(f"set_version {version}")
    out.p(f"index_version {index_version}  ({len(corpus_ids)} files, {len(engine.passages)} passages)")
    out.p(f"date {args.date}; modes {','.join(modes)}; offline, no paid call; scores are rounded, no timings (R11)")
    out.p("Metrics are over answerable questions only. K counts files for L/HR (one passage per file) and for lms (cap 1).")
    out.p("nDCG ideal = every corpus file that matches an expect piece, so a broad piece (for example 'models') lowers nDCG even for a rank-1 hit.")
    out.p("The rag-core sync timing line is left out of this file so the numbers repeat exactly (R11).\n")
    out.data.update({"set_version": version, "index_version": index_version, "date": args.date, "modes": modes})

    items = [(n, sets[n]["prefix"], sets[n]["questions"]) for n in sorted(sets)]
    no_answer = [q for n in sorted(sets) for q in sets[n]["out_of_scope"]]
    searchers = {"lms": lms_searcher(keyword)} if "lms" in modes else {}
    closers: list = []
    ragnote = ""
    if any(m in modes for m in ("L", "HR")):
        if not args.ragcore_root:
            print("--ragcore-root is needed for modes L and HR")
            return 2
        rs, closers, ragnote = ragcore_searchers(Path(args.ragcore_root), rows_src, Path(args.ragcore_index_dir), modes,
                                                 args.embedder, args.reranker,
                                                 lambda t: [out.p(ln) for ln in t.splitlines() if "second" not in ln])
        searchers.update(rs)
        out.p(f"rag-core: {ragnote}\n")
        out.data["ragcore"] = ragnote

    try:
        if "baseline" in sections or "misses" in sections:
            out.p("=" * 100)
            out.p("R5. BASELINE: the six Gemini sets (240 answerable, 60 out-of-scope)")
            out.p("=" * 100)
            gemini_rows = {}
            for mode in modes:
                rows, a, o, sc = evaluate(searchers[mode], items, no_answer, corpus_ids)
                gemini_rows[mode] = rows
                stamp = f"set_version={version[:12]} index_version={index_version[:12]} mode={mode} date={args.date}"
                report_mode(out, f"gemini/{mode}", stamp, rows, a, o, sc, refusal=(mode == "lms"))

            out.p("=" * 100)
            out.p("Old sets, same modes, for before/after (rag-core real-corpus sets; SPEC-20 fixture)")
            out.p("=" * 100)
            if args.ragcore_root:
                o_items, o_no = old_sets(Path(args.ragcore_root), corpus_ids)
                for mode in modes:
                    rows, a, o, sc = evaluate(searchers[mode], [(n, p, q) for n, p, q in o_items], o_no, corpus_ids)
                    stamp = f"set_version=n/a (rag-core sets, unversioned) old real-corpus sets ({sum(len(q) for _, _, q in o_items)} answerable, {len(o_no)} no-answer) index_version={index_version[:12]} mode={mode} date={args.date}"
                    report_mode(out, f"old-real/{mode}", stamp, rows, a, o, sc, refusal=(mode == "lms"))
            else:
                out.p("  (old real-corpus sets need --ragcore-root; skipped)\n")
            fixture_block(out, args, modes)

        if "misses" in sections and "lms" in modes:
            out.p("=" * 100)
            out.p("R6. MISS ANALYSIS: answerable questions that miss at K=3, one label each (rule-based, fixed order)")
            out.p("=" * 100)
            for mode in modes:
                miss_analysis(out, f"gemini/{mode}", gemini_rows[mode], engine, corpus_ids, examples=(mode == "lms"))
        if "passages" in sections:
            out.p("=" * 100)
            passages_test(out, index_dir, sets)
        if "tuning" in sections:
            out.p("=" * 100)
            tuning(out, index_dir, sets)
        if "sheet" in sections:
            write_sheet(out_dir / f"{args.date}-gemini-review-sheet.md", sets, version)
            out.p(f"Review sheet written: {args.date}-gemini-review-sheet.md")
    finally:
        for c in closers:
            c.close()

    if "baseline" in sections:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.date}-gemini-baseline.txt").write_text("\n".join(out.lines) + "\n", encoding="utf-8", newline="\n")
        (out_dir / f"{args.date}-gemini-baseline.json").write_text(
            json.dumps(rnd(out.data), indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    return 0


def fixture_block(out: Out, args, modes):
    """The SPEC-20 fixture (41 answerable, 9 no-answer) in each mode, for before/after (the CI floor set)."""
    import retrieval_quality as rq
    from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever

    qs = rq.load_questions()
    ans = [q for q in qs if q["expected_source"]]
    no = [q for q in qs if not q["expected_source"]]
    items = [("spec20-fixture", "", [{"q": q["question"], "expect": [q["expected_source"]], "kind": q["kind"]} for q in ans])]
    no_q = [{"q": q["question"]} for q in no]
    fixture_ids = sorted(p.name for p in (rq.SET_DIR / "docs").glob("*.md"))
    adapter = KeywordRetriever.from_hybrid(rq.build_keyword_retriever(), min_matched_terms=2)
    searchers = {"lms": lms_searcher(adapter)} if "lms" in modes else {}
    closers: list = []
    if any(m in modes for m in ("L", "HR")) and args.ragcore_root:
        import hashlib as _h
        from ragcore.contracts import normalize_text

        rows = []
        for path in sorted((rq.SET_DIR / "docs").glob("*.md")):
            text = normalize_text(path.read_text(encoding="utf-8"))
            rows.append({"source_id": path.name, "version": "fixture-1", "text": text,
                         "raw_sha256": _h.sha256(text.encode()).hexdigest(), "loader_version": "markdown-fixture-1",
                         "licence": "CC0-1.0", "licence_basis": "declared"})
        with tempfile.TemporaryDirectory() as tmp:
            rs, closers, _ = ragcore_searchers(Path(args.ragcore_root), rows, Path(tmp), modes, args.embedder, args.reranker, lambda _t: None)
            searchers.update(rs)
            run_fixture(out, items, no_q, fixture_ids, searchers, modes, args)
            for c in closers:
                c.close()
        return
    run_fixture(out, items, no_q, fixture_ids, searchers, modes, args)


def run_fixture(out, items, no_q, fixture_ids, searchers, modes, args):
    import retrieval_quality as rq

    floor = rq.load_floor()
    for mode in modes:
        rows, a, o, sc = evaluate(searchers[mode], items, no_q, fixture_ids)
        stamp = f"set_version=fixture-{floor['set_version']} SPEC-20 fixture (41 answerable, 9 no-answer; lms uses min 2 terms) mode={mode} date={args.date}"
        report_mode(out, f"fixture/{mode}", stamp, rows, a, o, sc, refusal=(mode == "lms"), by_set=False)
        if mode == "lms":
            first = sum(r["flags"][0] for r in rows)
            top3 = sum(any(r["flags"][:3]) for r in rows)
            out.p(f"  CI floor check: first_hit {first} (floor {floor['first_hit']}), top3 {top3} (floor {floor['top3']}) -> "
                  f"{'not below the floor' if first >= floor['first_hit'] and top3 >= floor['top3'] else 'BELOW THE FLOOR: stop and report'}\n")


if __name__ == "__main__":
    sys.exit(main())
