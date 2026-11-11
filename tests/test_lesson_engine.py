"""Tests for the interactive lesson engine, overlay loader, and learner workflow (SPEC-06)."""
import json
from pathlib import Path

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_roadmap_from_file, overlay_curriculum_packages
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.cli import handle_explain_command, handle_pull_command, handle_verify_command
from lms.core.models import (
    ActivityType,
    EvidenceCategory,
    EvidenceStrength,
)


def test_overlay_curriculum_packages():
    roadmap_path = Path("reference/Python Subject Roadmap v4.md")
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


def test_stage_0_playgrounds_need_no_functions():
    for unit in ("py-0.4", "py-0.1", "py-0.3"):
        starter = Path(f"curriculum/python/{unit}/starter.py").read_text(encoding="utf-8")

        assert "def " not in starter, unit


def test_first_unit_introduces_the_text_cleaning_tools():
    package = Path("curriculum/python/py-0.4")
    lesson = (package / "lesson.md").read_text(encoding="utf-8")
    meta = json.loads((package / "meta.json").read_text(encoding="utf-8"))
    starter = (package / "starter.py").read_text(encoding="utf-8")

    for tool in ("str(", ".strip()", ".title()", ".upper()"):
        assert tool in lesson, tool
    assert {"str()", ".strip()", ".title()", ".upper()"} <= set(meta["concepts"])
    assert "ticket" in starter and "clean_name" in starter


def test_first_lesson_warns_about_the_tools_real_traps():
    lesson = Path("curriculum/python/py-0.4/lesson.md").read_text(encoding="utf-8")

    assert "name = name.strip()" in lesson
    assert "Mcdonald" in lesson


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
        'raw_name = input("Applicant Name: ")\n'
        'raw_zone = input("Pickup Zone: ")\n'
        'clean_name = raw_name.strip().title()\n'
        'clean_zone = raw_zone.strip().upper()\n'
        'queue_number = 7\n'
        'ticket = "TICKET-" + str(queue_number)\n'
        'print(f"REGISTRATION CONFIRMED: {clean_name} [ZONE-{clean_zone}] {ticket}")\n'
    )
    solution_file.write_text(correct_code, encoding="utf-8")
    pass_res = handle_verify_command("PY-0.4", workspace, learner_id="learner_001", repo=repo)
    assert pass_res["success"] is True

    # PY-0.4 has no Modify or Build, so its playground is practice (SPEC-12 section 3.2)
    assert pass_res["evidence_logged"] is False
    assert repo.get_evidence_ledger("learner_001") == []


def test_cli_verify_logs_evidence_when_the_unit_has_a_graded_playground(tmp_path):
    workspace = tmp_path / "workspace"
    unit_dir = workspace / "PY-1.7"
    unit_dir.mkdir(parents=True)
    (unit_dir / "solution.py").write_text("x = 1\n", encoding="utf-8")
    (unit_dir / "test_solution.py").write_text(
        "def test_x():\n    assert x == 1\n", encoding="utf-8"
    )
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()

    result = handle_verify_command("PY-1.7", workspace, learner_id="learner_001", repo=repo)

    assert result["success"] is True
    assert result["evidence_logged"] is True
    entries = repo.get_evidence_ledger("learner_001")
    assert entries[0].skill_id == "BU-1"
    assert entries[0].evidence_category == EvidenceCategory.PERFORM_SOLVE
    assert entries[0].evidence_strength == EvidenceStrength.STRONG
    assert entries[0].activity == ActivityType.MODIFY


def test_cli_concept_check_soft_gate(tmp_path):
    db_path = tmp_path / "test_ledger.db"
    repo = SQLiteLearnerRepository(db_path=db_path)
    repo.initialize()

    # Solid explanation
    res_solid = handle_explain_command(
        unit_id="PY-0.4",
        explanation="The input function always gives back text, a string. Doing math on that text without converting it to a number stops with an error.",
        learner_id="learner_001",
        repo=repo,
        companion=MockAxisCompanion(),
    )
    assert res_solid["success"] is True
    assert res_solid["status"] == "Solid"

    # Shaky explanation (warns, records, does not crash)
    res_shaky = handle_explain_command(
        unit_id="PY-0.4",
        explanation="It takes stuff from the keyboard.",
        learner_id="learner_002",
        repo=repo,
        companion=MockAxisCompanion(),
    )
    assert res_shaky["success"] is True
    assert res_shaky["status"] == "Shaky"

    # Verify both recorded in Evidence Ledger
    entries_1 = repo.get_evidence_ledger("learner_001")
    assert any(e.evidence_category == EvidenceCategory.EXPLAIN_REASON for e in entries_1)

    entries_2 = repo.get_evidence_ledger("learner_002")
    assert any(e.evidence_strength == EvidenceStrength.WEAK for e in entries_2)
