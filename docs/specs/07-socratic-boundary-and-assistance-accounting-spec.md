# Specification 07: Socratic Boundary Guardrail and Assistance Accounting

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed By:** 
  - `ADR-0009: Socratic Boundary Guardrails and Assistance Accounting`
  - `AGENTS.md` (Sections 5 & 6)
- **Domain:** AI Companion Governance, Socratic Invariant Enforcement, Progression Ledger Accounting
- **Date:** 2026-10-30

---

## 1. Scope & Objective

To prevent generative AI hallucinations and unearned capability inflation, AXIS AI interactions must enforce strict architectural boundaries:
1. When operating in `AxisMode.SOCRATIC`, the system must never transmit code blocks, function implementations, or direct algorithmic answers to the learner.
2. The system must classify each interaction's assistance tier (`AssistanceLevel`).
3. If an interaction supplies reasoning (`SUPPLIED_REASONING`), the Evidence Ledger must record a `WEAK` evidence strength entry, routing `evaluate_progression()` to `STRENGTHEN`.

---

## 2. Component Specifications

### 2.1 Socratic Guardrail (`SocraticGuardrail`)

```python
class SocraticViolationError(Exception):
    """Raised when an AI response violates the Socratic zero-code boundary."""
    pass

class SocraticGuardrail:
    """Inspects and enforces boundaries on companion responses."""

    def validate_or_sanitize(
        self,
        mode: AxisMode,
        reply: str,
        strict: bool = False,
    ) -> str:
        """Inspects reply. If mode is SOCRATIC:
        - Detects markdown code blocks (` ```...``` `)
        - Detects statement definitions (def, class, import, return)
        - If strict=True: raises SocraticViolationError
        - If strict=False: strips code and replaces with an inquiry prompt.
        """
```

### 2.2 Assistance Classifier (`AssistanceClassifier`)

```python
class AssistanceClassifier:
    """Classifies learner queries and assistant replies into AssistanceLevel."""

    @staticmethod
    def classify(query_text: str, reply_text: str, mode: AxisMode) -> AssistanceLevel:
        """Determines assistance level:
        - SYNTAX_LOOKUP: Query asks how to format, import, or call standard library/syntax.
        - SMALL_HINT: Socratic inquiry or high-level conceptual nudge.
        - STRUCTURAL_DIRECTION: Architecture/schema layout without code.
        - SUPPLIED_REASONING: Direct solution, code block, or full algorithm provided.
        - NONE: Unassisted / standalone query.
        """
```

### 2.3 Companion Wrapper Integration

The companion interface `IAXISCompanion.consult(query: AxisQuery) -> AxisResponse` routes output through the guardrail before returning to the caller.

---

## 3. Test & Verification Acceptance Criteria

1. **Code Rejection in Socratic Mode:** Calling `consult()` in `AxisMode.SOCRATIC` with a prompt asking for code never returns executable code blocks or `def `.
2. **Sanitization Fallback:** When a model accidentally yields code in Socratic mode, the guardrail neutralizes the code and outputs an inquiry question.
3. **Syntax Lookup Protection:** Asking "How do I use str.strip()?" is tagged as `SYNTAX_LOOKUP` and preserves full progression eligibility.
4. **Reasoning Accounting:** Answers containing code solutions in `COACH` or `HYBRID` mode are tagged as `SUPPLIED_REASONING` or `STRUCTURAL_DIRECTION`.
5. **Ledger Consequence:** Logging a `SUPPLIED_REASONING` interaction to the Evidence Ledger forces `ProgressionDecision.STRENGTHEN`.
