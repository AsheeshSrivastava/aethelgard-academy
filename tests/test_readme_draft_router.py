"""The provider switcher's README draft (SPEC-15 section 9.4, ADR-0028). Offline: fake companions only."""

from datetime import datetime, timezone

import pytest

from lms.adapters.ai.providers.axis_rules import readme_draft_prompts
from lms.adapters.ai.providers.metering import BudgetExceeded
from lms.adapters.ai.providers.router import DraftFailed, ProviderRouter
from lms.adapters.db.model_usage import UsageStore
from test_model_settings_api import PROFILES, FAKE_OPENAI_KEY


class Drafter:
    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = []

    def draft_readme(self, entry, code, brief):
        self.calls.append((entry, code, brief))
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        return self.behaviour


def router_with(tmp_path, companion, env=None, mock=False):
    store = UsageStore(tmp_path / "u.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc), session_id="r")
    store.initialize()
    return ProviderRouter(
        PROFILES, store, environ={"OPENAI_API_KEY": FAKE_OPENAI_KEY} if env is None else env,
        mock=mock, factory=lambda profile, key, meter: companion,
    )


def test_the_active_provider_drafts_and_reports_what_answered(tmp_path):
    companion = Drafter(("# R\n", "some-model"))

    text, model = router_with(tmp_path, companion).draft_readme("checkin.py", "print(1)", "A brief")

    assert (text, model) == ("# R\n", "some-model")
    assert companion.calls == [("checkin.py", "print(1)", "A brief")]


def test_mock_mode_never_builds_a_provider(tmp_path):
    def boom(*args):
        raise AssertionError("no provider may be built")

    store = UsageStore(tmp_path / "u.db", session_id="r")
    store.initialize()
    router = ProviderRouter(PROFILES, store, environ={}, mock=True, factory=boom)

    text, _ = router.draft_readme("checkin.py", "", "")

    assert "uv run checkin.py" in text


def test_a_provider_failure_is_plain_and_hides_the_provider_text(tmp_path):
    router = router_with(tmp_path, Drafter(RuntimeError("secret sk-12345 leaked")))

    with pytest.raises(DraftFailed) as raised:
        router.draft_readme("checkin.py", "", "")

    assert "sk-12345" not in str(raised.value) and "could not draft" in str(raised.value)


def test_a_spent_budget_is_named(tmp_path):
    router = router_with(tmp_path, Drafter(BudgetExceeded("cap")))

    with pytest.raises(DraftFailed, match="budget"):
        router.draft_readme("checkin.py", "", "")


def test_an_empty_reply_is_a_failure_not_a_fallback(tmp_path):
    with pytest.raises(DraftFailed, match="empty"):
        router_with(tmp_path, Drafter(("  \n", "m"))).draft_readme("checkin.py", "", "")


def test_a_missing_key_is_a_failure_not_a_fallback(tmp_path):
    router = router_with(tmp_path, Drafter(("x", "m")), env={})
    router.active_profile = lambda: PROFILES["openai"]

    with pytest.raises(DraftFailed, match="not set up"):
        router.draft_readme("checkin.py", "", "")


def test_the_prompt_asks_for_the_five_headings_and_the_run_command_and_names_no_exercise():
    system, user = readme_draft_prompts("checkin.py", "print(1)", "Write a slip script.")

    for heading in ("What it does", "What you need first", "How to run it", "A sample run", "Limits"):
        assert f"## {heading}" in system
    assert "uv run checkin.py" in system and "(paste a real run here)" in system
    assert "python/stage-0/build" not in system + user
    assert "<script" in user and "print(1)" in user
