"""Provider switcher and the /api/v1/settings/models routes (SPEC-17 sections 2.2, 5, 6).

Offline: the switcher builds fake companions; no SDK is called and no real key is used."""

import logging
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers.metering import BudgetExceeded, UsageMeter
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.ai.providers.router import (
    BUDGET_MESSAGE,
    KeyMissing,
    PaidNotConfirmed,
    ProviderRouter,
    UnknownProfile,
)
from lms.adapters.db.model_usage import UsageStore
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import create_app
from lms.core.interfaces import AxisMode, AxisQuery, AxisResponse
from lms.core.models import ActivityType

FAKE_OPENAI_KEY = "sk-FAKE-never-shown-0001"
FAKE_GEMINI_KEY = "AIza-FAKE-never-shown-0002"

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


class FakeCompanion:
    """Stands in for a real adapter; records usage through the meter like one."""

    def __init__(self, profile, meter, answered_model):
        self.profile, self.meter, self.last_model_answered = profile, meter, answered_model

    def consult(self, query):
        if self.meter:
            self.meter.check(self.profile, input_chars=len(query.user_prompt))
            self.meter.record(self.profile, self.last_model_answered, "consult", 7, 3)
        return AxisResponse(reply=f"[{self.profile.id}] What does it hold?")

    def stream(self, query):
        if self.meter:
            self.meter.check(self.profile, input_chars=len(query.user_prompt))
        return iter([f"[{self.profile.id}] ok"]), []

    def ping(self):
        if self.meter:
            self.meter.check(self.profile, input_chars=30)
            self.meter.record(self.profile, self.last_model_answered, "connection_test", 7, 3)
        return self.last_model_answered, 7, 3


def _factory(built):
    def make(profile, api_key, meter):
        built.append((profile.id, api_key))
        return FakeCompanion(profile, meter, answered_model=f"{profile.model}-answered")
    return make


@pytest.fixture
def env():
    return {"OPENAI_API_KEY": FAKE_OPENAI_KEY, "GEMINI_API_KEY": FAKE_GEMINI_KEY}


@pytest.fixture
def store(tmp_path):
    s = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc),
                   session_id="run-1")
    s.initialize()
    return s


@pytest.fixture
def built():
    return []


@pytest.fixture
def router(store, env, built):
    return ProviderRouter(PROFILES, store, environ=env, mock=False, factory=_factory(built))


@pytest.fixture
def client(router):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(repo=repo, runner=SubprocessRunner(), providers=router)
    return TestClient(app)


def _query():
    return AxisQuery(unit_id="PY-0.4", mode=AxisMode.SOCRATIC,
                     current_activity=ActivityType.TRACE, user_prompt="why?")


# --- switcher --------------------------------------------------------------------


def test_starts_on_local(router):
    assert router.active_profile().id == "local"


def test_switch_routes_calls_to_the_new_profile(router):
    assert router.consult(_query()).reply.startswith("[local]")
    router.switch("gemini", confirm_paid=True)
    assert router.consult(_query()).reply.startswith("[gemini]")


def test_choice_survives_a_restart(store, env, built):
    ProviderRouter(PROFILES, store, environ=env, mock=False, factory=_factory(built)).switch(
        "openai", confirm_paid=True)
    again = ProviderRouter(PROFILES, store, environ=env, mock=False, factory=_factory(built))
    assert again.active_profile().id == "openai"


def test_switch_rules(router, store, built):
    with pytest.raises(UnknownProfile):
        router.switch("nope", confirm_paid=True)
    with pytest.raises(PaidNotConfirmed):
        router.switch("openai", confirm_paid=False)
    no_keys = ProviderRouter(PROFILES, store, environ={}, mock=False, factory=_factory(built))
    with pytest.raises(KeyMissing):
        no_keys.switch("gemini", confirm_paid=True)


def test_budget_refusal_becomes_a_plain_message(router, store):
    router.switch("openai", confirm_paid=True)
    router.meter.cap_usd = 0.0
    assert router.consult(_query()).reply == BUDGET_MESSAGE
    deltas, _ = router.stream(_query())
    assert "".join(deltas) == BUDGET_MESSAGE


