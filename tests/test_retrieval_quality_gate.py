"""CI gate for keyword-only retrieval quality.

Implements: SPEC-20 sections 2, 3 and 5; ADR-0035 section 2.6 and work step 1.
"""

import json
import shutil

import pytest

import retrieval_quality as rq
from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever


def _adapter(set_dir=rq.SET_DIR):
    """The shipped keyword_only adapter, with the fixture's own minimum (SPEC-23 R8)."""
    return KeywordRetriever.from_hybrid(rq.build_keyword_retriever(set_dir), min_matched_terms=2)


def _search(adapter):
    return lambda q: [p.source_id for p in adapter.search(q, top_k=3).passages]


# --- guards on the set itself (SPEC-20 3.3) -----------------------------------


def test_set_size_is_30_to_50():
    assert 30 <= len(rq.load_questions()) <= 50


def test_question_ids_are_unique():
    ids = [q["id"] for q in rq.load_questions()]
    assert len(ids) == len(set(ids))


def test_every_expected_source_is_a_real_doc():
    assert rq.dangling_sources() == []


def test_at_least_eight_questions_have_no_answer():
    assert sum(q["expected_source"] is None for q in rq.load_questions()) >= 8


def test_question_kinds_are_known():
    assert {q["kind"] for q in rq.load_questions()} <= {"plain", "error", "paraphrase"}


def test_guard_fails_on_a_broken_copy(tmp_path):
    """A copy with a dangling expected_source is caught by the same check."""
    shutil.copytree(rq.SET_DIR, tmp_path / "set")
    qfile = tmp_path / "set" / "questions.json"
    data = json.loads(qfile.read_text(encoding="utf-8"))
    data["questions"][0]["expected_source"] = "missing.md"
    qfile.write_text(json.dumps(data), encoding="utf-8")
    assert rq.dangling_sources(tmp_path / "set") == ["Q01"]


# --- the gate (SPEC-20 3.1, 3.2) ----------------------------------------------


def test_floor_file_records_value_date_and_set_version():
    floor = rq.load_floor()
    assert {"first_hit", "top3", "date", "set_version"} <= floor.keys()
    assert floor["set_version"] == json.loads(
        (rq.SET_DIR / "questions.json").read_text(encoding="utf-8")
    )["set_version"]


def test_keyword_only_meets_the_recorded_floor():
    floor = rq.load_floor()
    result = rq.score(_search(_adapter()))
    assert result.first_hit >= floor["first_hit"], result
    assert result.top3 >= floor["top3"], result


def test_gate_fails_when_a_doc_is_dropped(tmp_path):
    """Acceptance 2: a regression (a missing source) pushes the score below the floor."""
    shutil.copytree(rq.SET_DIR, tmp_path / "set")
    for name in ("lists.md", "dicts.md", "git.md", "sql.md"):
        (tmp_path / "set" / "docs" / name).unlink()
    floor = rq.load_floor()
    result = rq.score(_search(_adapter(tmp_path / "set")))
    assert result.first_hit < floor["first_hit"] or result.top3 < floor["top3"]


def test_gate_needs_no_ragcore_or_models():
    """Run in a fresh interpreter so other tests' imports cannot affect the result."""
    import subprocess
    import sys

    code = (
        "import sys; sys.path.insert(0, 'tests'); import retrieval_quality as rq; "
        "rq.build_keyword_retriever(); "
        "assert 'ragcore' not in sys.modules and 'torch' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True, cwd=rq.SET_DIR.parents[2])


@pytest.mark.parametrize("q", [q for q in rq.load_questions() if q["expected_source"] is None])
def test_no_answer_questions_still_return_without_error(q):
    """No crash on a question with no answer; the refusal share is gated in test_query_and_not_found.py (SPEC-23 R8)."""
    _adapter().search(q["question"], top_k=3)
