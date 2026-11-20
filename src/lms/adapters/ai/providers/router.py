"""The provider switcher (SPEC-17 sections 2.2, 3 and 5).

The app holds one ProviderRouter as its AXIS companion. Each call goes to the
adapter of the active profile, so switching needs no restart and nothing else
in the app knows which provider answers.
"""

from __future__ import annotations

import logging
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
from lms.core.retrieval import IRetriever, RetrievalStatus
from lms.adapters.db.model_usage import UsageStore
from lms.core import tracing
from lms.core.ai_judgement import AiJudgement, Rubric, not_judged
from lms.core.interfaces import AxisQuery, AxisResponse

logger = logging.getLogger(__name__)

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


class DraftFailed(Exception):
    """A README draft could not be made. The message is plain and safe to show."""


def default_factory(
    concept_store: Optional[ConceptStore] = None,
    retriever: Optional[IRetriever] = None,
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


def course_reference_for(retriever: Optional[IRetriever], mock: bool = False) -> str:
    """ready, not_loaded, unavailable or mock: what the AXIS panel may show (SPEC-24 R10).

    Never carries a path, a version or an error text.
    """
    if mock:
        return "mock"
    if retriever is None:
        return "not_loaded"
    try:
        status = retriever.index_status()
    except Exception:
        return "unavailable"
    return {RetrievalStatus.OK: "ready", RetrievalStatus.NO_INDEX: "not_loaded"}.get(status, "unavailable")


def course_reference_of(axis: Any) -> str:
    """The status for whatever answers AXIS: a router, a companion that holds a retriever, or the mock."""
    if hasattr(axis, "course_reference"):
        return str(axis.course_reference)
    if isinstance(axis, MockAxisCompanion):
        return "mock"
    return course_reference_for(getattr(axis, "retriever", None))


class ProviderRouter:
    def __init__(
        self,
        profiles: Dict[str, ProviderProfile],
        store: UsageStore,
        environ: Optional[Mapping[str, str]] = None,
        mock: bool = False,
        factory: Optional[Factory] = None,
        meter: Optional[UsageMeter] = None,
        retriever: Optional[IRetriever] = None,
    ) -> None:
        self.retriever = retriever  # only to report its status to the panel (SPEC-24 R10)
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
            with tracing.span("model_call", call="concept_check", mock=True) as call:
                return self._noted(call, judge_with(self._mock_companion, unit_id, prompt, explanation, rubric))
        profile = self.judge_profile()
        if not self.key_set(profile):
            return not_judged("ai_off")  # no model is called, so there is no model_call span
        with tracing.span("model_call", call="concept_check", mock=False, profile_id=profile.id) as call:
            return self._noted(call, judge_with(self._companion_for(profile), unit_id, prompt, explanation, rubric))

    @staticmethod
    def _noted(call: tracing.ISpan, judgement: AiJudgement) -> AiJudgement:
        """Put a not-judged outcome on the span, with a reason from the fixed set (SPEC-28 R11)."""
        if judgement.status != "judged":
            call.set(not_judged_reason=judgement.reason)
            call.fail("budget" if judgement.reason == "cap_reached" else "provider_error")
        return judgement

    # --- document drafts (SPEC-15 section 9.4, ADR-0028) ------------------------------

    def summarise_feedback(self, points: list, readme: str, note: str, script: str = "", run_output: str = "") -> Tuple[str, str]:
        """A summary of the measured feedback points. Raises DraftFailed with a plain message; no fallback."""
        if self.mock:
            with tracing.span("model_call", call="build_feedback", mock=True):
                return self._mock_companion.summarise_feedback(points, readme, note, script, run_output)
        profile = self.active_profile()
        with tracing.span("model_call", call="build_feedback", mock=False, profile_id=profile.id) as call:
            if not self.key_set(profile):
                call.fail("not_set_up")
                raise DraftFailed("AXIS is not set up for summaries. Check the model settings.")
            try:
                text, model = self._companion_for(profile).summarise_feedback(points, readme, note, script, run_output)
            except BudgetExceeded:
                call.fail("budget")
                raise DraftFailed(BUDGET_MESSAGE) from None
            except Exception as exc:
                call.fail("provider_error")
                logger.warning("Feedback summary call failed: %s", type(exc).__name__)
                raise DraftFailed("AXIS could not write the summary right now. The points above still stand.") from None
            if not text.strip():
                call.fail("empty")
                raise DraftFailed("AXIS sent back an empty summary. The points above still stand.")
            return text, model or profile.model

    def draft_readme(self, entry: str, code: str, brief: str) -> Tuple[str, str]:
        """A README draft from the active profile. Raises DraftFailed with a plain message; no fallback."""
        if self.mock:
            with tracing.span("model_call", call="document_draft", mock=True):
                return self._mock_companion.draft_readme(entry, code, brief)
        profile = self.active_profile()
        with tracing.span("model_call", call="document_draft", mock=False, profile_id=profile.id) as call:
            if not self.key_set(profile):
                call.fail("not_set_up")
                raise DraftFailed("AXIS is not set up for drafting. Check the model settings.")
            try:
                text, model = self._companion_for(profile).draft_readme(entry, code, brief)
            except BudgetExceeded:
                call.fail("budget")
                raise DraftFailed(BUDGET_MESSAGE) from None
            except Exception as exc:
                call.fail("provider_error")
                logger.warning("README draft call failed: %s", type(exc).__name__)  # a provider's text can echo a key
                raise DraftFailed("AXIS could not draft the README right now. Try again, or write it yourself.") from None
            if not text.strip():
                call.fail("empty")
                raise DraftFailed("AXIS sent back an empty draft. Try again, or write it yourself.")
            return text, model or profile.model

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

    def _call_attributes(self, call: str) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {"call": call, "mock": self.mock}
        if not self.mock:
            attrs["profile_id"] = self.active_profile().id
        return attrs

    def consult(self, query: AxisQuery) -> AxisResponse:
        with tracing.span("model_call", **self._call_attributes("consult")) as call:
            try:
                return self.current().consult(query)
            except BudgetExceeded:
                call.fail("budget")
                return AxisResponse(reply=BUDGET_MESSAGE, suggested_action="Switch to the local model in Settings.")
            except Exception:
                call.fail("provider_error")
                raise

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], List[str]]:
        """One `model_call` span for the whole stream: opened at the first delta, closed when the reply ends."""
        attrs = self._call_attributes("stream")
        try:
            deltas, cited = self.current().stream(query)
        except BudgetExceeded:
            with tracing.span("model_call", **attrs) as call:
                call.fail("budget")
            return iter([BUDGET_MESSAGE]), []
        except Exception:
            with tracing.span("model_call", **attrs) as call:
                call.fail("provider_error")
            raise
        return self._traced_deltas(deltas, attrs), cited

    @staticmethod
    def _traced_deltas(deltas: Iterator[str], attrs: Dict[str, Any]) -> Iterator[str]:
        with tracing.span("model_call", **attrs) as call:
            try:
                yield from deltas
            except GeneratorExit:
                raise
            except Exception:
                call.fail("provider_error")
                raise

    @property
    def course_reference(self) -> str:
        return course_reference_for(self.retriever, self.mock)

    @property
    def last_retrieval(self) -> Any:
        """What the last answer's retrieval did (SPEC-21 R8); None for the mock."""
        return getattr(self.current(), "last_retrieval", None)

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

    from lms.adapters.ai.local_llm_companion import load_dotenv_if_present
    from lms.adapters.ai.rag.startup import build_retriever, configured_mode
    from lms.adapters.ai.providers.profiles import DEFAULT_PROFILES_PATH, load_profiles

    load_dotenv_if_present()
    mock = os.environ.get("MOCK_AI", "true").strip().lower() in ("1", "true", "yes")
    profiles = load_profiles(Path(profiles_path) if profiles_path else DEFAULT_PROFILES_PATH)
    store = UsageStore(db_path)
    store.initialize()
    configured_mode()  # a bad LMS_RETRIEVAL_MODE stops startup even with MOCK_AI=true (SPEC-21 R6)
    retriever = None if mock else build_retriever()
    return ProviderRouter(
        profiles, store, environ=os.environ, mock=mock,
        factory=default_factory(retriever=retriever), retriever=retriever,
    )


__all__ = [
    "BUDGET_MESSAGE",
    "DraftFailed",
    "KeyMissing",
    "MONTHLY_CAP_USD",
    "PaidNotConfirmed",
    "ProviderRouter",
    "UnknownProfile",
    "build_default_router",
    "course_reference_for",
    "course_reference_of",
    "default_factory",
]
