"""Abstract interfaces (Ports) and data transport envelopes for the LMS platform.

Follows Hexagonal Architecture:
- ILearnerRepository: Persistence port (SQLite / Postgres)
- ICodeRunner: Execution port (Subprocess / Docker)
- IAXISCompanion: AI Tutoring port (Mock / Cloud LLM)
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from pydantic import BaseModel, Field

from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceEntry,
)


class AxisMode(str, Enum):
    COACH = "Coach"        # Supportive, direct hints, encouraging
    HYBRID = "Hybrid"      # Balanced conceptual answers + guided tasks
    SOCRATIC = "Socratic"  # Inquiry only; never provides code solutions


class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    assertion_errors: List[str] = Field(default_factory=list)


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
    cited_concepts: List[str] = Field(default_factory=list)
    detected_assistance_level: AssistanceLevel = AssistanceLevel.NONE


class ILearnerRepository(Protocol):
    """Port for learner state, unit progress, and evidence ledger persistence."""

    def get_learner(self, learner_id: str) -> Optional[Dict[str, Any]]:
        ...

    def get_unit_progress(self, learner_id: str, unit_id: str) -> Optional[Dict[str, Any]]:
        ...

    def save_unit_progress(self, learner_id: str, unit_id: str, status: str) -> None:
        ...

    def record_evidence(self, entry: EvidenceEntry) -> None:
        ...

    def get_evidence_ledger(
        self, learner_id: str, skill_id: Optional[str] = None
    ) -> List[EvidenceEntry]:
        ...


class ICodeRunner(Protocol):
    """Port for isolated, deterministic code execution and test verification."""

    def execute(
        self, code: str, test_code: Optional[str] = None, timeout_seconds: float = 5.0
    ) -> ExecutionResult:
        ...


class IAXISCompanion(Protocol):
    """Port for the AI pedagogical assistant (AXIS AI)."""

    def consult(self, query: AxisQuery) -> AxisResponse:
        ...
