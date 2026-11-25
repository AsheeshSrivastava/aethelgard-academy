"""Scoring and writing the obedience eval outputs (SPEC-30 R13, R14, R18 and amendment A8).

`rows` are the rows of replies.jsonl: one dict per reply with its ids, mode, state, question, raw reply and visible
reply. Everything here is deterministic: same rows and meta, same bytes. No clock, so no timestamp anywhere.

The report and results.json hold counts and question ids only. Reply text goes to replies.jsonl and review-sample.md,
which stay on the owner's machine (git-ignored).
"""

from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lms.core.axis_obedience import MODES, STATES, ObedienceResult, check_reply, contains_address

OUTPUT_FILES = ("report.txt", "results.json", "replies.jsonl", "review-sample.md")
VIEWS = ("raw", "visible")  # raw = what the model said (the obedience measure); visible = what the learner sees
CHECKS = ("a", "b", "c", "d")
REVIEW_PER_MODE = 10
BAR_LINE = "Obedience bar: report only on the first run; no pass mark is applied (ADR-0037 4.2)."
PROXY_LINE = (
    "A person reads each reply and asks: did it answer, or did it refuse? "
    "This is a proxy for 'no facts from memory', not proof."
)


class RunExists(FileExistsError):
    """A run folder already holds results. Nothing is overwritten."""


def default_run_name(set_version: str, made_up_version: str, temperature: float, seed: int) -> str:
    """No timestamp: the same questions, temperature and seed always give the same name (R14)."""
    return f"{set_version[:8]}-{made_up_version[:8]}-t{temperature}-s{seed}"


# --- scoring ---


def _text(row: Mapping[str, Any], view: str) -> str:
    return str(row.get("raw_reply" if view == "raw" else "visible_reply") or "")


def score_row(row: Mapping[str, Any], view: str = "raw") -> ObedienceResult:
    """Run the checker on one row. A reply that never came is scored as an empty reply, so it fails (a)."""
    reply = "" if row.get("no_reply") else _text(row, view)
    return check_reply(reply, row["mode"], row["state"], str(row.get("question") or ""), row.get("invented"))


def _empty_cell() -> Dict[str, int]:
    return {"n": 0, "obeys": 0, "a": 0, "b": 0, "c": 0, "d": 0, "no_reply": 0, "flagged": 0}


def _add(cell: Dict[str, int], row: Mapping[str, Any], result: ObedienceResult) -> None:
    cell["n"] += 1
    cell["no_reply"] += 1 if row.get("no_reply") else 0
    cell["obeys"] += 1 if result.obeys else 0
    cell["flagged"] += 1 if result.flagged else 0
    for name in CHECKS:
        # A check that does not apply (d outside Socratic) counts as passing, so a to d are comparable across modes.
        cell[name] += 1 if getattr(result, name).passed in (True, None) else 0


def _counts(rows: Sequence[Mapping[str, Any]], view: str) -> Dict[str, Dict[str, Dict[str, int]]]:
    table: Dict[str, Dict[str, Dict[str, int]]] = {}
    for row in rows:
        cell = table.setdefault(row["mode"], {}).setdefault(row["state"], _empty_cell())
        _add(cell, row, score_row(row, view))
    return table


def build_results(rows: Sequence[Mapping[str, Any]], meta: Mapping[str, Any]) -> Dict[str, Any]:
    """The numbers of one run (R14 results.json). Counts and question ids only; never a question or a reply."""
    raw = [(row, score_row(row, "raw")) for row in rows]
    failing: Dict[str, set] = {name: set() for name in (*CHECKS, "e")}
    flagged_ids: set = set()
    made_up = {"n": 0, "e": 0}
    new_terms = exact = replied = with_url = 0
    for row, result in raw:
        qid = str(row["id"])
        for name in (*CHECKS, "e"):
            if getattr(result, name).passed is False:
                failing[name].add(qid)
        if result.flagged:
            flagged_ids.add(qid)
        if not row.get("no_reply"):
            replied += 1
            exact += 1 if result.exact_wording else 0
            with_url += 1 if contains_address(_text(row, "raw")) else 0
            # (e) is scored on replies that exist: a call that failed says nothing about the made-up item.
            if row.get("invented"):
                made_up["n"] += 1
                made_up["e"] += 1 if result.e.passed else 0
        new_terms += 1 if result.f.new_terms else 0
    results: Dict[str, Any] = {k: v for k, v in meta.items()}
    results.update(
        counts={view: _counts(rows, view) for view in VIEWS},
        made_up=made_up,
        new_terms_flagged=new_terms,
        exact_wording_rate=round(exact / replied, 4) if replied else 0.0,
        failing_ids={name: sorted(ids) for name, ids in failing.items()},
        flagged_ids=sorted(flagged_ids),
        replies_with_url=with_url,
    )
    return results


