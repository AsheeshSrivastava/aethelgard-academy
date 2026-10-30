"""Automated verification assertions for Unit PY-0.1."""

import io
from pathlib import Path
import runpy
import sys
import unittest.mock


def test_intake_display_script():
    solution_path = Path("solution.py")
    if not solution_path.exists():
        # Fallback when running from unit folder directly
        solution_path = Path(__file__).parent / "starter.py"

    captured_stdout = io.StringIO()

    # Mock input() to supply a predictable name without blocking
    with unittest.mock.patch("builtins.input", return_value="Amara Okafor"):
        with unittest.mock.patch("sys.stdout", captured_stdout):
            scope = runpy.run_path(str(solution_path))

    # 1. Verify variable captured the returned string
    assert "applicant_name" in scope, "Missing variable 'applicant_name'"
    assert scope["applicant_name"] == "Amara Okafor", (
        f"Expected applicant_name to be 'Amara Okafor', got {scope['applicant_name']!r}"
    )

    # 2. Verify terminal output
    output_text = captured_stdout.getvalue()
    lines = [line.strip() for line in output_text.splitlines()]

    # Must contain the raw name print
    assert any(line == "Amara Okafor" for line in lines), (
        "Output missing raw print of applicant_name"
    )

    # Must contain comma-separated print: 'Applicant: Amara Okafor'
    assert any(line == "Applicant: Amara Okafor" for line in lines), (
        "Output missing comma-separated print: 'Applicant: Amara Okafor'"
    )

    # Must contain modern f-string print: 'Intake Record: Amara Okafor'
    assert any(line == "Intake Record: Amara Okafor" for line in lines), (
        "Output missing f-string print: 'Intake Record: Amara Okafor'"
    )

    # Must have blank separator lines produced by empty print()
    raw_lines = output_text.splitlines()
    empty_lines_count = sum(1 for line in raw_lines if line.strip() == "")
    assert empty_lines_count >= 2, (
        f"Expected at least 2 blank lines created by print(), but found {empty_lines_count}"
    )
