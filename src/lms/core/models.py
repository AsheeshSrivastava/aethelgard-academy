"""Core domain models and schema definitions for the LMS / KMS platform.

Governed by:
- Learning Method v2 (10 activities, CO-6 soft gate)
- Proficiency & Progression System v1 (4 levels, 4 progression decisions, evidence ledger)
- AI-Era Programming Skills Framework v1 (27 skills)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


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
    prerequisites: List[str] = Field(default_factory=list)
    carry_forward: Optional[DataContext] = None
    wiki_links: List[ConceptWikiLink] = Field(default_factory=list)
    starter_code: Optional[str] = None
    test_code: Optional[str] = None


class EvidenceEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str
    unit_id: str
    skill_id: str                      # e.g., "CO-1"
    evidence_category: EvidenceCategory
    evidence_strength: EvidenceStrength
    assistance_level: AssistanceLevel
    demonstration_context: str         # Brief record of the task/activity
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    observed_reasoning: Optional[str] = None
