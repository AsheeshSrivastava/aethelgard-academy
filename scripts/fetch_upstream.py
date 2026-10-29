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

from lms.core.rag.files import snapshot_hash
from lms.adapters.ai.inspect_sources import inspect_folder
from lms.adapters.ai.loaders.registry import DEFAULT_READERS

CPYTHON_REPO = "https://github.com/python/cpython"
UV_REPO = "https://github.com/astral-sh/uv"
RUFF_REPO = "https://github.com/astral-sh/ruff"
ZED_REPO = "https://github.com/zed-industries/zed"

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and snapshot curated upstream technical documentation.")
    parser.add_argument("target", choices=["python-docs", "uv-docs", "ruff-docs", "zed-docs", "all"], help="Target documentation to fetch")
    parser.add_argument("--ref", default="", help="Optional Git ref override")
    args = parser.parse_args(argv)

    if args.target in ("uv-docs", "all"):
        fetch_uv_docs(ref=args.ref or DEFAULT_TOOL_REF)
    if args.target in ("ruff-docs", "all"):
        fetch_ruff_docs(ref=args.ref or DEFAULT_TOOL_REF)
    if args.target in ("zed-docs", "all"):
        fetch_zed_docs(ref=args.ref or DEFAULT_TOOL_REF)
    if args.target == "python-docs":
        fetch_python_docs(ref=args.ref or DEFAULT_PYTHON_REF)
    return 0


if __name__ == "__main__":
    sys.exit(main())
