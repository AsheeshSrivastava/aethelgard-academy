"""Adapters for each provider: same AXIS rules, token counts, the model that answered,
fallback rules and the cap (SPEC-17 sections 3, 4.2 and 5). All offline: SDK clients are faked."""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from lms.adapters.ai.gemini_companion import GeminiCompanion, GeminiError
from lms.adapters.ai.local_llm_companion import (
    LocalLLMError,
    OpenAICompatibleCompanion,
)
from lms.adapters.ai.providers.metering import BudgetExceeded, UsageMeter
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.db.model_usage import UsageStore
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType

PROFILES = parse_profiles(
    {
        "profiles": [
            {"id": "local", "label": "Local", "kind": "openai_compatible",
             "base_url": "http://127.0.0.1:8888/v1", "model": "auto", "paid": False},
            {"id": "openai", "label": "OpenAI", "kind": "openai_compatible",
             "base_url": "https://api.openai.com/v1", "model": "gpt-6-luna",
             "key_env": "OPENAI_API_KEY", "paid": True,
             "price_per_million": {"input": 0.10, "output": 0.50}},
            {"id": "gemini", "label": "Gemini", "kind": "gemini", "model": "gemini-3.8-flash",
             "key_env": "GEMINI_API_KEY", "paid": True,
             "price_per_million": {"input": 0.75, "output": 3.75}},
        ]
    }
)

LEAKY = "Here you go:\n```python\ndef run_intake(name):\n    return name.strip()\n```\nWhat type is name?"


def _query(mode=AxisMode.SOCRATIC) -> AxisQuery:
    return AxisQuery(
        learner_id="me",
        unit_id="PY-0.4",
        current_activity=ActivityType.TRACE,
        user_prompt="Why does my intake fail?",
        learner_code="print(name)",
        mode=mode,
    )


@pytest.fixture
def store(tmp_path):
    s = UsageStore(
        tmp_path / "usage.db",
        clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc),
        session_id="run-1",
    )
    s.initialize()
    return s


# --- OpenAI-compatible -----------------------------------------------------------


def _completion(content: str, model: str, usage: dict | None) -> dict:
    body = {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
    }
    if usage is not None:
        body["usage"] = usage
    return body


def _openai_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_openai_compatible_records_usage_and_the_model_that_answered(store):
    sent = {}

    def handler(request):
        sent["body"] = json.loads(request.content)
        return httpx.Response(200, json=_completion(
            "What does name hold?", "gpt-6-luna-2026-10-01",
            {"prompt_tokens": 321, "completion_tokens": 12, "total_tokens": 333}))

    companion = OpenAICompatibleCompanion(
        base_url="https://api.openai.com/v1", model="gpt-6-luna", api_key="sk-test",
        http_client=_openai_client(handler), fallback_to_mock=False,
        profile=PROFILES["openai"], meter=UsageMeter(store),
    )
    companion.consult(_query())

    assert sent["body"]["model"] == "gpt-6-luna"
    assert companion.last_model_answered == "gpt-6-luna-2026-10-01"
    (row,) = store.totals("session")
    assert (row.profile_id, row.model, row.input_tokens, row.output_tokens) == (
        "openai", "gpt-6-luna-2026-10-01", 321, 12)


def test_openai_compatible_stream_asks_for_usage_and_reads_the_last_chunk(store):
    sent = {}

    def handler(request):
        sent["body"] = json.loads(request.content)
        chunks = [
            {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "gpt-6-luna",
             "choices": [{"index": 0, "delta": {"content": "What "}}]},
            {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "gpt-6-luna",
             "choices": [{"index": 0, "delta": {"content": "type?"}, "finish_reason": "stop"}]},
            {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "gpt-6-luna",
             "choices": [], "usage": {"prompt_tokens": 50, "completion_tokens": 3, "total_tokens": 53}},
        ]
        body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    companion = OpenAICompatibleCompanion(
        base_url="https://api.openai.com/v1", model="gpt-6-luna", api_key="sk-test",
        http_client=_openai_client(handler), fallback_to_mock=False,
        profile=PROFILES["openai"], meter=UsageMeter(store),
    )
    deltas, _ = companion.stream(_query())
    assert "".join(deltas) == "What type?"
    assert sent["body"]["stream_options"] == {"include_usage": True}
    (row,) = store.totals("session")
    assert (row.input_tokens, row.output_tokens, row.model) == (50, 3, "gpt-6-luna")


