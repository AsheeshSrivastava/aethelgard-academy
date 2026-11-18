"""AXIS grounding is honest (ADR-0034): no fake citation, no unrelated passage, a clear label."""

from pathlib import Path

import pytest

from lms.adapters.ai.concept_store import ConceptStore
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.local_llm_companion import load_default_retriever
from fake_retriever import FakeRetriever
from lms.core.interfaces import AxisMode
from lms.core.retrieval import RetrievalStatus

FIXTURES = Path(__file__).parent / "fixtures" / "concepts"


def EmptyRetriever():
    return FakeRetriever()


@pytest.fixture
def store():
    s = ConceptStore()
    for f in sorted(FIXTURES.glob("*.md")):
        s.ingest_file(f)
    return s


def test_no_retriever_and_no_store_cites_nothing():
    text, cited = axis_rules.retrieve_grounded_passages(None, None, "PY-0.4", "why does my loop print twice")
    assert text == ""
    assert cited == []


def test_nothing_found_cites_nothing(store):
    text, cited = axis_rules.retrieve_grounded_passages(
        EmptyRetriever(), None, "PY-9.9", "zzzzqqqq xxxxwwww"
    )
    assert (text, cited) == ("", [])


def test_a_question_matching_nothing_gets_no_unrelated_passage(store):
    text, cited = axis_rules.retrieve_grounded_passages(None, store, "PY-9.9", "zzzzqqqq xxxxwwww")
    assert text == ""
    assert cited == []


def test_a_matching_question_still_cites_the_matching_passage(store):
    text, cited = axis_rules.retrieve_grounded_passages(None, store, "PY-0.4", "communication cycle")
    assert cited
    assert all(c.startswith("concepts/") for c in cited)
    assert text


def test_default_citation_no_longer_exists():
    assert not hasattr(axis_rules, "DEFAULT_CITATION")


@pytest.mark.parametrize("mode", [AxisMode.COACH, AxisMode.HYBRID, AxisMode.SOCRATIC])
def test_the_prompt_says_when_nothing_was_found(mode):
    prompt = axis_rules.build_system_prompt(mode, "", "not_found")
    assert "NO COURSE SOURCE IS AVAILABLE" in prompt
    assert "not in the course yet" in prompt.lower()


def test_no_mode_gets_a_general_knowledge_path_any_more():
    """ADR-0034 amended 2026-11-18 (SPEC-24 R4): the Coach "Not from the course" exception is gone."""
    prompt = axis_rules.build_system_prompt(AxisMode.COACH, "", "not_found")
    assert "Not from the course" not in prompt


def test_socratic_stays_socratic_when_nothing_was_found():
    prompt = axis_rules.build_system_prompt(AxisMode.SOCRATIC, "", "not_found")
    assert "STRICT INVARIANT" in prompt
    assert "Not from the course" not in prompt


def test_a_grounded_prompt_has_no_missing_notice():
    prompt = axis_rules.build_system_prompt(AxisMode.COACH, "<reference_passages>x</reference_passages>")
    assert "NO COURSE SOURCE IS AVAILABLE" not in prompt
    assert "untrusted reference material" in prompt


def test_a_missing_index_is_reported_in_plain_words(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LMS_INDEX_DIR", raising=False)
    with caplog.at_level("WARNING"):
        assert load_default_retriever().search("anything").status is RetrievalStatus.NO_INDEX
    assert "No retrieval index is loaded" in caplog.text
