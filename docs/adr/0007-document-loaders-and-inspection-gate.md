# ADR-0007: Document Loaders, Format Normalization, and the Inspection Gate

## Status: Accepted (2026-10-30, systems-architect)

## Context
Curriculum documentation and educational notes come in diverse text formats: Markdown, MDX, reStructuredText (Sphinx), Jupyter Notebooks (.ipynb), HTML, and plain text. Naively indexing raw files results in syntax pollution (JSX components, directive markers, notebook output blobs, entity codes) that degrades embedding quality, causes hallucinated retrieval, and corrupts exact quote citations.

## Decision
1. **Harmonized Zero-Drop Loaders:** Port the format readers from `rag-core` directly into `src/lms/adapters/ai/loaders/`:
   - `markdown.py` (`md-1`): Strips JSX components, HTML comments, and imports while extracting frontmatter titles into `# Title` headings and preserving fenced code verbatim.
   - `rst.py` (`rst-1`): Converts Sphinx and Python documentation directives (`.. code-block::`, `.. note::`, `:func:`, `:class:`) into canonical markdown without syntax artifacts.
   - `html.py` (`html-1`): Standard library zero-dependency HTML parser converting headings, tables, and lists into markdown while purging scripts, navigation, and styles.
   - `notebook.py` (`ipynb-1`): Preserves author prose and fenced code cells while stripping noisy execution counts, outputs, and metadata.
   - `registry.py`: Central registry enforcing minimum character limits (`MIN_CHARS=100`) and disallowing empty stubs.
2. **Snapshot Folder Loader (`snapshot.py`):**
   - Implements `load_snapshot` with a single file classifier (`classify_file`).
   - Every file ends in exactly one bucket: `read`, `licence`, `ignored`, `code-config`, `skipped`, or `withheld`.
   - Never crashes on bad files: malformed files become named skips (`binary`, `not-utf8`, `too-large`, `empty`, `stub`).
   - Hard gate: If the skip share exceeds 25% (`max_skip_share=0.25`), raises `SkipShareExceeded` to halt half-loaded sources from entering the index.
3. **Deterministic Inspection Script (`scripts/inspect_sources.py`):**
   - Provides a pre-indexing quality audit tool reporting file counts, character changes, leftover markup, duplicate groups, and gate status.

## Consequences & Trade-Offs
- **Benefits:** Identical canonical text representation between LMS proprietary concept notes and upstream reference documentation; zero noise in AXIS AI RAG retrieval; deterministic and reproducible indexing.
- **Trade-offs:** Custom format parsers require unit test maintenance across diverse edge cases (covered by 250+ dedicated loader tests).
