"""The tracing port (SPEC-28, ADR-0037 sections 2.1, 2.2 and 2.8).

Pure standard library: no vendor import and no adapter type. Core and adapter code call `span`, `event`
and `annotate` here; the process tracer behind them is chosen at start-up and defaults to NoopTracer.

Three rules this module keeps for every caller:
- A tracer never raises into the caller. A fault is logged once per process and the turn carries on.
- A span attribute is kept only if its key is in ALLOWED_ATTRIBUTES and its value passes the type rule.
  Anything else is dropped and counted. Learner text has no key, so it can never be recorded.
- Spans nest through an ambient context (contextvars), so a child opened inside a parent is linked.
"""

from __future__ import annotations

import contextvars
import logging
import math
import re
from contextlib import contextmanager
from typing import Any, ContextManager, Dict, Iterator, List, Optional, Protocol, Tuple, runtime_checkable

logger = logging.getLogger(__name__)

# --- the attribute allow-list (SPEC-28 R14) ---------------------------------------------------------------

_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_UNIT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")
_HEX_INDEX = re.compile(r"^(?:[0-9a-f]{12}|[0-9a-f]{64})$")
_PROMPT_VERSION = re.compile(r"[0-9a-f]{12}")  # SPEC-31 R13
# A passage id looks like `source@version#c0-120~digest` (make_passage_id): path characters, no spaces.
_PASSAGE_ID = re.compile(r"^[A-Za-z0-9._/@#~-]{8,200}$")
_SOURCE_ID = re.compile(r"^[^\s]{1,200}$")
_BLANK_RUN = re.compile(r"\s{2,}")
MAX_SHORT = 80
MAX_REFS = 10
# Fixed sets (SPEC-28 R11): a reason is one of these words, never a provider's text.
FAIL_REASONS = frozenset({"not_set_up", "budget", "provider_error", "empty"})
RETRIEVAL_REASONS = frozenset({"busy", "timeout", "stalled", "start_failed", "model_fault"})  # SPEC-29 R17
NOT_JUDGED_REASONS = frozenset({"ai_off", "no_rubric", "cap_reached", "provider_refused", "no_answer", "unreadable_reply"})

_ID_KEYS = frozenset({"interaction_id"})
_SHORT_KEYS = frozenset({
    "kind", "call", "mode", "source_state", "retrieval_mode", "retrieval_status", "status", "reason",
    "not_judged_reason", "error_class", "profile_id", "model_answered", "fallback",
})
_BOOL_KEYS = frozenset({"downgraded", "mock", "blocked", "test_mode", "stream"})
_COUNT_KEYS = frozenset({
    "terms_matched", "terms_total", "passages_retrieved", "passages_cited", "input_tokens", "output_tokens",
    "dropped_attributes", "latency_ms", "duration_ms",
})
_OTHER_KEYS = frozenset({
    "unit_id", "index_version", "passage_refs", "cited_passage_ids", "retrieval_reason", "prompt_version",
})

ALLOWED_ATTRIBUTES = frozenset(_ID_KEYS | _SHORT_KEYS | _BOOL_KEYS | _COUNT_KEYS | _OTHER_KEYS)


