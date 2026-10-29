import pytest
from lms.core.models import ActivityType, AssistanceLevel
from lms.core.interfaces import AxisMode, AxisQuery
from lms.adapters.ai.mock_axis import MockAxisCompanion

@pytest.fixture
def companion():
    return MockAxisCompanion()

def test_socratic_mode_never_returns_code(companion):
    query = AxisQuery(
        learner_id="learner_001",
        unit_id="PY-1.2",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.PREDICT,
        user_prompt="Can you give me the code to fix this?",
        learner_code="x = '10' + 5",
    )
    response = companion.consult(query)
    # Socratic response should guide without giving code
    assert "?" in response.reply
    assert "def " not in response.reply
    assert response.detected_assistance_level == AssistanceLevel.SMALL_HINT

def test_coach_mode_provides_encouraging_guidance(companion):
    query = AxisQuery(
        learner_id="learner_001",
        unit_id="PY-1.2",
        mode=AxisMode.COACH,
        current_activity=ActivityType.DEBUG_VALIDATE,
        user_prompt="Why is my test failing?",
    )
    response = companion.consult(query)
    assert response.reply is not None
    assert len(response.cited_concepts) > 0
