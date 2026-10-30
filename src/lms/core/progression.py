"""Progression and evidence evaluation engine.

Governed by:
- 04 - Proficiency & Progression System v1
- ADR-0016: decisions use the whole ledger, not only the latest entry.
  This function keeps its original signature for the CLI and delegates to
  `lms.core.proficiency`.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from lms.core.models import (
    EvidenceEntry,
    ProficiencyLevel,
    ProgressionDecision,
)
from lms.core.proficiency import decide_skill


def evaluate_progression(
    target_level: ProficiencyLevel,
    evidence_entries: List[EvidenceEntry],
    now: Optional[datetime] = None,
) -> Tuple[ProgressionDecision, str]:
    """Evaluate observable evidence for one skill against a target proficiency level.

    Returns:
        (ProgressionDecision, reason_str)
    """
    skill_id = evidence_entries[-1].skill_id if evidence_entries else None
    result = decide_skill(target_level, evidence_entries, skill_id, now=now)
    return result.decision, result.reason
