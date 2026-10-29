"""Tests for the interactive lesson engine, overlay loader, and learner workflow (SPEC-06)."""
from pathlib import Path
import pytest

from lms.adapters.curriculum.loader import load_roadmap_from_file, overlay_curriculum_packages
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.cli import handle_explain_command, handle_pull_command, handle_verify_command
from lms.core.models import (
    ActivityType,
    EvidenceCategory,
    EvidenceStrength,
    ProficiencyLevel,
)


def test_overlay_curriculum_packages():
    roadmap_path = Path("reference/Python Subject Roadmap v3.md")
    catalog = load_roadmap_from_file(roadmap_path)
    curriculum_dir = Path("curriculum")

    overlay_curriculum_packages(catalog, curriculum_dir)
    unit = catalog.get_unit("PY-0.4")

    assert unit is not None
    assert unit.unit_id == "PY-0.4"
    assert unit.starter_code is not None
    assert "input(" in unit.starter_code
    assert unit.test_code is not None
    assert "test_intake_registration" in unit.test_code
    assert len(unit.media) >= 1
    assert unit.media[0].kind == "video"
    assert "Running Your First Program" in unit.media[0].title
    assert len(unit.media[0].timestamps) >= 3


def test_cli_pull_authored_lesson(tmp_path):
    workspace = tmp_path / "workspace"
    result = handle_pull_command("PY-0.4", workspace)

    assert result["success"] is True
    unit_dir = workspace / "PY-0.4"
    assert (unit_dir / "solution.py").exists()
    assert (unit_dir / "test_solution.py").exists()
    assert (unit_dir / "README.md").exists()

    readme_text = (unit_dir / "README.md").read_text(encoding="utf-8")
    assert "PY-0.4: Run a first program" in readme_text
    assert "Video Walkthrough" in readme_text
    assert "Zed" in readme_text and "VS Code" in readme_text


def test_cli_verify_authored_lesson(tmp_path):
    workspace = tmp_path / "workspace"
    handle_pull_command("PY-0.4", workspace)
    unit_dir = workspace / "PY-0.4"
    solution_file = unit_dir / "solution.py"

    db_path = tmp_path / "test_ledger.db"
    repo = SQLiteLearnerRepository(db_path=db_path)
    repo.initialize()

    # 1. Incomplete solution fails
    solution_file.write_text("# broken code\nprint('incomplete')\n", encoding="utf-8")
    fail_res = handle_verify_command("PY-0.4", workspace, learner_id="learner_001", repo=repo)
    assert fail_res["success"] is False

    # 2. Correct implementation passes
    correct_code = (
        'def run_intake(name: str, ward_code: str) -> str:\n'
        '    """Process intake desk registration."""\n'
        '    clean_name = name.strip()\n'
        '    clean_ward = ward_code.strip().upper()\n'
        '    return f"REGISTRATION CONFIRMED: {clean_name} [WARD-{clean_ward}]"\n\n'
        'if __name__ == "__main__":\n'
        '    user_name = input("Applicant Name: ")\n'
        '    ward = input("Ward Code: ")\n'
        '    print(run_intake(user_name, ward))\n'
    )
    solution_file.write_text(correct_code, encoding="utf-8")
    pass_res = handle_verify_command("PY-0.4", workspace, learner_id="learner_001", repo=repo)
    assert pass_res["success"] is True

    # Check evidence was logged to ledger
    entries = repo.get_evidence_ledger("learner_001")
    assert len(entries) >= 1
    assert entries[0].skill_id == "CO-1"
    assert entries[0].evidence_category == EvidenceCategory.PERFORM_SOLVE
    assert entries[0].evidence_strength == EvidenceStrength.STRONG


def test_cli_concept_check_soft_gate(tmp_path):
    db_path = tmp_path / "test_ledger.db"
    repo = SQLiteLearnerRepository(db_path=db_path)
    repo.initialize()

    # Solid explanation
    res_solid = handle_explain_command(
        unit_id="PY-0.4",
        explanation="The input function always returns a string data type. If we do math directly on it without converting via int(), Python raises a TypeError.",
        learner_id="learner_001",
        repo=repo,
    )
    assert res_solid["success"] is True
    assert res_solid["status"] == "Solid"

    # Shaky explanation (warns, records, does not crash)
    res_shaky = handle_explain_command(
        unit_id="PY-0.4",
        explanation="It takes stuff from the keyboard.",
        learner_id="learner_002",
        repo=repo,
    )
    assert res_shaky["success"] is True
    assert res_shaky["status"] == "Shaky"

    # Verify both recorded in Evidence Ledger
    entries_1 = repo.get_evidence_ledger("learner_001")
    assert any(e.evidence_category == EvidenceCategory.EXPLAIN_REASON for e in entries_1)

    entries_2 = repo.get_evidence_ledger("learner_002")
    assert any(e.evidence_strength == EvidenceStrength.WEAK for e in entries_2)
