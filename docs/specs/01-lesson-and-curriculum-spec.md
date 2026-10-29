# Specification 01: Unit, Activity & Evidence Ledger Contract

- **Status:** Draft (Step 2: Specification Drafting)
- **Governed By:** 
  - `Learning Method v2` (10 activities, CO-6 soft gate)
  - `Proficiency & Progression System v1` (4 levels, 4 decisions, evidence ledger)
  - `AI-Era Programming Skills Framework v1` (27 skills)
  - `Python Subject Roadmap v3` & `AI Engineering Roadmap v2`
- **Domain:** Platform Core, Adaptive Learning Engine & Telemetry
- **Date:** 2026-10-29

---

## 1. Purpose & Architectural Context

This specification defines the core data models, interfaces, and operational contracts for the Learning Management & Knowledge Platform.

The platform is designed around **Capability-Based Progression** rather than passive course completion. It decouples:
1. **The Terrain:** Static roadmap units and target skills.
2. **The Method Activities:** 10 discrete learning activities that elicit observable evidence.
3. **The Evidence Ledger:** An auditable, append-only record of demonstrated learner capability across 27 skills.
4. **The Pluggable Infrastructure:** Hexagonal ports for storage (SQLite/PostgreSQL), execution (Subprocess/Docker), and AI tutoring (Mock/Cloud LLM).

---

## 2. Core Data Contracts (Schemas)

### 2.1 Proficiency & Progression Enums

```python
from enum import Enum

class ProficiencyLevel(str, Enum):
    UNDERSTAND = "Understand"  # Accurate mental model, reconstructs idea
    APPLY = "Apply"            # Correct performance in familiar situation
    ADAPT = "Adapt"            # Handles meaningful variation / unfamiliar condition
    OWN = "Own"                # Frames problem, directs tools, minimal scaffolding

class EvidenceCategory(str, Enum):
    EXPLAIN_REASON = "Explain / Reason"
    PERFORM_SOLVE = "Perform / Solve"
    DIAGNOSE_JUDGE_TRANSFER = "Diagnose / Judge / Transfer"

class EvidenceStrength(str, Enum):
    WEAK = "Weak"                  # Relied on externally supplied reasoning/imitation
    MODERATE = "Moderate"          # Meaningful reasoning, familiar or bounded context
    STRONG = "Strong"              # Important reasoning owned, handled variation/validation
    INSUFFICIENT = "Insufficient"  # Ambiguous or incomplete observation

class AssistanceLevel(str, Enum):
    NONE = "none"                          # Learner owned the cognitive path entirely
    SYNTAX_LOOKUP = "syntax_lookup"        # Looked up docs/syntax (not disqualifying)
    SMALL_HINT = "small_hint"              # Minor pointer to direction
    STRUCTURAL_DIRECTION = "structural"    # High-level architecture given
    SUPPLIED_REASONING = "supplied"        # AI or tutor provided the solution/reasoning

class ProgressionDecision(str, Enum):
    PROGRESS = "Progress"      # Evidence sufficient for required depth -> next unit
    ACCELERATE = "Accelerate"  # Prior/current evidence clearly stronger -> skip/compress
    STRENGTHEN = "Strengthen"  # Specific skill dimension fragile -> targeted micro-task
    REBUILD = "Rebuild"        # Unreliable mental model -> revisit concept foundation
    UNDECIDED = "Undecided"    # Insufficient/conflicting evidence -> collect smallest probe
```

---

### 2.2 Method Activity Enum (The 10 Activities)

```python
class ActivityType(str, Enum):
    EXPLAIN = "Explain"                  # Mental model + CO-6 concept check (always first)
    PREDICT = "Predict"                  # Commit to outcome before running code
    TRACE = "Trace"                      # Follow state / execution step-by-step
    SPECIFY = "Specify"                  # Formulate input/output contract before code
    DECOMPOSE = "Decompose"              # Split requirement into checked sub-tasks
    MODIFY = "Modify"                    # Extend/refactor existing code in small steps
    DEBUG_VALIDATE = "Debug & Validate"  # Diagnose error, fix assertion, prove result
    BUILD = "Build"                      # Synthesize solution using documentation
    EVALUATE = "Evaluate"                # Compare trade-offs, review AI output, verify trust
    DIRECT = "Direct"                    # Direct AI/tool purposefully with boundary control
```

