"""Heading-aware sentence chunker.

Splits technical markdown documents first by heading sections,
then subdivides long sections at sentence boundaries into passages
targeting ~375 tokens (~1,500 characters max, median ~640 chars).

Guarantees 100% exact substring slicing against the original text.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from lms.core.rag_contracts import Span

SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`\"'#])")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class HeadingSentenceSplitter:
    """Extracts sentence-aligned chunk spans respecting markdown headings."""

    def __init__(self, max_chars: int = 1500, min_chars: int = 100) -> None:
        self.max_chars = max_chars
        self.min_chars = min_chars

    def split(self, text: str) -> List[Span]:
        """Slices text into Spans strictly referencing character offsets."""
        spans: List[Span] = []
        if not text.strip():
            return spans

        # 1. Identify all heading boundaries
        heading_matches = list(HEADING_RE.finditer(text))
        sections: List[Tuple[int, int, Tuple[str, ...]]] = []

        if not heading_matches:
            sections.append((0, len(text), ()))
        else:
            # Preamble before first heading
            if heading_matches[0].start() > 0:
                preamble_text = text[: heading_matches[0].start()].strip()
                if preamble_text:
                    sections.append((0, heading_matches[0].start(), ()))

            heading_stack: List[Tuple[int, str]] = []
            for i, match in enumerate(heading_matches):
                level = len(match.group(1))
                title = match.group(2).strip()

                # Maintain heading hierarchy stack
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, title))
                current_headings = tuple(t for _, t in heading_stack)

                sec_start = match.start()
                sec_end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(text)
                sections.append((sec_start, sec_end, current_headings))

        # 2. Subdivide sections that exceed max_chars at sentence boundaries
        for sec_start, sec_end, headings in sections:
            sec_text = text[sec_start:sec_end]
            if len(sec_text) <= self.max_chars:
                if len(sec_text.strip()) >= self.min_chars:
                    spans.append(Span(start=sec_start, end=sec_end, headings=headings))
                continue

            # Subdivide long section at sentence or paragraph boundaries
            curr_pos = sec_start
            while curr_pos < sec_end:
                target_end = min(curr_pos + self.max_chars, sec_end)
                if target_end == sec_end:
                    slice_len = target_end - curr_pos
                    if slice_len >= self.min_chars or not spans:
                        spans.append(Span(start=curr_pos, end=target_end, headings=headings))
                    break

                # Look for sentence boundary near target_end
                window = text[curr_pos:target_end]
                split_idx = -1

                # Try double newline first (paragraph end)
                para_split = window.rfind("\n\n")
                if para_split > self.min_chars:
                    split_idx = para_split + 2
                else:
                    # Try sentence punctuation end (.!?)
                    for punct in [".\n", ".\r\n", ". ", "! ", "? "]:
                        p_idx = window.rfind(punct)
                        if p_idx > self.min_chars:
                            split_idx = p_idx + len(punct)
                            break

                if split_idx == -1:
                    # Fallback to single newline or space
                    space_idx = window.rfind(" ")
                    split_idx = space_idx + 1 if space_idx > self.min_chars else len(window)

                chunk_end = curr_pos + split_idx
                if chunk_end - curr_pos >= self.min_chars:
                    spans.append(Span(start=curr_pos, end=chunk_end, headings=headings))
                curr_pos = chunk_end

        if not spans and text.strip():
            spans.append(Span(start=0, end=len(text), headings=()))

        return spans
