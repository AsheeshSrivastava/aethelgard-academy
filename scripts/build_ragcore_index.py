"""Build the rag-core index (SQLite, with vectors) from the LMS loader output. Local only, never in CI (SPEC-27 R7).

    uv sync --extra retrieval
    uv run python scripts/build_ragcore_index.py            # data/index/sources.jsonl -> data/ragcore/index.db

Reads data/index/sources.jsonl (unchanged) and writes only the output file. A second run with the same
sources changes nothing. The app never builds an index; it only opens this file (ADR-0035 2.1).
The chunker and sync come from rag-core internals, as in scripts/measure_gemini.py; the models and
the index setup come from the public `ragcore.load_models`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_sources(sources_jsonl: Path) -> list[dict]:
    rows = [json.loads(line) for line in sources_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise SystemExit(f"{sources_jsonl} holds no sources")
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--index-dir", default=str(ROOT / "data" / "index"), help="folder with sources.jsonl")
    ap.add_argument("--out", default=str(ROOT / "data" / "ragcore" / "index.db"))
    ap.add_argument("--embedder", default="jina-v2-base-en")
    ap.add_argument("--reranker", default="bge-reranker-v2-m3")
    args = ap.parse_args(argv)

    rows = load_sources(Path(args.index_dir) / "sources.jsonl")
    out = Path(args.out)

    from ragcore import load_models, open_index
    from ragcore.chunking import ChunkConfig
    from ragcore.contracts import Source
    from ragcore.index_sync import sync
    from ragcore.llamaindex_chunker import LlamaIndexChunker

    embedder, _reranker, setup = load_models(args.embedder, args.reranker)
    config = ChunkConfig()
    sources = [Source(r["source_id"], r["version"], r["text"], r["raw_sha256"], r["loader_version"],
                      r["licence"], r["licence_basis"]) for r in rows]
    chunker = LlamaIndexChunker()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open_index(out, setup) as store:
        report = sync(sources, store, lambda s: chunker(s, config), embedder)
    print(report.render())
    print(f"Index file: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
