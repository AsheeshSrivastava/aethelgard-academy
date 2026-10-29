from pathlib import Path
import pytest
from lms.adapters.ai.concept_store import ConceptStore
from lms.core.rag_contracts import verify_passage


def test_concept_store_ingestion(tmp_path):
    # Create synthetic concept note
    concept_dir = tmp_path / "concepts"
    concept_dir.mkdir()

    sample_note = (
        "---\n"
        "source_id: concepts/test-concept\n"
        "version: v1.0.0\n"
        "licence: Proprietary-LMS\n"
        "---\n"
        "# The Communication Cycle\n\n"
        "Programs communicate across boundaries using input for ingress and print for egress.\n\n"
        "Values have types that decide what operations are valid.\n"
    )
    (concept_dir / "sample.md").write_text(sample_note, encoding="utf-8")

    store = ConceptStore()
    count = store.ingest_directory(concept_dir)
    assert count == 1

    source = store.get_source("concepts/test-concept")
    assert source is not None
    assert source.licence == "Proprietary-LMS"

    passages = store.get_passages("concepts/test-concept")
    assert len(passages) >= 2

    # Every generated passage must be mechanically verified
    for p in passages:
        assert verify_passage(source, p) is True


def test_real_docs_concepts_ingestion():
    real_concepts_dir = Path("docs/concepts")
    assert real_concepts_dir.exists()

    store = ConceptStore()
    count = store.ingest_directory(real_concepts_dir)
    assert count >= 3

    sources = store.list_all_sources()
    assert len(sources) >= 3

    for source in sources:
        assert source.licence == "Proprietary-LMS"
        passages = store.get_passages(source.source_id)
        assert len(passages) > 0
        for p in passages:
            assert verify_passage(source, p) is True

