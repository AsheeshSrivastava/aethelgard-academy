"""LocalTracer: one JSON line per finished span in a local file (SPEC-28 R4, R6, R18).

No network, no new table, no thread. Writes are short, synchronous and under a lock. The file is capped:
when the next line would pass `max_bytes`, the file is renamed to `<name>.1` (replacing an older one) and a
new file starts, so at most one rotated file is kept. Two failed writes in a row switch writing off for the
rest of the run, so a dead disk costs two failed writes and never one per span.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from lms.core.tracing import sanitise_attributes

logger = logging.getLogger(__name__)

TRACE_FILE = "axis-trace.jsonl"
DEFAULT_MAX_BYTES = 10_000_000
MAX_FAILURES_IN_A_ROW = 2


def _new_id() -> str:
    return secrets.token_hex(8)


class _LocalSpan:
    """A span and the context manager that records it. Also what callers hold as the span handle."""

    def __init__(self, tracer: "LocalTracer", name: str, parent: Any, attributes: Dict[str, Any]) -> None:
        self._tracer = tracer
        self.name = name
        parent_trace = getattr(parent, "trace_id", None)
        self.trace_id = parent_trace or _new_id()
        self.parent_id = getattr(parent, "span_id", None) if parent_trace else None
        self.span_id = _new_id()
        self.status = "ok"
        self._attributes: Dict[str, Any] = {}
        self._dropped = 0
        self._done = False
        self._started_ms = tracer.clock_ms()
        self._started = time.perf_counter()
        self.set(**attributes)

    def set(self, **attributes: Any) -> None:
        if self._done:
            return
        kept, dropped = sanitise_attributes(attributes)
        self._attributes.update(kept)
        self._dropped += dropped

    def fail(self, reason: str) -> None:
        if self._done:
            return
        self.status = "error"
        self.set(reason=reason)

    def __enter__(self) -> "_LocalSpan":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if exc_type is not None and exc_type is not GeneratorExit:  # a reader who leaves a stream is not an error
            self.status = "error"
            self.set(error_class=exc_type.__name__)  # the class name only: the message could hold learner text
        self._finish()
        return False

    def _finish(self) -> None:
        if self._done:
            return
        duration = max(0, int((time.perf_counter() - self._started) * 1000))
        self._done = True
        attributes = dict(self._attributes)
        if self._dropped:
            attributes["dropped_attributes"] = self._dropped
        self._tracer.write({
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "started_at_ms": self._started_ms,
            "duration_ms": duration,
            "status": self.status,
            "attributes": attributes,
        })


class LocalTracer:
    def __init__(
        self,
        directory: Path | str,
        max_bytes: int = DEFAULT_MAX_BYTES,
        clock_ms: Optional[Callable[[], int]] = None,
    ) -> None:
        self.directory = Path(directory)
        self.max_bytes = max_bytes
        self.clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self.path = self.directory / TRACE_FILE
        self.rotated = self.directory / (TRACE_FILE + ".1")
        self._lock = threading.Lock()
        self._failures = 0
        self._disabled = False
        self._tail_checked = False
        self.directory.mkdir(parents=True, exist_ok=True)  # a folder that cannot be made is a start-up message

    # --- the port -----------------------------------------------------------------------------------

    def span(self, name: str, parent: Any = None, **attributes: Any) -> _LocalSpan:
        return _LocalSpan(self, name, parent, attributes)

    def event(self, name: str, parent: Any = None, **attributes: Any) -> None:
        with _LocalSpan(self, name, parent, attributes):
            pass

    # --- writing ------------------------------------------------------------------------------------

    def write(self, record: Dict[str, Any]) -> None:
        if self._disabled:
            return
        data = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
        with self._lock:
            if self._disabled:
                return
            try:
                self._append(data)
                self._failures = 0
            except Exception as exc:  # a trace write never breaks a turn
                self._failures += 1
                if self._failures >= MAX_FAILURES_IN_A_ROW:
                    self._disabled = True
                    logger.warning(
                        "Trace writing is disabled for this run after %d failed writes (%s).",
                        self._failures, type(exc).__name__,
                    )
                else:
                    logger.warning("A trace write failed (%s).", type(exc).__name__)

    def _append(self, data: bytes) -> None:
        size = self.path.stat().st_size if self.path.exists() else 0
        if size and size + len(data) > self.max_bytes:
            os.replace(self.path, self.rotated)
            size = 0
        prefix = b""
        if size and not self._tail_checked:
            with open(self.path, "rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    prefix = b"\n"  # a torn last line from an earlier crash: start on a fresh line
        self._tail_checked = True
        with open(self.path, "ab") as handle:
            handle.write(prefix + data)
