"""Token metering and the monthly spending cap (SPEC-17 sections 4 and 5).

Every adapter calls `check` before a provider call and `record` after it.
"""

from __future__ import annotations

from typing import Optional

from lms.adapters.ai.providers.profiles import ProviderProfile
from lms.adapters.db.model_usage import UsageStore

MONTHLY_CAP_USD = 5.0  # owner decision 2026-11-04 (ADR-0025 section 4)

CALLS = ("consult", "stream", "concept_check", "connection_test")


class BudgetExceeded(Exception):
    """A paid call would pass this month's cap. Raised before the provider is called."""


class UsageMeter:
    def __init__(self, store: UsageStore, cap_usd: float = MONTHLY_CAP_USD) -> None:
        self.store = store
        self.cap_usd = cap_usd

    def worst_case_cost(self, profile: ProviderProfile, input_chars: int) -> float:
        """Upper bound for one call. A token is at least one character, so the
        character count bounds the input tokens; the reply is bounded by max_output_tokens."""
        return profile.cost_usd(max(0, input_chars), profile.max_output_tokens)

    def check(self, profile: ProviderProfile, input_chars: int) -> None:
        """Refuse a paid call that could take this month's spend past the cap."""
        if not profile.paid:
            return  # free profiles are never blocked
        projected = self.store.month_spend() + self.worst_case_cost(profile, input_chars)
        if projected > self.cap_usd:
            raise BudgetExceeded(f"Monthly AI budget of ${self.cap_usd:.2f} would be passed.")

    def record(
        self,
        profile: ProviderProfile,
        model: str,
        call: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        input_chars: int = 0,
    ) -> None:
        """Store one call's counts. A paid call with no counts is costed at its limit."""
        if call not in CALLS:
            raise ValueError(f"unknown call type '{call}'")
        estimated = False
        if input_tokens is not None and output_tokens is not None:
            cost: Optional[float] = profile.cost_usd(input_tokens, output_tokens)
        elif profile.paid:
            cost = self.worst_case_cost(profile, input_chars)
            estimated = True
        else:
            cost = 0.0
        self.store.add(profile.id, model, call, input_tokens, output_tokens, cost, estimated)
