"""Loader registry matching rag-core."""
from __future__ import annotations

from lms.core.rag.errors import LoadError
from lms.core.rag.files import MIN_CHARS
from lms.adapters.ai.loaders.html import HTML_VERSION, read_html
from lms.adapters.ai.loaders.markdown import MD_VERSION, read_md, read_mdx
from lms.adapters.ai.loaders.notebook import NOTEBOOK_VERSION, read_ipynb
from lms.adapters.ai.loaders.plain import PLAIN_READERS, Reader
from lms.adapters.ai.loaders.rst import RST_VERSION, read_rst


def _no_stubs(read: Reader) -> Reader:
    def checked(raw: bytes) -> str:
        text = read(raw)
        if not text.strip():
            raise LoadError("empty")
        if len(text.strip()) < MIN_CHARS:
            raise LoadError("stub")
        return text
    return checked


DEFAULT_READERS: dict[str, tuple[str, Reader]] = {
    **PLAIN_READERS,
    ".md": (MD_VERSION, _no_stubs(read_md)),
    ".mdx": (MD_VERSION, _no_stubs(read_mdx)),
    ".rst": (RST_VERSION, _no_stubs(read_rst)),
    ".html": (HTML_VERSION, _no_stubs(read_html)),
    ".htm": (HTML_VERSION, _no_stubs(read_html)),
    ".ipynb": (NOTEBOOK_VERSION, _no_stubs(read_ipynb)),
}
