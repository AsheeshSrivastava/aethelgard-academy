"""Mock implementation of IAXISCompanion.

Provides deterministic responses for Coach, Hybrid, and Socratic modes
without incurring external API calls or network dependency (MOCK_AI=true).
"""

from typing import List
from lms.core.interfaces import AxisMode, AxisQuery, AxisResponse
from lms.core.models import AssistanceLevel


class MockAxisCompanion:
    """Deterministic, zero-token mock implementation of the AXIS AI Companion."""

    def consult(self, query: AxisQuery) -> AxisResponse:
        cited: List[str] = ["Operational Communication Cycle"]

        if query.mode == AxisMode.SOCRATIC:
            reply = (
                f"Consider the data entering your system in activity {query.current_activity.value}. "
                "What is the expected type of your variable before transformation occurs? "
                "What happens to the program flow when incompatible types are combined?"
            )
            assistance = AssistanceLevel.SMALL_HINT
            action = "Trace variable types step-by-step before re-running."

        elif query.mode == AxisMode.COACH:
            reply = (
                f"You are doing well working through unit {query.unit_id}. "
                "Remember our principle: input is intake, formatting is packaging, and print is egress. "
                "Check the contract in the unit description to ensure all required fields are included."
            )
            assistance = AssistanceLevel.SMALL_HINT
            action = "Review the unit's required input/output schema."
            cited.append("Schema Validation")

        else:  # Hybrid
            reply = (
                f"In unit {query.unit_id}, notice that functions isolate logic from presentation. "
                "Try structuring your data into a dictionary first before passing it to the formatter."
            )
            assistance = AssistanceLevel.STRUCTURAL_DIRECTION
            action = "Define a dictionary schema for the intake record."
            cited.append("Data Contracts")

        return AxisResponse(
            reply=reply,
            suggested_action=action,
            cited_concepts=cited,
            detected_assistance_level=assistance,
        )