---

### 2.3 The Unit & Curriculum Schema

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TargetSkill(BaseModel):
    skill_id: str                      # e.g., "CO-1", "BU-1", "VE-6", "SP-1"
    skill_name: str                    # e.g., "Predict before running"
    goal_level: ProficiencyLevel       # Target depth required by this unit

class ConceptCheck(BaseModel):
    concept_line: str                  # The one-line canonical concept taught in Explain
    status: str = "Pending"            # "Solid" | "Shaky" | "Skipped"
    learner_explanation: Optional[str] = None
    example: Optional[str] = None
    non_example: Optional[str] = None
    ai_feedback: Optional[str] = None

class DataContext(BaseModel):
    description: str                   # Plain-English summary of carried-forward state
    state_payload: Dict[str, Any]      # Structured artifacts inherited from previous unit
    source_unit_id: str                # Originating unit ID (e.g., "PY-1.1")

class ConceptWikiLink(BaseModel):
    concept_name: str                  # e.g., "Type Casting", "Data Ingress"
    wiki_slug: str                     # e.g., "concepts/python/type-casting"

class Unit(BaseModel):
    unit_id: str                       # e.g., "PY-1.2", "AI-0.2"
    title: str                         # e.g., "Numbers, booleans and None"
    stage: int                         # e.g., 0, 1, 2
    concept_line: str                  # Canonical core concept
    target_skills: List[TargetSkill]   # 1 to 3 primary skills targeted for evaluation
    methods: List[ActivityType]        # Activity sequence (e.g., [EXPLAIN, PREDICT, DEBUG_VALIDATE])
    prerequisites: List[str] = []      # Required unit IDs (e.g., ["PY-0.1"])
    carry_forward: Optional[DataContext] = None
    wiki_links: List[ConceptWikiLink] = []
    starter_code: Optional[str] = None
    test_code: Optional[str] = None    # Deterministic test assertions
```

---

### 2.4 The Evidence Ledger Schema

An append-only audit trail capturing observable learner performance. Normal learning activities generate evidence implicitly.

```python
from datetime import datetime
import uuid

class EvidenceEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str
    unit_id: str
    skill_id: str                      # e.g., "CO-1"
    evidence_category: EvidenceCategory
    evidence_strength: EvidenceStrength
    assistance_level: AssistanceLevel
    demonstration_context: str         # Brief record of the task/activity (e.g., "PY-1.2 Predict task")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    observed_reasoning: Optional[str] = None  # Learner's own words or action summary
```

---

## 3. Pluggable Infrastructure Interfaces (Ports)

To ensure zero vendor lock-in and complete swappability, all system boundaries are defined as abstract protocols.

### 3.1 Repository Port (`ILearnerRepository`)

```python
from typing import Protocol, List

class ILearnerRepository(Protocol):
    def get_learner(self, learner_id: str) -> Optional[Dict[str, Any]]: ...
    def get_unit_progress(self, learner_id: str, unit_id: str) -> Optional[Dict[str, Any]]: ...
    def save_unit_progress(self, learner_id: str, unit_id: str, status: str) -> None: ...
    def record_evidence(self, entry: EvidenceEntry) -> None: ...
    def get_evidence_ledger(self, learner_id: str, skill_id: Optional[str] = None) -> List[EvidenceEntry]: ...
    def get_skill_proficiency(self, learner_id: str, skill_id: str) -> Dict[str, Any]: ...
```

* **Current Adapter:** SQLite repository (`src/adapters/db/sqlite_repo.py`) using lightweight SQL / `sqlite3`.
* **Future Adapter:** PostgreSQL repository (`src/adapters/db/postgres_repo.py`) without changing any business logic.

---

### 3.2 Execution Runner Port (`ICodeRunner`)

```python
class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    assertion_errors: List[str] = []

class ICodeRunner(Protocol):
    def execute(self, code: str, test_code: Optional[str] = None, timeout_seconds: float = 5.0) -> ExecutionResult: ...