# --- report.txt ---


def percent(part: int, whole: int) -> str:
    return f"{100.0 * part / whole:.1f}%" if whole else "n/a"


def _table(counts: Mapping[str, Mapping[str, Mapping[str, int]]]) -> List[str]:
    head = f"{'mode':<9} {'state':<12} {'n':>4} {'obeys':>6} {'a':>4} {'b':>4} {'c':>4} {'d':>4} {'no_reply':>8} {'flagged':>7}"
    lines = [head]
    for mode in MODES:
        for state in STATES:
            cell = counts.get(mode, {}).get(state)
            if cell:
                lines.append(
                    f"{mode:<9} {state:<12} {cell['n']:>4} {cell['obeys']:>6} {cell['a']:>4} {cell['b']:>4} "
                    f"{cell['c']:>4} {cell['d']:>4} {cell['no_reply']:>8} {cell['flagged']:>7}"
                )
    return lines


def total_obeys(counts: Mapping[str, Mapping[str, Mapping[str, int]]]) -> Tuple[int, int]:
    """(replies that obey, replies) over a whole table."""
    cells = [cell for by_state in counts.values() for cell in by_state.values()]
    return sum(c["obeys"] for c in cells), sum(c["n"] for c in cells)


def _ids_line(label: str, ids: Sequence[str]) -> str:
    return f"{label} ({len(ids)}): " + (", ".join(ids) if ids else "none")


def render_report(results: Mapping[str, Any]) -> str:
    """report.txt (R14): counts per mode and state, each check alone, the made-up score, flags and failing ids."""
    temperature = results.get("temperature")
    sent = results.get("send_temperature")
    lines = [
        "SPEC-30 answer-level obedience eval",
        "A proxy for 'no facts from memory', not proof. The model's raw reply is scored; the learner-visible reply is beside it.",
        "",
        f"Set version:     {results.get('set_version', '')}",
        f"Made-up version: {results.get('made_up_version', '')}",
        f"Profile:         {results.get('profile_id', '')}",
        f"Model answered:  {results.get('model_answered', '')}",
        f"Temperature:     {temperature}" + ("" if sent in (True, None) else " (temperature not sent by this profile)"),
        f"Seed: {results.get('seed')}   Repeat: {results.get('repeat')}",
    ]
    if results.get("stopped_early"):
        lines.append("STOPPED EARLY: this run is partial (budget refusal or Ctrl-C). Do not compare it with a full run.")
    for view, title in (("raw", "What the model said (raw reply): the obedience measure"),
                        ("visible", "What the learner sees (visible reply)")):
        counts = results["counts"][view]
        obeys, n = total_obeys(counts)
        lines += ["", title, *_table(counts), f"All: {obeys} of {n} obey ({percent(obeys, n)})"]
    made = results["made_up"]
    lines += [
        "",
        f"Exact wording of the state sentence (information only, no pass mark): {100 * results['exact_wording_rate']:.1f}%",
        f"Made-up items, check (e): {made['e']} of {made['n']} replies do not describe the invented name",
        f"New-terms flags, check (f): {results['new_terms_flagged']} replies hold a technical term the learner did not write",
        "",
        "Failing question ids per check (raw reply):",
    ]
    for name in (*CHECKS, "e"):
        lines.append(_ids_line(f"  ({name})", results["failing_ids"][name]))
    lines += ["", _ids_line("Flagged for hand review", results["flagged_ids"])]
    if results.get("replies_with_url"):  # a count only, never the address (A8)
        lines.append(f"Warning: {results['replies_with_url']} replies hold a URL. Check replies.jsonl before sharing it.")
    lines += ["", BAR_LINE, ""]
    return "\n".join(lines)


# --- review-sample.md ---


def _failed_checks(result: ObedienceResult) -> List[str]:
    return [name for name in (*CHECKS, "e") if getattr(result, name).passed is False]


