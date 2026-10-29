"""The stand-in reader for plain text types: UTF-8, no markup removal."""
from __future__ import annotations

from typing import Callable

from lms.core.rag_contracts import normalize_text
from lms.core.rag.files import TEXT_EXTS

Reader = Callable[[bytes], str]
PLAIN_VERSION = "plain-1"
PLAIN_READERS: dict[str, tuple[str, Reader]] = {
    ext: (PLAIN_VERSION, lambda raw: normalize_text(raw.decode("utf-8"))) for ext in TEXT_EXTS
}
