"""Snapshot and folder loader for LMS RAG: folder -> contracts.Source objects (harmonized with rag-core spec 06).

Only gated files load. Every file ends in exactly one bucket and nothing is dropped without a named reason.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from lms.core.rag_contracts import Source, normalize_text
from lms.core.rag.errors import LoadError, LoadRefused, SkipShareExceeded
from lms.core.rag.files import MAX_FILE_BYTES, classify_file, raw_problem
from lms.adapters.ai.loaders.plain import PLAIN_READERS, PLAIN_VERSION, Reader
from lms.adapters.ai.loaders.registry import DEFAULT_READERS

LOADABLE_STATUSES = ("approved", "limited")
BUCKETS = ("read", "licence", "ignored", "code-config", "skipped", "withheld")


@dataclass
class LoadResult:
    sources: list[Source] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)
    withheld: dict[str, str] = field(default_factory=dict)
    code_config: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(BUCKETS, 0))

    @property
    def skip_share(self) -> float:
        candidates = self.counts["read"] + self.counts["skipped"]
        return self.counts["skipped"] / candidates if candidates else 1.0


def load_snapshot(
    folder: Path | str,
    record: Any = None,
    rules: Any = None,
    *,
    source_id: str = "",
    version: str = "",
    licence: str = "Proprietary-LMS",
    licence_basis: str = "declared",
    readers: dict[str, tuple[str, Reader]] | None = None,
    max_skip_share: float = 0.25,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> LoadResult:
    """Load a folder of files into Source objects with full provenance."""
    folder = Path(folder)
    
    # Resolve metadata from record if present, else kwargs
    rec_id = getattr(record, "id", None) or source_id or folder.name
    rec_status = getattr(record, "status", None) or "approved"
    if rec_status not in LOADABLE_STATUSES:
        raise LoadRefused(f"{rec_id}: status is {rec_status}; only {' or '.join(LOADABLE_STATUSES)} sources load.")

    rec_version = ""
    if record is not None:
        rec_version = (
            getattr(record.fetch, "commit", "")
            if getattr(record, "fetch", None) and getattr(record.fetch, "commit", None)
            else ""
        ) or getattr(record, "version_ref", "")
    rec_version = rec_version or version
    if not rec_version:
        raise LoadRefused(f"{rec_id}: no pinned commit or version, so the text cannot be tied to a version.")

    active_readers = {ext.lower(): pair for ext, pair in (DEFAULT_READERS if readers is None else readers).items()}
    result = LoadResult()

    for path in sorted(folder.rglob("*")):
        parts = path.relative_to(folder).parts
        if ".git" in parts or not (path.is_file() or path.is_symlink()):
            continue
        rel = path.relative_to(folder).as_posix()
        bucket, reason = classify_file(rel, symlink=path.is_symlink(), loaders=active_readers)
        if bucket == "code-config":
            result.code_config.append(rel)
        if bucket != "read":
            result.counts[bucket] += 1
            if bucket == "skipped":
                result.skipped[rel] = reason
            continue

        # Check rules/licensing if provided
        if rules is not None and hasattr(rules, "check_path"):
            verdict = rules.check_path(record, rel)
            if getattr(verdict, "status", None) == "reference-only":
                result.counts["withheld"] += 1
                result.withheld[rel] = " ".join(getattr(verdict, "reasons", ["withheld"]))
                continue

        def skip(why: str) -> None:
            result.counts["skipped"] += 1
            result.skipped[rel] = why

        reader_entry = active_readers.get(path.suffix.lower())
        if reader_entry is None:
            skip("no-reader")
            continue

        try:
            raw = path.read_bytes()
        except OSError:
            skip("unreadable")
            continue

        problem = raw_problem(raw, max_file_bytes)
        if problem:
            skip(problem)
            continue

        loader_version, read_fn = reader_entry
        try:
            text = normalize_text(read_fn(raw))
        except UnicodeDecodeError:
            skip("not-utf8")
            continue
        except LoadError as exc:
            skip(str(exc))
            continue
        except Exception:
            skip("unreadable")
            continue

        if not text.strip():
            skip("empty")
            continue

        result.counts["read"] += 1
        result.sources.append(
            Source(
                source_id=f"{rec_id}/{rel}",
                version=rec_version,
                text=text,
                raw_sha256=hashlib.sha256(raw).hexdigest(),
                loader_version=loader_version,
                licence=getattr(record, "licence", licence),
                licence_basis=getattr(record, "licence_basis", licence_basis),
            )
        )

    candidates = result.counts["read"] + result.counts["skipped"]
    if candidates == 0 or result.skip_share > max_skip_share:
        raise SkipShareExceeded(
            f"{rec_id}: {result.counts['skipped']} of {result.counts['read'] + result.counts['skipped']} "
            f"files were skipped ({result.skip_share:.0%}, limit {max_skip_share:.0%}).",
            result,
        )

    return result