def _sse(chunks) -> httpx.Response:
    body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})


def test_paid_stream_closed_early_is_still_counted(store):
    """A learner who leaves mid-reply must not let a paid call slip past the cap."""
    chunks = [{"id": "c", "object": "chat.completion.chunk", "created": 0, "model": "gpt-6-luna",
               "choices": [{"index": 0, "delta": {"content": f"part{i} "}}]} for i in range(3)]
    companion = OpenAICompatibleCompanion(
        base_url="https://api.openai.com/v1", model="gpt-6-luna", api_key="sk-test",
        http_client=_openai_client(lambda r: _sse(chunks)), fallback_to_mock=False,
        profile=PROFILES["openai"], meter=UsageMeter(store),
    )
    deltas, _ = companion.stream(_query())
    assert next(deltas) == "part0 "
    deltas.close()  # the browser went away
    (row,) = store.totals("session")
    assert row.calls == 1 and row.estimated is True and row.cost_usd > 0


def test_gemini_stream_closed_early_is_still_counted(store):
    deltas, _ = _gemini(FakeGeminiModels("What type is name?"), store).stream(_query())
    next(deltas)
    deltas.close()
    (row,) = store.totals("session")
    assert row.calls == 1 and row.estimated is True and row.cost_usd > 0


def test_local_server_without_usage_is_stored_as_not_reported(store):
    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"object": "list", "data": [{"id": "qwen3.5-9b", "object": "model"}]})
        return httpx.Response(200, json=_completion("What type?", "qwen3.5-9b", None))

    companion = OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:8888/v1", model="auto", api_key="local",
        http_client=_openai_client(handler), profile=PROFILES["local"], meter=UsageMeter(store),
    )
    companion.consult(_query())
    (row,) = store.totals("session")
    assert row.input_tokens is None and row.cost_usd == 0.0


def test_local_failure_falls_back_to_mock():
    companion = OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:8888/v1", model="m", api_key="local",
        http_client=_openai_client(lambda r: httpx.Response(500)),
        profile=PROFILES["local"],
    )
    assert companion.consult(_query()).reply  # mock answered
    assert "Offline Mock" in companion.last_backend_used


def test_paid_failure_does_not_fall_back_and_hides_the_key():
    companion = OpenAICompatibleCompanion(
        base_url="https://api.openai.com/v1", model="gpt-6-luna", api_key="sk-SECRET-123",
        http_client=_openai_client(lambda r: httpx.Response(401, json={"error": {"message": "bad key sk-SECRET-123"}})),
        fallback_to_mock=False, profile=PROFILES["openai"],
    )
    with pytest.raises(LocalLLMError) as info:
        companion.consult(_query())
    assert "sk-SECRET-123" not in str(info.value)


def test_cap_refuses_before_the_provider_is_called(store):
    called = []

    def handler(request):
        called.append(1)
        return httpx.Response(200, json=_completion("x", "gpt-6-luna", None))

    companion = OpenAICompatibleCompanion(
        base_url="https://api.openai.com/v1", model="gpt-6-luna", api_key="sk-test",
        http_client=_openai_client(handler), fallback_to_mock=False,
        profile=PROFILES["openai"], meter=UsageMeter(store, cap_usd=0.0),
    )
    with pytest.raises(BudgetExceeded):
        companion.consult(_query())
    assert called == []


# --- Gemini ------------------------------------------------------------------------


