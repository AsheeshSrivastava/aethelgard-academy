"""Gemini companion adapter implementing IAXISCompanion (ADR-0025, SPEC-17 section 3).

Uses Google's own `google-genai` SDK. AXIS rules come from `providers.axis_rules`,
the same module every adapter uses. Gemini is a paid profile, so a failure is
reported and never falls back to another provider.
"""

from __future__ import annotations

from typing import Any, Iterator, List, Optional, Tuple

from google.genai import types

from lms.adapters.ai.concept_store import ConceptStore
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.metering import BudgetExceeded, UsageMeter
from lms.adapters.ai.providers.profiles import ProviderProfile
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.core.interfaces import AxisQuery, AxisResponse


class GeminiError(Exception):
    """A Gemini call failed. The message names the failure class only, never the key."""


def _counts(response: Any) -> Tuple[Optional[int], Optional[int]]:
    """(input, output). Gemini bills thinking tokens as output, so they are added in;
    a reply that was all thinking reports no candidates but still costs its thoughts."""
    meta = getattr(response, "usage_metadata", None)
    if meta is None:
        return None, None
    candidates = getattr(meta, "candidates_token_count", None)
    thoughts = getattr(meta, "thoughts_token_count", None)
    output = None if candidates is None and thoughts is None else (candidates or 0) + (thoughts or 0)
    return getattr(meta, "prompt_token_count", None), output


