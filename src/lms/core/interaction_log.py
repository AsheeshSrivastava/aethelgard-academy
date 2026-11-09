"""The interaction log: every learner action, kept apart from the evidence ledger.

Governed by ADR-0022. Deterministic and pure apart from the random part of a ULID.
"""

import os
import re
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MAX_TEXT_CHARS = 64 * 1024
MAX_PAYLOAD_CHARS = 256 * 1024
TRUNCATED = "…[truncated]"
REDACTED = "[redacted]"
ID_PATTERN = r"^[A-Za-z0-9_-]{8,64}$"
_SECRET_KEY = re.compile(r"key|token|secret|password", re.IGNORECASE)
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

EventType = Literal[
    "answer_submitted",
    "concept_check",
    "judgement_disputed",
    "run",
    "verify",
    "regenerate",
    "reset",
    "axis",
    "opened",
    "closed",
    "hint_viewed",
    "feedback_viewed",
    "document_draft",
]
ClientEventType = Literal["opened", "closed", "hint_viewed", "feedback_viewed"]


class InteractionEvent(BaseModel):
    interaction_id: str
    learner_id: str
    recorded_at_ms: int
    event_type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    attempt_id: Optional[str] = None
    unit_id: Optional[str] = None
    activity: Optional[str] = None
    item_id: Optional[str] = None
    test_mode: bool = False


class ClientPayload(BaseModel):
    """The only fields a client event may carry; anything else is refused."""

    model_config = ConfigDict(extra="forbid")

    seconds_open: Optional[int] = Field(None, ge=0, le=7 * 24 * 3600)
    step: Optional[str] = Field(None, max_length=64)


class ClientEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: ClientEventType
    interaction_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    unit_id: Optional[str] = Field(None, max_length=32)
    activity: Optional[str] = Field(None, max_length=32)
    item_id: Optional[str] = Field(None, max_length=128)
    payload: ClientPayload = Field(default_factory=ClientPayload)


def new_ulid(time_ms: int) -> str:
    """10 time characters, then 16 random ones (Crockford base 32)."""
    stamp, rest = "", time_ms
    for _ in range(10):
        stamp = _CROCKFORD[rest % 32] + stamp
        rest //= 32
    return stamp + "".join(_CROCKFORD[b % 32] for b in os.urandom(16))


def valid_id(value: Optional[str]) -> bool:
    return value is not None and re.fullmatch(ID_PATTERN, value) is not None


def clean_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cap every text, redact secret-looking keys at any depth, and cap the whole payload."""

    def clean(value: Any, key: str = "") -> Any:
        if _SECRET_KEY.search(key):
            return REDACTED
        if isinstance(value, dict):
            return {k: clean(v, str(k)) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        if isinstance(value, str) and len(value) > MAX_TEXT_CHARS:
            return value[:MAX_TEXT_CHARS] + TRUNCATED
        return value

    cleaned = clean(payload)
    if len(str(cleaned)) > MAX_PAYLOAD_CHARS:
        return {"truncated": True, "keys": sorted(map(str, cleaned))}
    return cleaned
