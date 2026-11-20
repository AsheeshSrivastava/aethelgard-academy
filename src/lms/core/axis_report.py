"""AXIS reports: pure aggregation over interaction-log rows and SPEC-28 trace records (SPEC-29 R1 to R16).

Pure standard library, no I/O. The input is already-parsed rows and records; the output is plain data and plain
text. Nothing here reads learner text: from a log row it reads only the event type, the learner (to count distinct
learners, never to show them), the unit, the time, the test-mode flag, `payload.mode`, and `turn_id` / `vote` of a
thumbs row. From a trace record it reads only the span name, its duration and the SPEC-28 allow-listed attributes.
There is no clock: the same input always gives the same output.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

KNOWN_MODES = ("Socratic", "Hybrid", "Coach")
UNKNOWN_MODE = "unknown"
NO_UNIT = "(none)"
NO_WEEK = "(unknown)"
UTC_WEEK_NOTE = "Weeks run Monday to Sunday, UTC."
NO_TURNS_NOTE = "No AXIS turns recorded."
NO_TRACES_NOTE = "No traces recorded yet. Set LMS_TRACER=local (the default under `lms serve`) and use AXIS."

STAGES = ("retrieve", "prompt_build", "model_call", "citation_check", "check_requirements", "feedback_points")
KINDS = ("axis_question", "concept_check", "readme_draft", "build_review")
RETRIEVAL_STATUSES = ("ok", "not_found", "no_index", "unavailable")
REFUSAL_STATUSES = ("not_found", "no_index", "unavailable")
RETRIEVAL_REASONS = ("busy", "timeout", "stalled", "start_failed", "model_fault")
FEW = 20  # fewer spans than this: the row is marked (few) and never hidden (SPEC-29 R9)
MAX_DURATION_MS = 86_400_000  # a span longer than a day is a bad record, not a measurement
_DAY_MS = 86_400_000
_EPOCH = date(1970, 1, 1)


# --- weeks ------------------------------------------------------------------------------------------------


def week_of(recorded_at_ms: Any) -> str:
    """The UTC Monday on or before the time, as an ISO date; exact to the millisecond (SPEC-29 R4)."""
    if type(recorded_at_ms) is not int:
        return NO_WEEK
    try:
        day = _EPOCH + timedelta(days=recorded_at_ms // _DAY_MS)
        return (day - timedelta(days=day.weekday())).isoformat()
    except (OverflowError, ValueError):
        return NO_WEEK


# --- mode usage -------------------------------------------------------------------------------------------


def _mode_of(payload: Any) -> str:
    mode = payload.get("mode") if isinstance(payload, dict) else None
    return mode if isinstance(mode, str) and mode in KNOWN_MODES else UNKNOWN_MODE


def aggregate_modes(events: Iterable[Any], include_test_mode: bool = False) -> Dict[str, Any]:
    """Counts of AXIS turns per mode, per mode and unit, per mode and week, plus thumbs counts per mode."""
    turns: Dict[Tuple[str, str], Tuple[str, str, str]] = {}  # (learner, turn id) -> (mode, unit, week)
    latest_vote: Dict[Tuple[str, str], Tuple[int, str, str]] = {}  # (learner, turn id) -> (time, vote id, vote)
    for event in events:
        if getattr(event, "test_mode", False) and not include_test_mode:
            continue
        kind = getattr(event, "event_type", None)
        learner = str(getattr(event, "learner_id", ""))
        if kind == "axis":
            unit = getattr(event, "unit_id", None)
            turns[(learner, str(event.interaction_id))] = (
                _mode_of(getattr(event, "payload", None)),
                unit if isinstance(unit, str) and unit else NO_UNIT,
                week_of(getattr(event, "recorded_at_ms", None)),
            )
        elif kind == "axis_feedback":
            payload = getattr(event, "payload", None)
            if isinstance(payload, dict) and isinstance(payload.get("turn_id"), str) and payload.get("vote") in ("up", "down", "clear"):
                at = event.recorded_at_ms if type(event.recorded_at_ms) is int else 0
                key = (learner, payload["turn_id"])
                stamp = (at, str(event.interaction_id), payload["vote"])
                if key not in latest_vote or stamp[:2] > latest_vote[key][:2]:
                    latest_vote[key] = stamp

    learners_all = {learner for learner, _ in turns}
    multi = len(learners_all) > 1

    by_mode: Dict[str, Dict[str, Any]] = {}
    by_unit: Dict[Tuple[str, str], Dict[str, Any]] = {}
    by_week: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for (learner, _), (mode, unit, week) in turns.items():
        for table, key in ((by_mode, mode), (by_unit, (mode, unit)), (by_week, (mode, week))):
            slot = table.setdefault(key, {"turns": 0, "learners": set(), "up": 0, "down": 0})
            slot["turns"] += 1
            slot["learners"].add(learner)
    for (learner, turn_id), (_, _, value) in latest_vote.items():
        known = turns.get((learner, turn_id))
        if known is not None and value in ("up", "down"):
            by_mode[known[0]][value] += 1  # a vote counts toward the mode of its own turn

    def with_learners(row: Dict[str, Any], slot: Dict[str, Any]) -> Dict[str, Any]:
        if multi:
            row["learners"] = len(slot["learners"])
        return row

    return {
        "test_mode": "included" if include_test_mode else "excluded",
        "total_turns": len(turns),
        "multi_learner": multi,
        "by_mode": [with_learners({"mode": m, "turns": s["turns"], "up": s["up"], "down": s["down"]}, s)
                    for m, s in sorted(by_mode.items())],
        "by_mode_unit": [with_learners({"mode": m, "unit": u, "turns": s["turns"]}, s)
                         for (m, u), s in sorted(by_unit.items())],
        "by_mode_week": [with_learners({"mode": m, "week": w, "turns": s["turns"]}, s)
                         for (m, w), s in sorted(by_week.items())],
    }


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> List[str]:
    cells = [[str(v) for v in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in cells)) if cells else len(h) for i, h in enumerate(headers)]
    lines = ["  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip()]
    lines += ["  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip() for row in cells]
    return lines


def format_modes_table(report: Mapping[str, Any]) -> str:
    """The plain-text report: header, then one table per grouping. Counts only."""
    lines = ["AXIS mode usage (counts only)", UTC_WEEK_NOTE, f"test_mode rows: {report['test_mode']}"]
    if not report["total_turns"]:
        return "\n".join(lines + ["", NO_TURNS_NOTE]) + "\n"
    extra = ["learners"] if report["multi_learner"] else []

    def rows(key: str, first: Sequence[str]) -> List[List[Any]]:
        return [[r[k] for k in first] + [r["turns"]] + [r[k] for k in extra] for r in report[key]]

    lines += ["", f"Turns: {report['total_turns']}", "", "By mode (with thumbs: latest vote per answer)"]
    lines += _table(["mode", "turns", "up", "down"] + extra,
                    [[r["mode"], r["turns"], r["up"], r["down"]] + [r[k] for k in extra] for r in report["by_mode"]])
    lines += ["", "By mode and unit"] + _table(["mode", "unit", "turns"] + extra, rows("by_mode_unit", ["mode", "unit"]))
    lines += ["", "By mode and week (week starts on the Monday shown)"] + _table(
        ["mode", "week", "turns"] + extra, rows("by_mode_week", ["mode", "week"]))
    return "\n".join(lines) + "\n"


# --- latency and refusals ---------------------------------------------------------------------------------


def _nearest_rank(sorted_values: Sequence[int], percent: int) -> int:
    rank = max(1, math.ceil(percent / 100 * len(sorted_values)))
    return sorted_values[rank - 1]


def _stats(name: str, durations: List[int]) -> Dict[str, Any]:
    ordered = sorted(durations)
    return {"name": name, "n": len(ordered), "p50": _nearest_rank(ordered, 50), "p95": _nearest_rank(ordered, 95),
            "max": ordered[-1], "few": len(ordered) < FEW}


def _valid(record: Any) -> bool:
    return (isinstance(record, dict) and isinstance(record.get("name"), str)
            and type(record.get("duration_ms")) is int and 0 <= record["duration_ms"] <= MAX_DURATION_MS)


def _attrs(record: Mapping[str, Any]) -> Mapping[str, Any]:
    attributes = record.get("attributes")
    return attributes if isinstance(attributes, dict) else {}


def summarise_latency(records: Iterable[Any], include_test_mode: bool = False, skipped_lines: int = 0) -> Dict[str, Any]:
    """p50, p95 and max per stage and trace kind, plus retrieval, refusal and model-call counts (SPEC-29 R9 to R14)."""
    good: List[Mapping[str, Any]] = []
    skipped = skipped_lines
    for record in records:
        if _valid(record):
            good.append(record)
        else:
            skipped += 1

    test_traces: Set[Any] = set()
    if not include_test_mode:
        test_traces = {r.get("trace_id") for r in good
                       if r.get("parent_id") is None and r["name"] in KINDS and _attrs(r).get("test_mode") is True}
    kept = [r for r in good if r.get("trace_id") not in test_traces]

    stage_durations: Dict[str, List[int]] = {}
    kind_durations: Dict[str, List[int]] = {}
    for r in kept:
        if r.get("parent_id") is None and r["name"] in KINDS:
            kind_durations.setdefault(r["name"], []).append(r["duration_ms"])
        elif r["name"] in STAGES:
            stage_durations.setdefault(r["name"], []).append(r["duration_ms"])

    question_traces = {r.get("trace_id") for r in kept if r.get("parent_id") is None and r["name"] == "axis_question"}
    first_retrieve: Dict[Any, Mapping[str, Any]] = {}
    for r in kept:
        if r["name"] == "retrieve" and r.get("trace_id") in question_traces and r.get("trace_id") not in first_retrieve:
            first_retrieve[r.get("trace_id")] = r
    status = {s: 0 for s in RETRIEVAL_STATUSES}
    reason = {x: 0 for x in RETRIEVAL_REASONS}
    downgraded = 0
    latest = 0
    for r in first_retrieve.values():
        a = _attrs(r)
        if a.get("retrieval_status") in status:
            status[a["retrieval_status"]] += 1
        if a.get("downgraded") is True:
            downgraded += 1
        if a.get("retrieval_reason") in reason:
            reason[a["retrieval_reason"]] += 1
        measured = a.get("latency_ms")
        latest = max(latest, measured if type(measured) is int and measured >= 0 else r["duration_ms"])
    turns = len(first_retrieve)
    refused = sum(status[s] for s in REFUSAL_STATUSES)

    errors: Dict[str, int] = {}
    mock = fallback = 0
    for r in kept:
        if r["name"] != "model_call":
            continue
        a = _attrs(r)
        if r.get("status") == "error":
            why = a.get("reason") if isinstance(a.get("reason"), str) else "other"
            errors[why] = errors.get(why, 0) + 1
        mock += 1 if a.get("mock") is True else 0
        fallback += 1 if a.get("fallback") == "mock" else 0

    return {
        "test_mode": "included" if include_test_mode else "excluded",
        "skipped_lines": skipped,
        "stages": [_stats(n, stage_durations[n]) for n in STAGES if n in stage_durations],
        "kinds": [_stats(n, kind_durations[n]) for n in KINDS if n in kind_durations],
        "retrieval": {
            "turns": turns, "status": status, "downgraded": downgraded, "reason": reason,
            "refusal_rate": round(refused / turns, 4) if turns else None, "max_latency_ms": latest,
        },
        "model_calls": {"errors": dict(sorted(errors.items())), "mock": mock, "fallback_mock": fallback},
    }


def _fmt_setting(value: Any) -> str:
    return f"{value:g}" if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)


def format_latency_table(report: Mapping[str, Any], settings: Optional[Mapping[str, Any]] = None) -> str:
    """The plain-text latency report. It prints numbers and the settings in force; it never gives a verdict."""
    lines = ["AXIS latency and refusals (from the local trace file)", f"test_mode traces: {report['test_mode']}"]
    if settings:
        lines.append("Settings in force: LMS_RETRIEVAL_TIMEOUT_S={t}, LMS_RERANK_CONCURRENCY={c}".format(
            t=_fmt_setting(settings.get("timeout_s")), c=_fmt_setting(settings.get("concurrency"))))
    if report["skipped_lines"]:
        lines.append(f"skipped_lines: {report['skipped_lines']}")
    if not report["stages"] and not report["kinds"]:
        return "\n".join(lines + ["", NO_TRACES_NOTE]) + "\n"

    def stat_rows(items: Sequence[Mapping[str, Any]]) -> List[List[Any]]:
        return [[i["name"] + (" (few)" if i["few"] else ""), i["n"], i["p50"], i["p95"], i["max"]] for i in items]

    head = ["name", "n", "p50 ms", "p95 ms", "max ms"]
    lines += ["", "By stage"] + _table(head, stat_rows(report["stages"]))
    lines += ["", "By trace kind (whole interaction)"] + _table(head, stat_rows(report["kinds"]))
    r = report["retrieval"]
    lines += ["", f"Retrieval (AXIS questions with a search): {r['turns']}"]
    lines += _table(["status", "count"], [[s, n] for s, n in r["status"].items()])
    lines += ["", f"downgraded (keyword search only): {r['downgraded']}"]
    lines += _table(["reason", "count"], [[x, n] for x, n in r["reason"].items()])
    rate = "n/a" if r["refusal_rate"] is None else f"{r['refusal_rate']:.4f}"
    lines += ["", f"refusal rate (not_found + no_index + unavailable): {rate}", f"largest search latency: {r['max_latency_ms']} ms"]
    m = report["model_calls"]
    lines += ["", "Model calls", f"mock: {m['mock']}, fallback to mock: {m['fallback_mock']}"]
    lines += _table(["error reason", "count"], [[k, v] for k, v in m["errors"].items()]) if m["errors"] else ["errors: none"]
    return "\n".join(lines) + "\n"
