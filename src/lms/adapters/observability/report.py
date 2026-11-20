"""Reading the SPEC-28 trace file, and writing the static HTML report (SPEC-29 R10, R16, R18, R19).

The HTML is one self-contained file: no script, no external asset, a Content-Security-Policy that allows only inline
style, and every value escaped. It holds counts, mode names, unit ids, weeks and timings; never a learner id,
interaction id, trace id, span id, passage id or any text.
"""

from __future__ import annotations

import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lms.adapters.observability.local_tracer import TRACE_FILE
from lms.core.axis_report import NO_TRACES_NOTE, NO_TURNS_NOTE, UTC_WEEK_NOTE


class ReportWriteError(Exception):
    """The report could not be written. The message names the error class only."""


# --- reading the trace file ---------------------------------------------------------------------------------


def trace_files(trace_dir: Path | str) -> List[Path]:
    """The rotated file first, then the current one, whichever exist."""
    folder = Path(trace_dir)
    return [p for p in (folder / (TRACE_FILE + ".1"), folder / TRACE_FILE) if p.is_file()]


def read_trace_records(trace_dir: Path | str) -> Tuple[List[Dict[str, Any]], int]:
    """(records, skipped_lines). A torn, blank-free but non-object or non-JSON line is skipped and counted."""
    records: List[Dict[str, Any]] = []
    skipped = 0
    for path in trace_files(trace_dir):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        value = json.loads(line)
                    except ValueError:
                        skipped += 1
                        continue
                    if isinstance(value, dict):
                        records.append(value)
                    else:
                        skipped += 1
        except OSError:
            continue  # an unreadable file counts as absent: the report never fails on it
    return records, skipped


# --- the HTML report ----------------------------------------------------------------------------------------

_STYLE = """
:root { color-scheme: light dark; --bg: #ffffff; --fg: #1a1a1a; --muted: #555555; --line: #c8c8c8; --head: #eeeeee; }
@media (prefers-color-scheme: dark) { :root { --bg: #16181c; --fg: #e8e8e8; --muted: #a8a8a8; --line: #3a3d44; --head: #23262c; } }
body { background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, sans-serif; margin: 0 auto; max-width: 56rem; padding: 1rem; }
h1 { font-size: 1.5rem; } h2 { font-size: 1.2rem; margin-top: 2rem; }
.note { color: var(--muted); }
table { border-collapse: collapse; margin: 0.75rem 0 1.5rem; width: 100%; }
caption { font-weight: 600; text-align: left; padding: 0.25rem 0; }
th, td { border: 1px solid var(--line); padding: 0.3rem 0.6rem; text-align: left; }
th { background: var(--head); }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
"""


def esc(value: Any) -> str:
    """Escape a value for HTML text, quotes included, and drop control characters."""
    text = "".join(ch for ch in str(value) if ch in "\n\t" or ord(ch) >= 32)
    return html.escape(text, quote=True)


