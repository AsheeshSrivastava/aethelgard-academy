"""SPEC-30 tests, part 2: raw reply capture and AXIS_TEMPERATURE.

Covers ADR-0037 section 2.5 / SPEC-30 R16 (`last_raw_reply` on both companions, never logged, traced or returned)
and ADR-0037 section 2.5 C / SPEC-30 R20, R21, R23 (`AXIS_TEMPERATURE`, `chat_temperature`, the live default 0.2).
Offline: SDK clients are faked with httpx.MockTransport and a fake Gemini models object; no key, no network.

Names under test (SPEC-30 section 3; the module of the parser is this file's contract, see the phase 1 report):
  OpenAICompatibleCompanion / GeminiCompanion: `last_raw_reply: Optional[str]`, `chat_temperature: float = 0.2`
  lms.adapters.ai.providers.router.configured_axis_temperature(env) -> float   (raises on a bad value)
  lms.adapters.ai.providers.router.default_factory(..., chat_temperature=0.2)
  lms.adapters.ai.providers.router.build_default_router reads AXIS_TEMPERATURE once.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from test_stage_build import T0

from lms.adapters.ai.gemini_companion import GeminiCompanion
from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.ai.providers.router import ProviderRouter
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.model_usage import UsageStore
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType

REPO = Path(__file__).resolve().parents[1]
RAW_MARK = "zz_raw_marker_fn"
RAW = f"Here is a thought.\n```python\n{RAW_MARK}()\n```\nSee [1] for more. What is x?"
THINK = "<think>private thoughts</think>"

PROFILES = parse_profiles({"profiles": [
    {"id": "local", "label": "Local", "kind": "openai_compatible", "base_url": "http://127.0.0.1:8888/v1",
     "model": "auto", "paid": False},
    {"id": "quiet", "label": "Quiet", "kind": "openai_compatible", "base_url": "https://api.example.test/v1",
     "model": "m", "key_env": "QUIET_KEY", "paid": True, "send_temperature": False,
     "price_per_million": {"input": 0.1, "output": 0.5}},
]})


def query(mode=AxisMode.SOCRATIC) -> AxisQuery:
    return AxisQuery(learner_id="me", unit_id="PY-0.4", current_activity=ActivityType.TRACE,
                     user_prompt="Why does my intake fail?", learner_code="print(name)", mode=mode)


def completion(content: str, model: str = "m") -> dict:
    return {"id": "c1", "object": "chat.completion", "created": 0, "model": model,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}]}


def sse(parts, model: str = "m") -> httpx.Response:
    chunks = [{"id": "c", "object": "chat.completion.chunk", "created": 0, "model": model,
               "choices": [{"index": 0, "delta": {"content": p}}]} for p in parts]
    body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})


class Server:
    """A fake OpenAI-compatible server: records every request body, answers `content` (streamed in two parts)."""

    def __init__(self, content: str = "What does name hold?"):
        self.content, self.bodies = content, []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.bodies.append(body)
        if body.get("stream"):
            half = len(self.content) // 2
            return sse([self.content[:half], self.content[half:]])
        return httpx.Response(200, json=completion(self.content))


def openai(server: Server, **kwargs) -> OpenAICompatibleCompanion:
    return OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:8888/v1", model="m", api_key="k", fallback_to_mock=False,
        http_client=httpx.Client(transport=httpx.MockTransport(server)), **kwargs,
    )


class FakeGeminiModels:
    def __init__(self, text: str = "What does name hold?"):
        self.text, self.calls = text, []

    def _response(self, text):
        return SimpleNamespace(text=text, usage_metadata=None, model_version="gemini-x")

    def generate_content(self, *, model, contents, config):
        self.calls.append({"contents": contents, "config": config})
        return self._response(self.text)

    def generate_content_stream(self, *, model, contents, config):
        self.calls.append({"contents": contents, "config": config})
        half = len(self.text) // 2
        yield self._response(self.text[:half])
        yield self._response(self.text[half:])


def gemini(models: FakeGeminiModels, **kwargs) -> GeminiCompanion:
    return GeminiCompanion(model="gemini-x", api_key="AIza-test", client=SimpleNamespace(models=models), **kwargs)


def drain(companion, q=None):
    deltas, _ = companion.stream(q or query())
    return "".join(deltas)


# --- raw reply capture (R16) ---


def test_companions_keep_last_raw_reply_before_the_guardrail():
    oa = openai(Server(THINK + RAW))
    gm = gemini(FakeGeminiModels(RAW))
    assert oa.last_raw_reply is None and gm.last_raw_reply is None  # nothing asked yet

    for companion in (oa, gm):
        visible = companion.consult(query()).reply

        assert RAW_MARK not in visible and "```" not in visible  # the learner never sees it
        assert companion.last_raw_reply is not None
        assert RAW_MARK in companion.last_raw_reply and "```python" in companion.last_raw_reply  # before the guardrail
        assert "[1]" in companion.last_raw_reply  # before label stripping
        assert "private thoughts" not in companion.last_raw_reply and "<think>" not in companion.last_raw_reply


def test_companions_keep_last_raw_reply_after_a_stream_too():
    oa = openai(Server(THINK + RAW))
    gm = gemini(FakeGeminiModels(RAW))

    for companion in (oa, gm):
        shown = drain(companion)

        assert companion.last_raw_reply is not None
        assert companion.last_raw_reply.strip() == shown.strip() == RAW.strip()
        assert "private thoughts" not in companion.last_raw_reply


def test_last_raw_reply_follows_each_new_call():
    server = Server("First reply?")
    companion = openai(server)
    companion.consult(query())
    assert companion.last_raw_reply.strip() == "First reply?"

    server.content = "Second reply?"
    companion.consult(query())

    assert companion.last_raw_reply.strip() == "Second reply?"


@pytest.fixture
def traces(tmp_path):
    import lms.core.tracing as tracing
    from lms.adapters.observability.local_tracer import LocalTracer

    folder = tmp_path / "traces"
    tracing.set_tracer(LocalTracer(folder))
    yield folder
    tracing.set_tracer(tracing.NoopTracer())


def test_raw_reply_is_not_in_any_route_response_log_or_trace(tmp_path, traces):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    store = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc), session_id="r")
    store.initialize()
    made = []

    def factory(profile, key, meter):
        made.append(openai(Server(RAW), profile=profile, meter=meter))
        return made[-1]

    router = ProviderRouter(PROFILES, store, environ={}, mock=False, factory=factory)
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=router,
                                   catalog=load_all_roadmaps(Path("reference")), clock=lambda: T0))
    body = {"unit_id": "PY-0.1", "mode": "Socratic", "current_activity": "Predict",
            "user_prompt": "Why does my intake fail?", "learner_code": "print(name)", "page": "predict"}

    res = client.post("/api/v1/axis/consult", json=body)

    assert res.status_code == 200, res.text
    assert made and RAW_MARK in made[0].last_raw_reply  # it was captured ...
    assert RAW_MARK not in res.text and "last_raw_reply" not in res.text and "raw_reply" not in res.text
    log = " ".join(e.model_dump_json() for e in repo.get_interactions(LOCAL_LEARNER_ID))
    assert RAW_MARK not in log and "last_raw_reply" not in log
    trace_files = [p for p in traces.glob("axis-trace.jsonl*") if p.is_file()]
    assert trace_files, "a real tracer was set, so the turn must have left a trace"
    text = "".join(p.read_text(encoding="utf-8") for p in trace_files)
    assert RAW_MARK not in text and "private" not in text and "last_raw_reply" not in text


# --- AXIS_TEMPERATURE: parsing and validation (R20) ---


def parser():
    from lms.adapters.ai.providers.router import configured_axis_temperature

    return configured_axis_temperature


def test_temperature_unset_is_0_2():
    read = parser()

    assert read({}) == 0.2
    assert read({"AXIS_TEMPERATURE": ""}) == 0.2
    assert read({"AXIS_TEMPERATURE": "   "}) == 0.2


@pytest.mark.parametrize("raw, expected", [
    ("0", 0.0), ("0.0", 0.0), ("0.2", 0.2), ("0.20", 0.2), (" 0.5 ", 0.5), ("1", 1.0), ("1.5", 1.5), ("2", 2.0), ("2.0", 2.0),
])
def test_temperature_accepts_numbers_from_0_to_2(raw, expected):
    value = parser()({"AXIS_TEMPERATURE": raw})

    assert isinstance(value, float) and value == expected


@pytest.mark.parametrize("raw", ["-0.1", "2.1", "abc", "nan", "NaN", "inf", "-inf", "Infinity", "0x1", "1,5", "0.2.1"])
def test_temperature_bounds_and_bad_values_stop_startup(raw, tmp_path, monkeypatch):
    read = parser()
    with pytest.raises(Exception, match="AXIS_TEMPERATURE"):
        read({"AXIS_TEMPERATURE": raw})

    # Start-up stops too, even with MOCK_AI=true (like LMS_TRACER).
    from lms.adapters.ai.providers.router import build_default_router

    monkeypatch.chdir(tmp_path)  # no .env of the real project is read
    monkeypatch.setenv("MOCK_AI", "true")
    monkeypatch.setenv("AXIS_TEMPERATURE", raw)
    with pytest.raises(Exception, match="AXIS_TEMPERATURE"):
        build_default_router(str(tmp_path / "u.db"), str(REPO / "config" / "providers.yaml"))


def test_temperature_error_is_not_an_import_or_attribute_error():
    read = parser()
    with pytest.raises(Exception) as info:
        read({"AXIS_TEMPERATURE": "3"})

    assert not isinstance(info.value, (ImportError, AttributeError, TypeError))
    assert math.isfinite(read({"AXIS_TEMPERATURE": "2"}))


def test_build_default_router_reads_the_setting_once_and_passes_it_on(tmp_path, monkeypatch):
    from lms.adapters.ai.providers.router import build_default_router

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MOCK_AI", "true")
    monkeypatch.setenv("AXIS_TEMPERATURE", "0.5")
    router = build_default_router(str(tmp_path / "u.db"), str(REPO / "config" / "providers.yaml"))

    companion = router.factory(router.active_profile(), None, router.meter)
    monkeypatch.setenv("AXIS_TEMPERATURE", "1.9")  # read once at start-up: a later change is not seen

    assert companion.chat_temperature == 0.5
    assert router.factory(router.active_profile(), None, router.meter).chat_temperature == 0.5


def test_unset_setting_leaves_the_router_at_0_2(tmp_path, monkeypatch):
    from lms.adapters.ai.providers.router import build_default_router

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MOCK_AI", "true")
    monkeypatch.delenv("AXIS_TEMPERATURE", raising=False)
    router = build_default_router(str(tmp_path / "u.db"), str(REPO / "config" / "providers.yaml"))

    assert router.factory(router.active_profile(), None, router.meter).chat_temperature == 0.2


# --- chat only (R20) ---


def test_temperature_applies_to_chat_only():
    server = Server("ok?")
    companion = openai(server, chat_temperature=0.9)

    companion.consult(query())
    drain(companion)
    companion.ping()
    companion.judge("PY-0.4", "prompt", "explanation", [])
    companion.draft_readme("entry", "code", "brief")
    companion.summarise_feedback([], "readme", "note")

    assert [b.get("temperature") for b in server.bodies] == [0.9, 0.9, 0.0, 0.0, 0.3, 0.2]


def test_gemini_temperature_applies_to_chat_only():
    models = FakeGeminiModels("ok?")
    companion = gemini(models, chat_temperature=0.9)

    companion.consult(query())
    drain(companion)
    companion.ping()
    companion.judge("PY-0.4", "prompt", "explanation", [])
    companion.draft_readme("entry", "code", "brief")
    companion.summarise_feedback([], "readme", "note")

    assert [c["config"].temperature for c in models.calls] == [0.9, 0.9, 0.0, 0.0, 0.3, 0.2]


# --- plumbing (R21) ---


@pytest.mark.parametrize("value", [0.0, 0.7, 2.0])
def test_chat_temperature_reaches_openai_and_gemini_calls(value):
    server = Server("ok?")
    oa = openai(server, chat_temperature=value)
    oa.consult(query())
    drain(oa)
    assert [b["temperature"] for b in server.bodies] == [value, value]  # 0.0 is sent too

    models = FakeGeminiModels("ok?")
    gm = gemini(models, chat_temperature=value)
    gm.consult(query())
    drain(gm)
    assert [c["config"].temperature for c in models.calls] == [value, value]


def test_send_temperature_false_still_sends_none():
    server = Server("ok?")
    companion = openai(server, send_temperature=False, chat_temperature=0.7)

    companion.consult(query())
    drain(companion)
    companion.ping()

    assert len(server.bodies) == 3
    assert all("temperature" not in body for body in server.bodies)


def test_default_factory_passes_the_configured_temperature():
    from lms.adapters.ai.providers.router import default_factory

    make = default_factory(chat_temperature=0.7)

    local = make(PROFILES["local"], None, None)
    quiet = make(PROFILES["quiet"], "key", None)

    assert local.chat_temperature == 0.7 and local.send_temperature is True
    assert quiet.chat_temperature == 0.7 and quiet.send_temperature is False  # the profile still decides if it is sent


def test_live_default_is_unchanged_at_0_2():
    import inspect

    from lms.adapters.ai.providers.router import default_factory

    for cls in (OpenAICompatibleCompanion, GeminiCompanion):
        assert inspect.signature(cls.__init__).parameters["chat_temperature"].default == 0.2

    server = Server("ok?")
    oa = openai(server)
    oa.consult(query())
    drain(oa)
    assert oa.chat_temperature == 0.2 and [b["temperature"] for b in server.bodies] == [0.2, 0.2]

    models = FakeGeminiModels("ok?")
    gm = gemini(models)
    gm.consult(query())
    drain(gm)
    assert gm.chat_temperature == 0.2 and [c["config"].temperature for c in models.calls] == [0.2, 0.2]

    assert default_factory()(PROFILES["local"], None, None).chat_temperature == 0.2
    assert parser()({}) == 0.2
