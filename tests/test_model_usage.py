"""Token counts, session and month totals, and the monthly cap (SPEC-17 sections 4 and 5)."""

from datetime import datetime, timezone

import pytest

from lms.adapters.ai.providers.metering import (
    MONTHLY_CAP_USD,
    BudgetExceeded,
    UsageMeter,
)
from lms.adapters.ai.providers.profiles import parse_profiles
from lms.adapters.db.model_usage import UsageStore


class Clock:
    def __init__(self, when: datetime) -> None:
        self.when = when

    def __call__(self) -> datetime:
        return self.when


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


@pytest.fixture
def clock():
    return Clock(datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc))


@pytest.fixture
def store(tmp_path, clock):
    s = UsageStore(tmp_path / "usage.db", clock=clock, session_id="run-1")
    s.initialize()
    return s


def test_cap_is_five_dollars():
    assert MONTHLY_CAP_USD == 5.0


def test_switches_within_a_session_are_counted_per_profile_and_model(store):
    meter = UsageMeter(store)
    meter.record(PROFILES["local"], "qwen3.5-9b", "consult", 100, 20)
    meter.record(PROFILES["gemini"], "gemini-3.8-flash", "stream", 200, 50)
    meter.record(PROFILES["gemini"], "gemini-3.8-flash", "consult", 300, 50)
    meter.record(PROFILES["gemini"], "gemini-3.6-flash", "consult", 10, 5)  # provider swapped model
    meter.record(PROFILES["openai"], "gpt-6-luna", "consult", 1000, 100)

    rows = {(r.profile_id, r.model): r for r in store.totals("session")}
    assert set(rows) == {
        ("local", "qwen3.5-9b"),
        ("gemini", "gemini-3.8-flash"),
        ("gemini", "gemini-3.6-flash"),
        ("openai", "gpt-6-luna"),
    }
    g = rows[("gemini", "gemini-3.8-flash")]
    assert (g.calls, g.input_tokens, g.output_tokens) == (2, 500, 100)
    assert rows[("local", "qwen3.5-9b")].cost_usd == 0.0
    assert rows[("openai", "gpt-6-luna")].cost_usd == pytest.approx((1000 * 0.10 + 100 * 0.50) / 1e6)


def test_session_totals_exclude_other_runs_but_month_includes_them(tmp_path, clock):
    db = tmp_path / "usage.db"
    first = UsageStore(db, clock=clock, session_id="run-1")
    first.initialize()
    UsageMeter(first).record(PROFILES["openai"], "gpt-6-luna", "consult", 10, 10)
    second = UsageStore(db, clock=clock, session_id="run-2")
    second.initialize()
    UsageMeter(second).record(PROFILES["openai"], "gpt-6-luna", "consult", 30, 30)

    assert [r.input_tokens for r in second.totals("session")] == [30]
    assert [r.input_tokens for r in second.totals("month")] == [40]


def test_missing_counts_on_a_free_profile_are_stored_as_not_reported(store):
    UsageMeter(store).record(PROFILES["local"], "qwen3.5-9b", "stream", None, None)
    (row,) = store.totals("session")
    assert row.input_tokens is None and row.output_tokens is None
    assert row.cost_usd == 0.0
    assert row.calls == 1


def test_missing_counts_on_a_paid_profile_are_costed_at_the_limit(store):
    meter = UsageMeter(store)
    meter.record(PROFILES["openai"], "gpt-6-luna", "stream", None, None, input_chars=400)
    (row,) = store.totals("session")
    profile = PROFILES["openai"]
    expected = profile.cost_usd(400, profile.max_output_tokens)
    assert row.cost_usd == pytest.approx(expected)
    assert row.estimated is True


def test_month_spend_resets_in_a_new_month(store, clock):
    meter = UsageMeter(store)
    meter.record(PROFILES["openai"], "gpt-6-luna", "consult", 1_000_000, 1_000_000)
    assert store.month_spend() == pytest.approx(0.60)
    clock.when = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)
    assert store.month_spend() == 0.0


def test_paid_call_that_would_pass_the_cap_is_refused(store):
    meter = UsageMeter(store, cap_usd=1.0)
    # $0.95 already spent this month on Gemini
    meter.record(PROFILES["gemini"], "gemini-3.8-flash", "consult", 1_000_000, 53_334)
    with pytest.raises(BudgetExceeded):
        # worst case: 100k input tokens ($0.075) plus the full reply limit; 0.95 + 0.075 > 1.0
        meter.check(PROFILES["gemini"], input_chars=100_000)


def test_paid_call_under_the_cap_is_allowed(store):
    UsageMeter(store).check(PROFILES["openai"], input_chars=4_000)  # no raise


def test_free_profile_is_never_refused(store):
    meter = UsageMeter(store, cap_usd=0.0)
    meter.check(PROFILES["local"], input_chars=10_000_000)  # no raise


def test_no_text_is_stored(store):
    UsageMeter(store).record(PROFILES["openai"], "gpt-6-luna", "consult", 5, 5)
    columns = store.column_names()
    assert not {"prompt", "reply", "text", "code", "key", "api_key"} & set(columns)


def test_active_profile_round_trips(store):
    assert store.get_active() is None
    store.set_active("gemini")
    assert store.get_active() == "gemini"
    store.set_active("local")
    assert store.get_active() == "local"
