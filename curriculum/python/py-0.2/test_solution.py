"""Practice checks for Unit PY-0.2 (ungraded playground)."""

import ast
import io
from pathlib import Path
import runpy
import unittest.mock


def _source():
    path = Path("solution.py")
    if not path.exists():
        path = Path(__file__).parent / "starter.py"
    return path


def test_the_slip_is_unchanged():
    captured = io.StringIO()
    with unittest.mock.patch("sys.stdout", captured):
        runpy.run_path(str(_source()))
    assert captured.getvalue().strip() == "Asha Rao: 2 parcels (records saved: 1)"


def test_every_function_has_a_purpose_line_above_it():
    text = _source().read_text(encoding="utf-8")
    lines = text.splitlines()
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef):
            above = lines[node.lineno - 2].strip() if node.lineno >= 2 else ""
            assert above.startswith("#") and not above.startswith("# ---"), (
                f"Write a one-line comment saying what '{node.name}' does, just above 'def {node.name}'."
            )
