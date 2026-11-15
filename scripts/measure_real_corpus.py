"""Measure retrieval on the REAL LMS corpus (data/index/sources.jsonl). Local only, not CI.

Corpus: the 1,371 upstream sources the LMS indexed (python-docs, uv, ruff, pytest, fastapi, ...).
In-scope questions: rag-core's python-docs (codex + gemini), uv-docs and ruff-docs sets, plus any
learner-style YAML files you pass with --extra. Out-of-scope: rag-core's MCP-spec and OpenTelemetry sets,
whose documents are not in the LMS corpus, so the right answer is "not found".
A search is right when a returned source id contains one of the `expect` path pieces and starts
with the set's source prefix. Modes: lms (current LMS keyword search), L, HR.

Run with the rag-core interpreter (torch + cached models), with the LMS src on the path:

    $env:PYTHONPATH="D:\\01-Project\\lms\\src"; $env:HF_HUB_OFFLINE="1"
    D:\\01-Project\\rag-core\\.venv\\Scripts\\python.exe scripts/measure_real_corpus.py --ragcore-root D:\\01-Project\\rag-core

The ragcore index is built once into --index-dir (default ~/.ragcore/lms-measure) and reused.
ADR-0035 2.6 decision (a); SPEC-20 section 4.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from importlib import metadata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# (yaml file under rag-core/eval/questions, source prefix the expected pieces belong to)
IN_SCOPE = [
    ("python-docs-codex-questions.yaml", "python-docs/"),
    ("python-docs-gemini-questions.yaml", "python-docs/"),
    ("uv-docs-questions.yaml", "uv-docs/"),
    ("ruff-docs-questions.yaml", "ruff-docs/"),
]
OUT_OF_SCOPE = ["mcp-spec-questions-codex.yaml", "mcp-spec-questions-gemini.yaml",
                "opentelemetry-docs-questions-codex.yaml", "opentelemetry-docs-questions-gemini.yaml",
                "opentelemetry-genai-conventions-questions-codex.yaml",
                "opentelemetry-genai-conventions-questions-gemini.yaml"]


def load_yaml(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["questions"]


def is_right(source_id: str, prefix: str, expect: list[str]) -> bool:
    return source_id.startswith(prefix) and any(piece in source_id for piece in expect)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ragcore-root", required=True)
    ap.add_argument("--corpus", default=str(ROOT / "data" / "index" / "sources.jsonl"))
    ap.add_argument("--index-dir", default=str(Path.home() / ".ragcore" / "lms-measure"))
    ap.add_argument("--modes", default="lms,L,HR")
    ap.add_argument("--embedder", default="jina-v2-base-en")
    ap.add_argument("--reranker", default="bge-reranker-v2-m3")
    ap.add_argument("--extra", nargs="*", default=[],
                    help="learner-style YAML files: 'path::source-prefix' (in scope) or 'path::' (out of scope)")
    args = ap.parse_args()
    rc = Path(args.ragcore_root)

    in_sets: list[tuple[str, str, list[dict]]] = []
    for name, prefix in IN_SCOPE:
        in_sets.append((name, prefix, load_yaml(rc / "eval" / "questions" / name)))
    out_qs: list[dict] = []
    for name in OUT_OF_SCOPE:
        out_qs += load_yaml(rc / "eval" / "questions" / name)
    for spec in args.extra:
        path, prefix = spec.split("::")
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        qs = data.get("questions", [])
        out_qs += data.get("out_of_scope", [])  # learner-style files carry their own no-answer questions
        if prefix and qs:
            in_sets.append((Path(path).name, prefix, qs))
        elif qs:
            out_qs += qs

    rows = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r["source_id"] for r in rows]
    # A question is answerable only if one of its expected files is in THIS corpus; the LMS holds a subset
    # of rag-core's python-docs. The others become "missing" no-answer questions (a hard negative: the topic
    # exists nearby, the answering file does not).
    missing: list[dict] = []
    kept = []
    for name, prefix, qs in in_sets:
        have = [q for q in qs if any(i.startswith(prefix) and any(p in i for p in q["expect"]) for i in ids)]
        missing += [q for q in qs if q not in have]
        kept.append((name, prefix, have))
    in_sets = kept
    print(f"corpus: {len(rows)} sources; in-scope: "
          + ", ".join(f"{n} {len(q)}" for n, _, q in in_sets) + f"; out-of-scope: {len(out_qs)}\n")
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    searchers: dict[str, callable] = {}   # mode -> fn(query) -> list[(source_id, score)]
    closers = []

    if "lms" in modes:
        from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
        lms = HybridRerankedRetriever.load(ROOT / "data" / "index")
        searchers["lms"] = lambda q: [(p.source_id, 0.0) for p in lms.retrieve(q, 3)]

    if any(m in modes for m in ("L", "HR")):
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
        models, rerankers = rc / "configs" / "models.yaml", rc / "configs" / "rerankers.yaml"
        model = load_model_specs(models)[args.embedder]
        rspec = load_reranker_specs(rerankers)[args.reranker]
        revision = model.revision + (f"+{model.code_revision}" if model.code_revision else "")
        setup = IndexSetup(model.id, revision, "llamaindex", llamaindex_version(config),
                           f"{config.max_chars}/{config.hard_limit}", metadata.version("llama-index-core"),
                           rspec.id, rspec.revision)
        embedder = make_embedder(args.embedder, models)
        index = Path(args.index_dir) / "index.db"
        index.parent.mkdir(parents=True, exist_ok=True)
        sources = [Source(r["source_id"], r["version"], r["text"], r["raw_sha256"], r["loader_version"],
                          r["licence"], r["licence_basis"]) for r in rows]
        t0 = time.perf_counter()
        chunker = LlamaIndexChunker()
        with open_index(index, setup) as store:
            report = sync(sources, store, lambda s: chunker(s, config), embedder, allow_mass_delete=True)
        print(report.render() + f"\n  (sync took {time.perf_counter() - t0:.0f} s)\n")
        reranker = make_reranker(args.reranker, rerankers)[0] if "HR" in modes else None
        for mode in ("L", "HR"):
            if mode not in modes:
                continue
            kw = dict(embedder=embedder, reranker=reranker) if mode == "HR" else {}
            r = Retriever.open(index, setup, variant=mode, **kw)
            closers.append(r)
            searchers[mode] = (lambda r: lambda q: [(x.source_id, x.score)
                                                    for x in r.search(q, k=3, max_per_file=1)])(r)

    for mode in modes:
        search = searchers[mode]
        print(f"=== {mode}")
        start = time.perf_counter()
        tot = {"n": 0, "first": 0, "top3": 0}
        good_scores, results = [], {}
        for name, prefix, qs in in_sets:
            n = first = top3 = 0
            for q in qs:
                res = search(q["q"])
                results[(name, q["q"])] = res
                ids = [s for s, _ in res]
                n += 1
                first += bool(ids) and is_right(ids[0], prefix, q["expect"])
                top3 += any(is_right(i, prefix, q["expect"]) for i in ids)
                good_scores.append(res[0][1] if res else float("-inf"))
            print(f"  {name:<36} first {first:>3}/{n:<3} top3 {top3:>3}/{n:<3}")
            tot["n"] += n
            tot["first"] += first
            tot["top3"] += top3
        print(f"  {'ALL in-scope':<36} first {tot['first']:>3}/{tot['n']:<3} top3 {tot['top3']:>3}/{tot['n']:<3}"
              f"  first {tot['first'] / tot['n']:.0%} top3 {tot['top3'] / tot['n']:.0%}")
        bad_scores, miss_scores = [], []
        for pool, sink in ((out_qs, bad_scores), (missing, miss_scores)):
            for q in pool:
                res = search(q["q"])
                sink.append(res[0][1] if res else float("-inf"))
        ms = (time.perf_counter() - start) / (tot["n"] + len(out_qs) + len(missing)) * 1000
        print(f"  ({ms:.0f} ms/question)")
        if mode != "lms":
            good, bad, miss = sorted(good_scores), sorted(bad_scores), sorted(miss_scores)
            print(f"  top-1 score in-scope: p10 {good[len(good) // 10]:.2f} median {good[len(good) // 2]:.2f}; "
                  f"foreign ({len(bad)}): median {bad[len(bad) // 2]:.2f} p90 {bad[len(bad) * 9 // 10]:.2f}; "
                  f"file-missing ({len(miss)}): median {miss[len(miss) // 2]:.2f} p90 {miss[len(miss) * 9 // 10]:.2f}")
            print("  floor     in-scope lost    foreign refused   file-missing refused")
            cands = sorted(set(good + bad + miss))
            step = max(1, len(cands) // 14)
            for t in cands[::step]:
                lost = sum(s < t for s in good)
                refused = sum(s < t for s in bad)
                refused_m = sum(s < t for s in miss)
                print(f"  {t:>8.2f}  {lost:>4}/{len(good):<4} {lost / len(good):>5.0%}   "
                      f"{refused:>4}/{len(bad)} {refused / len(bad):>4.0%}   {refused_m:>4}/{len(miss)} {refused_m / len(miss):.0%}")
        print()
    for c in closers:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
