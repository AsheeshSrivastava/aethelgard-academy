"""Socratic Boundary Guardrail and Assistance Accounting.

Governed by:
- ADR-0009: Socratic Boundary Guardrails and Assistance Accounting
- SPEC-07: Socratic Boundary Guardrail and Assistance Accounting
- ADR-0039 section 8 and SPEC-31 section 9.2: what counts as code, and the learner's own words
"""

import re
from typing import List, Tuple

from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import AssistanceLevel


GUIDING_INQUIRY = (
    "\n\n*(In Socratic mode, direct code solutions are withheld.)*\n"
    "Consider the data flow: What is the exact input type entering this step, "
    "and what specific transformation is required before egress?"
)
REFLECTION_PROMPT = "\n\nWhat is your hypothesis for why this step behaves the way it does?"

PROMPT_TAG_NAMES = (
    "learner_query",
    "learner_code",
    "execution_stderr",
    "learner_explanation",
    "reference_passages",
    "passage",
)
# Opening or closing, any case; an opening tag may carry attributes (SPEC-22 R2).
PROMPT_TAG_PATTERN = re.compile(rf"</?(?:{'|'.join(PROMPT_TAG_NAMES)})(?:\s[^<>]*)?/?>", re.IGNORECASE)


def remove_prompt_tags(text: str) -> str:
    """Models sometimes echo the tags our prompt wraps learner text in."""
    while True:  # until none is left, so "<pas<passage>sage>" cannot rebuild a tag
        stripped = PROMPT_TAG_PATTERN.sub("", text)
        if stripped == text:
            return text
        text = stripped


def learner_text_of(query: AxisQuery) -> str:
    """Everything the learner wrote this turn: question, code and error output (SPEC-31 9.2 A4)."""
    stderr = query.execution_result.stderr if query.execution_result else ""
    # The NUL keeps a quoted span from matching across the end of one part and the start of the next.
    return "\n\x00\n".join(part for part in (query.user_prompt, query.learner_code, stderr) if part)


_BACKTICK_RUN = re.compile(r"`+")
_NEUTRAL_SPAN = "\u2026"  # stands in for a quoted learner span: no letter, bracket or sign for a pattern to match


def code_spans(line: str) -> Tuple[List[Tuple[int, int, int, int]], List[int]]:
    """The inline backtick spans of one line, and where each backtick run that nothing closes starts.

    A span is (start, content start, content end, end). One or two backticks open it and the next run of the same
    length closes it, as in Markdown. Three or more are a fence, not a span.
    """
    runs = [m for m in _BACKTICK_RUN.finditer(line) if len(m.group(0)) < 3]
    closer = [None] * len(runs)
    seen = {}
    for i in range(len(runs) - 1, -1, -1):
        size = len(runs[i].group(0))
        closer[i] = seen.get(size)
        seen[size] = i
    spans: List[Tuple[int, int, int, int]] = []
    unclosed: List[int] = []
    i = 0
    while i < len(runs):
        j = closer[i]
        if j is None:
            unclosed.append(runs[i].start())
            i += 1
            continue
        spans.append((runs[i].start(), runs[i].end(), runs[j].start(), runs[j].end()))
        i = j + 1
    return spans, unclosed


class SocraticBoundaryViolation(Exception):
    """Raised when an AI response violates the Socratic zero-code boundary."""
    pass