def _short(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= MAX_SHORT and not _BLANK_RUN.search(value)


def _count(value: Any) -> bool:
    return type(value) is int and value >= 0


def _passage_ref(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {"passage_id", "source_id", "score"}:
        return None
    pid, sid, score = value["passage_id"], value["source_id"], value["score"]
    if not (isinstance(pid, str) and _PASSAGE_ID.match(pid) and isinstance(sid, str) and _SOURCE_ID.match(sid)):
        return None
    if type(score) not in (int, float) or not math.isfinite(score):
        return None
    return {"passage_id": pid, "source_id": sid, "score": round(float(score), 4)}


def _clean(key: str, value: Any) -> Tuple[bool, Any]:
    """(kept, value) for one attribute under the type rules of SPEC-28 R14."""
    if key in _ID_KEYS:
        return (isinstance(value, str) and bool(_ID.match(value))), value
    if key == "reason":
        return value in FAIL_REASONS, value
    if key == "not_judged_reason":
        return value in NOT_JUDGED_REASONS, value
    if key == "retrieval_reason":
        return value in RETRIEVAL_REASONS, value
    if key in _SHORT_KEYS:
        return _short(value), value
    if key in _BOOL_KEYS:
        return type(value) is bool, value
    if key in _COUNT_KEYS:
        return _count(value), value
    if key == "unit_id":
        return (isinstance(value, str) and bool(_UNIT.match(value))), value
    if key == "index_version":
        return (isinstance(value, str) and bool(_HEX_INDEX.match(value))), value
    if key == "prompt_version":
        return (isinstance(value, str) and bool(_PROMPT_VERSION.fullmatch(value))), value
    if key == "passage_refs":
        if not isinstance(value, list) or len(value) > MAX_REFS:
            return False, None
        refs = [_passage_ref(item) for item in value]
        return (None not in refs), refs
    if key == "cited_passage_ids":
        ok = (isinstance(value, list) and len(value) <= MAX_REFS
              and all(isinstance(v, str) and _PASSAGE_ID.match(v) for v in value))
        return ok, value
    return False, None


def sanitise_attributes(attributes: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """The attributes that may be recorded, and how many were dropped (unknown key or a value that breaks its rule)."""
    kept: Dict[str, Any] = {}
    dropped = 0
    for key, value in attributes.items():
        if key not in ALLOWED_ATTRIBUTES:
            dropped += 1
            continue
        ok, clean = _clean(key, value)
        if ok:
            kept[key] = clean
        else:
            dropped += 1
    return kept, dropped


# --- the port ---------------------------------------------------------------------------------------------


@runtime_checkable
class ISpan(Protocol):
    def set(self, **attributes: Any) -> None: ...

    def fail(self, reason: str) -> None:
        """Mark the span as an error with a reason from a fixed set (never a provider's text)."""
        ...


@runtime_checkable
class ITracer(Protocol):
    def span(self, name: str, **attributes: Any) -> ContextManager[ISpan]:
        """Open a span. `parent` (an ISpan or None) may arrive as an attribute-style keyword and is not recorded."""
        ...

    def event(self, name: str, **attributes: Any) -> None: ...


class _NoopSpan:
    trace_id = None
    span_id = None

    def set(self, **attributes: Any) -> None:
        return None

    def fail(self, reason: str) -> None:
        return None


_NOOP_SPAN = _NoopSpan()


class _NoopContext:
    def __enter__(self) -> _NoopSpan:
        return _NOOP_SPAN

    def __exit__(self, *exc: Any) -> bool:
        return False


_NOOP_CONTEXT = _NoopContext()


class NoopTracer:
    """Does nothing and allocates nothing per span. The default in tests and CI."""

    def span(self, name: str, **attributes: Any) -> ContextManager[ISpan]:
        return _NOOP_CONTEXT

    def event(self, name: str, **attributes: Any) -> None:
        return None


# --- the process tracer and the safe entry points ----------------------------------------------------------

_tracer: Any = NoopTracer()
_faulted = False
_current: contextvars.ContextVar = contextvars.ContextVar("lms_current_span", default=None)


def set_tracer(tracer: Any) -> None:
    """Set the process tracer. Resets the once-per-process fault note."""
    global _tracer, _faulted
    _tracer = tracer
    _faulted = False


def get_tracer() -> Any:
    return _tracer


def _fault(exc: BaseException) -> None:
    """A tracer failed: say so once per process (class name only) and carry on."""
    global _faulted
    if _faulted:
        return
    _faulted = True
    logger.warning("Tracing failed (%s); the turn carries on without it.", type(exc).__name__)


class _SafeSpan:
    """What callers hold: every call is guarded, so a broken span can never break a turn."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def set(self, **attributes: Any) -> None:
        try:
            self._inner.set(**attributes)
        except Exception as exc:
            _fault(exc)

    def fail(self, reason: str) -> None:
        try:
            self._inner.fail(reason)
        except Exception as exc:
            _fault(exc)


def _restore(token: Any) -> None:
    """Put the ambient span back. A generator closed from another context cannot reset; that must not lose the span."""
    try:
        _current.reset(token)
    except ValueError:
        _current.set(None)


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[_SafeSpan]:
    """Open a span under the ambient parent. Errors in the caller's code propagate unchanged (and mark the span)."""
    cm: Any = None
    inner: Any = _NOOP_SPAN
    try:
        cm = _tracer.span(name, parent=_current.get(), **attributes)
        inner = cm.__enter__()
    except Exception as exc:
        _fault(exc)
        cm, inner = None, _NOOP_SPAN
    token = _current.set(inner)
    try:
        yield _SafeSpan(inner)
    except BaseException as caught:
        _restore(token)
        if cm is not None:
            try:
                cm.__exit__(type(caught), caught, caught.__traceback__)
            except Exception as exc:
                _fault(exc)
        raise
    else:
        _restore(token)
        if cm is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception as exc:
                _fault(exc)


def event(name: str, **attributes: Any) -> None:
    try:
        _tracer.event(name, parent=_current.get(), **attributes)
    except Exception as exc:
        _fault(exc)


def annotate(**attributes: Any) -> None:
    """Add attributes to the span that is open right now (for example token counts at the metering call)."""
    current = _current.get()
    if current is None:
        return
    try:
        current.set(**attributes)
    except Exception as exc:
        _fault(exc)


def pinned_context(iterator: Iterator[Any]) -> Iterator[Any]:
    """Run every step of a generator in one captured context.

    A streaming reply is read one step at a time, and a server may run each step in a fresh copy of the
    context. Pinning keeps a span opened inside the generator (and its ambient parent) alive across yields.
    """
    context = contextvars.copy_context()
    try:
        while True:
            try:
                item = context.run(next, iterator)
            except StopIteration:
                return
            yield item
    finally:
        close = getattr(iterator, "close", None)
        if close is not None:
            context.run(close)


def token_attributes(input_tokens: Optional[int], output_tokens: Optional[int]) -> Dict[str, int]:
    """`input_tokens` and `output_tokens` for a span, leaving out any count the provider did not give."""
    counts = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return {key: value for key, value in counts.items() if isinstance(value, int)}


def passage_refs(passages: List[Any]) -> List[Dict[str, Any]]:
    """The `passage_refs` attribute for retrieved passages: id, source id and score, never text."""
    return [{"passage_id": p.passage_id, "source_id": p.source_id, "score": p.score} for p in passages[:MAX_REFS]]


__all__ = [
    "ALLOWED_ATTRIBUTES",
    "ISpan",
    "ITracer",
    "NoopTracer",
    "annotate",
    "event",
    "get_tracer",
    "passage_refs",
    "pinned_context",
    "sanitise_attributes",
    "set_tracer",
    "span",
    "token_attributes",
]
