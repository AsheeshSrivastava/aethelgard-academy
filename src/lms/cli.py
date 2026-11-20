"""CLI for local developer workspace management.

Governed by ADR-0006:
Supports learners developing in Zed or VS Code using local `uv` environments,
pulling exercises, running local verification, and recording Evidence Ledger entries.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.docker_cli import RunnerUnavailable
from lms.adapters.runner.docker_runner import get_code_runner
from lms.core.models import (
    GRADED_PLAYGROUND_ACTIVITIES,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)


def _get_default_catalog():
    # A missing reference folder gives an empty catalog
    return load_all_roadmaps(Path("reference"))


def handle_list_command(stage: Optional[int] = None) -> str:
    """List available curriculum units."""
    catalog = _get_default_catalog()
    units = catalog.get_stage_units(stage) if stage is not None else catalog.list_all_units()

    lines = ["Available Curriculum Units:", "-" * 40]
    for u in units:
        skills = ", ".join(f"{s.skill_id} ({s.goal_level.value})" for s in u.target_skills)
        lines.append(f"[{u.unit_id}] {u.stage_label}: {u.title}")
        lines.append(f"  Concept: {u.concept_line}")
        lines.append(f"  Targets: {skills}")
        lines.append("")
    return "\n".join(lines)


def handle_pull_command(unit_id: str, target_dir: Path) -> Dict[str, Any]:
    """Pull starter code and tests for a unit into local workspace."""
    catalog = _get_default_catalog()
    unit = catalog.get_unit(unit_id)

    if not unit:
        return {"success": False, "message": f"Unit {unit_id} not found."}

    unit_dir = target_dir / unit_id
    unit_dir.mkdir(parents=True, exist_ok=True)

    solution_file = unit_dir / "solution.py"
    test_file = unit_dir / "test_solution.py"
    readme_file = unit_dir / "README.md"

    # Starter template
    starter = unit.starter_code or (
        f'"""\nUnit {unit.unit_id}: {unit.title}\n'
        f'Concept: {unit.concept_line}\n'
        f'Methods: {" -> ".join(m.value for m in unit.methods)}\n"""\n\n'
        f'# Write your implementation below\n'
    )
    if not solution_file.exists():
        solution_file.write_text(starter, encoding="utf-8")

    # Tests template
    test_content = unit.test_code or (
        f'"""Verification tests for {unit.unit_id}"""\n\n'
        f'def test_solution():\n'
        f'    # Import and verify solution\n'
        f'    pass\n'
    )
    if not test_file.exists():
        test_file.write_text(test_content, encoding="utf-8")

    # Readme with Zed / VS Code tips and video media
    media_section = ""
    if unit.media:
        m = unit.media[0]
        timestamps_str = "\n".join(f"- **{t['time']}** {t['topic']}" for t in m.timestamps)
        duration_min = (m.duration_seconds or 0) // 60
        duration_sec = (m.duration_seconds or 0) % 60
        media_section = (
            f"### Video Walkthrough\n"
            f"> **{m.title}**\n"
            f"> URL: `{m.url}` (Duration: {duration_min}m {duration_sec}s)\n\n"
            f"{timestamps_str}\n\n"
        )

    readme_content = (
        f"# {unit.unit_id}: {unit.title}\n\n"
        f"**The Concept:** {unit.concept_line}\n\n"
        f"{media_section}"
        f"### Local Editor Instructions (Zed / VS Code)\n"
        f"1. Open this folder in **Zed** (`zed .`) or **VS Code** (`code .`).\n"
        f"2. Edit `solution.py` to satisfy the requirements.\n"
        f"3. Verify locally by running: `uv run lms verify {unit.unit_id}`.\n"
    )
    readme_file.write_text(readme_content, encoding="utf-8")

    return {
        "success": True,
        "message": f"Successfully pulled {unit_id} into {unit_dir}",
        "path": str(unit_dir),
    }