class GeminiCompanion:
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        client: Any = None,
        concept_store: Optional[ConceptStore] = None,
        retriever: Optional[HybridRerankedRetriever] = None,
        guardrail: Optional[SocraticGuardrail] = None,
        classifier: Optional[AssistanceClassifier] = None,
        profile: Optional[ProviderProfile] = None,
        meter: Optional[UsageMeter] = None,
    ) -> None:
        if client is None:
            from google import genai  # imported here so tests never build a real client

            client = genai.Client(api_key=api_key)
        self._client = client  # the key lives only inside the SDK client
        self.model = model
        self.concept_store = concept_store
        self.retriever = retriever
        self.guardrail = guardrail or SocraticGuardrail()
        self.classifier = classifier or AssistanceClassifier()
        self.profile = profile
        self.meter = meter
        self.last_model_answered: Optional[str] = None
        self.last_backend_used: str = "Gemini (pending)"

    # --- helpers -------------------------------------------------------------

    def _config(self, system: str, temperature: float, limit: int) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system, temperature=temperature, max_output_tokens=limit
        )

    def _check_budget(self, *texts: str) -> None:
        if self.meter is not None and self.profile is not None:
            self.meter.check(self.profile, input_chars=sum(len(t) for t in texts))

    def _record(self, call: str, answered: str, response: Any, input_chars: int) -> None:
        if self.meter is None or self.profile is None:
            return
        input_tokens, output_tokens = _counts(response)
        self.meter.record(self.profile, answered, call, input_tokens, output_tokens, input_chars=input_chars)

    def _answered(self, response: Any) -> str:
        answered = getattr(response, "model_version", None) or self.model
        self.last_model_answered = answered
        self.last_backend_used = f"Gemini ({answered})"
        return answered

    def _grounding(self, query: AxisQuery) -> Tuple[str, List[str]]:
        return axis_rules.retrieve_grounded_passages(
            self.retriever, self.concept_store, query.unit_id, query.user_prompt
        )

    # --- IAXISCompanion ----------------------------------------------------------

    def consult(self, query: AxisQuery) -> AxisResponse:
        grounded_text, cited = self._grounding(query)
        sys_prompt = axis_rules.build_system_prompt(query.mode, grounded_text)
        user_msg = axis_rules.build_user_message(query)
        self._check_budget(sys_prompt, user_msg)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_msg,
                config=self._config(sys_prompt, 0.2, axis_rules.REPLY_MAX_TOKENS),
            )
            raw = response.text or ""
        except BudgetExceeded:
            raise
        except Exception as exc:
            raise GeminiError(f"Gemini consultation failed: {type(exc).__name__}") from None
        self._record("consult", self._answered(response), response, len(sys_prompt) + len(user_msg))
        return axis_rules.finish_reply(raw, query, cited, self.guardrail, self.classifier)

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], List[str]]:
        grounded_text, cited = self._grounding(query)
        sys_prompt = axis_rules.build_system_prompt(query.mode, grounded_text)
        user_msg = axis_rules.build_user_message(query)
        self._check_budget(sys_prompt, user_msg)
        return self._stream_deltas(sys_prompt, user_msg), cited

    def _stream_deltas(self, sys_prompt: str, user_msg: str) -> Iterator[str]:
        last: Any = None
        usage_chunk: Any = None
        input_chars = len(sys_prompt) + len(user_msg)
        requested = False
        try:
            stream = self._client.models.generate_content_stream(
                model=self.model,
                contents=user_msg,
                config=self._config(sys_prompt, 0.2, axis_rules.REPLY_MAX_TOKENS),
            )
            requested = True
            for chunk in stream:
                last = chunk
                if getattr(chunk, "usage_metadata", None) is not None:
                    usage_chunk = chunk
                if chunk.text:
                    yield chunk.text
        except GeneratorExit:
            raise
        except Exception as exc:
            raise GeminiError(f"Gemini stream failed: {type(exc).__name__}") from None
        finally:
            # Always counted, even when the learner leaves mid-reply: without counts
            # the call is costed at its limit, so the cap is never undercounted.
            if requested:
                answered = self._answered(last) if last is not None else self.model
                self._record("stream", answered, usage_chunk, input_chars)

    def ping(self) -> Tuple[str, Optional[int], Optional[int]]:
        """One short call for the Settings page: (model that answered, input tokens, output tokens)."""
        sys_prompt, user_msg = axis_rules.PING_SYSTEM_PROMPT, axis_rules.PING_USER_MESSAGE
        self._check_budget(sys_prompt, user_msg)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_msg,
                config=self._config(sys_prompt, 0.0, axis_rules.PING_MAX_TOKENS),
            )
        except Exception as exc:
            raise GeminiError(f"Connection test failed: {type(exc).__name__}") from None
        answered = self._answered(response)
        self._record("connection_test", answered, response, len(sys_prompt) + len(user_msg))
        return (answered, *_counts(response))

    def draft_readme(self, entry: str, code: str, brief: str) -> Tuple[str, Optional[str]]:
        """One README drafting call (SPEC-15 section 9.4). Returns the Markdown and the model that answered.

        Never falls back to anything: a failure is raised for the caller to name.
        """
        sys_prompt, user_msg = axis_rules.readme_draft_prompts(entry, code, brief)
        self._check_budget(sys_prompt, user_msg)
        response = self._client.models.generate_content(
            model=self.model,
            contents=user_msg,
            config=self._config(sys_prompt, 0.3, axis_rules.DRAFT_MAX_TOKENS),
        )
        answered = self._answered(response)
        self._record("document_draft", answered, response, len(sys_prompt) + len(user_msg))
        return response.text or "", answered

    def judge(self, unit_id: str, prompt: str, explanation: str, ideas: List[Any]) -> Tuple[str, Optional[str]]:
        """One judging call (SPEC-18 section 3). Returns the raw reply and the model that answered.

        Never falls back to anything: a failure is raised for the router to name.
        """
        user_msg = axis_rules.build_judging_message(unit_id, prompt, explanation, ideas)
        sys_prompt = axis_rules.JUDGE_SYSTEM_PROMPT
        self._check_budget(sys_prompt, user_msg)
        response = self._client.models.generate_content(
            model=self.model,
            contents=user_msg,
            config=self._config(sys_prompt, 0.0, axis_rules.JUDGE_MAX_TOKENS),
        )
        answered = self._answered(response)
        self._record("concept_check", answered, response, len(sys_prompt) + len(user_msg))
        return response.text or "", answered
