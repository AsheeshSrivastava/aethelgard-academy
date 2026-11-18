"""SPEC-25 R1: the six Gemini question files in eval/gemini-sets/ (no corpus text, no answers)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import measure_lib as ml  # noqa: E402

SETS_DIR = ROOT / "eval" / "gemini-sets"
EXPECTED = {"fastapi-docs", "httpx-docs", "pydantic-docs", "pytest-docs", "python-docs", "uv-docs"}
ALLOWED_FIELDS = {"q", "kind", "expect", "why"}
KINDS = {"plain", "error", "paraphrase", "pasted"}


def _files():
    return sorted(SETS_DIR.glob("*.yaml"))


def test_the_six_files_are_there():
    assert {f.stem for f in _files()} == EXPECTED


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.stem)
def test_each_file_has_40_answerable_and_10_out_of_scope(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(data) == {"questions", "out_of_scope"}
    assert len(data["questions"]) == 40
    assert len(data["out_of_scope"]) == 10
    for kind in KINDS:
        assert sum(q["kind"] == kind for q in data["questions"]) == 10


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.stem)
def test_only_allowed_fields_and_expect_is_a_list_of_path_pieces(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for q in data["questions"] + data["out_of_scope"]:
        assert set(q) <= ALLOWED_FIELDS, q
        assert q["q"].strip()
    for q in data["questions"]:
        assert isinstance(q["expect"], list) and q["expect"]
        assert all(isinstance(p, str) and p and " " not in p for p in q["expect"])


def test_set_version_file_matches_the_files():
    recorded = (SETS_DIR / "SET_VERSION").read_text(encoding="utf-8").strip()
    assert recorded == ml.set_version(SETS_DIR)


def test_set_version_changes_when_a_question_changes(tmp_path):
    for f in _files():
        (tmp_path / f.name).write_bytes(f.read_bytes())
    before = ml.set_version(tmp_path)
    target = tmp_path / "uv-docs.yaml"
    target.write_text(target.read_text(encoding="utf-8").replace("how do i", "how can i", 1), encoding="utf-8")
    assert ml.set_version(tmp_path) != before


def test_set_version_ignores_line_ending_style(tmp_path):
    for f in _files():
        (tmp_path / f.name).write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert ml.set_version(tmp_path) == ml.set_version(SETS_DIR)
