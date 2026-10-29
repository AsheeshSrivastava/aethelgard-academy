"""Fetch and snapshot curated upstream technical documentation (Spec 03 / ADR-0003).

Usage:
    uv run python scripts/fetch_upstream.py python-docs [--ref 3.12]
    uv run python scripts/fetch_upstream.py uv-docs
    uv run python scripts/fetch_upstream.py ruff-docs
    uv run python scripts/fetch_upstream.py zed-docs
"""
from __future__ import annotations

import argparse
import hashlib
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
DEFAULT_REF = "3.12"
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


def fetch_python_docs(ref: str = DEFAULT_REF, dest_root: Path = DEST_ROOT) -> Path:
    """Fetch the curated Python Documentation slice: tutorial + reference + LICENSE."""
    out_dir = dest_root / "python-docs"
    temp_dir = dest_root / f".tmp-python-{int(time.time())}"
    
    _force_rm(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Initializing sparse fetch from {CPYTHON_REPO} at ref '{ref}'...")
    try:
        _run_git(["init", "--quiet"], cwd=temp_dir)
        _run_git(["remote", "add", "origin", CPYTHON_REPO], cwd=temp_dir)
        _run_git(["config", "core.sparseCheckout", "true"], cwd=temp_dir)
        _run_git(
            ["sparse-checkout", "set", "--no-cone", "/Doc/tutorial/", "/Doc/reference/", "/LICENSE"],
            cwd=temp_dir,
        )
        print("[*] Fetching documentation tree via partial clone (blobs-on-demand)...")
        _run_git(["fetch", "--depth", "1", "--filter=blob:none", "origin", ref], cwd=temp_dir)
        _run_git(["checkout", "--quiet", "FETCH_HEAD"], cwd=temp_dir)
        commit_sha = _run_git(["rev-parse", "HEAD"], cwd=temp_dir)

        # Prepare destination folder
        _force_rm(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy tutorial, reference, and LICENSE
        tutorial_src = temp_dir / "Doc" / "tutorial"
        reference_src = temp_dir / "Doc" / "reference"
        license_src = temp_dir / "LICENSE"

        if tutorial_src.exists():
            shutil.copytree(tutorial_src, out_dir / "tutorial")
        if reference_src.exists():
            shutil.copytree(reference_src, out_dir / "reference")
        if license_src.exists():
            shutil.copy2(license_src, out_dir / "LICENSE")

        # Create manifest
        snap_hash = snapshot_hash(out_dir)
        files = [p.relative_to(out_dir).as_posix() for p in sorted(out_dir.rglob("*")) if p.is_file()]
        manifest = {
            "source_id": "python-docs",
            "title": "Python Language Official Documentation (Curated Slice)",
            "repo_url": CPYTHON_REPO,
            "ref": ref,
            "commit_sha": commit_sha,
            "licence": "PSF-2.0",
            "snapshot_hash": snap_hash,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "files_count": len(files),
            "sections": ["tutorial", "reference"],
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"[+] Successfully fetched {len(files)} files into {out_dir}")
        print(f"[+] Pinned Commit: {commit_sha}")
        print(f"[+] Snapshot Hash: {snap_hash}")

    finally:
        _force_rm(temp_dir)

    # Run inspection audit
    print("\n[*] Running inspection audit through harmonized readers...")
    readers = {ext: r for ext, (_v, r) in DEFAULT_READERS.items()}
    report = inspect_folder(out_dir, source_id="python-docs", loaders=readers, max_skip_share=0.25)
    print(f"    Files read: {report.buckets['read']}, Skipped: {report.buckets['skipped']}")
    print(f"    Gate Status: {'PASSED' if report.gate_passed else 'FAILED'}")
    if not report.gate_passed:
        raise RuntimeError(f"Inspection gate failed: {report.skipped}")

    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and snapshot curated upstream technical documentation.")
    parser.add_argument("target", choices=["python-docs"], help="Which source to fetch")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git branch or tag to pin")
    args = parser.parse_args(argv)

    if args.target == "python-docs":
        fetch_python_docs(ref=args.ref)
    return 0


if __name__ == "__main__":
    sys.exit(main())
