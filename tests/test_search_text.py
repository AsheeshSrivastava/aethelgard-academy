"""SPEC-26 (ADR-0035 5.2a): search-only text for keyword search.

R1/R2 word lists, R3 found only through a path word, R4 display text unchanged, R6 index_version, setting.
"""

from __future__ import annotations

import hashlib
import json

import pytest

import retrieval_quality as rq
from lms.adapters.ai.rag.keyword_retriever import KeywordRetriever
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.adapters.ai.rag.startup import SEARCH_TEXT_ENV, RetrievalConfigError, configured_search_text
from lms.core.rag_contracts import Passage, Source, Span, make_passages
from lms.core.retrieval import SourceRecord, compute_index_version
from lms.core.search_text import (
    DEFAULT_RECIPE,
    SEARCH_TEXT_RECIPES,
    SEARCH_TEXT_VERSION,
    path_words,
    search_text,
    title_words,
)


def _source(source_id: str, text: str) -> Source:
    return Source(source_id, "v1", text, hashlib.sha256(text.encode()).hexdigest(), "t-1", "CC0-1.0", "declared")


def _passage(source_id: str, text: str = "body text here", headings: tuple[str, ...] = ()) -> Passage:
    """One passage with the given heading path (made up; the chunker is not involved)."""
    base = make_passages(_source(source_id, text), [Span(0, len(text))], chunker_version="t-1")[0]
    return Passage(base.source_id, base.version, base.start, base.end, base.text, headings, base.chunker_version, base.passage_id)


# --- R2: path words -----------------------------------------------------------------------------------


def test_path_words_keep_each_segment_whole_and_split_it():
    assert path_words("pytest-docs/how-to/tmp_path.rst") == ["how-to", "how", "to", "tmp_path", "tmp", "path"]


def test_path_words_drop_set_prefix_and_extension_and_lowercase():
    assert path_words("Set-Docs/Reference/Customize.MD") == ["reference", "customize"]


def test_path_words_split_on_dots_and_dedupe():
    assert path_words("x-docs/announce/release-5.3.3.rst") == ["announce", "release-5.3.3", "release", "5", "3"]


def test_path_words_for_an_id_with_no_slash_have_no_prefix_to_drop():
    assert path_words("classes.md") == ["classes"]
    assert path_words("how-to.md") == ["how-to", "how", "to"]


def test_path_words_keep_an_unknown_suffix_as_a_word():
    assert path_words("a-docs/notes/v1.2") == ["notes", "v1.2", "v1", "2"]


def test_path_words_of_an_empty_id_are_empty():
    assert path_words("") == []


# --- R1: title words ----------------------------------------------------------------------------------


def test_title_is_the_outermost_heading():
    p = _passage("a-docs/x/page.md", headings=("Temporary Directories", "The tmp_path fixture"))
    assert title_words(p) == ["temporary", "directories"]


def test_empty_title_falls_back_to_the_file_name():
    assert title_words(_passage("a-docs/x/notes.md")) == ["notes"]
    assert title_words(_passage("classes.md")) == ["classes"]


def test_title_words_are_deduplicated_and_lowercased():
    p = _passage("a-docs/p.md", headings=("Fixtures and FIXTURES",))
    assert title_words(p) == ["fixtures", "and"]


# --- R1/R5: the recipes -------------------------------------------------------------------------------


def test_recipe_names_and_default():
    assert DEFAULT_RECIPE == "none"
    assert list(SEARCH_TEXT_RECIPES) == ["none", "path", "title", "path_title", "path_title_x2"]


def test_search_text_by_recipe():
    p = _passage("pytest-docs/how-to/tmp_path.rst", headings=("Temporary directories",))
    assert search_text(p, "none") == ""
    assert search_text(p, "path") == "how-to how to tmp_path tmp path"
    assert search_text(p, "title") == "temporary directories"
    assert search_text(p, "path_title") == "how-to how to tmp_path tmp path temporary directories"
    both = "how-to how to tmp_path tmp path temporary directories"
    assert search_text(p, "path_title_x2") == f"{both} {both}"


def test_search_text_is_pure_and_unknown_recipe_is_an_error():
    p = _passage("a-docs/b/c.md", headings=("T",))
    assert search_text(p, "path") == search_text(p, "path")
    with pytest.raises(ValueError):
        search_text(p, "nope")


# --- R3: found only through a path word ---------------------------------------------------------------


def _engine(recipe: str) -> HybridRerankedRetriever:
    engine = HybridRerankedRetriever(search_recipe=recipe)
    engine.index_source(_source("pytest-docs/how-to/tmp_path.md", "Use this to make temporary folders in tests."))
    engine.index_source(_source("pytest-docs/other/page.md", "Something unrelated about colours and shapes."))
    return engine


def test_a_passage_found_only_through_its_path_word_is_returned():
    found = KeywordRetriever.from_hybrid(_engine("path"), min_matched_terms=1).search("tmp_path", top_k=3)
    assert [p.source_id for p in found.passages] == ["pytest-docs/how-to/tmp_path.md"]
    assert found.status.value == "ok"
    missed = KeywordRetriever.from_hybrid(_engine("none"), min_matched_terms=1).search("tmp_path", top_k=3)
    assert missed.status.value == "not_found"


def test_split_path_words_also_match():
    hits, _ = _engine("path").keyword_search("tmp")
    assert [h.passage.source_id for h in hits] == ["pytest-docs/how-to/tmp_path.md"]


