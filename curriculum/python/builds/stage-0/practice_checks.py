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


def check_sample_run():
    _compare(
        _slip("Meera", "housing"),
        ["", "--- CHECK-IN SLIP ---", "Name: Meera", "Service: Housing", "Please wait for the Housing desk."],
    )


def check_messy_input():
    _compare(
        _slip("   farah KHAN ", "  medical aid "),
        ["", "--- CHECK-IN SLIP ---", "Name: Farah Khan", "Service: Medical Aid", "Please wait for the Medical Aid desk."],
    )
