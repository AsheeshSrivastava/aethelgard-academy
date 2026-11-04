"""Local models run with thinking off (owner request 2026-11-04, SPEC-17 section 3.4).

Two layers: ask the server to switch thinking off, and remove any <think> block that
still comes back, in whole replies and in streamed pieces."""

import json

import httpx

from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion, ThinkFilter
from lms.adapters.ai.providers.profiles import load_profiles, parse_profiles
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType

LOCAL = parse_profiles({"profiles": [
    {"id": "local", "label": "Local", "kind": "openai_compatible",
     "base_url": "http://127.0.0.1:8888/v1", "model": "qwen3.5-9b", "paid": False,
     "disable_thinking": True},
]})["local"]


def _query():
    return AxisQuery(unit_id="PY-0.4", mode=AxisMode.COACH,
                     current_activity=ActivityType.TRACE, user_prompt="What does strip do?")


def _completion(content):
    return {"id": "x", "object": "chat.completion", "created": 0, "model": "qwen3.5-9b",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": content}}]}


def _companion(handler, disable_thinking=True):
    return OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:8888/v1", model="qwen3.5-9b", api_key="local",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        profile=LOCAL, disable_thinking=disable_thinking,
    )


def test_shipped_local_profile_has_thinking_off():
    assert load_profiles()["local"].disable_thinking is True


def test_request_asks_the_server_to_switch_thinking_off():
    sent = {}

    def handler(request):
        sent["body"] = json.loads(request.content)
        return httpx.Response(200, json=_completion("It removes spaces at both ends."))

    _companion(handler).consult(_query())
    assert sent["body"]["chat_template_kwargs"] == {"enable_thinking": False}


def test_profiles_without_the_flag_send_nothing_extra():
    sent = {}

    def handler(request):
        sent["body"] = json.loads(request.content)
        return httpx.Response(200, json=_completion("ok"))

    _companion(handler, disable_thinking=False).consult(_query())
    assert "chat_template_kwargs" not in sent["body"]


def test_think_block_is_removed_from_a_whole_reply():
    def handler(request):
        return httpx.Response(200, json=_completion(
            "<think>The learner wants strip. Let me plan...</think>\nIt removes spaces at both ends."))

    reply = _companion(handler).consult(_query()).reply
    assert "Let me plan" not in reply and "<think>" not in reply
    assert "removes spaces" in reply


def test_think_block_split_across_stream_pieces_is_removed():
    pieces = ["<thi", "nk>planning", " more</th", "ink>It removes", " spaces."]

    def handler(request):
        chunks = [{"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "qwen3.5-9b",
                   "choices": [{"index": 0, "delta": {"content": p}}]} for p in pieces]
        body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    deltas, _ = _companion(handler).stream(_query())
    text = "".join(deltas)
    assert text == "It removes spaces."


def test_filter_keeps_ordinary_angle_brackets():
    f = ThinkFilter()
    out = f.feed("if a < b and b > c: <tag>") + f.flush()
    assert out == "if a < b and b > c: <tag>"


def test_filter_drops_an_unclosed_think_block_at_the_end():
    f = ThinkFilter()
    assert f.feed("Answer first. <think>never closed") + f.flush() == "Answer first. "
