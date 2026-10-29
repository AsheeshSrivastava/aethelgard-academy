"""Snapshot and folder loader test suite matching rag-core spec 06."""
import hashlib
from pathlib import Path
import shutil
from dataclasses import dataclass

import pytest

from lms.core.rag_contracts import Source, normalize_text
from lms.core.rag.errors import LoadError, LoadRefused, SkipShareExceeded
from lms.adapters.ai.loaders.plain import PLAIN_VERSION
from lms.adapters.ai.loaders.snapshot import LoadResult, load_snapshot

COMMIT = "c" * 40
LONG = "A sentence about retrieval. " * 10
DECOMPOSED_E = chr(0x65) + chr(0x301)


@dataclass
class DummyFetch:
    commit: str = COMMIT


@dataclass
class DummyRecord:
    id: str = "s1"
    status: str = "approved"
    version_ref: str = "v1"
    licence: str = "MIT"
    licence_basis: str = "detected"
    fetch: DummyFetch | None = None


def tree(root: Path, files: dict) -> Path:
    for name, data in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return root


def load(tmp_path: Path, files: dict, rec=None, **kw) -> LoadResult:
    folder = tree(tmp_path / "snap", files)
    return load_snapshot(folder, rec or DummyRecord(fetch=DummyFetch()), **kw)


# --- who may load ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["approved", "limited"])
def test_approved_and_limited_load(tmp_path, status):
    r = load(tmp_path, {"a.md": LONG}, DummyRecord(status=status, fetch=DummyFetch()))
    assert isinstance(r, LoadResult) and len(r.sources) == 1


@pytest.mark.parametrize("status", ["quarantine", "reference-only", "rejected"])
def test_other_statuses_are_refused(tmp_path, status):
    with pytest.raises(LoadRefused):
        load(tmp_path, {"a.md": LONG}, DummyRecord(status=status, fetch=DummyFetch()))


def test_a_record_with_no_version_is_refused(tmp_path):
    with pytest.raises(LoadRefused):
        load(tmp_path, {"a.md": LONG}, DummyRecord(version_ref="", fetch=None), version="")


# --- what a Source carries ------------------------------------------------------------------

def test_source_fields(tmp_path):
    r = load(tmp_path, {"docs/a.txt": LONG})
    (s,) = r.sources
    assert isinstance(s, Source)
    assert s.source_id == "s1/docs/a.txt" and s.version == COMMIT
    assert s.loader_version == PLAIN_VERSION == "plain-1"
    assert s.licence == "MIT" and s.licence_basis == "detected"
    assert s.text == LONG and s.raw_sha256 == hashlib.sha256(LONG.encode()).hexdigest()


def test_markdown_files_use_the_markdown_reader_by_default(tmp_path):
    r = load(tmp_path, {"a.md": "<Tip>\n" + LONG + "</Tip>\n", "b.mdx": LONG, "c.rst": LONG, "d.txt": LONG})
    assert {s.source_id: s.loader_version for s in r.sources} == {
        "s1/a.md": "md-1",
        "s1/b.mdx": "md-1",
        "s1/c.rst": "rst-1",
        "s1/d.txt": PLAIN_VERSION,
    }
    assert "<Tip>" not in r.sources[0].text


def test_text_is_canonical_and_raw_hash_is_of_the_original_bytes(tmp_path):
    raw = b"\xef\xbb\xbf" + ("caf" + DECOMPOSED_E + "\r\n" + LONG).encode()
    (s,) = load(tmp_path, {"a.txt": raw}).sources
    assert normalize_text(s.text) == s.text and "\r" not in s.text and DECOMPOSED_E not in s.text
    assert s.raw_sha256 == hashlib.sha256(raw).hexdigest()


# --- skipping -------------------------------------------------------------------------------

