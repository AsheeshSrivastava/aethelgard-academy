"""The provider switcher (SPEC-17 sections 2.2, 3 and 5).

The app holds one ProviderRouter as its AXIS companion. Each call goes to the
adapter of the active profile, so switching needs no restart and nothing else
in the app knows which provider answers.
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple

from lms.adapters.ai.concept_store import ConceptStore
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers.judging import judge_with
from lms.adapters.ai.providers.metering import BudgetExceeded, MONTHLY_CAP_USD, UsageMeter
from lms.adapters.ai.providers.profiles import (
    DEFAULT_PROFILE_ID,
    ProviderKind,
    ProviderProfile,
)
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.adapters.db.model_usage import UsageStore
from lms.core.ai_judgement import AiJudgement, Rubric, not_judged
from lms.core.interfaces import AxisQuery, AxisResponse

BUDGET_MESSAGE = (
    "The monthly AI budget is used up. Switch to the local model or wait until next month."
)

# factory(profile, api_key, meter) -> companion
Factory = Callable[[ProviderProfile, Optional[str], UsageMeter], Any]


class UnknownProfile(LookupError):
    pass


class KeyMissing(Exception):
    pass


class PaidNotConfirmed(Exception):
    pass


def default_factory(
    concept_store: Optional[ConceptStore] = None,
    retriever: Optional[HybridRerankedRetriever] = None,
) -> Factory:
    def make(profile: ProviderProfile, api_key: Optional[str], meter: UsageMeter) -> Any:
        if profile.kind is ProviderKind.GEMINI:
            from lms.adapters.ai.gemini_companion import GeminiCompanion

            return GeminiCompanion(
                model=profile.model, api_key=api_key, concept_store=concept_store,
                retriever=retriever, profile=profile, meter=meter,
            )
        from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion

        return OpenAICompatibleCompanion(
            base_url=profile.base_url, model=profile.model, api_key=api_key,
            concept_store=concept_store, retriever=retriever,
            fallback_to_mock=not profile.paid,  # a paid failure is reported, never hidden
            profile=profile, meter=meter,
            token_limit_field=profile.token_limit_field,
            send_temperature=profile.send_temperature,
            disable_thinking=profile.disable_thinking,
        )

    return make


class ProviderRouter:
    def __init__(
        self,
        profiles: Dict[str, ProviderProfile],
        store: UsageStore,
        environ: Optional[Mapping[str, str]] = None,
        mock: bool = False,
        factory: Optional[Factory] = None,
        meter: Optional[UsageMeter] = None,
    ) -> None:
        self.profiles = profiles
        self.store = store
        self.environ = environ if environ is not None else os.environ
        self.mock = mock
        self.factory = factory or default_factory()
        self.meter = meter or UsageMeter(store)
        self._mock_companion = MockAxisCompanion()
        self._companions: Dict[str, Any] = {}
        stored = store.get_active()
        self._active_id = stored if stored in profiles else self._fallback_id()
        stored_judge = store.get_judge()
        self._judge_id: Optional[str] = stored_judge if stored_judge in profiles else None

    def _fallback_id(self) -> str:
        return DEFAULT_PROFILE_ID if DEFAULT_PROFILE_ID in self.profiles else next(iter(self.profiles))

    # --- choosing --------------------------------------------------------------

    def active_profile(self) -> ProviderProfile:
        return self.profiles[self._active_id]

    def key_set(self, profile: ProviderProfile) -> bool:
        return profile.key_set(self.environ)

    def _checked_profile(self, profile_id: str, confirm_paid: bool) -> ProviderProfile:
        if self.mock:
            raise RuntimeError("Mock mode is on (MOCK_AI=true); switching is disabled.")
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise UnknownProfile(profile_id)
        if not self.key_set(profile):
            raise KeyMissing(f"{profile.key_env} is not set in .env")
        if profile.paid and not confirm_paid:
            raise PaidNotConfirmed(profile_id)
        return profile

    def switch(self, profile_id: str, confirm_paid: bool) -> ProviderProfile:
        profile = self._checked_profile(profile_id, confirm_paid)
        self.store.set_active(profile_id)
        self._active_id = profile_id
        return profile

    # --- the judging model (SPEC-18 section 8) ---------------------------------------

    @property
    def judge_profile_id(self) -> Optional[str]:
        """The chosen judging profile; None means the same as AXIS chat."""
        return self._judge_id

    def judge_profile(self) -> ProviderProfile:
        return self.profiles[self._judge_id] if self._judge_id else self.active_profile()

    def set_judge(self, profile_id: Optional[str], confirm_paid: bool) -> None:
        if profile_id is None:
            self.store.set_judge(None)
            self._judge_id = None
            return
        self._checked_profile(profile_id, confirm_paid)
        self.store.set_judge(profile_id)
        self._judge_id = profile_id

    def judge_explanation(self, unit_id: str, prompt: str, explanation: str, rubric: Rubric) -> AiJudgement:
        """Judge with the judging profile. Never raises and never falls back to keywords."""
        if self.mock:
            return judge_with(self._mock_companion, unit_id, prompt, explanation, rubric)
        profile = self.judge_profile()
        if not self.key_set(profile):
            return not_judged("ai_off")
        return judge_with(self._companion_for(profile), unit_id, prompt, explanation, rubric)

    def _companion_for(self, profile: ProviderProfile) -> Any:
        if profile.id not in self._companions:
            self._companions[profile.id] = self.factory(profile, profile.api_key(self.environ), self.meter)
        return self._companions[profile.id]

    def current(self) -> Any:
        """The companion that answers right now."""
        if self.mock:
            return self._mock_companion
        return self._companion_for(self.active_profile())

    # --- IAXISCompanion -----------------------------------------------------------

    def consult(self, query: AxisQuery) -> AxisResponse:
        try:
            return self.current().consult(query)
        except BudgetExceeded:
            return AxisResponse(reply=BUDGET_MESSAGE, suggested_action="Switch to the local model in Settings.")

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], List[str]]:
        try:
            return self.current().stream(query)
        except BudgetExceeded:
            return iter([BUDGET_MESSAGE]), []

    @property
    def last_backend_used(self) -> str:
        return getattr(self.current(), "last_backend_used", "Offline Mock (MOCK_AI=true)")

    # --- Settings page ------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        if self.mock:
            return {"ok": False, "reason": "Mock mode is on (MOCK_AI=true): no model is called."}
        started = time.perf_counter()
        try:
            model, input_tokens, output_tokens = self.current().ping()
        except BudgetExceeded:
            return {"ok": False, "reason": BUDGET_MESSAGE}
        except Exception as exc:
            from lms.adapters.ai.gemini_companion import GeminiError
            from lms.adapters.ai.local_llm_companion import LocalLLMError

            # Our adapter errors carry a safe message; anything else is named by class only,
            # since a provider's own text can echo a key.
            safe = isinstance(exc, (GeminiError, LocalLLMError))
            return {"ok": False, "reason": str(exc) if safe else type(exc).__name__}
        return {
            "ok": True,
            "model_answered": model,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    @property
    def cap_usd(self) -> float:
        return self.meter.cap_usd


def build_default_router(db_path: str, profiles_path: Optional[str] = None) -> ProviderRouter:
    """The router the app uses when nothing is injected."""
    from pathlib import Path

    from lms.adapters.ai.local_llm_companion import load_default_retriever, load_dotenv_if_present
    from lms.adapters.ai.providers.profiles import DEFAULT_PROFILES_PATH, load_profiles

    load_dotenv_if_present()
    mock = os.environ.get("MOCK_AI", "true").strip().lower() in ("1", "true", "yes")
    profiles = load_profiles(Path(profiles_path) if profiles_path else DEFAULT_PROFILES_PATH)
    store = UsageStore(db_path)
    store.initialize()
    retriever = None if mock else load_default_retriever()
    return ProviderRouter(
        profiles, store, environ=os.environ, mock=mock,
        factory=default_factory(retriever=retriever),
    )


__all__ = [
    "BUDGET_MESSAGE",
    "KeyMissing",
    "MONTHLY_CAP_USD",
    "PaidNotConfirmed",
    "ProviderRouter",
    "UnknownProfile",
    "build_default_router",
    "default_factory",
]