def test_mock_mode_uses_the_mock_and_refuses_switching(store, env, built):
    r = ProviderRouter(PROFILES, store, environ=env, mock=True, factory=_factory(built))
    assert isinstance(r.current(), MockAxisCompanion)
    with pytest.raises(RuntimeError):
        r.switch("gemini", confirm_paid=True)
    assert built == []


# --- API -------------------------------------------------------------------------


def test_get_lists_profiles_with_key_set_and_never_the_key(client):
    res = client.get("/api/v1/settings/models")
    assert res.status_code == 200
    body = res.json()
    assert body["active"] == "local"
    assert body["mock"] is False
    assert body["cap_usd"] == 5.0
    by_id = {p["id"]: p for p in body["profiles"]}
    assert by_id["openai"]["key_set"] is True
    assert by_id["gemini"]["paid"] is True
    assert by_id["openai"]["price_per_million"] == {"input": 0.10, "output": 0.50}
    assert "estimate_per_question_usd" in by_id["openai"]
    assert FAKE_OPENAI_KEY not in res.text and FAKE_GEMINI_KEY not in res.text


def test_put_active_status_codes(client):
    assert client.put("/api/v1/settings/models/active",
                      json={"profile_id": "nope", "confirm_paid": True}).status_code == 404
    assert client.put("/api/v1/settings/models/active",
                      json={"profile_id": "gemini", "confirm_paid": False}).status_code == 409
    ok = client.put("/api/v1/settings/models/active",
                    json={"profile_id": "gemini", "confirm_paid": True})
    assert ok.status_code == 200 and ok.json()["active"] == "gemini"


def test_put_active_without_key_is_409(store, built):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    r = ProviderRouter(PROFILES, store, environ={}, mock=False, factory=_factory(built))
    c = TestClient(create_app(repo=repo, runner=SubprocessRunner(), providers=r))
    res = c.put("/api/v1/settings/models/active", json={"profile_id": "openai", "confirm_paid": True})
    assert res.status_code == 409


def test_connection_test_reports_the_model_that_answered_and_counts(client):
    client.put("/api/v1/settings/models/active", json={"profile_id": "gemini", "confirm_paid": True})
    res = client.post("/api/v1/settings/models/test")
    body = res.json()
    assert body["ok"] is True
    assert body["model_answered"] == "gemini-3.8-flash-answered"
    assert body["input_tokens"] == 7 and body["output_tokens"] == 3
    assert "latency_ms" in body


def test_usage_shows_session_and_month_by_profile_and_model(client):
    client.post("/api/v1/settings/models/test")  # local
    client.put("/api/v1/settings/models/active", json={"profile_id": "gemini", "confirm_paid": True})
    client.post("/api/v1/settings/models/test")
    body = client.get("/api/v1/settings/models/usage").json()
    pairs = {(r["profile_id"], r["model"]) for r in body["session"]}
    assert pairs == {("local", "auto-answered"), ("gemini", "gemini-3.8-flash-answered")}
    assert body["month_spend_usd"] >= 0
    assert body["cap_usd"] == 5.0


def test_axis_routes_go_through_the_active_profile(client):
    client.put("/api/v1/settings/models/active", json={"profile_id": "gemini", "confirm_paid": True})
    res = client.post("/api/v1/axis/consult", json={
        "unit_id": "PY-0.4", "mode": "Socratic", "current_activity": "Trace", "user_prompt": "why?"})
    assert res.status_code == 200
    assert res.json()["reply"].startswith("[gemini]")


def test_mock_mode_api_disables_switching(store, env, built):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    r = ProviderRouter(PROFILES, store, environ=env, mock=True, factory=_factory(built))
    c = TestClient(create_app(repo=repo, runner=SubprocessRunner(), providers=r))
    assert c.get("/api/v1/settings/models").json()["mock"] is True
    res = c.put("/api/v1/settings/models/active", json={"profile_id": "gemini", "confirm_paid": True})
    assert res.status_code == 409


def test_keys_never_reach_logs_or_the_usage_table(client, store, caplog):
    caplog.set_level(logging.DEBUG)
    client.put("/api/v1/settings/models/active", json={"profile_id": "openai", "confirm_paid": True})
    client.post("/api/v1/settings/models/test")
    client.get("/api/v1/settings/models/usage")
    assert FAKE_OPENAI_KEY not in caplog.text
    assert FAKE_OPENAI_KEY not in store.dump_text()