class SocraticGuardrail:
    """Inspects and enforces boundaries on companion responses."""

    # Patterns indicating executable Python constructs (what counts: SPEC-31 section 9.2 A1 to A3)
    CODE_FENCE_PATTERN = re.compile(r"```[\w]*\n?(.*?)```", re.DOTALL)
    FENCE_MARKERS = ("```", "~~~")
    # A1: an import only at the start of a line. A2: so is a `return` followed by anything.
    # A list, quote, heading or bold mark does not move an import off the start of its line (9.7 reading 5). One mark
    # per repeat, so there is one way to read a run of them.
    _MARKS = r"[^\S\n]*(?:(?:[-*+>#_]|\d+[.)])[^\S\n]*)*"
    _IMPORT_AT_START = r"^" + _MARKS + r"(?:import[^\S\n]+\w|from[^\S\n]+[\w.]+[^\S\n]+import\b)"
    _RETURN_AT_START = r"^[^\S\n]*return\b[^\S\n]*\S"
    # A2: inside a sentence, `return` counts only before a call `name(` or an expression with an operator.
    # Backticks, bold marks, brackets and a colon may stand between them, or "return `len(rows)`" would pass.
    # That run is read one character at a time, with one way to read each, so long input cannot backtrack badly.
    _OPERAND = (
        r"(?:[rRbBfF]{0,2}\"[^\"\n]*\"|[rRbBfF]{0,2}'[^'\n]*'|\w+)"
        r"(?:\.\w+|\[[^\[\]\n]*\])*"
    )
    _OPERATOR = (
        r"(?:[^\S\n]+(?:\*\*|//|==|!=|<=|>=|[-+*/%<>])[^\S\n]+(?=\S)"  # spaced: total - tax
        r"|(?:\*\*|==|!=|<=|>=|[+*])(?=[\w(\[{\"']))"  # tight: total*rate. Not "-" or "/": well-known, True/False
    )
    _RETURN_EXPRESSION = (
        r"\breturn(?=[^\S\n]|[\[({`*:])"
        r"(?:[^\S\n]|[\[({`*:~-]|(?:not|await)(?=[^\S\n]))*"
        + _OPERAND
        + r"[`*]{0,3}(?:\(|\[|" + _OPERATOR + r")"  # a subscript counts like a call: return rows[0]
    )
    STATEMENT_PATTERN = re.compile(
        r"\bdef\s+\w+\s*\(|\bclass\s+\w+\s*[:(]|^\s*assert\b"
        + "|" + _IMPORT_AT_START + "|" + _RETURN_AT_START + "|" + _RETURN_EXPRESSION,
        re.MULTILINE,
    )
    # SPEC-31 9.7 reading 1: a quoted span the learner did not write is also read as if it started a line.
    SPAN_START_PATTERN = re.compile(_IMPORT_AT_START + "|" + _RETURN_AT_START)
    ASSIGNMENT_PATTERN = re.compile(
        r"(?:[a-zA-Z_]\w*\s*=\s*(?:input\(|[\"'].*?[\"']|\[|\{))",
        re.MULTILINE,
    )

    # A whole line that is code: a bare call, a block header, or any assignment
    CODE_LINE_PATTERN = re.compile(
        r"^\s*(?:[\w.\[\]]+\(.*\)"
        r"|(?:for|while|if|elif|else|try|except|with)\b.*:"
        r"|[A-Za-z_][\w.\[\]]*\s*[-+*/%]?=\s*\S.*)\s*$",
        re.MULTILINE,
    )

    def contains_code(self, text: str, learner_text: str = "") -> bool:
        """Determines if the text contains executable code blocks or definitions.

        A non-empty `learner_text` leaves out inline spans the learner wrote (SPEC-31 9.2 A4). Fences never are.
        """
        if any(fence in text for fence in self.FENCE_MARKERS):
            return True
        return self._has_code_lines(text, learner_text)

    def mask_learner_spans(self, text: str, learner_text: str) -> str:
        """`text` with the inside of every inline span the learner wrote replaced by a neutral mark."""
        return self._read_spans(text, learner_text)[0]

    def _read_spans(self, text: str, learner_text: str) -> Tuple[str, bool]:
        """(the text with learner spans masked, whether another span starts with a statement)."""
        learner = " ".join(learner_text.split())
        statement = False
        lines = []
        for line in text.splitlines():
            pieces: List[str] = []
            done = 0
            for _start, inner, inner_end, _end in code_spans(line)[0]:
                content = line[inner:inner_end]
                quoted = " ".join(content.split())
                if quoted and quoted in learner:
                    pieces += [line[done:inner], _NEUTRAL_SPAN]
                    done = inner_end
                elif self.SPAN_START_PATTERN.match(content):
                    statement = True
            lines.append("".join(pieces) + line[done:])
        return "\n".join(lines), statement

    def _has_code_lines(self, text: str, learner_text: str) -> bool:
        """Code outside fences: statements, code lines and assignments."""
        masked, statement = self._read_spans(text, learner_text)
        return statement or any(
            pattern.search(masked)
            for pattern in (self.STATEMENT_PATTERN, self.CODE_LINE_PATTERN, self.ASSIGNMENT_PATTERN)
        )

    def _drop_code_lines(self, text: str, learner_text: str) -> str:
        kept: List[str] = []
        in_fence = False
        for line in text.splitlines():
            markers = sum(line.count(fence) for fence in self.FENCE_MARKERS)
            # A4 never applies to a fence, so a line in or on one is read without the learner's text.
            learner = "" if in_fence or markers else learner_text
            if markers % 2:
                in_fence = not in_fence
            if not self._has_code_lines(line, learner):
                kept.append(line)
        return "\n".join(kept).strip()

    def enforce(
        self,
        reply: str,
        mode: AxisMode,
        strict: bool = False,
        learner_text: str = "",
    ) -> str:
        """Inspects and enforces the Socratic boundary on an AI response."""
        if mode != AxisMode.SOCRATIC:
            return reply

        has_code = self.contains_code(reply, learner_text=learner_text)

        if has_code:
            if strict:
                raise SocraticBoundaryViolation(
                    "Socratic mode response violated zero-executable-code boundary."
                )

            # Sanitize: Strip code blocks and code lines
            sanitized = self.CODE_FENCE_PATTERN.sub("", reply)
            reply = self._drop_code_lines(sanitized, learner_text) + GUIDING_INQUIRY

        # Socratic mode must always provoke learner reflection
        if "?" not in reply:
            reply += REFLECTION_PROMPT

        return reply