```

* **Current Adapter:** Isolated Subprocess / Docker Runner (`src/adapters/runner/docker_runner.py`).
* **Testability:** Mock Runner for instant, deterministic unit testing without spinning up containers.

---

### 3.3 AXIS AI Companion Port (`IAXISCompanion`)

```python
class AxisMode(str, Enum):
    COACH = "Coach"        # Supportive, direct hints, encouraging
    HYBRID = "Hybrid"      # Balanced conceptual answers + guided tasks
    SOCRATIC = "Socratic"  # Inquiry only; never provides code solutions

class AxisQuery(BaseModel):
    learner_id: str
    unit_id: str
    mode: AxisMode
    current_activity: ActivityType
    user_prompt: str
    learner_code: Optional[str] = None
    execution_result: Optional[ExecutionResult] = None

class AxisResponse(BaseModel):
    reply: str
    suggested_action: Optional[str] = None
    cited_concepts: List[str] = []
    detected_assistance_level: AssistanceLevel

class IAXISCompanion(Protocol):
    def consult(self, query: AxisQuery) -> AxisResponse: ...
```

* **Default Adapter:** Mock Companion (`MOCK_AI=true`) returning deterministic pedagogical hints for offline/free testing.
* **Production Adapter:** Cloud Frontier API Adapter (Gemini/Claude) grounded against our proprietary curriculum markdown notes.

---

## 4. Non-Functional Requirements (NFRs)

1. **Zero-Cost Offline Development (`MOCK_AI=true`):**  
   The entire test suite, progress tracking, code execution, and activity loop must run without API keys or active internet access.
2. **Deterministic Code Evaluation:**  
   Code correctness is verified strictly through automated unit tests (`assert` / `pytest`) inside the runner sandbox. AI is never used as an arbitrary pass/fail judge.
3. **Execution Sandbox Limits:**  
   Execution timeouts are capped at 5.0 seconds. Memory is restricted to 128MB. Disallowed syscalls / dangerous imports (`os.system`, `subprocess`) are blocked in untrusted execution mode.
4. **Sub-100ms State Operations:**  
   All SQLite state and evidence ledger operations must execute under 50ms on commodity hardware.

---

## 5. Edge Cases & Failure States

1. **The "Shaky Concept" Soft Gate (CO-6):**  
   * If a learner's explanation is marked `Shaky`, they are **never hard-blocked** from progressing to the next activity.
   * A warning is recorded in the session state. If the learner subsequently fails practical activities twice in that unit, AXIS AI proactively guides them back to the concept foundation.
2. **Infinite Loops or OOM in Learner Code:**  
   * The `ICodeRunner` catches `TimeoutExpired` or memory exhaustion, returning a structured `ExecutionResult(success=False, stderr="Execution timed out after 5.0s. Check for an infinite while loop.")`.
3. **Malformed Inputs or AI Service Outages:**  
   * If the external AI provider is unreachable, AXIS AI gracefully falls back to static lesson hints and canonical concept notes with zero platform crash.
4. **Missing Carried-Forward Data Context:**  
   * If a learner jumps into Unit 5 without running Unit 4, the platform automatically initializes the default canonical `state_payload` for Unit 4 so the workspace is immediately functional.

---

## 5.1 Chaos & Falsification Verification Matrix

The test suite must verify resilience against:
1. **Adversarial SQL Injection:** Malformed IDs (e.g. `' OR '1'='1' --`) must never compromise the SQLite Evidence Ledger.
2. **Adversarial Prompting against Socratic Mode:** Socratic mode must strictly refuse to yield executable code blocks or `def ` definitions even when directly commanded by the user.
3. **Boundary Schema Violations:** Invalid enums (e.g. non-existent proficiency levels) and malformed payloads must be rejected immediately at the model layer.
4. **Multilingual / Hinglish Input Resilience:** System must safely handle non-ASCII, regional operational phrasing (e.g. *"Form mein pincode enter kiya par error aa gaya"*).
5. **Idempotent Updates:** Repeated, out-of-order, or duplicate updates to learner progress must not corrupt database state.
