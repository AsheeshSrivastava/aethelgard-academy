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
    starter = (
        f'"""\nUnit {unit.unit_id}: {unit.title}\n'
        f'Concept: {unit.concept_line}\n'
        f'Methods: {" -> ".join(m.value for m in unit.methods)}\n"""\n\n'
        f'# Write your implementation below\n'
    )
    if not solution_file.exists():
        solution_file.write_text(starter, encoding="utf-8")

    # Tests template
    test_content = (
        f'"""Verification tests for {unit.unit_id}"""\n\n'
        f'def test_solution():\n'
        f'    # Import and verify solution\n'
        f'    pass\n'
    )
    if not test_file.exists():
        test_file.write_text(test_content, encoding="utf-8")

    # Readme with Zed / VS Code tips
    readme_content = (
        f"# {unit.unit_id}: {unit.title}\n\n"
        f"**The Concept:** {unit.concept_line}\n\n"
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
