"""Provider profiles: which model AXIS may call, and how (SPEC-17 section 2.1).

A profile names the environment variable that holds a key, never the key itself.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Literal, Mapping, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

KEY_ENV_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
DEFAULT_PROFILE_ID = "local"
DEFAULT_PROFILES_PATH = Path("config/providers.yaml")

# One typical AXIS question, used for the estimate shown before a paid switch (SPEC-17 5.2).
TYPICAL_INPUT_TOKENS = 1_500
TYPICAL_OUTPUT_TOKENS = 400


class ProfileError(ValueError):
    """The profiles file is wrong. Raised at start, never silently ignored."""


class ProviderKind(str, Enum):
    OPENAI_COMPATIBLE = "openai_compatible"
    GEMINI = "gemini"


class Prices(BaseModel):
    """US dollars per one million tokens."""

    input: float = Field(ge=0)
    output: float = Field(ge=0)


class ProviderProfile(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    kind: ProviderKind
    base_url: Optional[str] = None
    model: str = Field(min_length=1)
    key_env: Optional[str] = None
    paid: bool = False
    price_per_million: Optional[Prices] = None
    max_output_tokens: int = Field(default=1024, gt=0)
    # OpenAI's newer models take max_completion_tokens and reject a temperature; local servers want max_tokens.
    token_limit_field: Literal["max_tokens", "max_completion_tokens"] = "max_tokens"
    send_temperature: bool = True
    # Ask an OpenAI-compatible local server to skip thinking (owner request 2026-11-04).
    disable_thinking: bool = False

    @field_validator("key_env")
    @classmethod
    def _key_env_is_a_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not KEY_ENV_PATTERN.match(value):
            # Do not echo the value: it may be a pasted key.
            raise ValueError("key_env must be an environment variable name such as OPENAI_API_KEY")
        return value

    @model_validator(mode="after")
    def _rules(self) -> "ProviderProfile":
        if self.paid and self.price_per_million is None:
            raise ValueError(f"paid profile '{self.id}' needs price_per_million")
        if self.kind is ProviderKind.OPENAI_COMPATIBLE and not self.base_url:
            raise ValueError(f"profile '{self.id}' needs a base_url")
        return self

    def key_set(self, environ: Mapping[str, str]) -> bool:
        """True when the key variable holds something. Says nothing else about the key."""
        if self.key_env is None:
            return True
        return bool((environ.get(self.key_env) or "").strip())

    def api_key(self, environ: Mapping[str, str]) -> Optional[str]:
        if self.key_env is None:
            return None
        return (environ.get(self.key_env) or "").strip() or None

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        if not self.paid or self.price_per_million is None:
            return 0.0
        p = self.price_per_million
        return (input_tokens * p.input + output_tokens * p.output) / 1_000_000

    def estimate_per_question_usd(self) -> float:
        return self.cost_usd(TYPICAL_INPUT_TOKENS, TYPICAL_OUTPUT_TOKENS)


def parse_profiles(data: Any) -> Dict[str, ProviderProfile]:
    if not isinstance(data, dict) or not isinstance(data.get("profiles"), list) or not data["profiles"]:
        raise ProfileError("the profiles file needs a non-empty 'profiles' list")
    profiles: Dict[str, ProviderProfile] = {}
    for index, raw in enumerate(data["profiles"]):
        try:
            profile = ProviderProfile.model_validate(raw)
        except ValidationError as exc:
            # Report fields and messages only, never the input values.
            reasons = "; ".join(f"{'.'.join(map(str, e['loc'])) or 'profile'}: {e['msg']}" for e in exc.errors())
            raise ProfileError(f"profile #{index + 1} is invalid: {reasons}") from None
        if profile.id in profiles:
            raise ProfileError(f"duplicate profile id '{profile.id}'")
        profiles[profile.id] = profile
    return profiles


def load_profiles(path: Path = DEFAULT_PROFILES_PATH) -> Dict[str, ProviderProfile]:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProfileError(f"cannot read profiles file {path}: {type(exc).__name__}") from None
    return parse_profiles(data)
