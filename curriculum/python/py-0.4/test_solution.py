"""Automated verification assertions for Unit PY-0.4."""

import io
from pathlib import Path
import runpy
import unittest.mock


def run_script(name, ward):
    solution_path = Path("solution.py")
    if not solution_path.exists():
        # Fallback when running from unit folder directly
        solution_path = Path(__file__).parent / "starter.py"

    captured_stdout = io.StringIO()
    with unittest.mock.patch("builtins.input", side_effect=[name, ward]):
        with unittest.mock.patch("sys.stdout", captured_stdout):
            scope = runpy.run_path(str(solution_path))
    return scope, captured_stdout.getvalue()


def test_intake_registration_clean_input():
    _, output = run_script("Alice Smith", "north-01")
    assert "REGISTRATION CONFIRMED: Alice Smith [WARD-NORTH-01] TICKET-7" in output


def test_intake_registration_messy_input():
    _, output = run_script("   bob JONES   ", "  east-04  ")
    assert "REGISTRATION CONFIRMED: Bob Jones [WARD-EAST-04] TICKET-7" in output


def test_raw_values_are_cleaned_into_new_names():
    scope, _ = run_script("  carol  ", " c-12 ")
    assert scope["clean_name"] == "Carol", "Did you call .strip() and .title()?"
    assert scope["clean_ward"] == "C-12", "Did you call .strip() and .upper()?"


def test_ticket_uses_str_on_the_queue_number():
    scope, _ = run_script("Carol", "c-12")
    assert scope["queue_number"] == 7, "Keep queue_number as the number 7"
    assert scope["ticket"] == "TICKET-7", "Join 'TICKET-' and str(queue_number)"
