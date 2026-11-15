"""Score ragcore L (keyword only) and HR (hybrid + reranker) on the SPEC-20 question set. Not run in CI.

ragcore, torch and the pinned models live in the rag-core checkout, so run this with ITS interpreter:

    D:\\01-Project\\rag-core\\.venv\\Scripts\\python.exe scripts/measure_ragcore.py --ragcore-root D:\\01-Project\\rag-core

It builds a throwaway index from tests/fixtures/retrieval/docs in a temp folder (nothing is written
into either repo), then reads it back with Retriever.open(), the way the LMS adapter will.
It imports nothing from `lms`. ADR-0035 2.6 decision (a); SPEC-20 section 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SET_DIR = ROOT / "tests" / "fixtures" / "retrieval"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ragcore-root", required=True, help="the rag-core checkout (for configs/)")
    ap.add_argument("--modes", default="L,HR")
    ap.add_argument("--embedder", default="jina-v2-base-en")
    ap.add_argument("--reranker", default="bge-reranker-v2-m3")
    args = ap.parse_args()
    rc_root = Path(args.ragcore_root)

    from importlib import metadata

    from ragcore import IndexSetup, Retriever, open_index
    from ragcore.chunking import ChunkConfig
    from ragcore.contracts import Source, normalize_text
    from ragcore.embed.base import load_model_specs
    from ragcore.index_sync import sync
    from ragcore.llamaindex_chunker import LlamaIndexChunker, llamaindex_version
    from ragcore.rerank import load_reranker_specs
    from ragcore.stage import make_embedder
    from ragcore.stage3 import make_reranker

    questions = json.loads((SET_DIR / "questions.json").read_text(encoding="utf-8"))["questions"]
    answerable = [q for q in questions if q["expected_source"]]
    unanswerable = [q for q in questions if not q["expected_source"]]

    sources = []
    for path in sorted((SET_DIR / "docs").glob("*.md")):
        text = normalize_text(path.read_text(encoding="utf-8"))
        sources.append(Source(path.name, "fixture-1", text, hashlib.sha256(text.encode()).hexdigest(),
                              "markdown-fixture-1", "CC0-1.0", "declared"))

    config = ChunkConfig()
    models, rerankers = rc_root / "configs" / "models.yaml", rc_root / "configs" / "rerankers.yaml"
    model = load_model_specs(models)[args.embedder]
    rspec = load_reranker_specs(rerankers)[args.reranker]
    revision = model.revision + (f"+{model.code_revision}" if model.code_revision else "")
    setup = IndexSetup(model.id, revision, "llamaindex", llamaindex_version(config),
                       f"{config.max_chars}/{config.hard_limit}",
                       metadata.version("llama-index-core"), rspec.id, rspec.revision)

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    embedder = make_embedder(args.embedder, models)  # also needed to build the index
    reranker = make_reranker(args.reranker, rerankers)[0] if "HR" in modes else None
    chunker = LlamaIndexChunker()

    with tempfile.TemporaryDirectory() as tmp:
        index = Path(tmp) / "fixture-index.db"
        t0 = time.perf_counter()
        with open_index(index, setup) as store:
            report = sync(sources, store, lambda s: chunker(s, config), embedder)
        print(report.render())
        print(f"index built in {time.perf_counter() - t0:.1f} s; set: {len(answerable)} answerable, "
              f"{len(unanswerable)} no-answer\n")

        for mode in modes:
            kwargs = dict(embedder=embedder, reranker=reranker) if mode == "HR" else {}
            with Retriever.open(index, setup, variant=mode, **kwargs) as retriever:
                first = top3 = 0
                start = time.perf_counter()
                rows = {}
                for q in questions:
                    res = retriever.search(q["question"], k=3, max_per_file=1)
                    rows[q["id"]] = res
                ms = (time.perf_counter() - start) / len(questions) * 1000
                for q in answerable:
                    ids = [r.source_id for r in rows[q["id"]]]
                    first += bool(ids) and ids[0] == q["expected_source"]
                    top3 += q["expected_source"] in ids
                print(f"== {mode}: first {first}/{len(answerable)}  top3 {top3}/{len(answerable)}  "
                      f"({ms:.0f} ms/question)")
                for q in answerable:
                    ids = [r.source_id for r in rows[q["id"]]]
                    if not ids or ids[0] != q["expected_source"]:
                        print(f"   miss {q['id']} {q['kind']:<10} got {ids}")

                def top(q):
                    r = rows[q["id"]]
                    return r[0].score if r else float("-inf")

                good = sorted(top(q) for q in answerable)
                bad = sorted(top(q) for q in unanswerable)
                print(f"   top-1 score, answerable: min {good[0]:.3f} median {good[len(good) // 2]:.3f}")
                print(f"   top-1 score, no-answer:  min {bad[0]:.3f} median {bad[len(bad) // 2]:.3f} max {bad[-1]:.3f}")
                print("   floor   answerable lost   no-answer refused")
                cands = sorted({round(s, 3) for s in good + bad})
                step = max(1, len(cands) // 12)
                for t in cands[::step]:
                    lost = sum(1 for q in answerable if top(q) < t)
                    refused = sum(1 for q in unanswerable if top(q) < t)
                    print(f"   {t:>8.3f}   {lost:>5}/{len(answerable)}         {refused}/{len(unanswerable)}")
                print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
