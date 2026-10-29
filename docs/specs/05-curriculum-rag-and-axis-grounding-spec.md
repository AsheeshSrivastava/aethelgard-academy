# Specification 05: Curriculum RAG & AXIS Grounding Contracts

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed By:** 
  - `ADR-0003: Two-Stage RAG: Upstream Research vs. Downstream AXIS AI Grounding`
  - Upstream reference contracts in `rag-core` (ADR 0003 / Spec 01)
- **Domain:** Curriculum Knowledge Ingestion, Mechanical Passage Verification & AXIS Grounding
- **Date:** 2026-10-30

---

## 1. Purpose & Architectural Context

To eliminate educational hallucinations and guarantee 100% citation provenance, the LMS Platform's RAG subsystem adopts the exact contract primitives established in the research engine (`rag-core`):

1. **Canonical Text Invariance:** All curriculum and concept text must be normalized via `normalize_text()` (Unicode NFC, standard LF line endings, no BOM).
2. **Immutable Provenance (`Source`):** Every ingested concept note is tracked with its `source_id`, `version`, `licence` (e.g. `Proprietary-LMS` or open standards), `licence_basis`, and cryptographic SHA-256 hashes (`raw_sha256`, `text_sha256`).
3. **Mechanical Quotation Verification (`Passage`):** AXIS AI citations are represented as deterministic `Passage` slices. The platform can mechanically verify (`verify_passage`) that a cited quotation is an exact substring slice of the canonical source text.

---

## 2. Shared Data Contract

### 2.1 Text Normalization
* `normalize_text(text: str) -> str`
  * Strips leading BOM (`\ufeff`).
  * Normalizes Unicode to NFC form.
  * Standardizes line endings: `\r\n` $\rightarrow$ `\n` and lone `\r` $\rightarrow$ `\n`.
  * Idempotent; preserves all other indentation and whitespace.

### 2.2 Core Objects
* **`Source`**:
  * Fields: `source_id`, `version`, `text`, `raw_sha256`, `loader_version`, `licence`, `licence_basis`, `normalizer_version`, `schema_version`, `text_sha256`.
  * Validation: Immutable/frozen. Ensures `normalize_text(text) == text` and `raw_sha256` is a 64-char hex string.
* **`Span`**:
  * Fields: `start: int`, `end: int`, `headings: tuple[str, ...]`.
  * Invariant: `0 <= start < end`.
* **`Passage`**:
  * Fields: `source_id`, `version`, `start`, `end`, `text`, `headings`, `chunker_version`, `passage_id`, `content_id`.
  * Deterministic ID: `passage_id = make_passage_id(source_id, version, start, end, content_id, chunker_version)`.
  * Invariant: `verify_passage(source, passage) == True`.

---

## 3. Grounded AXIS Companion Query Envelope

When AXIS AI consults the RAG knowledge store, it returns citations adhering to the `Passage` schema:

```python
class GroundedAxisResponse(BaseModel):
    reply: str
    suggested_action: Optional[str] = None
    cited_passages: List[str] = []         # List of verified passage_ids
    detected_assistance_level: AssistanceLevel
```

---

## 4. Non-Functional Requirements (NFRs)

1. **Zero Drift:** Hash and passage ID generation in `lms` is 100% byte-for-byte identical to `rag-core`.
2. **Deterministic Verification:** Verifying a cited passage takes $< 0.1$ms.
3. **Self-Validating:** Objects raise `ContractError` immediately on initialization if any rule is violated.