def test_named_skips_and_the_rest_still_loads(tmp_path):
    files = {f"ok{i}.md": LONG for i in range(10)}
    files.update({
        "bin.md": b"ab\x00cd",
        "bad.md": b"\xff\xfe\xfa bad",
        "empty.md": b"",
        "big.md": b"x" * 500,
        "n.ipynb": "{}",
    })
    r = load(tmp_path, files, max_file_bytes=400, max_skip_share=1.0)
    assert len(r.sources) == 10
    assert r.skipped == {
        "bin.md": "binary",
        "bad.md": "not-utf8",
        "empty.md": "empty",
        "big.md": "too-large",
        "n.ipynb": "bad-notebook",
    }


def test_a_text_that_normalises_to_blank_is_empty(tmp_path):
    r = load(tmp_path, {"a.md": LONG, "b.md": chr(0xFEFF) + "  \n"}, max_skip_share=1.0)
    assert r.skipped == {"b.md": "empty"}


def test_a_reader_that_raises_is_unreadable(tmp_path):
    def boom(raw):
        raise RuntimeError("no")

    r = load(
        tmp_path,
        {"a.md": LONG, "b.rst": LONG},
        readers={".md": ("t-1", boom), ".rst": ("t-1", lambda b: b.decode())},
        max_skip_share=1.0,
    )
    assert r.skipped == {"a.md": "unreadable"} and [s.loader_version for s in r.sources] == ["t-1"]


def test_over_the_skip_share_stops_with_the_result_attached(tmp_path):
    files = {"a.md": LONG, "b.md": b"", "c.md": b"", "d.md": LONG}
    with pytest.raises(SkipShareExceeded) as exc:
        load(tmp_path, files, max_skip_share=0.25)
    assert exc.value.result.skipped == {"b.md": "empty", "c.md": "empty"}
    assert len(exc.value.result.sources) == 2


def test_exactly_at_the_limit_passes(tmp_path):
    r = load(tmp_path, {"a.md": LONG, "b.md": LONG, "c.md": LONG, "d.md": b""}, max_skip_share=0.25)
    assert len(r.sources) == 3


def test_an_empty_folder_cannot_pass(tmp_path):
    with pytest.raises(SkipShareExceeded):
        load(tmp_path, {"p.png": b"x"}, max_skip_share=1.0)


def test_code_config_and_licence_files_are_counted_not_loaded(tmp_path):
    r = load(tmp_path, {"a.md": LONG, "LICENSE": "MIT", "x.py": "1", ".git/config": "x"})
    assert r.counts == {"read": 1, "licence": 1, "ignored": 0, "code-config": 1, "skipped": 0, "withheld": 0}
    assert r.code_config == ["x.py"]


# --- determinism ----------------------------------------------------------------------------

def test_two_runs_and_a_copy_elsewhere_give_equal_sources(tmp_path):
    files = {"b.md": LONG, "a.md": LONG + "x", "sub/c.txt": LONG + "y"}
    one = load(tmp_path, files)
    two = load_snapshot(tmp_path / "snap", DummyRecord(fetch=DummyFetch()))
    shutil.copytree(tmp_path / "snap", tmp_path / "elsewhere" / "deeper")
    three = load_snapshot(tmp_path / "elsewhere" / "deeper", DummyRecord(fetch=DummyFetch()))
    assert one.sources == two.sources == three.sources
    assert [s.source_id for s in one.sources] == ["s1/a.md", "s1/b.md", "s1/sub/c.txt"]


# --- reasons from readers ---------------------------------------------------------------------

def test_a_reader_may_refuse_a_file_with_a_reason(tmp_path):
    def refuse(raw):
        raise LoadError("stub")

    r = load(
        tmp_path,
        {"a.md": LONG, "b.txt": LONG},
        readers={".md": ("t-1", refuse), ".txt": ("t-1", lambda b: b.decode())},
        max_skip_share=1.0,
    )
    assert r.skipped == {"a.md": "stub"} and len(r.sources) == 1


def test_a_markdown_page_with_almost_nothing_left_is_a_named_stub(tmp_path):
    r = load(tmp_path, {"a.md": LONG, "tiny.md": "# Title\n\n<Tip/>\n", "b.mdx": LONG}, max_skip_share=1.0)
    assert r.skipped == {"tiny.md": "stub"}
