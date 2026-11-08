"""Mock implementation of IAXISCompanion.

Provides deterministic responses for Coach, Hybrid, and Socratic modes
without incurring external API calls or network dependency (MOCK_AI=true).
"""

import json
import re
from typing import Any, Iterator, List, Tuple
from lms.core.interfaces import AxisMode, AxisQuery, AxisResponse
from lms.core.models import AssistanceLevel
from lms.adapters.ai.providers.judging import judge_with
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.core.ai_judgement import AiJudgement, Rubric


class MockAxisCompanion:
    """Deterministic, zero-token mock implementation of the AXIS AI Companion."""

    def __init__(self, guardrail: SocraticGuardrail = None, classifier: AssistanceClassifier = None):
        self.guardrail = guardrail or SocraticGuardrail()
        self.classifier = classifier or AssistanceClassifier()

    def judge(self, unit_id: str, prompt: str, explanation: str, ideas: List[Any]) -> Tuple[str, str]:
        """Offline judging (SPEC-18 section 3): an idea is met when the explanation holds a
        whole word of 5 or more letters from the idea's text. Same input, same answer."""
        words = set(re.findall(r"[a-z]+", explanation.lower()))
        results = []
        for idea in ideas:
            wanted = {w for w in re.findall(r"[a-z]+", idea.text.lower()) if len(w) >= 5}
            results.append({"id": idea.id, "met": bool(wanted & words)})
        missed = [i.text for i, r in zip(ideas, results) if not r["met"]]
        feedback = "Every idea is shown." if not missed else "Not shown yet: " + " ".join(missed)
        return json.dumps({"ideas": results, "feedback": feedback[:400]}), "offline-mock"

    def judge_explanation(self, unit_id: str, prompt: str, explanation: str, rubric: Rubric) -> AiJudgement:
        return judge_with(self, unit_id, prompt, explanation, rubric)

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], List[str]]:
        """The consult reply, word by word. Returns (deltas, cited concepts)."""
        response = self.consult(query)
        return iter(re.findall(r"\S+\s*", response.reply)), response.cited_concepts

    def consult(self, query: AxisQuery) -> AxisResponse:
        cited: List[str] = ["Operational Communication Cycle"]
        action = None

        q_lower = query.user_prompt.lower()

        if query.mode == AxisMode.SOCRATIC:
            reply = (
                f"Consider the data entering your system in activity {query.current_activity.value}. "
                "What is the expected type of your variable before transformation occurs? "
                "What happens to the program flow when incompatible types are combined?"
            )
            action = "Trace variable types step-by-step before re-running."

        elif any(kw in q_lower for kw in ["syntax", "how to uppercase", "how to strip"]):
            reply = (
                "To clean whitespace and uppercase a string in Python, use the standard methods: "
                "`.strip()` returns a string with leading/trailing spaces removed, and `.upper()` converts all characters."
            )
            action = "Apply string formatting methods to your variables."
            cited.append("Standard Library String Methods")

        elif "solution" in q_lower or "whole" in q_lower:
            reply = (
                "Here is an implementation:\n"
                "```python\n"
                "def run_intake(name, ward_code):\n"
                "    clean_name = name.strip()\n"
                "    clean_ward = ward_code.strip().upper()\n"
                "    return f'REGISTRATION CONFIRMED: {clean_name} [WARD-{clean_ward}]'\n"
                "```"
            )
            action = "Review the provided implementation and adapt to your scenario."
            cited.append("Intake Transformation Implementation")

        elif query.mode == AxisMode.COACH:
            reply = (
                f"You are doing well working through unit {query.unit_id}. "
                "Remember our principle: input is intake, formatting is packaging, and print is egress. "
                "Check the contract in the unit description to ensure all required fields are included."
            )
            action = "Review the unit's required input/output schema."
            cited.append("Schema Validation")

        else:  # Hybrid
            reply = (
                f"In unit {query.unit_id}, notice that functions isolate logic from presentation. "
                "Try structuring your data into a dictionary first before passing it to the formatter."
            )
            action = "Define a dictionary schema for the intake record."
            cited.append("Data Contracts")

        # Pass reply through Socratic Guardrail
        enforced_reply = self.guardrail.enforce(reply, query.mode, strict=False)

        # Classify assistance level
        assistance = self.classifier.classify(query.user_prompt, enforced_reply, query.mode)

        return AxisResponse(
            reply=enforced_reply,
            suggested_action=action,
            cited_concepts=cited,
            detected_assistance_level=assistance,
        )
