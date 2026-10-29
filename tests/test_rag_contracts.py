import pytest
from lms.core.rag_contracts import (
    ContractError,
    Passage,
    Source,
    Span,
    content_sha256,
    make_passage_id,
    make_passages,
    normalize_text,
    verify_passage,
)


def test_normalize_text_properties():
    # Strips BOM
    assert normalize_text("\ufeffhello") == "hello"

    # Standardizes CRLF and lone CR to LF
    assert normalize_text("line1\r\nline2\rline3\n") == "line1\nline2\nline3\n"

    # Idempotent
    sample = "concept:\n  title: Types\n"
    assert normalize_text(normalize_text(sample)) == normalize_text(sample)


def test_source_creation_and_validation():
    text = normalize_text("Python values have types that dictate valid operations.")
    raw_hash = "a" * 64

    source = Source(
        source_id="concepts/py-1.2-types",
        version="v1.0.0",
        text=text,
        raw_sha256=raw_hash,
        loader_version="1.0",
        licence="Proprietary-LMS",
        licence_basis="declared",
    )
    assert source.source_id == "concepts/py-1.2-types"
    assert source.text_sha256 == content_sha256(text)

    # Rejection of un-normalized text
    with pytest.raises(ContractError):
        Source(
            source_id="bad",
            version="v1",
            text="unnormalized\r\ntext",
            raw_sha256=raw_hash,
            loader_version="1.0",
            licence="Proprietary-LMS",
            licence_basis="declared",
        )

    # Rejection of invalid sha256
    with pytest.raises(ContractError):
        Source(
            source_id="bad_hash",
            version="v1",
            text=text,
            raw_sha256="not-a-valid-hex-hash",
            loader_version="1.0",
            licence="Proprietary-LMS",
            licence_basis="declared",
        )


def test_span_validation():
    span = Span(start=0, end=10, headings=("Types", "Int"))
    assert span.start == 0
    assert span.end == 10

    with pytest.raises(ContractError):
        Span(start=10, end=5)

    with pytest.raises(ContractError):
        Span(start=-1, end=5)


def test_make_passages_and_mechanical_verification():
    raw_text = "Variables bind names to values. Values possess distinct data types."
    text = normalize_text(raw_text)
    raw_hash = "b" * 64

    source = Source(
        source_id="concepts/py-1.1-variables",
        version="commit123",
        text=text,
        raw_sha256=raw_hash,
        loader_version="1.0",
        licence="Proprietary-LMS",
        licence_basis="declared",
    )

    # Create spans
    span1 = Span(start=0, end=31, headings=("Variables",))
    span2 = Span(start=32, end=len(text), headings=("Types",))

    passages = make_passages(source, [span1, span2], chunker_version="1.0")
    assert len(passages) == 2
    assert passages[0].text == "Variables bind names to values."
    assert passages[1].text == "Values possess distinct data types."

    # Mechanical verification
    assert verify_passage(source, passages[0]) is True
    assert verify_passage(source, passages[1]) is True

    # Tampered passage fails verification
    tampered_passage = Passage(
        source_id=source.source_id,
        version=source.version,
        start=span1.start,
        end=span1.end,
        text="Tampered text that is not in the source.",
        headings=span1.headings,
        chunker_version="1.0",
        passage_id=make_passage_id(
            source.source_id,
            source.version,
            span1.start,
            span1.end,
            content_sha256("Tampered text that is not in the source."),
            "1.0",
        ),
    )
    assert verify_passage(source, tampered_passage) is False
