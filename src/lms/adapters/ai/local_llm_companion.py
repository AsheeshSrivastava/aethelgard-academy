"""OpenAI-compatible companion adapter implementing IAXISCompanion.

Governed by:
- ADR-0001: Hexagonal Architecture and Pluggable Boundary Ports
- ADR-0009: Socratic Boundary Guardrails and Assistance Accounting
- ADR-0010: Deterministic Telemetry, Andragogical Facilitation, and Local-First AI Stack
- ADR-0025 / SPEC-17: one OpenAI-SDK adapter for local servers and OpenAI itself
- SPEC-08: Runtime-Agnostic Local LLM Companion & Rubric Classifier

Uses the official `openai` SDK with a configurable address, so it serves any
OpenAI-compatible local server (Unsloth Desktop, llama.cpp, LM Studio, vLLM,
Ollama) and OpenAI. AXIS rules come from `providers.axis_rules`, shared with
every other adapter.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import httpx
from openai import OpenAI

from lms.adapters.ai.concept_store import ConceptStore
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.axis_rules import (  # noqa: F401 (re-exports)
    MAX_CODE_CHARS,
    MAX_PROMPT_CHARS,
    ThinkFilter,
)
from lms.adapters.ai.providers.metering import UsageMeter
from lms.adapters.ai.providers.profiles import ProviderProfile
from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.core.interfaces import AxisQuery, AxisResponse, IAXISCompanion

FALLBACK_MODEL = "qwen3.5-9b"


def load_dotenv_if_present() -> None:
    """Read a local .env file into os.environ if not already set."""
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v


class LocalLLMError(Exception):
    """Raised when the model server fails and fallback_to_mock is disabled.

    The message names the failure class only: a provider's own message can echo a key.
    """


def _reasoning_text(obj: Any) -> str:
    """Deep-thinking models (e.g. Qwen3.6) may answer in `reasoning_content`, an extra field."""
    value = getattr(obj, "reasoning_content", None)
    if value is None and getattr(obj, "model_extra", None):
        value = obj.model_extra.get("reasoning_content")
    return value or ""


class OpenAICompatibleCompanion:
    """AXIS over any OpenAI-compatible server, through the OpenAI SDK."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 30.0,
        concept_store: Optional[ConceptStore] = None,
        retriever: Optional[HybridRerankedRetriever] = None,
        guardrail: Optional[SocraticGuardrail] = None,
        classifier: Optional[AssistanceClassifier] = None,
        fallback_to_mock: bool = True,
        http_client: Optional[httpx.Client] = None,
        profile: Optional[ProviderProfile] = None,
        meter: Optional[UsageMeter] = None,
        token_limit_field: str = "max_tokens",
        send_temperature: bool = True,
        disable_thinking: bool = False,
    ) -> None:
        raw_url = base_url or os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8888/v1")
        self.base_url = raw_url.rstrip("/")
        self.model = model or os.environ.get("LOCAL_LLM_MODEL", "auto")
        api_key = (
            api_key
            or os.environ.get("LOCAL_LLM_API_KEY")
            or os.environ.get("UNSLOTH_STUDIO_AUTH_TOKEN", "local-no-key")
        )
        self.timeout_seconds = timeout_seconds
        self.concept_store = concept_store
        self.retriever = retriever
        self.guardrail = guardrail or SocraticGuardrail()
        self.classifier = classifier or AssistanceClassifier()
        self.fallback_to_mock = fallback_to_mock
        self.profile = profile
        self.meter = meter
        self.token_limit_field = token_limit_field
        self.send_temperature = send_temperature
        self.disable_thinking = disable_thinking
        # The key lives only inside the SDK client; it is never kept on this object.
        self._client = OpenAI(
            base_url=self.base_url,
            api_key=api_key,
            http_client=http_client or httpx.Client(timeout=self.timeout_seconds),
            max_retries=0,
            timeout=self.timeout_seconds,
        )
        self._resolved_model: Optional[str] = None
        self._mock_fallback = MockAxisCompanion(guardrail=self.guardrail, classifier=self.classifier)
        self.last_backend_used: str = "LocalLLM (pending)"
        self.last_model_answered: Optional[str] = None

    # --- model and request shape -----------------------------------------------

    def resolve_model(self) -> str:
        """Target model id; asks GET /models when model == 'auto'."""
        if self._resolved_model:
            return self._resolved_model
        if self.model != "auto":
            self._resolved_model = self.model
            return self._resolved_model
        try:
            models = list(self._client.models.list())
            if models and getattr(models[0], "id", None):
                self._resolved_model = str(models[0].id)
                return self._resolved_model
        except Exception:
            if not self.fallback_to_mock:
                raise LocalLLMError("Failed to auto-discover model from local server /v1/models.")
        self._resolved_model = FALLBACK_MODEL
        return self._resolved_model

    def _params(self, model: str, system: str, user: str, temperature: float, limit: int) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            self.token_limit_field: limit,
        }
        if self.send_temperature:
            params["temperature"] = temperature
        if self.disable_thinking:
            # Read by llama.cpp (Unsloth Studio), vLLM and SGLang chat templates such as
            # Qwen3's; servers that do not know it ignore it. Any <think> block that still
            # arrives is removed by ThinkFilter / finish_reply.
            params["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        return params

    # --- metering ----------------------------------------------------------------

    def _check_budget(self, *texts: str) -> None:
        if self.meter is not None and self.profile is not None:
            self.meter.check(self.profile, input_chars=sum(len(t) for t in texts))

    def _record(self, call: str, model: str, usage: Any, input_chars: int) -> None:
        if self.meter is None or self.profile is None:
            return
        input_tokens = getattr(usage, "prompt_tokens", None) if usage is not None else None
        output_tokens = getattr(usage, "completion_tokens", None) if usage is not None else None
        self.meter.record(self.profile, model, call, input_tokens, output_tokens, input_chars=input_chars)

    # --- IAXISCompanion -------------------------------------------------------------

    def _grounding(self, query: AxisQuery) -> Tuple[str, List[str]]:
        return axis_rules.retrieve_grounded_passages(
            self.retriever, self.concept_store, query.unit_id, query.user_prompt
        )

    def consult(self, query: AxisQuery) -> AxisResponse:
        grounded_text, cited_concepts = self._grounding(query)
        sys_prompt = axis_rules.build_system_prompt(query.mode, grounded_text)
        user_msg = axis_rules.build_user_message(query)
        self._check_budget(sys_prompt, user_msg)  # BudgetExceeded is never swallowed

        try:
            target_model = self.resolve_model()
            resp = self._client.chat.completions.create(
                **self._params(target_model, sys_prompt, user_msg, 0.2, axis_rules.REPLY_MAX_TOKENS)
            )
            message = resp.choices[0].message
            raw_content = message.content or ""
            if not raw_content.strip():
                raw_content = _reasoning_text(message)
            answered = resp.model or target_model
            self.last_model_answered = answered
            self.last_backend_used = f"LocalLLM ({answered} @ {self.base_url})"
            self._record("consult", answered, resp.usage, len(sys_prompt) + len(user_msg))
        except LocalLLMError:
            raise
        except Exception as exc:
            if self.fallback_to_mock:
                self.last_backend_used = f"Offline Mock (Fallback reason: {type(exc).__name__})"
                return self._mock_fallback.consult(query)
            raise LocalLLMError(f"Model consultation failed: {type(exc).__name__}") from None

        return axis_rules.finish_reply(raw_content, query, cited_concepts, self.guardrail, self.classifier)

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], List[str]]:
        """Stream the model's reply. Returns (deltas, cited concepts)."""
        grounded_text, cited_concepts = self._grounding(query)
        sys_prompt = axis_rules.build_system_prompt(query.mode, grounded_text)
        user_msg = axis_rules.build_user_message(query)
        self._check_budget(sys_prompt, user_msg)
        return self._stream_deltas(query, sys_prompt, user_msg), cited_concepts

    def _stream_deltas(self, query: AxisQuery, sys_prompt: str, user_msg: str) -> Iterator[str]:
        sent_any = False
        reasoning: List[str] = []
        usage: Any = None
        answered: Optional[str] = None
        think = ThinkFilter()
        input_chars = len(sys_prompt) + len(user_msg)
        target_model: Optional[str] = None
        requested = recorded = False
        try:
            target_model = self.resolve_model()
            params = self._params(target_model, sys_prompt, user_msg, 0.2, axis_rules.REPLY_MAX_TOKENS)
            chunks = self._client.chat.completions.create(
                **params, stream=True, stream_options={"include_usage": True}
            )
            requested = True
            for chunk in chunks:
                answered = getattr(chunk, "model", None) or answered
                if getattr(chunk, "usage", None) is not None:
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                if delta.content:
                    visible = think.feed(delta.content)
                    if visible:
                        sent_any = True
                        yield visible
                else:
                    extra = _reasoning_text(delta)
                    if extra:
                        reasoning.append(extra)
            tail = think.flush()
            if tail:
                sent_any = True
                yield tail
            answered = answered or target_model
            self.last_model_answered = answered
            self.last_backend_used = f"LocalLLM ({answered} @ {self.base_url})"
            recorded = True
            self._record("stream", answered, usage, input_chars)
            if not sent_any and reasoning:
                yield "".join(reasoning)
        except LocalLLMError:
            raise
        except Exception as exc:
            if sent_any or not self.fallback_to_mock:
                raise LocalLLMError(f"Model stream failed: {type(exc).__name__}") from None
            self.last_backend_used = f"Offline Mock (Fallback reason: {type(exc).__name__})"
            yield from self._mock_fallback.stream(query)[0]
        finally:
            # A reply cut short (the learner left, or an error) still counts. Without
            # counts a paid call is costed at its limit, so the cap is never undercounted.
            paid = self.profile is not None and self.profile.paid
            if requested and not recorded and (paid or sent_any):
                self._record("stream", answered or target_model or self.model, usage, input_chars)

    def ping(self) -> Tuple[str, Optional[int], Optional[int]]:
        """One short call for the Settings page: (model that answered, input tokens, output tokens).

        Never falls back to the mock: a connection test must report the real result."""
        sys_prompt, user_msg = axis_rules.PING_SYSTEM_PROMPT, axis_rules.PING_USER_MESSAGE
        self._check_budget(sys_prompt, user_msg)
        try:
            target_model = self.resolve_model()
            resp = self._client.chat.completions.create(
                **self._params(target_model, sys_prompt, user_msg, 0.0, axis_rules.PING_MAX_TOKENS)
            )
        except Exception as exc:
            raise LocalLLMError(f"Connection test failed: {type(exc).__name__}") from None
        answered = resp.model or target_model
        self.last_model_answered = answered
        self._record("connection_test", answered, resp.usage, len(sys_prompt) + len(user_msg))
        usage = resp.usage
        return (
            answered,
            getattr(usage, "prompt_tokens", None) if usage else None,
            getattr(usage, "completion_tokens", None) if usage else None,
        )

    def judge(self, unit_id: str, prompt: str, explanation: str, ideas: List[Any]) -> Tuple[str, Optional[str]]:
        """One judging call (SPEC-18 section 3). Returns the raw reply and the model that answered.

        Never falls back to anything: a failure is raised for the router to name.
        """
        user_msg = axis_rules.build_judging_message(unit_id, prompt, explanation, ideas)
        sys_prompt = axis_rules.JUDGE_SYSTEM_PROMPT
        self._check_budget(sys_prompt, user_msg)
        target_model = self.resolve_model()
        resp = self._client.chat.completions.create(
            **self._params(target_model, sys_prompt, user_msg, 0.0, axis_rules.JUDGE_MAX_TOKENS)
        )
        answered = resp.model or target_model
        self.last_model_answered = answered
        self._record("concept_check", answered, resp.usage, len(sys_prompt) + len(user_msg))
        return axis_rules.strip_think(str(resp.choices[0].message.content)), answered


# Older name, kept for the CLI and SPEC-08 tests.
LocalLLMCompanion = OpenAICompatibleCompanion


def get_axis_companion(
    concept_store: Optional[ConceptStore] = None,
    retriever: Optional[HybridRerankedRetriever] = None,
) -> IAXISCompanion:
    """Factory returning MockAxisCompanion when MOCK_AI=true, else the local companion."""
    load_dotenv_if_present()
    mock_flag = os.environ.get("MOCK_AI", "true").strip().lower()
    if mock_flag in ("1", "true", "yes"):
        return MockAxisCompanion()

    if retriever is None:
        retriever = load_default_retriever()

    # The CLI talks to the local model directly; thinking stays off there too.
    return OpenAICompatibleCompanion(concept_store=concept_store, retriever=retriever, disable_thinking=True)


def load_default_retriever() -> Optional[HybridRerankedRetriever]:
    default_index = Path("data/index")
    if (default_index / "passages.jsonl").exists():
        try:
            return HybridRerankedRetriever.load(default_index)
        except Exception:
            return None
    return None
