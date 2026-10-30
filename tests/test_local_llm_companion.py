"""Unit and chaos tests for the runtime-agnostic LocalLLMCompanion adapter.

Governed by:
- ADR-0010: Deterministic Telemetry, Andragogical Facilitation, and Local-First AI Stack
- SPEC-08: Runtime-Agnostic Local LLM Companion & Rubric Classifier
"""

import json
from pathlib import Path
import httpx
import pytest

from lms.adapters.ai.concept_store import ConceptStore
from lms.adapters.ai.local_llm_companion import (
    LocalLLMCompanion,
    LocalLLMError,
    get_axis_companion,
)
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.core.interfaces import AxisMode, AxisQuery, ExecutionResult
from lms.core.models import ActivityType, AssistanceLevel


def _make_mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_auto_discover_model_from_unsloth_server():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [
                        {"id": "Qwen3.6-35B-A3B-UD-Q4_K_XL", "object": "model"},
                        {"id": "gemma-4-12b-it-GGUF", "object": "model"},
                    ],
                },
            )
        return httpx.Response(404)

    companion = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="auto",
        http_client=_make_mock_client(handler),
    )
    assert companion.resolve_model() == "Qwen3.6-35B-A3B-UD-Q4_K_XL"


def test_socratic_mode_enforces_zero_code_even_when_local_llm_leaks():
    captured_payload = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chat/completions":
            nonlocal captured_payload
            captured_payload = json.loads(request.content.decode("utf-8"))
            # Simulate a small local model accidentally leaking Python code in Socratic mode
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "Here is the code you need:\n"
                                    "```python\n"
                                    "def run_intake(name, ward):\n"
                                    "    return name.strip()\n"
                                    "```\n"
                                ),
                            }
                        }
                    ]
                },
            )
        return httpx.Response(404)

    companion = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="gemma-4-12b-it-GGUF",
        http_client=_make_mock_client(handler),
    )

    query = AxisQuery(
        learner_id="learner_01",
        unit_id="PY-0.4",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.BUILD,
        user_prompt="Just give me the code for run_intake!",
        learner_code="def run_intake(name, ward): pass",
        execution_result=ExecutionResult(
            success=False,
            stdout="",
            stderr="AssertionError: expected REGISTRATION CONFIRMED",
            exit_code=1,
            duration_ms=12.5,
            assertion_errors=["AssertionError: expected REGISTRATION CONFIRMED"],
        ),
    )

    res = companion.consult(query)

    # 1. Verify SocraticGuardrail sanitized the leaked code block
    assert "```" not in res.reply
    assert "def run_intake" not in res.reply
    assert "?" in res.reply
    assert res.detected_assistance_level == AssistanceLevel.SMALL_HINT

    # 2. Verify untrusted inputs were properly delimited in the outgoing prompt
    user_msg = captured_payload["messages"][-1]["content"]
    assert "<learner_code>" in user_msg
    assert "<execution_stderr>" in user_msg
    assert "<learner_query>" in user_msg


def test_coach_mode_syntax_lookup_classification_and_concept_grounding():
    store = ConceptStore()
    store.ingest_directory(Path("tests/fixtures/concepts"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "You can use `.strip()` to remove leading and trailing spaces, "
                                "and `.upper()` to convert characters to uppercase."
                            ),
                        }
                    }
                ]
            },
        )

    companion = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3.5-9b",
        concept_store=store,
        http_client=_make_mock_client(handler),
    )

    query = AxisQuery(
        learner_id="learner_01",
        unit_id="PY-0.4",
        mode=AxisMode.COACH,
        current_activity=ActivityType.BUILD,
        user_prompt="What is the syntax to strip whitespace and uppercase a string?",
    )

    res = companion.consult(query)
    assert res.detected_assistance_level == AssistanceLevel.SYNTAX_LOOKUP
    assert len(res.cited_concepts) >= 1


