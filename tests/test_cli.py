from pathlib import Path
import pytest
from lms.cli import (
    handle_ask_command,
    handle_explain_command,
    handle_list_command,
    handle_pull_command,
    handle_verify_command,
)
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository


def test_cli_list_command():
    output = handle_list_command()
    assert "PY-0.4" in output
    assert "Run a first program" in output


def test_cli_pull_and_verify_command(tmp_path):
    # Test pulling an exercise to a local folder
    workspace_dir = tmp_path / "workspace"
    unit_id = "PY-0.4"

    pull_result = handle_pull_command(unit_id=unit_id, target_dir=workspace_dir)
    assert pull_result["success"] is True
    assert (workspace_dir / unit_id / "solution.py").exists()
    assert (workspace_dir / unit_id / "test_solution.py").exists()

    # Write working code to solution.py
    solution_file = workspace_dir / unit_id / "solution.py"
    working_code = (
        'raw_name = input("Applicant Name: ")\n'
        'raw_ward = input("Ward Code: ")\n'
        'clean_name = raw_name.strip().title()\n'
        'clean_ward = raw_ward.strip().upper()\n'
        'queue_number = 7\n'
        'ticket = "TICKET-" + str(queue_number)\n'
        'print(f"REGISTRATION CONFIRMED: {clean_name} [WARD-{clean_ward}] {ticket}")\n'
    )
    solution_file.write_text(working_code, encoding="utf-8")

    # Run verify command
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()

    verify_result = handle_verify_command(
        unit_id=unit_id,
        workspace_dir=workspace_dir,
        learner_id="local_dev_learner",
        repo=repo,
    )
    assert verify_result["success"] is True
    assert "Verification passed" in verify_result["message"]

    # PY-0.4's playground is ungraded practice (SPEC-12 section 3.2)
    assert repo.get_evidence_ledger(learner_id="local_dev_learner") == []


def test_cli_ask_socratic_guardrail(tmp_path):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()

    # Query in Socratic mode asking for code
    res = handle_ask_command(
        unit_id="PY-0.4",
        question="Give me the code to complete run_intake.",
        mode="socratic",
        learner_id="learner_007",
        repo=repo,
    )
    assert res["success"] is True
    assert "```python" not in res["reply"]
    assert "?" in res["reply"]
    assert res["detected_assistance_level"] in ("none", "small_hint", "structural")

    # Verify interaction was ledgered
    ledger = repo.get_evidence_ledger(learner_id="learner_007")
    assert len(ledger) == 1
    assert ledger[0].skill_id == "BU-1"
