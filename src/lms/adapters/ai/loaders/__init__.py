"""Document loaders package for curriculum notes, documentation and notebooks."""
from __future__ import annotations

from lms.adapters.ai.loaders.html import HTML_VERSION, read_html
from lms.adapters.ai.loaders.markdown import MD_VERSION, read_md, read_mdx
from lms.adapters.ai.loaders.notebook import NOTEBOOK_VERSION, read_ipynb
from lms.adapters.ai.loaders.plain import PLAIN_READERS, PLAIN_VERSION
from lms.adapters.ai.loaders.registry import DEFAULT_READERS
from lms.adapters.ai.loaders.rst import RST_VERSION, read_rst
from lms.adapters.ai.loaders.snapshot import LoadResult, load_snapshot

__all__ = [
    "DEFAULT_READERS",
    "HTML_VERSION",
    "LoadResult",
    "MD_VERSION",
    "NOTEBOOK_VERSION",
    "PLAIN_READERS",
    "PLAIN_VERSION",
    "RST_VERSION",
    "load_snapshot",
    "read_html",
    "read_ipynb",
    "read_md",
    "read_mdx",
    "read_rst",
]
