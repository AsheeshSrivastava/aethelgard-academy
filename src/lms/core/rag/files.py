"""File classification and bucket boundaries matching rag-core."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Collection

LICENCE_NAMES = (
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "COPYING",
    "COPYING.md",
    "COPYING.txt",
    "LICENSE-MIT",
    "LICENSE-APACHE",
)

TEXT_EXTS = (".md", ".mdx", ".rst", ".txt", ".html", ".htm")
NOTEBOOK_EXT = ".ipynb"
IGNORED_EXTS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tif", ".tiff", ".svg",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp3", ".mp4", ".wav", ".webm", ".mov",
    ".zip", ".gz", ".tar", ".tgz", ".7z", ".css", ".js", ".map", ".lock",
})
CODE_CONFIG_EXTS = frozenset({
    ".py", ".pyi", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh", ".bat", ".yml", ".yaml", ".json",
    ".jsonc", ".toml", ".cfg", ".ini", ".cff", ".xml", ".env", ".dot", ".inc",
})
CODE_CONFIG_NAMES = frozenset({
    "makefile", "dockerfile", ".gitkeep", ".gitignore", ".gitattributes", ".editorconfig", ".prettierignore",
    ".prettierrc", ".ignore", ".git-blame-ignore-revs", ".htaccess", ".gitmodules", ".npmrc", ".nvmrc",
    ".python-version", ".python-versions", ".textlintignore", ".dockerignore",
})
MAX_FILE_BYTES = 2 * 1024 * 1024
MIN_CHARS = 100


def is_licence(rel: str) -> bool:
    """A licence file: only at the folder root."""
    name = rel.upper()
    return "/" not in rel and (name in {n.upper() for n in LICENCE_NAMES} or name.startswith(("LICENSE", "LICENCE")))


def classify_file(rel: str, *, symlink: bool = False, loaders: Collection[str] = ()) -> tuple[str, str]:
    """(bucket, reason) for a file by its relative posix path."""
    if symlink:
        return "skipped", "symlink"
    if is_licence(rel):
        return "licence", ""
    name = PurePosixPath(rel).name
    ext = PurePosixPath(rel).suffix.lower()
    if ext in IGNORED_EXTS:
        return "ignored", ""
    if ext not in loaders and (ext in CODE_CONFIG_EXTS or name.lower() in CODE_CONFIG_NAMES):
        return "code-config", ""
    if ext not in TEXT_EXTS and ext != NOTEBOOK_EXT and ext not in loaders:
        return "skipped", "no-reader"
    return "read", ""


def raw_problem(raw: bytes, max_file_bytes: int = MAX_FILE_BYTES) -> str:
    """The skip reason for file bytes that cannot be read at all, or '' when they can."""
    if len(raw) > max_file_bytes:
        return "too-large"
    if not raw.strip():
        return "empty"
    if b"\x00" in raw:
        return "binary"
    return ""


def snapshot_hash(folder: Path) -> str:
    """sha256 over the sorted relative paths and file bytes."""
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if ".git" in path.relative_to(folder).parts or path.is_symlink() or not path.is_file():
            continue
        digest.update(path.relative_to(folder).as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return "sha256:" + digest.hexdigest()

