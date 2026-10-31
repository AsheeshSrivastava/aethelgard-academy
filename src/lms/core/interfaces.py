"""Abstract interfaces (Ports) and data transport envelopes for the LMS platform.

Follows Hexagonal Architecture:
- ILearnerRepository: Persistence port (SQLite / Postgres)
- ICodeRunner: Execution port (Subprocess / Docker)
- IAXISCompanion: AI Tutoring port (Mock / Cloud LLM)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple
from pydantic import BaseModel, Field

from lms.core.cold_check import ColdCheckTimer
from lms.core.exercises import CurrentExercise
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
    learner_id: str = ""               # Set by the server from the session; a client value is ignored
    unit_id: str
    mode: AxisMode
    current_activity: ActivityType
    user_prompt: str
    learner_code: Optional[str] = None
    execution_result: Optional[ExecutionResult] = None
    exercise_id: Optional[str] = None  # Assistance is logged against this exercise (ADR-0009)


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

    def get_cold_check_timer(self, learner_id: str, unit_id: str) -> Optional[ColdCheckTimer]:
        ...

    def mark_unit_activities_completed(
        self, learner_id: str, unit_id: str, completed_at: datetime
    ) -> None:
        ...

    def record_cold_check_attempt(
        self, learner_id: str, unit_id: str, passed: bool, attempted_at: datetime
    ) -> None:
        ...

    def get_current_exercise(
        self, learner_id: str, unit_id: str, activity: str
    ) -> Optional[CurrentExercise]:
        ...

    def set_current_exercise(
        self, learner_id: str, unit_id: str, activity: str, exercise_id: str, served_at: datetime
    ) -> None:
        ...

    def clear_current_exercise(self, learner_id: str, unit_id: str, activity: str) -> None:
        ...

    def log_assistance(
        self, learner_id: str, exercise_id: str, level: AssistanceLevel, logged_at: datetime
    ) -> None:
        ...

    def get_assistance_levels(
        self, learner_id: str, exercise_id: str, since: datetime
    ) -> List[AssistanceLevel]:
        ...

    def get_cold_items(self, learner_id: str, unit_id: str) -> Dict[str, bool]:
        ...

    def record_cold_item(
        self, learner_id: str, unit_id: str, skill_id: str, passed: bool, attempted_at: datetime
    ) -> None:
        ...

    def clear_failed_cold_items(self, learner_id: str, unit_id: str) -> None:
        ...

    def get_seen_exercises(self, learner_id: str, unit_id: str, activity: str) -> List[str]:
        ...

    def get_unit_state(self, learner_id: str, unit_id: str) -> Dict[str, Any]:
        ...

    def save_unit_state(
        self, learner_id: str, unit_id: str, step: Optional[str], done_steps: List[str]
    ) -> None:
        ...

    def get_draft(self, learner_id: str, exercise_id: str) -> Dict[str, str]:
        ...

    def save_draft(
        self, learner_id: str, unit_id: str, exercise_id: str, files: Dict[str, str]
    ) -> None:
        ...

    def record_concept_opened(self, learner_id: str, concept_id: str) -> None:
        ...

    def get_recent_concepts(self, learner_id: str) -> List[str]:
        ...

    def reset_unit(self, learner_id: str, unit_id: str) -> None:
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
        self,
        code: str,
        test_code: Optional[str] = None,
        timeout_seconds: float = 5.0,
        stdin_input: Optional[str] = None,
    ) -> ExecutionResult:
        ...


class IAXISCompanion(Protocol):
    """Port for the AI pedagogical assistant (AXIS AI)."""

    def consult(self, query: AxisQuery) -> AxisResponse:
        ...

    def stream(self, query: AxisQuery) -> Tuple[Iterator[str], List[str]]:
        """The reply as text deltas, plus the concepts it cites."""
        ...