def test_title_words_match_only_with_a_title_recipe():
    def build(recipe):
        e = HybridRerankedRetriever(search_recipe=recipe)
        e.index_source(_source("s-docs/a/page.md", "# Zebra crossing\n\n## Details\n\nText about stripes."))
        return e

    # 'zebra' is in the heading path anyway; use the file name for a title-only word
    e = HybridRerankedRetriever(search_recipe="title")
    e.index_source(_source("s-docs/a/page.md", "Plain text with no heading at all."))
    assert [h.passage.source_id for h in e.keyword_search("page")[0]] == ["s-docs/a/page.md"]
    assert HybridRerankedRetriever().keyword_search("page")[0] == []
    assert build("none").keyword_search("zebra")[0]  # headings were always searchable


# --- R4: what the learner sees does not change --------------------------------------------------------


def test_returned_text_and_headings_are_identical_and_free_of_extra_words():
    plain, rich = _engine("none"), _engine("path_title")
    assert plain.passages == rich.passages  # Passage objects (text, headings, ids) are equal
    r = KeywordRetriever.from_hybrid(rich, min_matched_terms=1).search("tmp_path folders", top_k=3)
    assert r.passages
    for got in r.passages:
        original = rich.passages[got.passage_id]
        assert got.text == original.text
        assert "tmp_path" not in got.text and "how-to" not in got.text
        assert not any("tmp_path" in h for h in original.headings)


# --- R6: index_version --------------------------------------------------------------------------------

_RECORDS = [SourceRecord("a/b.md", "MIT", "declared", "a" * 64), SourceRecord("c.md", "MIT", "declared", "b" * 64)]
_TODAY = "195bfc5ceb42b4abe8715eb16c28fad10b3a14a4898cd4552c3bb3b543679aa1"  # computed before SPEC-26 existed


def test_recipe_none_keeps_todays_index_version_byte_for_byte():
    assert compute_index_version(_RECORDS, "loader-1") == _TODAY
    assert compute_index_version(_RECORDS, "loader-1", "none") == _TODAY


def test_every_other_recipe_changes_the_index_version():
    versions = {name: compute_index_version(_RECORDS, "loader-1", name) for name in SEARCH_TEXT_RECIPES}
    assert len(set(versions.values())) == len(versions)


def test_the_recipe_version_string_is_mixed_in(monkeypatch):
    before = compute_index_version(_RECORDS, "loader-1", "path")
    import lms.core.retrieval as retrieval

    monkeypatch.setattr(retrieval, "SEARCH_TEXT_VERSION", SEARCH_TEXT_VERSION + "-changed")
    assert compute_index_version(_RECORDS, "loader-1", "path") != before
    assert compute_index_version(_RECORDS, "loader-1", "none") == _TODAY


def test_manifest_version_follows_the_engine_recipe():
    none = KeywordRetriever.from_hybrid(_engine("none")).manifest.index_version
    path = KeywordRetriever.from_hybrid(_engine("path")).manifest.index_version
    assert none != path
    assert none == compute_index_version(
        [SourceRecord(s.source_id, s.licence, s.licence_basis, s.raw_sha256) for s in _engine("none").sources.values()], "t-1"
    )


# --- saving and loading -------------------------------------------------------------------------------


def test_default_save_format_is_unchanged(tmp_path):
    _engine("none").save(tmp_path)
    assert "search_text_recipe" not in json.loads((tmp_path / "bm25.json").read_text(encoding="utf-8"))


def test_load_with_the_saved_recipe_keeps_it_and_another_recipe_rebuilds(tmp_path):
    _engine("path").save(tmp_path)
    same = HybridRerankedRetriever.load(tmp_path, search_recipe="path")
    assert same.keyword_search("tmp_path")[0]
    other = HybridRerankedRetriever.load(tmp_path)  # default none: rebuilt, no path words
    assert other.keyword_search("tmp_path")[0] == []
    _engine("none").save(tmp_path)
    upgraded = HybridRerankedRetriever.load(tmp_path, search_recipe="path")  # an old file gets rebuilt
    assert upgraded.keyword_search("tmp_path")[0]
    assert upgraded.passages == _engine("none").passages


def test_from_index_dir_reports_the_recipe_in_the_version(tmp_path):
    _engine("none").save(tmp_path)
    for name in ("sources.jsonl",):
        assert (tmp_path / name).exists()
    a = KeywordRetriever.from_index_dir(tmp_path).manifest.index_version
    b = KeywordRetriever.from_index_dir(tmp_path, search_recipe="path").manifest.index_version
    assert a != b


# --- the setting --------------------------------------------------------------------------------------


def test_setting_defaults_to_none_and_rejects_unknown_names():
    assert configured_search_text({}) == "none"
    assert configured_search_text({SEARCH_TEXT_ENV: ""}) == "none"
    assert configured_search_text({SEARCH_TEXT_ENV: "path_title"}) == "path_title"
    with pytest.raises(RetrievalConfigError) as exc:
        configured_search_text({SEARCH_TEXT_ENV: "bogus"})
    assert "path_title_x2" in str(exc.value)


def test_fixture_gate_still_holds_with_the_default_recipe():
    floor = rq.load_floor()
    adapter = KeywordRetriever.from_hybrid(rq.build_keyword_retriever(), min_matched_terms=floor["min_matched_terms"])
    s = rq.score(lambda q: [p.source_id for p in adapter.search(q, top_k=3).passages])
    assert s.top3 >= floor["top3"] and s.first_hit >= floor["first_hit"]
