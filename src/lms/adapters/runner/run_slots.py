"""A cap on how many code runs happen at the same time (audit A4, 2026-11-09).

Each run is an operating-system process. Without a cap, a burst of requests can use up the
machine. A run takes a slot before it starts and gives it back when it ends. When no slot is
free the run is refused at once, not queued, so a busy server answers fast and stays up.

The cap is per process. With several server workers, the limit applies to each worker.
"""

import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_RUNS = 4
MAX_RUNS_ENV = "LMS_MAX_CONCURRENT_RUNS"
RETRY_AFTER_SECONDS = 2


class RunBusy(Exception):
    """Every run slot is taken."""


class RunSlots:
    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("The run limit must be at least 1.")
        self._slots = threading.BoundedSemaphore(limit)

    def try_acquire(self) -> bool:
        return self._slots.acquire(blocking=False)

    def release(self) -> None:
        self._slots.release()


class CappedRunner:
    """Wraps an ICodeRunner so every execute() takes a slot first. Grading, build checks and
    the playground all run code through the runner, so one wrapper caps them all."""

    def __init__(self, inner: Any, slots: RunSlots) -> None:
        self._inner = inner
        self._slots = slots

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        if not self._slots.try_acquire():
            raise RunBusy()
        try:
            return self._inner.execute(*args, **kwargs)
        finally:
            self._slots.release()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def max_runs_from_env() -> int:
    """LMS_MAX_CONCURRENT_RUNS, or the default (with a warning) when it is not a positive whole number."""
    raw = os.environ.get(MAX_RUNS_ENV, "").strip()
    if not raw:
        return DEFAULT_MAX_RUNS
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        logger.warning("%s=%r is not a positive whole number; using %d.", MAX_RUNS_ENV, raw, DEFAULT_MAX_RUNS)
        return DEFAULT_MAX_RUNS
    return value