def handle_verify_command(
    unit_id: str,
    workspace_dir: Path,
    learner_id: str = "default_learner",
    repo: Optional[SQLiteLearnerRepository] = None,
) -> Dict[str, Any]:
    """Verify local exercise solution against tests and log evidence."""
    unit_dir = workspace_dir / unit_id
    solution_file = unit_dir / "solution.py"
    test_file = unit_dir / "test_solution.py"

    if not solution_file.exists():
        return {"success": False, "message": f"Solution file missing at {solution_file}"}

    code = solution_file.read_text(encoding="utf-8")
    test_code = test_file.read_text(encoding="utf-8") if test_file.exists() else None

    # Follows LMS_RUNNER like the server (ADR-0036): Docker by default, and no run when Docker is down.
    try:
        result = get_code_runner().execute(code=code, test_code=test_code)
    except RunnerUnavailable:
        return {
            "success": False,
            "message": (
                "Cannot run your code: Docker is not available, and lms check runs code in Docker by default. "
                "Start Docker and run `docker pull python:3.14-slim` once. "
                "On your own machine you can opt in to running without a sandbox with LMS_RUNNER=subprocess."
            ),
        }

    if not result.success:
        return {
            "success": False,
            "message": "Verification failed.",
            "stderr": result.stderr,
            "errors": result.assertion_errors,
        }

    if repo is None:
        repo = SQLiteLearnerRepository()
        repo.initialize()

    catalog = _get_default_catalog()
    unit = catalog.get_unit(unit_id)
    repo.save_unit_progress(learner_id=learner_id, unit_id=unit_id, status="Completed")

    # The playground is ungraded practice unless the unit has Modify or Build (SPEC-12 section 3.2).
    if not (unit and unit.has_graded_playground):
        return {
            "success": True,
            "message": f"Verification passed for {unit_id}! This practice records no evidence.",
            "duration_ms": result.duration_ms,
            "evidence_logged": False,
        }

    entry = EvidenceEntry(
        learner_id=learner_id,
        unit_id=unit_id,
        skill_id=unit.target_skills[0].skill_id if unit.target_skills else "CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context=f"Local CLI verify for {unit_id}",
        observed_reasoning=f"Passed all local assertions in {result.duration_ms}ms",
        activity=next(m for m in unit.methods if m in GRADED_PLAYGROUND_ACTIVITIES),
    )
    repo.record_evidence(entry)

    return {
        "success": True,
        "message": f"Verification passed for {unit_id}! Evidence logged to ledger.",
        "duration_ms": result.duration_ms,
        "evidence_logged": True,
    }


def handle_explain_command(
    unit_id: str,
    explanation: str,
    learner_id: str = "default_learner",
    repo: Optional[SQLiteLearnerRepository] = None,
    companion: Optional[Any] = None,
) -> Dict[str, Any]:
    """Submit a CO-6 concept check explanation, have it judged (SPEC-18), and log evidence.

    Not judged (no rubric, AI off, a failed call) writes nothing and says why.
    """
    from lms.adapters.ai.local_llm_companion import get_axis_companion
    from lms.adapters.ai.providers.judging import judge_with
    from lms.adapters.curriculum.builds import answers_dir_from_env
    from lms.adapters.curriculum.rubric import load_rubric
    from lms.core import ai_judgement

    clean_unit = unit_id.upper()
    rubric = load_rubric(answers_dir_from_env(), clean_unit)
    if rubric is None:
        judgement = ai_judgement.not_judged("no_rubric")
    else:
        if companion is None:
            companion = get_axis_companion()
        judgement = judge_with(companion, clean_unit, clean_unit, explanation, rubric)

    if judgement.status != "judged":
        return {
            "success": True,
            "unit_id": clean_unit,
            "status": "not_judged",
            "feedback": judgement.message,
            "message": judgement.message,
        }

    if ai_judgement.CONCEPT_CHECK_WRITES_EVIDENCE:
        if repo is None:
            repo = SQLiteLearnerRepository()
            repo.initialize()
        met = [i.id for i in judgement.ideas if i.met]
        missed = [i.id for i in judgement.ideas if not i.met]
        repo.record_evidence(
            EvidenceEntry(
                learner_id=learner_id,
                unit_id=clean_unit,
                skill_id="CO-6",
                evidence_category=EvidenceCategory.EXPLAIN_REASON,
                evidence_strength=EvidenceStrength.STRONG if judgement.verdict == "Solid" else EvidenceStrength.WEAK,
                assistance_level=AssistanceLevel.NONE,
                demonstration_context=f"CO-6 concept check for {clean_unit}, judged by {judgement.model}",
                observed_reasoning=(
                    f"AI judged {judgement.verdict}. Ideas met: {', '.join(met) or 'none'}. "
                    f"Ideas missed: {', '.join(missed) or 'none'}."
                ),
            )
        )

    return {
        "success": True,
        "unit_id": clean_unit,
        "status": judgement.verdict,
        "feedback": judgement.feedback,
        "message": f"Judged {judgement.verdict} by {judgement.model}. AI can be wrong.",
    }