class AssistanceClassifier:
    """Classifies learner queries and assistant replies into AssistanceLevel."""

    SYNTAX_QUERY_KEYWORDS = [
        "syntax", "how do i use", "how to use", "signature", "docs", "documentation",
        "method", "what does", "return type", "how to convert", "how to uppercase",
        "how to strip", "built-in",
    ]

    def classify(
        self,
        query_text: str,
        reply_text: str,
        mode: AxisMode,
    ) -> AssistanceLevel:
        """Determines the assistance level provided in this turn."""
        q_lower = query_text.lower()
        guard = SocraticGuardrail()

        # 1. Supplied reasoning: full executable code solution provided
        if "```python" in reply_text or (guard.contains_code(reply_text) and mode != AxisMode.SOCRATIC):
            # If the user asked for full solution or code was given
            if any(term in reply_text for term in ["def ", "return ", "="]):
                return AssistanceLevel.SUPPLIED_REASONING

        # 2. Syntax lookup: User asked for API/syntax clarification
        if any(keyword in q_lower for keyword in self.SYNTAX_QUERY_KEYWORDS):
            # As long as the AI didn't provide a complete task solution
            if not guard.contains_code(reply_text):
                return AssistanceLevel.SYNTAX_LOOKUP

        # 3. Structural direction: Architecture/high-level steps without code
        if mode == AxisMode.HYBRID or "structure" in reply_text.lower() or "schema" in reply_text.lower():
            if not guard.contains_code(reply_text):
                return AssistanceLevel.STRUCTURAL_DIRECTION

        # 4. Socratic inquiry or small hints
        if mode == AxisMode.SOCRATIC or "?" in reply_text:
            return AssistanceLevel.SMALL_HINT

        return AssistanceLevel.NONE