def test_lightweight_classifier_evaluates_concept_check_json():
    def handler(request: httpx.Request) -> httpx.Response:
        # Simulate local LLM returning JSON wrapped in markdown fences
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "```json\n"
                                '{"status": "Solid", "feedback": "Clear grasp of input() returning str and requiring int() conversion."}\n'
                                "```"
                            ),
                        }
                    }
                ]
            },
        )

    companion = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="Qwopus3-5-9B-Coder-Flash-GGUF",
        http_client=_make_mock_client(handler),
    )

    result = companion.evaluate_concept_check(
        unit_id="PY-0.4",
        concept_line="A program takes input, transforms it, and produces output; input() always returns a string.",
        explanation="Because input() returns a string, we must convert it with int() before math to avoid TypeError.",
        solid_keywords=["string", "int", "typeerror", "convert"],
    )
    assert result["status"] == "Solid"
    assert "input()" in result["feedback"]


def test_offline_server_fallback_and_strict_mode():
    def failing_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused: Unsloth server not running")

    # 1. With fallback_to_mock=True (default), degrades smoothly
    resilient = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3.5-9b",
        fallback_to_mock=True,
        http_client=_make_mock_client(failing_handler),
    )
    query = AxisQuery(
        learner_id="learner_01",
        unit_id="PY-0.4",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.PREDICT,
        user_prompt="Why does this fail?",
    )
    res = resilient.consult(query)
    assert "?" in res.reply

    # 2. With fallback_to_mock=False, raises LocalLLMError
    strict = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3.5-9b",
        fallback_to_mock=False,
        http_client=_make_mock_client(failing_handler),
    )
    with pytest.raises(LocalLLMError):
        strict.consult(query)


def test_chaos_oversized_prompt_truncation():
    captured_user_content = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_user_content
        payload = json.loads(request.content.decode("utf-8"))
        captured_user_content = payload["messages"][-1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "What happens to the input variable before formatting?",
                        }
                    }
                ]
            },
        )

    companion = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3.5-9b",
        http_client=_make_mock_client(handler),
    )
    giant_prompt = "A" * 25000
    query = AxisQuery(
        learner_id="learner_01",
        unit_id="PY-0.4",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.BUILD,
        user_prompt=giant_prompt,
    )
    companion.consult(query)
    # Prompt should be bounded well below 25000 chars
    assert len(captured_user_content) < 10000


def test_get_axis_companion_factory_respects_mock_ai_env(monkeypatch):
    monkeypatch.setenv("MOCK_AI", "true")
    comp_mock = get_axis_companion()
    assert isinstance(comp_mock, MockAxisCompanion)

    monkeypatch.setenv("MOCK_AI", "false")
    monkeypatch.setenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8080/v1")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "Qwen3.6-35B-A3B-UD-Q4_K_XL")
    comp_local = get_axis_companion()
    assert isinstance(comp_local, LocalLLMCompanion)
    assert comp_local.base_url == "http://127.0.0.1:8080/v1"
    assert comp_local.model == "Qwen3.6-35B-A3B-UD-Q4_K_XL"


def test_hybrid_reranked_retriever_integration_in_companion():
    from lms.adapters.ai.rag.retriever import HybridRerankedRetriever
    from lms.core.rag_contracts import Source, content_sha256, normalize_text

    text = normalize_text("# Python Builtins\n\ninput() reads a line from stream and returns str.")
    source = Source(
        source_id="python/builtins",
        version="3.12",
        text=text,
        raw_sha256=content_sha256(text),
        loader_version="1.0",
        licence="PSF-2.0",
        licence_basis="declared",
    )
    retriever = HybridRerankedRetriever()
    retriever.index_source(source)

    captured_system_prompt = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_system_prompt
        payload = json.loads(request.content.decode("utf-8"))
        captured_system_prompt = payload["messages"][0]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "What type does input() return by default?",
                        }
                    }
                ]
            },
        )

    companion = LocalLLMCompanion(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3.5-9b",
        retriever=retriever,
        http_client=_make_mock_client(handler),
    )

    query = AxisQuery(
        learner_id="learner_01",
        unit_id="PY-0.4",
        mode=AxisMode.SOCRATIC,
        current_activity=ActivityType.BUILD,
        user_prompt="Why does input() fail?",
    )
    resp = companion.consult(query)

    assert "python/builtins" in captured_system_prompt
    assert len(resp.cited_concepts) > 0
    assert any("python/builtins" in cid for cid in resp.cited_concepts)

