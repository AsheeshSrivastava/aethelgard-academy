import pytest
from lms.core.models import ActivityType, AssistanceLevel
from lms.core.interfaces import (
    AxisMode,
    AxisQuery,
    AxisResponse,
    ExecutionResult,
)

def test_execution_result_contract():
    res = ExecutionResult(
        success=True,
        stdout="User: Alice registered with ID: 104\n",
        stderr="",
        exit_code=0,
        duration_ms=42.5,
    )
    assert res.success is True
    assert "104" in res.stdout
    assert res.assertion_errors == []

def test_execution_result_with_assertion_failure():
    res = ExecutionResult(
        success=False,
        stdout="",
        stderr="AssertionError: assert 'Alice' == 'ALICE'",
        exit_code=1,
        duration_ms=30.0,
        assertion_errors=["assert 'Alice' == 'ALICE'"],
    )
    assert res.success is False
    assert len(res.assertion_errors) == 1

def test_axis_query_and_response_contract():
    query = AxisQuery(
        learner_id="learner_001",
        unit_id="PY-1.2",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.PREDICT,
        user_prompt="I don't know what will happen if I add '25' and 5",
        learner_code="age = '25'\nprint(age + 5)",
    )
    assert query.mode == AxisMode.SOCRATIC
    assert query.current_activity == ActivityType.PREDICT

    response = AxisResponse(
        reply="Look closely at how '25' is enclosed. What data type is surrounded by quotation marks?",
        suggested_action="Review type casting in concepts/python/type-casting",
        cited_concepts=["Data Types", "Type Casting"],
        detected_assistance_level=AssistanceLevel.SMALL_HINT,
    )
    assert "quotation marks" in response.reply
    assert response.detected_assistance_level == AssistanceLevel.SMALL_HINT
