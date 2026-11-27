"""With no course source, AXIS never ends on a bare reply (SPEC-24 section 10; ADR-0041 section 1: facilitate).

Interface these tests fix:
  socratic_guardrail.NO_SOURCE_FOLLOW_UP   the one fixed line
  socratic_guardrail.asks_a_question(text) a "?" outside fenced and inline code
No model, no network. All text is made up.
"""

import pytest

from lms.adapters.ai import passage_safety
from lms.adapters.ai.axis_stream import stream_axis
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.socratic_guardrail import (NO_SOURCE_FOLLOW_UP, AssistanceClassifier, SocraticGuardrail,
                                                asks_a_question)
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType, AssistanceLevel
from lms.core.retrieval import RetrievalStatus, RetrievalTrace

MODES = [AxisMode.SOCRATIC, AxisMode.HYBRID, AxisMode.COACH]
STATES = ["not_found", "no_index", "unavailable"]
BARE = "This is not in the course yet."
ASKS = "This is not in the course yet. What did you try first?"
OLD_SOCRATIC = "What is your hypothesis for why this step behaves the way it does?"
GUARD, CLASSIFIER = SocraticGuardrail(), AssistanceClassifier()


def query(mode, question="How do I do the made-up thing?"):
    return AxisQuery(unit_id="PY-0.1", mode=mode, current_activity=ActivityType.PREDICT, user_prompt=question)


def no_source(state):
    status = {"not_found": RetrievalStatus.NOT_FOUND, "no_index": None, "unavailable": RetrievalStatus.UNAVAILABLE}[state]
    trace = None if status is None else RetrievalTrace(
        index_version="", mode="keyword_only", status=status.value, latency_ms=1, passages_retrieved=0,
        terms_matched=0, terms_total=0, downgraded=False, reason="")
    grounding = passage_safety.build_grounding([], trace)
    assert grounding.source_state == state
    return grounding


def with_source():
    grounding = passage_safety.build_grounding([("p1", "made-up/page", "A made-up passage about nothing.")], None)
    assert grounding.source_state == "course"
    return grounding


def whole(reply, mode, grounding):
    return axis_rules.finish_reply(reply, query(mode), grounding, GUARD, CLASSIFIER)


def streamed(reply, mode, grounding, size=7):
    class Companion:
        def stream(self, q):
            return (reply[i:i + size] for i in range(0, len(reply), size)), grounding

    events = list(stream_axis(Companion(), query(mode), GUARD, CLASSIFIER))
    text = "".join(d["text"] for name, d in events if name == "token")
    done = next(d for name, d in events if name == "done")
    return text, done


def test_the_line_is_exactly_the_approved_one():
    assert NO_SOURCE_FOLLOW_UP == "Start from your own code, error or question: what have you tried so far, and what did you see?"
    assert NO_SOURCE_FOLLOW_UP.count("?") == 1 and "`" not in NO_SOURCE_FOLLOW_UP


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("mode", MODES)
def test_a_bare_no_source_reply_gets_the_line_once(mode, state):
    for reply in (BARE, "", "   "):
        response = whole(reply, mode, no_source(state))
        shown, _done = streamed(reply, mode, no_source(state))

        for text in (response.reply, shown):
            assert text.count(NO_SOURCE_FOLLOW_UP) == 1 and text.rstrip().endswith(NO_SOURCE_FOLLOW_UP), text
            assert OLD_SOCRATIC not in text
        if reply.strip():
            assert response.reply == f"{BARE}\n\n{NO_SOURCE_FOLLOW_UP}"
            assert shown.startswith(BARE)


@pytest.mark.parametrize("mode", MODES)
def test_a_reply_that_asks_is_left_alone(mode):
    assert whole(ASKS, mode, no_source("not_found")).reply == ASKS
    assert streamed(ASKS, mode, no_source("not_found"))[0] == ASKS


@pytest.mark.parametrize("mode", [AxisMode.HYBRID, AxisMode.COACH])
def test_a_question_mark_inside_code_is_not_a_question(mode):
    reply = "This is not in the course yet. Look at `a ? b` again."

    assert asks_a_question(reply) is False
    assert NO_SOURCE_FOLLOW_UP in whole(reply, mode, no_source("not_found")).reply
    assert asks_a_question("Is it `x`?") is True and asks_a_question("```\nx?\n```") is False


@pytest.mark.parametrize("mode", MODES)
def test_a_reply_with_a_source_never_gets_the_line(mode):
    response = whole("A made-up answer [1].", mode, with_source())
    shown, _done = streamed("A made-up answer [1].", mode, with_source())

    assert NO_SOURCE_FOLLOW_UP not in response.reply and NO_SOURCE_FOLLOW_UP not in shown


def test_socratic_with_a_source_keeps_its_own_reflection_question():
    assert OLD_SOCRATIC in whole("A made-up statement [1].", AxisMode.SOCRATIC, with_source()).reply


@pytest.mark.parametrize("mode", [AxisMode.HYBRID, AxisMode.COACH])
def test_the_line_does_not_count_as_help(mode):
    """Assistance is judged on the reply before the line is added: a bare reply helped no more with it than without."""
    expected = CLASSIFIER.classify("How do I do the made-up thing?", BARE, mode)

    assert whole(BARE, mode, no_source("not_found")).detected_assistance_level == expected
    assert streamed(BARE, mode, no_source("not_found"))[1]["assistance_level"] == expected.value
    if mode is AxisMode.COACH:
        assert expected is AssistanceLevel.NONE


def test_withheld_code_already_ends_with_a_question_so_nothing_is_added():
    reply = "```\nx = [1]\n```"

    shown = whole(reply, AxisMode.SOCRATIC, no_source("not_found")).reply

    assert "withheld" in shown and NO_SOURCE_FOLLOW_UP not in shown


def test_the_mock_companion_is_unchanged():
    companion = MockAxisCompanion()
    events = list(stream_axis(companion, query(AxisMode.COACH), GUARD, CLASSIFIER))

    assert NO_SOURCE_FOLLOW_UP not in "".join(d["text"] for name, d in events if name == "token")
