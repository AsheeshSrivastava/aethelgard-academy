"""Cold Check timer rules per learner and unit.

Governed by:
- ADR-0016 section 2.6 (Cold Check: delayed retrieval)
- SPEC-12 section 4.1 (ColdCheckStatus)

Deterministic and pure: the status is derived from stored timestamps and a
`now` supplied by the caller, so no workflow engine or sleeping is needed.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ColdCheckState(str, Enum):
    NOT_READY = "not_ready"            # Unit activities not completed yet
    WAITING = "waiting"                # Completed; first delay still running
    AVAILABLE = "available"            # Can be attempted now
    PASSED = "passed"                  # Last attempt passed
    FAILED_WAITING = "failed_waiting"  # Last attempt failed; retry delay still running


@dataclass(frozen=True)
class ColdCheckConfig:
    """Delay marked *tunable* in ADR-0016."""

    delay_hours: int = 24


DEFAULT_CONFIG = ColdCheckConfig()


class ColdCheckTimer(BaseModel):
    """What is stored per learner and unit; the status is derived from it."""

    learner_id: str
    unit_id: str
    completed_at: datetime                       # Non-Cold-Check activities finished
    last_attempt_at: Optional[datetime] = None
    last_attempt_passed: Optional[bool] = None


class ColdCheckStatus(BaseModel):
    state: ColdCheckState
    available_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None


def cold_check_status(
    timer: Optional[ColdCheckTimer],
    now: datetime,
    config: ColdCheckConfig = DEFAULT_CONFIG,
) -> ColdCheckStatus:
    """Derive the learner-facing status from the stored timer."""
    if timer is None:
        return ColdCheckStatus(state=ColdCheckState.NOT_READY)

    delay = timedelta(hours=config.delay_hours)
    last_attempt_at = timer.last_attempt_at

    if last_attempt_at is None:
        available_at = timer.completed_at + delay
        blocked_state = ColdCheckState.WAITING
    elif timer.last_attempt_passed:
        return ColdCheckStatus(state=ColdCheckState.PASSED, last_attempt_at=last_attempt_at)
    else:
        available_at = last_attempt_at + delay
        blocked_state = ColdCheckState.FAILED_WAITING

    return ColdCheckStatus(
        state=ColdCheckState.AVAILABLE if now >= available_at else blocked_state,
        available_at=available_at,
        last_attempt_at=last_attempt_at,
    )