def handle_ask_command(
    unit_id: str,
    question: str,
    mode: str = "socratic",
    learner_id: str = "default_learner",
    repo: Optional[SQLiteLearnerRepository] = None,
    companion: Optional[Any] = None,
) -> Dict[str, Any]:
    """Consult AXIS AI Companion with Socratic guardrails and assistance accounting."""
    from lms.adapters.ai.local_llm_companion import get_axis_companion
    from lms.core.interfaces import AxisMode, AxisQuery
    from lms.core.models import ActivityType

    if companion is None:
        companion = get_axis_companion()

    clean_unit = unit_id.upper()
    axis_mode = (
        AxisMode.SOCRATIC
        if mode.lower() == "socratic"
        else (AxisMode.COACH if mode.lower() == "coach" else AxisMode.HYBRID)
    )

    query = AxisQuery(
        learner_id=learner_id,
        unit_id=clean_unit,
        mode=axis_mode,
        current_activity=ActivityType.BUILD,
        user_prompt=question,
    )
    response = companion.consult(query)

    # If repo provided, record inquiry interaction in ledger
    if repo is not None:
        strength = (
            EvidenceStrength.WEAK
            if response.detected_assistance_level == AssistanceLevel.SUPPLIED_REASONING
            else EvidenceStrength.MODERATE
        )
        entry = EvidenceEntry(
            learner_id=learner_id,
            unit_id=clean_unit,
            skill_id="BU-1",
            evidence_category=EvidenceCategory.PERFORM_SOLVE,
            evidence_strength=strength,
            assistance_level=response.detected_assistance_level,
            demonstration_context=f"AXIS AI consultation ({axis_mode.value}) for {clean_unit}",
            observed_reasoning=f"Question: {question[:80]} | Level: {response.detected_assistance_level.value}",
        )
        repo.record_evidence(entry)

    backend_label = getattr(companion, "last_backend_used", "Offline Mock (MOCK_AI=true)")

    return {
        "success": True,
        "unit_id": clean_unit,
        "mode": axis_mode.value,
        "backend": backend_label,
        "reply": response.reply,
        "suggested_action": response.suggested_action,
        "cited_concepts": response.cited_concepts,
        "detected_assistance_level": response.detected_assistance_level.value,
    }


def handle_index_upstream_command(
    corpus_dir: Path = Path("reference/upstream"),
    output_dir: Path = Path("data/index"),
) -> Dict[str, Any]:
    """Ingests upstream documentation, builds exact slices, and serializes artifacts."""
    from lms.adapters.ai.rag.indexer import CorpusIndexer

    indexer = CorpusIndexer(corpus_dir=corpus_dir, output_dir=output_dir)
    stats = indexer.build_and_save()
    return {
        "success": True,
        "source_count": stats["source_count"],
        "passage_count": stats["passage_count"],
        "duration_s": stats["duration_s"],
        "output_dir": str(output_dir),
        "message": (
            f"Successfully indexed {stats['source_count']} upstream sources into "
            f"{stats['passage_count']} verified passages in {stats['duration_s']}s -> {output_dir}"
        ),
    }


# --- lms report (SPEC-29) ---------------------------------------------------------------------------------

REPORT_USAGE = """Usage:
  lms report axis-modes   [--json] [--include-test-mode] [--db PATH]
  lms report axis-latency [--json] [--include-test-mode] [--trace-dir DIR]
  lms report axis-html    [--out FILE] [--include-test-mode] [--db PATH] [--trace-dir DIR]
Counts and timings only: the reports never print questions, answers or learner ids."""
_REPORT_FLAGS = {
    "axis-modes": {"--json": False, "--include-test-mode": False, "--db": True},
    "axis-latency": {"--json": False, "--include-test-mode": False, "--trace-dir": True},
    "axis-html": {"--out": True, "--include-test-mode": False, "--db": True, "--trace-dir": True},
}
DEFAULT_REPORT_PATH = "data/reports/axis-report.html"


