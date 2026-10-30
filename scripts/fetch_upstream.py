"""Fetch and snapshot curated upstream technical documentation (Spec 03 / ADR-0003).

Usage:
    uv run python scripts/fetch_upstream.py python-docs [--ref 3.12]
    uv run python scripts/fetch_upstream.py uv-docs [--ref main]
    uv run python scripts/fetch_upstream.py ruff-docs [--ref main]
    uv run python scripts/fetch_upstream.py zed-docs [--ref main]
    uv run python scripts/fetch_upstream.py all
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from lms.core.rag.files import MIN_CHARS, snapshot_hash
from lms.adapters.ai.inspect_sources import inspect_folder
from lms.adapters.ai.loaders.registry import DEFAULT_READERS

CPYTHON_REPO = "https://github.com/python/cpython"
UV_REPO = "https://github.com/astral-sh/uv"
RUFF_REPO = "https://github.com/astral-sh/ruff"
ZED_REPO = "https://github.com/zed-industries/zed"
FASTAPI_REPO = "https://github.com/fastapi/fastapi"
PYDANTIC_REPO = "https://github.com/pydantic/pydantic"
HTTPX_REPO = "https://github.com/encode/httpx"
PYTEST_REPO = "https://github.com/pytest-dev/pytest"
RASBT_REPO = "https://github.com/rasbt/LLMs-from-scratch"
DAIR_REPO = "https://github.com/dair-ai/Prompt-Engineering-Guide"
MSFT_GENAI_REPO = "https://github.com/microsoft/generative-ai-for-beginners"
HF_COURSE_REPO = "https://github.com/huggingface/course"
DSPY_REPO = "https://github.com/stanfordnlp/dspy"
OPENAI_EVALS_REPO = "https://github.com/openai/evals"

DEFAULT_PYTHON_REF = "3.12"
DEFAULT_TOOL_REF = "main"
DEST_ROOT = Path("reference/upstream")


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    res = subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def _force_rm(path: Path) -> None:
    def on_error(action, p, exc):
        os.chmod(p, stat.S_IWRITE)
        action(p)

    if path.exists():
        if path.is_dir():
            shutil.rmtree(path, onerror=on_error)
        else:
            path.unlink()


def _sparse_fetch(repo_url: str, ref: str, patterns: list[str], work_dir: Path) -> str:
    _force_rm(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    _run_git(["init", "--quiet"], cwd=work_dir)
    _run_git(["remote", "add", "origin", repo_url], cwd=work_dir)
    _run_git(["config", "core.sparseCheckout", "true"], cwd=work_dir)
    _run_git(["sparse-checkout", "set", "--no-cone", *patterns], cwd=work_dir)
    _run_git(["fetch", "--depth", "1", "--filter=blob:none", "origin", ref], cwd=work_dir)
    _run_git(["checkout", "--quiet", "FETCH_HEAD"], cwd=work_dir)
    return _run_git(["rev-parse", "HEAD"], cwd=work_dir)


def _copy_clean_docs(
    src_dir: Path,
    dest_dir: Path,
    allowed_exts: tuple[str, ...] = (".md", ".mdx", ".rst"),
    filter_fn: Any = None,
    min_chars: int = MIN_CHARS,
) -> int:
    """Recursively copies only allowed documentation text files and licenses, excluding noise and empty stubs."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in src_dir.rglob("*"):
        if p.is_file():
            if filter_fn and not filter_fn(p):
                continue
            if "license" in p.name.lower():
                target = dest_dir / p.relative_to(src_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
                continue
            if p.suffix.lower() in allowed_exts:
                if p.suffix.lower() in DEFAULT_READERS:
                    try:
                        raw_bytes = p.read_bytes()
                        look = raw_bytes.decode("utf-8", errors="ignore")
                        look_len = len(look.strip())
                        reader = DEFAULT_READERS[p.suffix.lower()][1]
                        loaded = reader(raw_bytes)
                        out_len = len(loaded.strip())
                        # Drop files where loader stripped >80% of text (e.g., toctree index / navigation files)
                        if look_len >= MIN_CHARS and out_len < 0.2 * look_len:
                            continue
                    except Exception:
                        continue  # File is an empty stub or unparseable markup

                rel = p.relative_to(src_dir)
                target = dest_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
                count += 1
    return count


def _audit_and_save_manifest(out_dir: Path, manifest: dict) -> None:
    snap_hash = snapshot_hash(out_dir)
    files = [p.relative_to(out_dir).as_posix() for p in sorted(out_dir.rglob("*")) if p.is_file()]
    manifest["snapshot_hash"] = snap_hash
    manifest["fetched_at"] = datetime.now(timezone.utc).isoformat()
    manifest["files_count"] = len(files)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"[+] Successfully staged {len(files)} files into {out_dir}")
    print(f"[+] Pinned Commit: {manifest['commit_sha']}")
    print(f"[+] Snapshot Hash: {snap_hash}")

    print("\n[*] Running inspection audit through harmonized readers...")
    readers = {ext: r for ext, (_v, r) in DEFAULT_READERS.items()}
    report = inspect_folder(out_dir, source_id=manifest["source_id"], loaders=readers, max_skip_share=0.25)
    print(f"    Files read: {report.buckets['read']}, Skipped: {report.buckets['skipped']}")
    print(f"    Gate Status: {'PASSED' if report.gate_passed else 'FAILED'}")
    if not report.gate_passed:
        raise RuntimeError(f"Inspection gate failed for {manifest['source_id']}: {report.skipped}")


