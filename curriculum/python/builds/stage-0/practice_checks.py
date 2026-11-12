"""Practice checks for the Stage 0 build (SPEC-15, ADR-0021). Public: read them, run them, learn from them.

The checks that grade your build are hidden and use other inputs, so a script
written only to pass these will not pass those.
"""

import io
from pathlib import Path
import runpy
import unittest.mock


def _slip(name, service):
    """The script's output for two answers, as lines."""
    captured = io.StringIO()
    answers = unittest.mock.patch("builtins.input", side_effect=[name, service])
    stdout = unittest.mock.patch("sys.stdout", captured)
    try:
        with answers, stdout:
            runpy.run_path(str(Path("solution.py")))
    except StopIteration:
        raise AssertionError("The script asked for more than two answers.")
    except SystemExit:
        raise AssertionError("The script stopped itself before it finished.")
    return captured.getvalue().rstrip("\n").split("\n")


def _compare(lines, expected):
    for number, wanted in enumerate(expected, start=1):
        got = lines[number - 1] if number <= len(lines) else "nothing"
        assert got == wanted, f"Output line {number} should be '{wanted}', but it was '{got}'."
    assert len(lines) == len(expected), f"The output should have {len(expected)} lines, but it has {len(lines)}."


TICKET_LINES = ["Your ticket: 41", "Desk counter now at: 42"]


def check_sample_run():
    _compare(
        _slip("Meera", "food parcel"),
        ["", "--- CHECK-IN SLIP ---", "Name: Meera", "Service: Food Parcel", "Please wait for the Food Parcel desk."]
        + TICKET_LINES,
    )


def check_messy_input():
    _compare(
        _slip("   farah KHAN ", "  baby supplies "),
        ["", "--- CHECK-IN SLIP ---", "Name: Farah Khan", "Service: Baby Supplies", "Please wait for the Baby Supplies desk."]
        + TICKET_LINES,
    )


def check_ticket_counter():
    source = Path("solution.py").read_text(encoding="utf-8")
    assert "ticket = ticket + 1" in source or "ticket += 1" in source, (
        "Keep the counter line that adds 1 to ticket. Fix the bug; do not print the numbers by hand."
    )
    try:
        lines = _slip("Meera", "food parcel")
    except TypeError:
        raise AssertionError("The script stops with a TypeError. Read the error's last line and the line it points to.")
    assert lines[-2:] == TICKET_LINES, (
        f"The last two lines should be '{TICKET_LINES[0]}' and '{TICKET_LINES[1]}', but they were {lines[-2:]}."
    )
