"""CLI for local developer workspace management.

Governed by ADR-0006:
Supports learners developing in Zed or VS Code using local `uv` environments,
pulling exercises, running local verification, and recording Evidence Ledger entries.
"""

from pathlib import Path
import sys
from typing import Any, Dict, Optional

from lms.adapters.curriculum.loader import load_roadmap_from_file
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.core.models import (
    AssistanceLevel,
    ConceptCheck,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)


def _get_default_catalog():
    roadmap_path = Path("reference/Python Subject Roadmap v3.md")
    if not roadmap_path.exists():
        # Fallback to empty catalog if file missing
        from lms.adapters.curriculum.loader import CurriculumCatalog
        return CurriculumCatalog()
    return load_roadmap_from_file(roadmap_path)


def handle_list_command(stage: Optional[int] = None) -> str:
    """List available curriculum units."""
    catalog = _get_default_catalog()
    units = catalog.get_stage_units(stage) if stage is not None else catalog.list_all_units()

    lines = ["Available Curriculum Units:", "-" * 40]
    for u in units:
        skills = ", ".join(f"{s.skill_id} ({s.goal_level.value})" for s in u.target_skills)
        lines.append(f"[{u.unit_id}] Stage {u.stage}: {u.title}")
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

    runner = SubprocessRunner()
    result = runner.execute(code=code, test_code=test_code)

    if not result.success:
        return {
            "success": False,
            "message": "Verification failed.",
            "stderr": result.stderr,
            "errors": result.assertion_errors,
        }

    # Record evidence in repository
    if repo is None:
        repo = SQLiteLearnerRepository()
        repo.initialize()

    catalog = _get_default_catalog()
    unit = catalog.get_unit(unit_id)
    skill_id = unit.target_skills[0].skill_id if (unit and unit.target_skills) else "CO-1"

    entry = EvidenceEntry(
        learner_id=learner_id,
        unit_id=unit_id,
        skill_id=skill_id,
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context=f"Local CLI verify for {unit_id}",
        observed_reasoning=f"Passed all local assertions in {result.duration_ms}ms",
    )
    repo.record_evidence(entry)
    repo.save_unit_progress(learner_id=learner_id, unit_id=unit_id, status="Completed")

    return {
        "success": True,
        "message": f"Verification passed for {unit_id}! Evidence logged to ledger.",
        "duration_ms": result.duration_ms,
    }


def handle_explain_command(
    unit_id: str,
    explanation: str,
    learner_id: str = "default_learner",
    repo: Optional[SQLiteLearnerRepository] = None,
    companion: Optional[Any] = None,
) -> Dict[str, Any]:
    """Submit CO-6 concept check explanation, evaluate mental model, and log evidence."""
    import json
    from lms.adapters.ai.local_llm_companion import get_axis_companion

    clean_unit = unit_id.upper()
    meta_path = Path(f"curriculum/python/{clean_unit.lower()}/meta.json")
    keywords = ["string", "text", "typeerror", "convert", "int"]
    concept_line = "A program takes input, transforms it, and produces output; input() always returns a string."
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            check_cfg = meta.get("concept_check", {})
            if "solid_keywords" in check_cfg:
                keywords = check_cfg["solid_keywords"]
            if "concept_line" in check_cfg:
                concept_line = check_cfg["concept_line"]
        except Exception:
            pass

    if companion is None:
        companion = get_axis_companion()

    if hasattr(companion, "evaluate_concept_check"):
        eval_res = companion.evaluate_concept_check(
            unit_id=clean_unit,
            concept_line=concept_line,
            explanation=explanation,
            solid_keywords=keywords,
        )
        status = eval_res["status"]
        feedback = eval_res["feedback"]
        is_solid = status == "Solid"
    else:
        # Deterministic keyword rubric when using MockAxisCompanion
        lower_exp = explanation.lower()
        matches = sum(1 for kw in keywords if kw.lower() in lower_exp)
        is_solid = matches >= 2
        status = "Solid" if is_solid else "Shaky"
        feedback = (
            "Explanation demonstrates solid operational mental model."
            if is_solid
            else "Explanation is emerging or shaky; remember to reflect on types and boundaries."
        )

    strength = EvidenceStrength.STRONG if is_solid else EvidenceStrength.WEAK

    if repo is None:
        repo = SQLiteLearnerRepository()
        repo.initialize()

    entry = EvidenceEntry(
        learner_id=learner_id,
        unit_id=clean_unit,
        skill_id="CO-6",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=strength,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context=f"CO-6 concept check explanation for {clean_unit}",
        observed_reasoning=f"Mental model graded as {status}: {explanation[:120]}",
    )
    repo.record_evidence(entry)

    return {
        "success": True,
        "unit_id": clean_unit,
        "status": status,
        "feedback": feedback,
        "message": f"Concept explanation evaluated as {status}. Evidence recorded in ledger.",
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

