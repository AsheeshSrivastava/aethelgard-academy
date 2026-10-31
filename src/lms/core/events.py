"""In-process domain events (SPEC-12 section 9, SPEC-15 section 6).

Later modules subscribe here. They read; they never change the ledger.
"""

from collections import defaultdict
import logging
import threading
from typing import Callable, Dict, List

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

EVIDENCE_RECORDED = "evidence.recorded"


class EvidenceRecorded(BaseModel):
    """A frozen copy of what was appended. Subscribers never get the entry or the repository."""

    model_config = ConfigDict(frozen=True)

    entry_id: str
    learner_id: str
    unit_id: str
    skill_id: str
    category: str
    strength: str
    assistance_level: str


class LedgerWriteRefused(RuntimeError):
    """A subscriber tried to write to the ledger."""


Handler = Callable[[EvidenceRecorded], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._local = threading.local()

    @property
    def dispatching(self) -> bool:
        """True on this thread while subscribers run."""
        return getattr(self._local, "dispatching", False)

    def subscribe(self, name: str, handler: Handler) -> None:
        self._handlers[name].append(handler)

    def publish(self, name: str, event: EvidenceRecorded) -> None:
        """Run every subscriber. One that fails is logged and stops nothing else."""
        self._local.dispatching = True
        try:
            for handler in self._handlers[name]:
                try:
                    handler(event)
                except Exception:
                    logger.exception("A subscriber to %s failed.", name)
        finally:
            self._local.dispatching = False
