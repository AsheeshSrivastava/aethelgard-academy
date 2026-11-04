"""Provider profiles: loading and rejection rules (SPEC-17 section 2.1, ADR-0025)."""

from pathlib import Path

import pytest

from lms.adapters.ai.providers.profiles import (
    ProfileError,
    ProviderKind,
    load_profiles,
    parse_profiles,
)


def _good() -> dict:
    return {
        "profiles": [
            {
                "id": "local",
                "label": "Local model",
                "kind": "openai_compatible",
                "base_url": "http://127.0.0.1:8888/v1",
                "model": "auto",
                "key_env": "UNSLOTH_STUDIO_AUTH_TOKEN",
                "paid": False,
            },
            {
                "id": "openai",
                "label": "OpenAI",
                "kind": "openai_compatible",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-6-luna",
                "key_env": "OPENAI_API_KEY",
                "paid": True,
                "price_per_million": {"input": 0.10, "output": 0.50},
            },
            {
                "id": "gemini",
                "label": "Gemini",
                "kind": "gemini",
                "model": "gemini-3.8-flash",
                "key_env": "GEMINI_API_KEY",
                "paid": True,
                "price_per_million": {"input": 0.75, "output": 3.75},
            },
        ]
    }


def test_good_file_loads_in_order():
    profiles = parse_profiles(_good())
    assert list(profiles) == ["local", "openai", "gemini"]
    assert profiles["gemini"].kind is ProviderKind.GEMINI
    assert profiles["openai"].paid is True


def test_shipped_profiles_file_loads():
    profiles = load_profiles(Path("config/providers.yaml"))
    assert {"local", "openai", "gemini"} <= set(profiles)
    assert profiles["local"].paid is False
    assert profiles["gemini"].paid is True  # owner decision: Gemini counts as paid
    assert profiles["openai"].paid is True


def test_duplicate_id_is_rejected():
    data = _good()
    data["profiles"][1]["id"] = "local"
    with pytest.raises(ProfileError, match="duplicate"):
        parse_profiles(data)


def test_unknown_kind_is_rejected():
    data = _good()
    data["profiles"][0]["kind"] = "anthropic_magic"
    with pytest.raises(ProfileError):
        parse_profiles(data)


def test_paid_profile_without_prices_is_rejected():
    data = _good()
    del data["profiles"][1]["price_per_million"]
    with pytest.raises(ProfileError, match="price"):
        parse_profiles(data)


def test_negative_price_is_rejected():
    data = _good()
    data["profiles"][1]["price_per_million"]["output"] = -1
    with pytest.raises(ProfileError):
        parse_profiles(data)


@pytest.mark.parametrize("bad", ["sk-abc123", "AIzaSyFakeKey", "openai_api_key", "MY KEY", ""])
def test_key_env_must_be_a_variable_name_not_a_key(bad):
    data = _good()
    data["profiles"][1]["key_env"] = bad
    with pytest.raises(ProfileError):
        parse_profiles(data)


def test_openai_compatible_needs_base_url():
    data = _good()
    del data["profiles"][1]["base_url"]
    with pytest.raises(ProfileError, match="base_url"):
        parse_profiles(data)


def test_key_set_reads_only_presence():
    profiles = parse_profiles(_good())
    assert profiles["openai"].key_set({"OPENAI_API_KEY": "sk-secret"}) is True
    assert profiles["openai"].key_set({"OPENAI_API_KEY": "   "}) is False
    assert profiles["openai"].key_set({}) is False


def test_cost_uses_prices_and_free_is_zero():
    profiles = parse_profiles(_good())
    # 1M input at $0.10 plus 1M output at $0.50
    assert profiles["openai"].cost_usd(1_000_000, 1_000_000) == pytest.approx(0.60)
    assert profiles["local"].cost_usd(5_000, 5_000) == 0.0


def test_empty_file_is_rejected():
    with pytest.raises(ProfileError):
        parse_profiles({})