class FakeGeminiModels:
    def __init__(self, text: str, model_version: str = "gemini-3.8-flash-001", usage=(400, 20)):
        self.text, self.model_version, self.usage = text, model_version, usage
        self.calls: list[dict] = []

    def _response(self, text, usage):
        meta = None if usage is None else SimpleNamespace(
            prompt_token_count=usage[0], candidates_token_count=usage[1])
        return SimpleNamespace(text=text, usage_metadata=meta, model_version=self.model_version)

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        return self._response(self.text, self.usage)

    def generate_content_stream(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        half = len(self.text) // 2
        yield self._response(self.text[:half], None)
        yield self._response(self.text[half:], self.usage)


def _gemini(models: FakeGeminiModels, store=None, cap=None) -> GeminiCompanion:
    meter = None if store is None else UsageMeter(store, **({"cap_usd": cap} if cap is not None else {}))
    return GeminiCompanion(
        model="gemini-3.8-flash", api_key="AIza-test",
        client=SimpleNamespace(models=models), profile=PROFILES["gemini"], meter=meter,
    )


def test_gemini_records_usage_and_model_version(store):
    models = FakeGeminiModels("What does name hold?")
    companion = _gemini(models, store)
    companion.consult(_query())
    assert companion.last_model_answered == "gemini-3.8-flash-001"
    (row,) = store.totals("session")
    assert (row.profile_id, row.model, row.input_tokens, row.output_tokens) == (
        "gemini", "gemini-3.8-flash-001", 400, 20)


def test_gemini_stream_reads_usage_from_the_last_chunk(store):
    models = FakeGeminiModels("What type is name?")
    deltas, cited = _gemini(models, store).stream(_query())
    assert "".join(deltas) == "What type is name?"
    (row,) = store.totals("session")
    assert (row.input_tokens, row.output_tokens) == (400, 20)


def test_gemini_thinking_tokens_count_as_output():
    """Seen in the real check on 2026-11-04: gemini-3.6-flash spent its whole limit thinking."""
    from lms.adapters.ai.gemini_companion import _counts

    both = SimpleNamespace(usage_metadata=SimpleNamespace(
        prompt_token_count=14, candidates_token_count=5, thoughts_token_count=11))
    only_thoughts = SimpleNamespace(usage_metadata=SimpleNamespace(
        prompt_token_count=14, candidates_token_count=None, thoughts_token_count=16))
    assert _counts(both) == (14, 16)
    assert _counts(only_thoughts) == (14, 16)


def test_gemini_failure_raises_without_the_key():
    class Broken:
        def generate_content(self, **kw):
            raise RuntimeError("API key AIza-test not valid")

    companion = GeminiCompanion(model="gemini-3.8-flash", api_key="AIza-test",
                                client=SimpleNamespace(models=Broken()), profile=PROFILES["gemini"])
    with pytest.raises(GeminiError) as info:
        companion.consult(_query())
    assert "AIza-test" not in str(info.value)


def test_gemini_cap_refuses_before_the_call(store):
    models = FakeGeminiModels("x")
    with pytest.raises(BudgetExceeded):
        _gemini(models, store, cap=0.0).consult(_query())
    assert models.calls == []


# --- Same AXIS rules everywhere ------------------------------------------------------


def test_both_adapters_send_the_same_system_prompt_and_user_message():
    sent = {}

    def handler(request):
        sent["body"] = json.loads(request.content)
        return httpx.Response(200, json=_completion("ok?", "gpt-6-luna", None))

    oa = OpenAICompatibleCompanion(base_url="https://api.openai.com/v1", model="gpt-6-luna",
                                   api_key="k", http_client=_openai_client(handler),
                                   fallback_to_mock=False, profile=PROFILES["openai"])
    models = FakeGeminiModels("ok?")
    gm = _gemini(models)

    for mode in AxisMode:
        oa.consult(_query(mode))
        gm.consult(_query(mode))
        msgs = sent["body"]["messages"]
        assert msgs[0]["content"] == models.calls[-1]["config"].system_instruction
        assert msgs[1]["content"] == models.calls[-1]["contents"]


def test_socratic_guardrail_strips_code_from_both_providers():
    oa = OpenAICompatibleCompanion(
        base_url="https://api.openai.com/v1", model="gpt-6-luna", api_key="k",
        http_client=_openai_client(lambda r: httpx.Response(200, json=_completion(LEAKY, "gpt-6-luna", None))),
        fallback_to_mock=False, profile=PROFILES["openai"])
    gm = _gemini(FakeGeminiModels(LEAKY))
    for companion in (oa, gm):
        reply = companion.consult(_query(AxisMode.SOCRATIC)).reply
        assert "def run_intake" not in reply
        assert "```" not in reply
