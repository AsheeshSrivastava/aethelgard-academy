"""LMS_TRACER and its settings, read once at start-up (SPEC-28 R7, R8, section 3).

Any bad value stops start-up with a plain message, even when MOCK_AI=true (same pattern as LMS_RUNNER, ADR-0036).
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from lms.adapters.observability.local_tracer import DEFAULT_MAX_BYTES, LocalTracer
from lms.core.tracing import NoopTracer

TRACER_ENV = "LMS_TRACER"
TRACE_DIR_ENV = "LMS_TRACE_DIR"
TRACE_MAX_BYTES_ENV = "LMS_TRACE_MAX_BYTES"
DEFAULT_TRACE_DIR = "data/traces"
CHOICES = ("noop", "local")
MIN_MAX_BYTES, MAX_MAX_BYTES = 100_000, 1_000_000_000


class TracerConfigError(Exception):
    """The tracing settings are wrong. Start-up stops; the message says what to change."""


def configured_max_bytes(env: Mapping[str, str]) -> int:
    raw = (env.get(TRACE_MAX_BYTES_ENV) or "").strip()
    if not raw:
        return DEFAULT_MAX_BYTES
    if not raw.isascii() or not raw.isdigit() or not MIN_MAX_BYTES <= int(raw) <= MAX_MAX_BYTES:
        raise TracerConfigError(
            f"{TRACE_MAX_BYTES_ENV}='{raw}' is not allowed. Use a whole number from {MIN_MAX_BYTES} to {MAX_MAX_BYTES}."
        )
    return int(raw)


def build_tracer(environ: Optional[Mapping[str, str]] = None) -> Any:
    """The tracer for this run: NoopTracer unless LMS_TRACER=local."""
    env = os.environ if environ is None else environ
    choice = (env.get(TRACER_ENV) or "").strip().lower() or "noop"
    if choice not in CHOICES:
        raise TracerConfigError(f"{TRACER_ENV}='{choice}' is not allowed. Choose one of: {', '.join(CHOICES)}.")
    if choice == "noop":
        return NoopTracer()
    max_bytes = configured_max_bytes(env)
    folder = (env.get(TRACE_DIR_ENV) or "").strip() or DEFAULT_TRACE_DIR
    try:
        return LocalTracer(folder, max_bytes=max_bytes)
    except OSError as exc:
        raise TracerConfigError(
            f"{TRACE_DIR_ENV}='{folder}' cannot be used ({type(exc).__name__}). Choose a folder this app can write to."
        ) from None


def describe(tracer: Any) -> str:
    """The start-up log line."""
    if isinstance(tracer, LocalTracer):
        return f"Tracing: local dir={tracer.directory} max_bytes={tracer.max_bytes}"
    return "Tracing: off (noop)"
