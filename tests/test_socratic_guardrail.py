"""Tests for Socratic boundary guardrail and assistance accounting.

Governed by:
- ADR-0009: Socratic Boundary Guardrails and Assistance Accounting
- SPEC-07: Socratic Boundary Guardrail and Assistance Accounting
"""

import pytest
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    ProgressionDecision,
)
from lms.core.progression import evaluate_progression
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.socratic_guardrail import (
    AssistanceClassifier,
    SocraticBoundaryViolation,
    SocraticGuardrail,
)


def test_guardrail_detects_code_blocks():
    guard = SocraticGuardrail()

    clean_text = "What happens to the variable type when input() is called? Have you inspected the string output?"
    assert guard.contains_code(clean_text) is False

    code_block = "Here is the fix:\n```python\nname = input().strip()\n```"
    assert guard.contains_code(code_block) is True

    function_def = "You can define it like: def run_intake(name, ward):\n    return name"
    assert guard.contains_code(function_def) is True


def test_guardrail_strict_mode_raises_on_code():
    guard = SocraticGuardrail()
    violating_reply = "Try this: def clean(x): return x.strip()"

    with pytest.raises(SocraticBoundaryViolation):
        guard.enforce(violating_reply, mode=AxisMode.SOCRATIC, strict=True)


def test_guardrail_sanitizes_code_in_socratic_mode():
    guard = SocraticGuardrail()
    violating_reply = (
        "Here is what you need:\n```python\nreturn f'REGISTRATION: {name}'\n```\nWhat do you think?"
    )

    sanitized = guard.enforce(violating_reply, mode=AxisMode.SOCRATIC, strict=False)
    assert "```" not in sanitized
    assert "return" not in sanitized
    assert "?" in sanitized


def test_guardrail_permits_code_in_coach_mode():
    guard = SocraticGuardrail()
    coach_reply = "Here is a starter snippet: `name.strip()` removes whitespace."
    result = guard.enforce(coach_reply, mode=AxisMode.COACH, strict=True)
    assert result == coach_reply


def test_assistance_classifier_syntax_lookup():
    classifier = AssistanceClassifier()

    level = classifier.classify(
        query_text="What is the Python syntax for converting a string to uppercase?",
        reply_text="Use the `.upper()` method on any string instance.",
        mode=AxisMode.COACH,
    )
    assert level == AssistanceLevel.SYNTAX_LOOKUP


def test_assistance_classifier_supplied_reasoning():
    classifier = AssistanceClassifier()

    level = classifier.classify(
        query_text="Write the whole solution for me.",
        reply_text="```python\ndef run_intake(name, ward):\n    return f'{name} {ward}'\n```",
        mode=AxisMode.COACH,
    )
    assert level == AssistanceLevel.SUPPLIED_REASONING


def test_mock_axis_adheres_to_socratic_boundary():
    companion = MockAxisCompanion()

    query = AxisQuery(
        learner_id="learner_001",
        unit_id="PY-0.4",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.BUILD,
        user_prompt="Give me the code for run_intake.",
    )
    res = companion.consult(query)

    guard = SocraticGuardrail()
    assert guard.contains_code(res.reply) is False
    assert "?" in res.reply
    assert res.detected_assistance_level in (AssistanceLevel.SMALL_HINT, AssistanceLevel.NONE)


def test_progression_impact_of_assistance_accounting():
    # If reasoning was supplied, progression forces STRENGTHEN
    assisted_entry = EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-0.4",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.WEAK,
        assistance_level=AssistanceLevel.SUPPLIED_REASONING,
        demonstration_context="Passed tests but AI supplied solution",
    )
    decision, reason = evaluate_progression(ProficiencyLevel.APPLY, [assisted_entry])
    assert decision == ProgressionDecision.STRENGTHEN
    assert "fragile" in reason.lower()

    # Syntax lookup does not disqualify evidence: two syntax-lookup entries from
    # different exercises, one a passed Cold Check, allow PROGRESS (ADR-0016).
    syntax_entries = [
        EvidenceEntry(
            learner_id="learner_002",
            unit_id="PY-0.4",
            skill_id="CO-1",
            evidence_category=EvidenceCategory.PERFORM_SOLVE,
            evidence_strength=EvidenceStrength.STRONG,
            assistance_level=AssistanceLevel.SYNTAX_LOOKUP,
            demonstration_context="Looked up .strip() docs then implemented independently",
            exercise_id=exercise_id,
            cold_check=cold_check,
        )
        for exercise_id, cold_check in (("ex-1", False), ("ex-2", True))
    ]
    decision_ok, _ = evaluate_progression(ProficiencyLevel.APPLY, syntax_entries)
    assert decision_ok == ProgressionDecision.PROGRESS
