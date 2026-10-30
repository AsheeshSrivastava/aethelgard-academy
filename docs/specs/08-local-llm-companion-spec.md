# Specification 08: Runtime-Agnostic Local LLM Companion & Rubric Classifier

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed By:**
  - `ADR-0001: Hexagonal Architecture and Pluggable Boundary Ports`
  - `ADR-0003: Two-Stage RAG: Upstream Research vs. Downstream AXIS AI Grounding`
  - `ADR-0009: Socratic Boundary Guardrails and Assistance Accounting`
  - `ADR-0010: Deterministic Telemetry, Andragogical Facilitation, and Local-First AI Stack`
- **Domain:** Local LLM Facilitation Adapter, Andragogical Prompt Assembly, 10% Lightweight Rubric Classifier
- **Date:** 2026-10-30

---

## 1. Purpose & Architectural Scope

To operate at **\$0.00 marginal token cost** without vendor or runner lock-in, the LMS platform implements `LocalLLMCompanion` behind the `IAXISCompanion` port.

It communicates over the standard **OpenAI-compatible local HTTP API** (`/v1/chat/completions` and `/v1/models`), supporting **Unsloth Desktop** (preferred), `llama.cpp`, `LM Studio`, `vLLM`, and `Ollama` interchangeably via configuration.

---

## 2. Interface & Configuration Contract

### 2.1 Environment Configuration
- `MOCK_AI`: `"true"` (default for offline CI/pytest) or `"false"` (enables live `LocalLLMCompanion`).
- `LOCAL_LLM_BASE_URL`: Base URL of the local inference server (default: `"http://127.0.0.1:8888/v1"`, Unsloth Studio's default port).
- `LOCAL_LLM_MODEL`: Target model identifier (default: `"auto"`, which auto-discovers the active model from `GET /v1/models`, falling back to `"qwen3.5-9b"`).
- `LOCAL_LLM_API_KEY` / `UNSLOTH_STUDIO_AUTH_TOKEN`: Optional bearer token for local servers (`sk-unsloth-...`, default: `"local-no-key"`).
- `LOCAL_LLM_TIMEOUT`: Request timeout in seconds (default: `30.0`).

### 2.2 Class Signature (`src/lms/adapters/ai/local_llm_companion.py`)

```python
class LocalLLMError(Exception):
    """Raised when the local LLM server returns an unrecoverable error in strict mode."""
    pass


class LocalLLMCompanion:
    """Runtime-agnostic local LLM adapter implementing IAXISCompanion."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 30.0,
        concept_store: Optional[ConceptStore] = None,
        guardrail: Optional[SocraticGuardrail] = None,
        classifier: Optional[AssistanceClassifier] = None,
        fallback_to_mock: bool = True,
        http_client: Optional[httpx.Client] = None,
    ) -> None: ...

    def resolve_model(self) -> str:
        """Resolves model name, querying GET /v1/models if model == 'auto'."""

    def consult(self, query: AxisQuery) -> AxisResponse:
        """Assembles grounded facilitator prompt, calls /v1/chat/completions,
        enforces SocraticGuardrail, and classifies AssistanceLevel."""

    def evaluate_concept_check(
        self,
        unit_id: str,
        concept_line: str,
        explanation: str,
        solid_keywords: List[str],
    ) -> Dict[str, str]:
        """The 10% lightweight classifier: grades a CO-6 free-text mental model
        as 'Solid' or 'Shaky' with brief facilitator feedback."""
```

---

## 3. Andragogical Prompt Engineering & Security Boundaries

1. **Three Facilitator Stances:**
   - **Socratic (`AxisMode.SOCRATIC`):** Prohibits code blocks or direct fixes; asks 1–2 diagnostic questions pointing the adult learner to inspect their ingress, transformation, or egress state.
   - **Coach (`AxisMode.COACH`):** Explains standard library syntax, signatures, and compiler errors clearly without writing the full exercise solution.
   - **Hybrid (`AxisMode.HYBRID`):** Guides structural decomposition and input/output contracts.
2. **Untrusted Input Delimiters:**
   - Learner prompts and code are isolated inside `<learner_code>` and `<learner_query>` tags with an explicit system instruction to ignore any prompt-injection attempts inside those tags.
3. **Post-Generation Mechanical Guardrail:**
   - Every response in `AxisMode.SOCRATIC` is passed through `SocraticGuardrail.enforce()` before returning.

---

## 4. Acceptance Criteria

1. **Auto-Discovery:** When `model="auto"`, `LocalLLMCompanion` queries `/v1/models` and selects the first active model loaded in Unsloth Desktop.
2. **Mode Fidelity & Socratic Enforcement:** Even if the local LLM attempts to output a ` ```python ` block in `SOCRATIC` mode, `LocalLLMCompanion.consult()` strips the code and returns a guiding inquiry.
3. **10% Classifier (`evaluate_concept_check`):** Parses JSON `{ "status": "Solid" | "Shaky", "feedback": "..." }` from the local LLM, and falls back deterministically if the response is malformed or offline.
4. **Resilient Fallback:** When `fallback_to_mock=True` and the local server is offline, `consult()` degrades gracefully to `MockAxisCompanion` without crashing the learner's CLI or API session; when `fallback_to_mock=False`, it raises `LocalLLMError`.
