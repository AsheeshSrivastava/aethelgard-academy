from pathlib import Path
import pytest
from lms.cli import handle_list_command, handle_pull_command, handle_verify_command
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
        'def run_intake(name: str, ward_code: str) -> str:\n'
        '    """Process intake desk registration."""\n'
        '    clean_name = name.strip()\n'
        '    clean_ward = ward_code.strip().upper()\n'
        '    return f"REGISTRATION CONFIRMED: {clean_name} [WARD-{clean_ward}]"\n\n'
        'if __name__ == "__main__":\n'
        '    print(run_intake("Jane", "4b"))\n'
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

    # Check evidence was recorded in ledger
    ledger = repo.get_evidence_ledger(learner_id="local_dev_learner")
    assert len(ledger) > 0