def _table(caption: str, headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(
        "<tr>" + f'<th scope="row">{esc(row[0])}</th>' + "".join(f'<td class="num">{esc(v)}</td>' for v in row[1:]) + "</tr>"
        for row in rows
    )
    return f"<table><caption>{esc(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _mode_section(modes: Mapping[str, Any]) -> str:
    parts = ["<h2>Mode usage</h2>", f'<p class="note">{esc(UTC_WEEK_NOTE)} test_mode rows: {esc(modes["test_mode"])}.</p>']
    if not modes["total_turns"]:
        return "".join(parts + [f"<p>{esc(NO_TURNS_NOTE)}</p>"])
    extra = ["learners"] if modes["multi_learner"] else []

    def rows(key: str, first: Sequence[str]) -> List[List[Any]]:
        return [[" / ".join(str(r[k]) for k in first), r["turns"]] + [r[k] for k in extra] for r in modes[key]]

    parts.append(f"<p>Turns: {esc(modes['total_turns'])}</p>")
    parts.append(_table("By mode (thumbs: latest vote per answer)", ["mode", "turns", "up", "down"] + extra,
                        [[r["mode"], r["turns"], r["up"], r["down"]] + [r[k] for k in extra] for r in modes["by_mode"]]))
    parts.append(_table("By mode and unit", ["mode / unit", "turns"] + extra, rows("by_mode_unit", ["mode", "unit"])))
    parts.append(_table("By mode and week (week starts on the Monday shown)", ["mode / week", "turns"] + extra,
                        rows("by_mode_week", ["mode", "week"])))
    return "".join(parts)


def _latency_section(latency: Mapping[str, Any], settings: Optional[Mapping[str, Any]]) -> str:
    parts = ["<h2>Latency and refusals</h2>", f'<p class="note">test_mode traces: {esc(latency["test_mode"])}.</p>']
    if settings:
        parts.append(f'<p class="note">Settings in force: LMS_RETRIEVAL_TIMEOUT_S={esc(settings.get("timeout_s"))}, '
                     f'LMS_RERANK_CONCURRENCY={esc(settings.get("concurrency"))}</p>')
    if latency["skipped_lines"]:
        parts.append(f"<p>skipped_lines: {esc(latency['skipped_lines'])}</p>")
    if not latency["stages"] and not latency["kinds"]:
        return "".join(parts + [f"<p>{esc(NO_TRACES_NOTE)}</p>"])

    def stat_rows(items: Sequence[Mapping[str, Any]]) -> List[List[Any]]:
        return [[i["name"] + (" (few)" if i["few"] else ""), i["n"], i["p50"], i["p95"], i["max"]] for i in items]

    head = ["name", "n", "p50 ms", "p95 ms", "max ms"]
    parts.append(_table("By stage", head, stat_rows(latency["stages"])))
    parts.append(_table("By trace kind (whole interaction)", head, stat_rows(latency["kinds"])))
    r = latency["retrieval"]
    rate = "n/a" if r["refusal_rate"] is None else f"{r['refusal_rate']:.4f}"
    parts.append(_table(f"Retrieval status ({r['turns']} AXIS questions with a search)", ["status", "count"],
                        [[s, n] for s, n in r["status"].items()]))
    parts.append(_table(f"Downgraded to keyword search: {r['downgraded']}", ["reason", "count"],
                        [[x, n] for x, n in r["reason"].items()]))
    parts.append(f"<p>Refusal rate (not_found + no_index + unavailable): {esc(rate)}. "
                 f"Largest search latency: {esc(r['max_latency_ms'])} ms.</p>")
    m = latency["model_calls"]
    parts.append(f"<p>Model calls: mock {esc(m['mock'])}, fallback to mock {esc(m['fallback_mock'])}.</p>")
    if m["errors"]:
        parts.append(_table("Model call errors", ["reason", "count"], [[k, v] for k, v in m["errors"].items()]))
    return "".join(parts)


def render_html(modes: Mapping[str, Any], latency: Mapping[str, Any], settings: Optional[Mapping[str, Any]] = None) -> str:
    """One offline page from the two aggregates. Same input, same bytes: there is no timestamp."""
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>AXIS usage report</title><style>{_STYLE}</style></head><body>"
        "<h1>AXIS usage report</h1>"
        '<p class="note">A local owner view, not a learner page. Counts and timings only: no questions, answers or learner ids.</p>'
        + _mode_section(modes) + _latency_section(latency, settings)
        + "</body></html>\n"
    )


def write_html(path: Path | str, content: str) -> None:
    """Write atomically: a temporary file in the same folder, then a rename. A failure leaves any older report alone."""
    target = Path(path)
    temp_name: Optional[str] = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile("wb", dir=target.parent, suffix=".tmp", delete=False)
        temp_name = handle.name
        with handle:
            handle.write(content.encode("utf-8"))
        os.replace(temp_name, target)
        temp_name = None
    except Exception as exc:
        raise ReportWriteError(f"Could not write the report ({type(exc).__name__}).") from None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
