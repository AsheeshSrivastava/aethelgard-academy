"""SPEC-21: the retrieval port, result type, manifest and startup load.

Implements: ADR-0035 sections 2.2, 2.3, 2.7 and work step 3. Test numbers match SPEC-21 section 4.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

import retrieval_quality as rq
from fake_retriever import FakeRetriever, passage
from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever, read_manifest
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever, KeywordHit
from lms.adapters.ai.rag.startup import RetrievalConfigError, build_retriever
from lms.core.retrieval import (
    MAX_TOP_K,
    IndexManifest,
    RetrievalMode,
    RetrievalResult,
    RetrievalStatus,
    SourceRecord,
    compute_index_version,
)

REPO = Path(__file__).resolve().parents[1]


def saved_index(tmp_path: Path, name: str = "index") -> Path:
    """Write the SPEC-20 fixture set to disk in the same layout as data/index."""
    target = tmp_path / name
    rq.build_keyword_retriever().save(target)
    return target


class BrokenHybrid:
    """Stands in for an adapter fault (a bug or a corrupt structure inside the engine)."""

    sources: dict = {}
    passages: dict = {"p": object()}

    def keyword_search(self, query):
        raise RuntimeError("engine fault")


def _ok_fake():
    return FakeRetriever((passage("a.md", "alpha beta"), passage("b.md", "gamma")))


# --- 1. Port contract, against both adapters (R1) -----------------------------------------------

CONTRACT = [
    ("fake-ok", lambda tp: _ok_fake(), "alpha", RetrievalStatus.OK),
    ("fake-not-found", lambda tp: FakeRetriever(), "alpha", RetrievalStatus.NOT_FOUND),
    ("fake-no-index", lambda tp: FakeRetriever(status=RetrievalStatus.NO_INDEX), "alpha", RetrievalStatus.NO_INDEX),
    ("fake-unavailable", lambda tp: FakeRetriever(status=RetrievalStatus.UNAVAILABLE), "alpha", RetrievalStatus.UNAVAILABLE),
    ("kw-ok", lambda tp: KeywordRetriever.from_index_dir(saved_index(tp), min_matched_terms=2), "How do I sort a list in Python?", RetrievalStatus.OK),
    ("kw-not-found", lambda tp: KeywordRetriever.from_index_dir(saved_index(tp), min_matched_terms=2), "   ", RetrievalStatus.NOT_FOUND),
    ("kw-no-index", lambda tp: KeywordRetriever.from_index_dir(tp / "missing"), "anything", RetrievalStatus.NO_INDEX),
    ("kw-unavailable", lambda tp: KeywordRetriever.from_hybrid(BrokenHybrid()), "anything", RetrievalStatus.UNAVAILABLE),
]


@pytest.mark.parametrize("case,make,query,expected", CONTRACT, ids=[c[0] for c in CONTRACT])
def test_the_port_returns_each_status_and_never_raises(case, make, query, expected, tmp_path):
    result = make(tmp_path).search(query)
    assert isinstance(result, RetrievalResult)
    assert result.status is expected
    assert isinstance(result.mode, RetrievalMode)
    if expected is RetrievalStatus.OK:
        assert result.passages
    else:
        assert result.passages == ()
    if expected is RetrievalStatus.NO_INDEX:
        assert result.index_version == ""


def test_the_result_is_immutable():
    result = _ok_fake().search("x")
    with pytest.raises(Exception):
        result.status = RetrievalStatus.NO_INDEX  # type: ignore[misc]


# --- 2. Deterministic order (R3) ----------------------------------------------------------------


def test_results_are_ordered_by_score_then_position_and_repeat_exactly(tmp_path):
    adapter = KeywordRetriever.from_index_dir(saved_index(tmp_path))
    first = adapter.search("Python list sort", top_k=10)
    again = adapter.search("Python list sort", top_k=10)
    assert [p.passage_id for p in first.passages] == [p.passage_id for p in again.passages]
    scores = [p.score for p in first.passages]
    assert scores == sorted(scores, reverse=True)
    keyed = [(-p.score, p.source_id) for p in first.passages]
    assert keyed == sorted(keyed) or all(  # equal scores must be in a fixed order
        a[0] != b[0] or a[1] <= b[1] for a, b in zip(keyed, keyed[1:])
    )


def test_equal_scores_are_broken_by_source_then_position():
    class Tied(HybridRerankedRetriever):
        def keyword_search(self, query):
            ps = list(self.passages.values())
            return [KeywordHit(p, 1.0, 1) for p in reversed(ps)], 1

    hybrid = Tied()
    rq_retriever = rq.build_keyword_retriever()
    hybrid.sources = rq_retriever.sources
    hybrid.passages = rq_retriever.passages
    result = KeywordRetriever.from_hybrid(hybrid, min_matched_terms=1).search("anything", top_k=10)
    start = {pid: p.start for pid, p in hybrid.passages.items()}
    order = [(p.source_id, start[p.passage_id]) for p in result.passages]
    assert order == sorted(order)
    assert len(order) > 3


# --- 3. index_version (R4) ----------------------------------------------------------------------


def _records(sha_a="a" * 64, sha_b="b" * 64):
    return (
        SourceRecord("b.md", "CC0-1.0", "declared", sha_b),
        SourceRecord("a.md", "CC0-1.0", "declared", sha_a),
    )


def test_index_version_is_stable_and_independent_of_input_order():
    one = compute_index_version(_records(), "loader-1")
    assert one == compute_index_version(tuple(reversed(_records())), "loader-1")
    assert one == compute_index_version(_records(), "loader-1")
    assert len(one) == 64


def test_index_version_changes_when_one_source_changes():
    assert compute_index_version(_records(), "loader-1") != compute_index_version(_records(sha_a="c" * 64), "loader-1")


def test_index_version_changes_with_loader_version():
    assert compute_index_version(_records(), "loader-1") != compute_index_version(_records(), "loader-2")


def test_index_version_ignores_licence_text():
    other = (SourceRecord("a.md", "MIT", "detected", "a" * 64), SourceRecord("b.md", "MIT", "detected", "b" * 64))
    assert compute_index_version(other, "l") == compute_index_version(_records(), "l")


def test_manifest_is_read_from_sources_jsonl(tmp_path):
    index = saved_index(tmp_path)
    manifest = read_manifest(index)
    assert isinstance(manifest, IndexManifest)
    assert manifest.index_version == compute_index_version(manifest.sources, manifest.loader_version)
    assert {s.source_id for s in manifest.sources} == {p.name for p in (rq.SET_DIR / "docs").glob("*.md")}
    assert manifest.built_at  # a readable timestamp, not empty
    assert KeywordRetriever.from_index_dir(index).search("list").index_version == manifest.index_version


def test_changing_one_source_in_the_file_changes_the_version(tmp_path):
    index = saved_index(tmp_path)
    before = read_manifest(index).index_version
    path = index / "sources.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows[0]["raw_sha256"] = "f" * 64
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert read_manifest(index).index_version != before


# --- 4. Import loads nothing (R5) ---------------------------------------------------------------


def test_importing_the_app_module_does_not_touch_the_index(tmp_path):
    code = (
        "import sys, builtins\n"
        "opened = []\n"
        "real = builtins.open\n"
        "def spy(file, *a, **k):\n"
        "    opened.append(str(file)); return real(file, *a, **k)\n"
        "builtins.open = spy\n"
        "import lms, lms.api.app\n"
        "builtins.open = real\n"
        "assert not any('passages.jsonl' in o or 'sources.jsonl' in o or 'bm25.json' in o for o in opened), opened\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "LMS_INDEX_DIR": str(tmp_path / "does-not-exist")},
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


# --- 5. Startup (R6, R7) ------------------------------------------------------------------------


def test_default_mode_is_keyword_only_and_loads_the_index(tmp_path, caplog):
    index = saved_index(tmp_path)
    with caplog.at_level(logging.INFO):
        retriever = build_retriever({"LMS_INDEX_DIR": str(index)})
    result = retriever.search("list")
    assert result.mode is RetrievalMode.KEYWORD_ONLY
    assert result.status is RetrievalStatus.OK
    text = caplog.text
    assert "keyword_only" in text and result.index_version in text


def test_a_missing_folder_gives_no_index_and_one_logged_line(tmp_path, caplog):
    with caplog.at_level(logging.INFO):
        retriever = build_retriever({"LMS_INDEX_DIR": str(tmp_path / "nope")})
    assert retriever.search("list").status is RetrievalStatus.NO_INDEX
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING and "No retrieval index is loaded" in r.getMessage()]
    assert len(warnings) == 1


def test_the_default_folder_is_data_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    saved = tmp_path / "data" / "index"
    rq.build_keyword_retriever().save(saved)
    assert build_retriever({}).search("list").status is RetrievalStatus.OK


def test_an_unknown_mode_fails_startup_with_a_clear_message(tmp_path):
    with pytest.raises(RetrievalConfigError) as err:
        build_retriever({"LMS_RETRIEVAL_MODE": "turbo", "LMS_INDEX_DIR": str(tmp_path)})
    assert "LMS_RETRIEVAL_MODE" in str(err.value) and "turbo" in str(err.value)
    assert "keyword_only" in str(err.value)


def test_hybrid_rerank_fails_startup_until_its_adapter_exists(tmp_path):
    with pytest.raises(RetrievalConfigError) as err:
        build_retriever({"LMS_RETRIEVAL_MODE": "hybrid_rerank", "LMS_INDEX_DIR": str(tmp_path)})
    assert "not available in this build" in str(err.value)


def test_the_router_fails_startup_on_a_bad_mode_even_with_mock_ai(tmp_path, monkeypatch):
    from lms.adapters.ai.providers.router import build_default_router

    monkeypatch.setenv("MOCK_AI", "true")
    monkeypatch.setenv("LMS_RETRIEVAL_MODE", "turbo")
    with pytest.raises(RetrievalConfigError):
        build_default_router(str(tmp_path / "state.db"))


# --- 6. Interaction log (R8) --------------------------------------------------------------------


def test_the_interaction_log_entry_carries_the_retrieval_fields(tmp_path):
    from fastapi.testclient import TestClient

    from lms.adapters.ai.mock_axis import MockAxisCompanion
    from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
    from lms.api.app import create_app
    from lms.core.retrieval import RetrievalTrace

    class TracingAxis(MockAxisCompanion):
        last_retrieval = RetrievalTrace("v123", "keyword_only", "ok", 7)

    repo = SQLiteLearnerRepository(str(tmp_path / "s.db"))
    repo.initialize()
    client = TestClient(create_app(repo=repo, axis=TracingAxis(), test_mode=False))
    resp = client.post(
        "/api/v1/axis/consult",
        json={"unit_id": "PY-0.1", "mode": "Socratic", "current_activity": "Predict", "user_prompt": "Why?"},
    )
    assert resp.status_code == 200, resp.text
    events = [e for e in repo.get_interactions("default_learner") if e.event_type == "axis"]
    assert events, "no axis event was logged"
    payload = events[-1].payload
    assert payload["index_version"] == "v123"
    assert payload["retrieval_mode"] == "keyword_only"
    assert payload["retrieval_status"] == "ok"
    assert payload["latency_ms"] == 7


def test_the_companion_records_a_trace_for_each_answer():
    from lms.adapters.ai.providers import axis_rules

    fake = FakeRetriever((passage("a.md", "alpha beta", pid="a.md#1"),), index_version="v9")
    grounding, trace = axis_rules.ground_with_trace(fake, None, "PY-1.1", "alpha")
    assert grounding.ids == ["a.md#1"] and "alpha beta" in grounding.block
    assert (trace.index_version, trace.mode, trace.status) == ("v9", "keyword_only", "ok")
    assert isinstance(trace.latency_ms, int) and trace.latency_ms >= 0


# --- 7. top_k and source_prefixes (R9) ----------------------------------------------------------


@pytest.fixture
def keyword(tmp_path):
    return KeywordRetriever.from_index_dir(saved_index(tmp_path), min_matched_terms=1)


@pytest.mark.parametrize("top_k", [0, -5, 1000])
def test_top_k_is_capped_between_1_and_10(keyword, top_k):
    result = keyword.search("Python list dict git sql", top_k=top_k)
    assert 1 <= len(result.passages) <= MAX_TOP_K


def test_top_k_one_returns_one_passage(keyword):
    assert len(keyword.search("Python list", top_k=1).passages) == 1


def test_source_prefixes_restrict_results(keyword):
    result = keyword.search("sort a list", top_k=10, source_prefixes=("git",))
    assert all(p.source_id.startswith("git") for p in result.passages)


def test_a_prefix_that_matches_nothing_gives_not_found(keyword):
    assert keyword.search("sort a list", source_prefixes=("zzz-",)).status is RetrievalStatus.NOT_FOUND


def test_the_fake_follows_the_same_rules():
    fake = FakeRetriever((passage("git/a.md"), passage("sql/b.md")))
    assert [p.source_id for p in fake.search("x", source_prefixes=("sql",)).passages] == ["sql/b.md"]
    assert len(fake.search("x", top_k=0).passages) == 1


# --- 8. Regression: same numbers through the port as through the old class (R10) ----------------


def test_the_port_meets_the_recorded_floor():
    """SPEC-23 R8: the floor is measured through the shipped adapter, with the fixture's own minimum (2)."""
    floor = rq.load_floor()
    adapter = KeywordRetriever.from_hybrid(rq.build_keyword_retriever(), min_matched_terms=2)
    result = rq.score(lambda q: [p.source_id for p in adapter.search(q, top_k=3).passages])
    assert result.first_hit >= floor["first_hit"], result
    assert result.top3 >= floor["top3"], result


