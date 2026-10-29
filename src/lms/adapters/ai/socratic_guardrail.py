"""Socratic Boundary Guardrail and Assistance Accounting.

Governed by:
- ADR-0009: Socratic Boundary Guardrails and Assistance Accounting
- SPEC-07: Socratic Boundary Guardrail and Assistance Accounting
"""

import re
from typing import Optional
from lms.core.interfaces import AxisMode
from lms.core.models import AssistanceLevel


class SocraticBoundaryViolation(Exception):
    """Raised when an AI response violates the Socratic zero-code boundary."""
    pass


class SocraticGuardrail:
    """Inspects and enforces boundaries on companion responses."""

    # Patterns indicating executable Python constructs
    CODE_FENCE_PATTERN = re.compile(r"```[\w]*\n?(.*?)```", re.DOTALL)
    STATEMENT_PATTERN = re.compile(
        r"(?:\b(?:def\s+\w+\s*\(|class\s+\w+|from\s+\w+\s+import|import\s+\w+)|(?:^\s*(?:return\b|assert\b)))",
        re.MULTILINE,
    )
    INLINE_RETURN_PATTERN = re.compile(r"\breturn\b")
    ASSIGNMENT_PATTERN = re.compile(
        r"(?:[a-zA-Z_]\w*\s*=\s*(?:input\(|[\"'].*?[\"']|\[|\{))",
        re.MULTILINE,
    )

    def contains_code(self, text: str) -> bool:
        """Determines if the text contains executable code blocks or definitions."""
        if "```" in text or "~~~" in text:
            return True
        if self.STATEMENT_PATTERN.search(text):
            return True
        if self.INLINE_RETURN_PATTERN.search(text) and ("def " in text or "(" in text):
            return True
        if self.ASSIGNMENT_PATTERN.search(text):
            return True
        return False

    def enforce(
        self,
        reply: str,
        mode: AxisMode,
        strict: bool = False,
    ) -> str:
        """Inspects and enforces the Socratic boundary on an AI response."""
        if mode != AxisMode.SOCRATIC:
            return reply

        has_code = self.contains_code(reply)

        if has_code:
            if strict:
                raise SocraticBoundaryViolation(
                    "Socratic mode response violated zero-executable-code boundary."
                )

            # Sanitize: Strip code blocks and code lines
            sanitized = self.CODE_FENCE_PATTERN.sub("", reply)
            lines = [
                line for line in sanitized.splitlines()
                if not self.STATEMENT_PATTERN.search(line) and not self.ASSIGNMENT_PATTERN.search(line)
            ]
            sanitized_text = "\n".join(lines).strip()

            guiding_inquiry = (
                "\n\n*(In Socratic mode, direct code solutions are withheld.)*\n"
                "Consider the data flow: What is the exact input type entering this step, "
                "and what specific transformation is required before egress?"
            )
            reply = sanitized_text + guiding_inquiry

        # Socratic mode must always provoke learner reflection
        if "?" not in reply:
            reply += "\n\nWhat is your hypothesis for why this step behaves the way it does?"

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