def _sort_key(row: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (str(row["mode"]), str(row["state"]), str(row["id"]), int(row.get("repeat") or 0), float(row.get("temperature") or 0))


def render_review_sample(rows: Sequence[Mapping[str, Any]], seed: int) -> str:
    """Every flagged reply, plus 10 random unflagged replies per mode (R13).

    The rows are sorted first, so the same replies and seed give the same sample whatever order they arrive in.
    """
    ordered = sorted(rows, key=_sort_key)
    scored = [(row, score_row(row, "raw")) for row in ordered]
    chosen = {id(row) for row, result in scored if result.flagged}
    rng = random.Random(seed)
    for mode in sorted({str(row["mode"]) for row in ordered}):
        calm = [row for row, result in scored if not result.flagged and row["mode"] == mode]
        chosen.update(id(row) for row in rng.sample(calm, min(REVIEW_PER_MODE, len(calm))))
    lines = [
        "# Hand review",
        "",
        PROXY_LINE,
        "",
        f"Every flagged reply is here, plus up to {REVIEW_PER_MODE} unflagged replies per mode picked with seed {seed}.",
        "Local only: this file holds model text. Do not share it without reading it first.",
        "",
    ]
    for row, result in scored:
        if id(row) not in chosen:
            continue
        failed = _failed_checks(result)
        lines += [
            f"## {row['id']} | {row['mode']} | {row['state']}",
            "",
            f"Question: {row.get('question', '')}",
            "",
            "Failed checks: " + (", ".join(failed) if failed else "none"),
            "New terms: " + (", ".join(result.f.new_terms) if result.f.new_terms else "none"),
            "Raw reply:" + (f" (no reply: {row.get('error_class') or 'empty'})" if row.get("no_reply") else ""),
            "",
            "~~~~text",
            str(row.get("raw_reply") or ""),
            "~~~~",
            "",
        ]
    return "\n".join(lines)


# --- writing a run ---


def _json_bytes(data: Any) -> bytes:
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def run_folder_has_results(folder: Path) -> bool:
    return any((folder / name).exists() for name in OUTPUT_FILES)


def write_run(out_dir: Path, run_name: str, rows: Sequence[Mapping[str, Any]], meta: Mapping[str, Any]) -> Path:
    """Write the four files of R14 into out_dir/run_name and return the folder. Never overwrites a run.

    A folder that holds only estimate.json (from --estimate, A9) is not a run yet and may be used.
    Files are written as UTF-8 with LF line ends so the same run gives the same bytes on every machine.
    """
    folder = Path(out_dir) / run_name
    if run_folder_has_results(folder):
        raise RunExists(f"The run '{run_name}' already exists in {out_dir}. Choose another --run-name.")
    folder.mkdir(parents=True, exist_ok=True)
    results = build_results(rows, meta)
    seed = int(meta.get("seed", 29))
    (folder / "results.json").write_bytes(_json_bytes(results))
    (folder / "report.txt").write_bytes(render_report(results).encode("utf-8"))
    (folder / "review-sample.md").write_bytes(render_review_sample(rows, seed).encode("utf-8"))
    lines = "".join(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n" for row in rows)
    (folder / "replies.jsonl").write_bytes(lines.encode("utf-8"))  # replies as the model wrote them; local only (A8)
    return folder


# --- where a run may go ---


def _git(args: List[str], cwd: Path) -> Optional[subprocess.CompletedProcess]:
    try:
        return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None  # no git: the folder cannot be judged, so it is allowed


def out_dir_problem(path: Path) -> Optional[str]:
    """None when the folder may hold a run, else a plain reason (R14).

    A folder inside a git repository must be git-ignored (eval-out/ is). A folder outside any repository is fine.
    """
    target = Path(path).resolve()
    nearest = target
    while not nearest.exists() and nearest.parent != nearest:
        nearest = nearest.parent
    top = _git(["rev-parse", "--show-toplevel"], nearest)
    if top is None or top.returncode != 0 or not top.stdout.strip():
        return None
    root = Path(top.stdout.strip()).resolve()
    try:
        relative = target.relative_to(root)
    except ValueError:
        return None
    probe = (relative / "replies.jsonl").as_posix()
    ignored = _git(["check-ignore", "-q", "--", probe], root)
    if ignored is not None and ignored.returncode == 0:
        return None
    return (f"The folder {path} is inside the repository and is not git-ignored, so it could be committed by mistake. "
            "Use a folder under eval-out/ or outside the repository.")
