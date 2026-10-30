"""Automated verification assertions for Unit PY-0.3."""

import io
from pathlib import Path
import runpy
import sys
import unittest.mock


def test_ai_tool_audit_and_ownership():
    solution_path = Path("solution.py")
    if not solution_path.exists():
        solution_path = Path(__file__).parent / "starter.py"

    captured_stdout = io.StringIO()

    with unittest.mock.patch("sys.stdout", captured_stdout):
        scope = runpy.run_path(str(solution_path))

    # 1. Part 1: Check whitespace stripping and clean ticket formatting
    assert "verified_name" in scope, "Missing variable 'verified_name'"
    assert scope["verified_name"] == "AMARA OKAFOR", (
        f"Expected verified_name to be 'AMARA OKAFOR', got {scope['verified_name']!r}. "
        "Did you call .strip() before .upper()?"
    )

    assert "official_ticket" in scope, "Missing variable 'official_ticket'"
    assert scope["official_ticket"] == "INTAKE-2026-AMARA OKAFOR", (
        f"Expected official_ticket to be 'INTAKE-2026-AMARA OKAFOR', got {scope['official_ticket']!r}"
    )

    # 2. Check terminal print output
    output_text = captured_stdout.getvalue()
    assert "INTAKE-2026-AMARA OKAFOR" in output_text, (
        "Output missing print of 'official_ticket'"
    )

    # 3. Part 2: Ownership Matrix (DE-3)
    assert scope.get("task_a_classification") == "DELEGATE_OK", (
        "Task A (syntax boilerplate and doc lookup) is fine to delegate to tools ('DELEGATE_OK')"
    )
    assert scope.get("task_b_classification") == "MUST_OWN", (
        "Task B (defining requirements and privacy rules) must be owned by the developer ('MUST_OWN')"
    )
    assert scope.get("task_c_classification") == "MUST_OWN", (
        "Task C (verifying edge cases and tests) must be owned by the developer ('MUST_OWN')"
    )

    # 4. Part 3: Source of Truth (DE-4)
    assert scope.get("authoritative_source") == "OFFICIAL_DOCS_AND_TESTS", (
        "Official documentation and verified tests outrank ungrounded AI chat ('OFFICIAL_DOCS_AND_TESTS')"
    )