def fetch_python_docs(ref: str = DEFAULT_PYTHON_REF, dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "python-docs"
    temp_dir = dest_root / f".tmp-python-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Python Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(CPYTHON_REPO, ref, ["/Doc/tutorial/", "/Doc/reference/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        tutorial_src = temp_dir / "Doc" / "tutorial"
        reference_src = temp_dir / "Doc" / "reference"
        license_src = temp_dir / "LICENSE"

        if tutorial_src.exists():
            shutil.copytree(tutorial_src, out_dir / "tutorial")
        if reference_src.exists():
            shutil.copytree(reference_src, out_dir / "reference")
        if license_src.exists():
            shutil.copy2(license_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "python-docs",
            "title": "Python Language Official Documentation (Curated Slice)",
            "repo_url": CPYTHON_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "PSF-2.0",
            "sections": ["tutorial", "reference"],
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_uv_docs(ref: str = DEFAULT_TOOL_REF, dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "uv-docs"
    temp_dir = dest_root / f".tmp-uv-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching uv Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(UV_REPO, ref, ["/docs/", "/LICENSE-MIT", "/LICENSE-APACHE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs"
        shutil.copytree(docs_src, out_dir)

        # Remove MkDocs website template overrides (not documentation)
        _force_rm(out_dir / ".overrides")

        lic_src = temp_dir / "LICENSE-MIT"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "uv-docs",
            "title": "uv: Unified Python Package & Project Manager Documentation",
            "repo_url": UV_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_ruff_docs(ref: str = DEFAULT_TOOL_REF, dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "ruff-docs"
    temp_dir = dest_root / f".tmp-ruff-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching ruff Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(RUFF_REPO, ref, ["/docs/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs"
        shutil.copytree(docs_src, out_dir)

        # Remove MkDocs website template overrides
        _force_rm(out_dir / ".overrides")

        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "ruff-docs",
            "title": "Ruff: Extremely Fast Python Linter and Formatter Documentation",
            "repo_url": RUFF_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_zed_docs(ref: str = DEFAULT_TOOL_REF, dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "zed-docs"
    temp_dir = dest_root / f".tmp-zed-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Zed Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(ZED_REPO, ref, ["/docs/", "/LICENSE-APACHE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs"
        shutil.copytree(docs_src, out_dir)

        # Clean non-doc template files
        _force_rm(out_dir / "theme")
        for extra_file in out_dir.glob("*.hbs"):
            extra_file.unlink()
        rules_file = out_dir / ".rules"
        if rules_file.exists():
            rules_file.unlink()

        lic_src = temp_dir / "LICENSE-APACHE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "zed-docs",
            "title": "Zed: High-Performance Multiplayer Code Editor Documentation",
            "repo_url": ZED_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "Apache-2.0",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_fastapi_docs(ref: str = "master", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "fastapi-docs"
    temp_dir = dest_root / f".tmp-fastapi-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching FastAPI Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(FASTAPI_REPO, ref, ["/docs/en/docs/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs" / "en" / "docs"
        _copy_clean_docs(docs_src, out_dir, allowed_exts=(".md",))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "fastapi-docs",
            "title": "FastAPI: High-Performance Web Framework Documentation (English Slice)",
            "repo_url": FASTAPI_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_pydantic_docs(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "pydantic-docs"
    temp_dir = dest_root / f".tmp-pydantic-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Pydantic Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(PYDANTIC_REPO, ref, ["/docs/concepts/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs" / "concepts"
        _copy_clean_docs(docs_src, out_dir, allowed_exts=(".md",))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "pydantic-docs",
            "title": "Pydantic v2: Core Conceptual Documentation (Concepts Slice)",
            "repo_url": PYDANTIC_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_httpx_docs(ref: str = "master", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "httpx-docs"
    temp_dir = dest_root / f".tmp-httpx-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching HTTPX Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(HTTPX_REPO, ref, ["/docs/", "/LICENSE.md"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs"
        _copy_clean_docs(docs_src, out_dir, allowed_exts=(".md",))
        lic_src = temp_dir / "LICENSE.md"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "httpx-docs",
            "title": "HTTPX: Modern, Async-Ready HTTP Client Documentation",
            "repo_url": HTTPX_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "BSD-3-Clause",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_pytest_docs(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "pytest-docs"
    temp_dir = dest_root / f".tmp-pytest-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Pytest Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(PYTEST_REPO, ref, ["/doc/en/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "doc" / "en"
        _copy_clean_docs(docs_src, out_dir, allowed_exts=(".rst", ".md"))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "pytest-docs",
            "title": "Pytest: Automated Testing Framework Documentation (English)",
            "repo_url": PYTEST_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_llms_from_scratch(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "llms-from-scratch"
    temp_dir = dest_root / f".tmp-rasbt-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching LLMs from Scratch ({ref})...\n========================================")
    try:
        patterns = [f"/ch{i:02d}/" for i in range(1, 8)] + ["/LICENSE", "/README.md"]
        commit_sha = _sparse_fetch(RASBT_REPO, ref, patterns, temp_dir)
        _force_rm(out_dir)
        _copy_clean_docs(temp_dir, out_dir, allowed_exts=(".md",))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "llms-from-scratch",
            "title": "Build a Large Language Model (From Scratch) - Sebastian Raschka",
            "repo_url": RASBT_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "Apache-2.0",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_prompt_engineering_guide(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "prompt-engineering-guide"
    temp_dir = dest_root / f".tmp-dair-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Prompt Engineering Guide ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(DAIR_REPO, ref, ["/pages/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pages_dir = temp_dir / "pages"
        # Filter strictly English mdx files, clean suffix to .md, validate content
        for p in pages_dir.rglob("*.en.mdx"):
            try:
                raw_bytes = p.read_bytes()
                look = raw_bytes.decode("utf-8", errors="ignore")
                reader = DEFAULT_READERS[".mdx"][1]
                loaded = reader(raw_bytes)
                if len(look.strip()) >= MIN_CHARS and len(loaded.strip()) < 0.2 * len(look.strip()):
                    continue
            except Exception:
                continue
            rel = p.relative_to(pages_dir)
            clean_name = rel.name.replace(".en.mdx", ".md")
            target = out_dir / rel.parent / clean_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)

        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "prompt-engineering-guide",
            "title": "DAIR.AI Prompt Engineering Guide (English Canonical Slice)",
            "repo_url": DAIR_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_generative_ai_for_beginners(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "generative-ai-for-beginners"
    temp_dir = dest_root / f".tmp-msft-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Generative AI for Beginners ({ref})...\n========================================")
    try:
        patterns = [f"/{i:02d}-*/" for i in range(22)] + ["/LICENSE", "/README.md"]
        commit_sha = _sparse_fetch(MSFT_GENAI_REPO, ref, patterns, temp_dir)
        _force_rm(out_dir)
        _copy_clean_docs(
            temp_dir,
            out_dir,
            allowed_exts=(".md",),
            filter_fn=lambda p: "translations" not in p.parts,
        )
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "generative-ai-for-beginners",
            "title": "Microsoft Generative AI for Beginners (21 English Lessons)",
            "repo_url": MSFT_GENAI_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_huggingface_course(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "huggingface-course"
    temp_dir = dest_root / f".tmp-hf-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching Hugging Face Course ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(HF_COURSE_REPO, ref, ["/chapters/en/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "chapters" / "en"
        _copy_clean_docs(docs_src, out_dir, allowed_exts=(".mdx", ".md"))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "huggingface-course",
            "title": "Hugging Face NLP & Transformers Course (English Chapters)",
            "repo_url": HF_COURSE_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "Apache-2.0",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_dspy_docs(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "dspy-docs"
    temp_dir = dest_root / f".tmp-dspy-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching DSPy Docs ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(DSPY_REPO, ref, ["/docs/", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        docs_src = temp_dir / "docs"
        _copy_clean_docs(docs_src, out_dir, allowed_exts=(".md",))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "dspy-docs",
            "title": "DSPy: Programming Foundation Models Documentation",
            "repo_url": DSPY_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


def fetch_openai_evals(ref: str = "main", dest_root: Path = DEST_ROOT) -> Path:
    out_dir = dest_root / "openai-evals"
    temp_dir = dest_root / f".tmp-evals-{int(time.time())}"
    print(f"\n========================================\n[*] Fetching OpenAI Evals ({ref})...\n========================================")
    try:
        commit_sha = _sparse_fetch(OPENAI_EVALS_REPO, ref, ["/docs/", "/README.md", "/LICENSE"], temp_dir)
        _force_rm(out_dir)
        _copy_clean_docs(temp_dir, out_dir, allowed_exts=(".md",))
        lic_src = temp_dir / "LICENSE"
        if lic_src.exists():
            shutil.copy2(lic_src, out_dir / "LICENSE")

        manifest = {
            "source_id": "openai-evals",
            "title": "OpenAI Evals Framework & Evaluation Protocols Documentation",
            "repo_url": OPENAI_EVALS_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "MIT",
        }
        _audit_and_save_manifest(out_dir, manifest)
    finally:
        _force_rm(temp_dir)
    return out_dir


ALL_TARGETS = {
    "python-docs": fetch_python_docs,
    "uv-docs": fetch_uv_docs,
    "ruff-docs": fetch_ruff_docs,
    "zed-docs": fetch_zed_docs,
    "fastapi-docs": fetch_fastapi_docs,
    "pydantic-docs": fetch_pydantic_docs,
    "httpx-docs": fetch_httpx_docs,
    "pytest-docs": fetch_pytest_docs,
    "llms-from-scratch": fetch_llms_from_scratch,
    "prompt-engineering-guide": fetch_prompt_engineering_guide,
    "generative-ai-for-beginners": fetch_generative_ai_for_beginners,
    "huggingface-course": fetch_huggingface_course,
    "dspy-docs": fetch_dspy_docs,
    "openai-evals": fetch_openai_evals,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and snapshot curated upstream technical documentation.")
    parser.add_argument("target", choices=[*ALL_TARGETS.keys(), "backend", "ai", "all"], help="Target documentation to fetch")
    parser.add_argument("--ref", default="", help="Optional Git ref override")
    args = parser.parse_args(argv)

    if args.target == "all":
        targets = list(ALL_TARGETS.keys())
    elif args.target == "backend":
        targets = ["python-docs", "uv-docs", "ruff-docs", "zed-docs", "fastapi-docs", "pydantic-docs", "httpx-docs", "pytest-docs"]
    elif args.target == "ai":
        targets = ["llms-from-scratch", "prompt-engineering-guide", "generative-ai-for-beginners", "huggingface-course", "dspy-docs", "openai-evals"]
    else:
        targets = [args.target]

    for t in targets:
        fn = ALL_TARGETS[t]
        if args.ref:
            fn(ref=args.ref)
        else:
            fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