# --- 9. The companions use the port ------------------------------------------------------------

_OLD_CLASS = "Hybrid" + "RerankedRetriever"


@pytest.mark.parametrize(
    "path",
    [
        "src/lms/adapters/ai/gemini_companion.py",
        "src/lms/adapters/ai/local_llm_companion.py",
        "src/lms/adapters/ai/providers/router.py",
        "src/lms/adapters/ai/providers/axis_rules.py",
        "tests/test_axis_grounding.py",
        "tests/test_local_llm_companion.py",
    ],
)
def test_companions_and_their_tests_do_not_name_the_concrete_retriever(path):
    assert _OLD_CLASS not in (REPO / path).read_text(encoding="utf-8")


def test_the_core_types_import_nothing_third_party():
    lines = (REPO / "src/lms/core/retrieval.py").read_text(encoding="utf-8").splitlines()
    imports = " ".join(x for x in lines if x.startswith(("import ", "from ")))
    for banned in ("sqlite3", "ragcore", "pydantic", "lms.adapters"):
        assert banned not in imports


# --- 5 (edge cases from SPEC-21 section 5) ------------------------------------------------------


def test_a_corrupt_sources_line_gives_no_index_not_a_crash(tmp_path):
    index = saved_index(tmp_path)
    with open(index / "sources.jsonl", "a", encoding="utf-8") as f:
        f.write("{not json\n")
    result = KeywordRetriever.from_index_dir(index).search("list")
    assert result.status is RetrievalStatus.NO_INDEX