def _parse_report_args(name: str, args):
    """(options, None) or (None, reason). A flag that needs a value must have one; anything unknown is refused."""
    allowed = _REPORT_FLAGS[name]
    options: Dict[str, Any] = {}
    i = 0
    while i < len(args):
        flag = args[i]
        if flag not in allowed:
            return None, f"Unknown option '{flag}' for {name}."
        if allowed[flag]:
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                return None, f"{flag} needs a value."
            options[flag] = args[i + 1]
            i += 2
        else:
            options[flag] = True
            i += 1
    return options, None


def _report_settings(env) -> Dict[str, Any]:
    """The hybrid-search limits in force, read the way start-up reads them; a bad value is shown as such."""
    from lms.adapters.ai.rag.startup import RetrievalConfigError, configured_rerank_concurrency, configured_timeout_s

    settings: Dict[str, Any] = {}
    for key, read in (("timeout_s", configured_timeout_s), ("concurrency", configured_rerank_concurrency)):
        try:
            settings[key] = read(env)
        except RetrievalConfigError:
            settings[key] = "invalid"
    return settings


def _read_modes(db_path: Path, include_test_mode: bool):
    """(report, status, message) with status "ok", "missing" or "error". Opens the log read-only; never creates a file."""
    import sqlite3

    from lms.core.axis_report import aggregate_modes

    if not db_path.exists():
        return aggregate_modes([], include_test_mode=include_test_mode), "missing", f"No interaction log found at {db_path}"
    try:
        repo = SQLiteLearnerRepository(str(db_path), read_only=True)
        return aggregate_modes(repo.iter_interactions(["axis", "axis_feedback"]), include_test_mode=include_test_mode), "ok", ""
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc):  # a database that has never logged anything: an empty log, not a failure
            return aggregate_modes([], include_test_mode=include_test_mode), "ok", ""
        return None, "error", f"Could not read the interaction log at {db_path} ({type(exc).__name__})."
    except (sqlite3.Error, OSError) as exc:
        return None, "error", f"Could not read the interaction log at {db_path} ({type(exc).__name__})."


def handle_report_command(args, environ=None) -> int:
    """`lms report axis-modes | axis-latency | axis-html`. Read-only; prints counts and timings only. Returns an exit code."""
    import json
    import os

    from lms.adapters.observability.report import ReportWriteError, read_trace_records, render_html, trace_files, write_html
    from lms.core.axis_report import format_latency_table, format_modes_table, summarise_latency

    env = os.environ if environ is None else environ
    if not args or args[0] not in _REPORT_FLAGS:
        print(REPORT_USAGE)
        return 2
    name = args[0]
    options, problem = _parse_report_args(name, args[1:])
    if options is None:
        print(problem)
        print(REPORT_USAGE)
        return 2
    include = bool(options.get("--include-test-mode"))
    db_path = Path(options.get("--db") or env.get("LMS_DB_PATH") or "lms_state.db")
    trace_dir = Path(options.get("--trace-dir") or env.get("LMS_TRACE_DIR") or "data/traces")

    if name == "axis-modes":
        report, state, message = _read_modes(db_path, include)
        if state != "ok":
            print(message)
            return 0 if state == "missing" else 1
        if options.get("--json"):
            print(json.dumps(report, sort_keys=True))
        else:
            print(format_modes_table(report), end="")
        return 0

    records, skipped = read_trace_records(trace_dir)
    latency = summarise_latency(records, include_test_mode=include, skipped_lines=skipped)
    settings = _report_settings(env)
    if name == "axis-latency":
        if options.get("--json"):
            print(json.dumps({**latency, "settings": settings}, sort_keys=True))
        else:
            print(format_latency_table(latency, settings), end="")
        return 0

    # axis-html
    out = Path(options.get("--out") or DEFAULT_REPORT_PATH)
    siblings = [db_path.with_name(db_path.name + suffix) for suffix in ("-wal", "-shm", "-journal")]
    protected = {p.resolve() for p in [db_path, *siblings, *trace_files(trace_dir)] if p.exists()}
    if out.resolve() in protected:
        print(f"Refusing to overwrite {out}: it is the interaction log or a trace file.")
        return 2
    report, state, message = _read_modes(db_path, include)
    if state == "error":
        print(message)
        return 1
    try:
        write_html(out, render_html(report, latency, settings))
    except ReportWriteError as exc:
        print(str(exc))
        return 1
    print(f"Report written to {out}")
    return 0

