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
from lms.core import tracing
from lms.core.retrieval import IRetriever, RetrievalTrace
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
        retriever: Optional[IRetriever] = None,
        guardrail: Optional[SocraticGuardrail] = None,
        classifier: Optional[AssistanceClassifier] = None,
        profile: Optional[ProviderProfile] = None,
        meter: Optional[UsageMeter] = None,
        chat_temperature: float = 0.2,
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
        self.last_retrieval: Optional[RetrievalTrace] = None
        self.chat_temperature = chat_temperature  # AXIS chat only (consult, stream); other calls keep their own (SPEC-30 R20)
        # The model's reply before the guardrail, label stripping and tag removal (SPEC-30 R16). Only the eval harness
        # reads it: no route, log or trace carries it.
        self.last_raw_reply: Optional[str] = None

    # --- helpers -------------------------------------------------------------

    def _config(self, system: str, temperature: float, limit: int) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system, temperature=temperature, max_output_tokens=limit
        )

    def _check_budget(self, *texts: str) -> None:
        if self.meter is not None and self.profile is not None:
            self.meter.check(self.profile, input_chars=sum(len(t) for t in texts))

    def _record(self, call: str, answered: str, response: Any, input_chars: int) -> None:
        input_tokens, output_tokens = _counts(response)
        tracing.annotate(model_answered=answered, **tracing.token_attributes(input_tokens, output_tokens))
        if self.meter is None or self.profile is None:
            return
        self.meter.record(self.profile, answered, call, input_tokens, output_tokens, input_chars=input_chars)

    def _answered(self, response: Any) -> str:
        answered = getattr(response, "model_version", None) or self.model
        self.last_model_answered = answered
        self.last_backend_used = f"Gemini ({answered})"
        return answered

    def _grounding(self, query: AxisQuery) -> Any:
        grounding, self.last_retrieval = axis_rules.ground_with_trace(
            self.retriever, self.concept_store, query.unit_id, query.user_prompt
        )
        return grounding

    # --- IAXISCompanion ----------------------------------------------------------

    def consult(self, query: AxisQuery) -> AxisResponse:
        self.last_raw_reply = None  # a failed call must not leave the previous reply behind
        grounding = self._grounding(query)
        sys_prompt, user_msg = axis_rules.build_prompts(query, grounding)
        self._check_budget(sys_prompt, user_msg)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_msg,
                config=self._config(sys_prompt, self.chat_temperature, axis_rules.REPLY_MAX_TOKENS),
            )
            raw = response.text or ""
        except BudgetExceeded:
            raise
        except Exception as exc:
            raise GeminiError(f"Gemini consultation failed: {type(exc).__name__}") from None
        self._record("consult", self._answered(response), response, len(sys_prompt) + len(user_msg))
        axis_rules.note_sent(axis_rules.chat_prompt_version(query.mode, grounding.source_state))
        self.last_raw_reply = axis_rules.strip_think(raw)
        return axis_rules.finish_reply(raw, query, grounding, self.guardrail, self.classifier)

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], Any]:
        self.last_raw_reply = None
        grounding = self._grounding(query)
        sys_prompt, user_msg = axis_rules.build_prompts(query, grounding)
        self._check_budget(sys_prompt, user_msg)
        version = axis_rules.chat_prompt_version(query.mode, grounding.source_state)
        return self._stream_deltas(sys_prompt, user_msg, version), grounding

    def _stream_deltas(self, sys_prompt: str, user_msg: str, version: str) -> Iterator[str]:
        last: Any = None
        usage_chunk: Any = None
        input_chars = len(sys_prompt) + len(user_msg)
        requested = False
        said: List[str] = []  # everything yielded, kept as last_raw_reply when the stream ends
        try:
            stream = self._client.models.generate_content_stream(
                model=self.model,
                contents=user_msg,
                config=self._config(sys_prompt, self.chat_temperature, axis_rules.REPLY_MAX_TOKENS),
            )
            requested = True
            for chunk in stream:
                last = chunk
                if getattr(chunk, "usage_metadata", None) is not None:
                    usage_chunk = chunk
                if chunk.text:
                    said.append(chunk.text)
                    yield chunk.text
        except GeneratorExit:
            raise
        except Exception as exc:
            raise GeminiError(f"Gemini stream failed: {type(exc).__name__}") from None
        finally:
            if said:
                self.last_raw_reply = axis_rules.strip_think("".join(said))
            # Always counted, even when the learner leaves mid-reply: without counts
            # the call is costed at its limit, so the cap is never undercounted.
            if requested:
                answered = self._answered(last) if last is not None else self.model
                self._record("stream", answered, usage_chunk, input_chars)
                axis_rules.note_sent(version)

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
        axis_rules.note_sent(axis_rules.prompt_version(*axis_rules.readme_draft_templates()))
        return response.text or "", answered

    def summarise_feedback(self, points: List[Any], readme: str, note: str, script: str = "", run_output: str = "") -> Tuple[str, Optional[str]]:
        """One summary call over the measured feedback points (SPEC-15 section 10.2). Never falls back."""
        sys_prompt, user_msg = axis_rules.feedback_summary_prompts(points, readme, note, script, run_output)
        self._check_budget(sys_prompt, user_msg)
        response = self._client.models.generate_content(
            model=self.model,
            contents=user_msg,
            config=self._config(sys_prompt, 0.2, axis_rules.DRAFT_MAX_TOKENS),
        )
        answered = self._answered(response)
        self._record("build_feedback", answered, response, len(sys_prompt) + len(user_msg))
        axis_rules.note_sent(axis_rules.prompt_version(*axis_rules.feedback_summary_templates()))
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
        axis_rules.note_sent(axis_rules.prompt_version(*axis_rules.judge_templates()))
        return response.text or "", answered