def test_sources_without_passages_gives_no_index(tmp_path):
    index = saved_index(tmp_path)
    (index / "passages.jsonl").unlink()
    assert KeywordRetriever.from_index_dir(index).search("list").status is RetrievalStatus.NO_INDEX


def test_empty_and_huge_queries_do_not_raise(keyword):
    assert keyword.search("").status is RetrievalStatus.NOT_FOUND
    assert keyword.search("list " * 2000).status in (RetrievalStatus.OK, RetrievalStatus.NOT_FOUND)


# --- Review round 1 ------------------------------------------------------------------------------


def test_ties_at_the_cut_off_are_broken_by_source_then_position():
    """SPEC-21 R3: the engine may truncate in its own order, so the adapter must not rely on it."""

    class Truncating(HybridRerankedRetriever):
        def keyword_search(self, query):
            first = {}  # one passage per source, worst order first
            for p in sorted(self.passages.values(), key=lambda x: x.start):
                first.setdefault(p.source_id, p)
            return [KeywordHit(p, 1.0, 1) for p in reversed(list(first.values()))], 1

    hybrid = Truncating()
    fixture = rq.build_keyword_retriever()
    hybrid.sources = fixture.sources
    hybrid.passages = fixture.passages
    result = KeywordRetriever.from_hybrid(hybrid, min_matched_terms=1).search("anything", top_k=2)
    one_each = {}
    for p in sorted(hybrid.passages.values(), key=lambda x: x.start):
        one_each.setdefault(p.source_id, p)
    expected = sorted((p.source_id, p.start, p.passage_id) for p in one_each.values())[:2]
    assert [(p.source_id, hybrid.passages[p.passage_id].start, p.passage_id) for p in result.passages] == expected


def test_the_startup_warning_says_why_the_index_was_not_loaded(tmp_path, caplog):
    index = saved_index(tmp_path)
    with open(index / "sources.jsonl", "a", encoding="utf-8") as f:
        f.write("{not json\n")
    with caplog.at_level(logging.WARNING):
        build_retriever({"LMS_INDEX_DIR": str(index)})
    assert "JSONDecodeError" in caplog.text
