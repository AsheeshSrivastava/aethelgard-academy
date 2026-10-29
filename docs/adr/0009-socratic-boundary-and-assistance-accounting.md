# ADR-0009: Socratic Boundary Guardrails and Assistance Accounting

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Asheesh Ranjan Srivastava (Platform Architect & Owner), AI Systems Architect

---

## 1. Context and Problem Statement

A fundamental risk in AI-assisted learning platforms is the "illusion of competence": learners ask an LLM companion for assistance, the LLM provides working code or direct logic, the learner copies it, the test suite passes, and the platform registers false progression.

In the AI Era, looking up syntax or documentation is completely legitimate and standard practice (engineers search APIs daily). However, delegating the cognitive path—the reasoning and structural design—means the learner has not developed the targeted capability.

We need an architectural mechanism to:
1. Guarantee that in Socratic mode, AXIS AI never generates code solutions or direct algorithmic fixes, regardless of prompt variations or user coaxing.
2. Formally classify the level of assistance (`AssistanceLevel`) provided during any learner-companion interaction.
3. Account for assistance transparently in the Evidence Ledger: syntax lookups do not penalize progression, but supplied reasoning automatically downgrades evidence strength and routes progression to `STRENGTHEN` (targeted micro-practice).

---

## 2. Decision

We establish the **Socratic Boundary & Assistance Accounting Architecture**:

### 2.1 The Socratic Boundary Guardrail
- Any response produced under `AxisMode.SOCRATIC` is intercepted by an inspection boundary before reaching the learner or client interface.
- The guardrail validates two invariants:
  1. **Zero-Executable-Code Invariant:** Socratic replies must not contain code blocks (```python / ```), function definitions (`def `), class declarations (`class `), or complete executable assignments.
  2. **Inquiry Requirement:** Socratic replies must prompt reflection through guiding questions (`?`) and directed observation rather than declaratives.
- If an upstream model or mock produces executable code in Socratic mode, the guardrail triggers a `SocraticBoundaryViolation`, sanitizes the response into an inquiry-based guide, and records a guardrail event.

### 2.2 Assistance Accounting Tiers
Every interaction with AXIS AI is classified into one of five mutually exclusive levels:
- `NONE`: Learner solved the problem autonomously.
- `SYNTAX_LOOKUP`: Learner queried documentation, keyword syntax, or library method signatures.
- `SMALL_HINT`: Companion provided a conceptual nudge or pointed to an error type without detailing code.
- `STRUCTURAL_DIRECTION`: Companion suggested overall architecture or high-level schema design.
- `SUPPLIED_REASONING`: Companion or external source gave the algorithmic logic, transformation steps, or code solution.

### 2.3 Evidence Ledger Integration & Progression Impact
- When `lms verify` or `lms explain` records evidence into the `EvidenceLedger`, any accompanying or preceding companion interaction attaches its `AssistanceLevel`.
- Under `evaluate_progression()`:
  - `SYNTAX_LOOKUP` and `SMALL_HINT` preserve `MODERATE` or `STRONG` evidence strength for `APPLY`.
  - `SUPPLIED_REASONING` forces `ProgressionDecision.STRENGTHEN`, guaranteeing the learner must demonstrate autonomy in a fresh scenario before advancing.

---

## 3. Consequences

### Positive
- **Integrity of Portfolio & Skill Badging:** Prevents generative AI from cheating the competency ledger.
- **Fair Accounting:** Learners are not punished for looking up syntax (`SYNTAX_LOOKUP`), matching real-world engineering workflows.
- **Deterministic Testing:** Fully testable offline with `MOCK_AI=true`.

### Negative / Trade-offs
- Guardrail checks add negligible latency (< 1ms via regex and AST scanning).
- Strict Socratic mode may occasionally require prompt tuning to avoid false positive alarms on small mathematical symbols.
