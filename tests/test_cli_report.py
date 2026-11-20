"""SPEC-29 tests, part E: the `lms report` command (section 3 of the spec)."""

import sys

import pytest

from test_axis_report import ev, seed_db


def run(args, capsys=None):
    from lms.cli import handle_report_command

    return handle_report_command(args)


def test_report_subcommands_and_flags(tmp_path, capsys):
    db = seed_db(tmp_path, [ev("t1")])
    traces = tmp_path / "traces"

    assert run(["axis-modes", "--db", str(db)]) == 0
    assert run(["axis-modes", "--db", str(db), "--json", "--include-test-mode"]) == 0
    assert run(["axis-latency", "--trace-dir", str(traces), "--json", "--include-test-mode"]) == 0
    assert run(["axis-html", "--out", str(tmp_path / "r.html"), "--db", str(db), "--trace-dir", str(traces), "--include-test-mode"]) == 0
    capsys.readouterr()


@pytest.mark.parametrize("args", [
    [], ["nonsense"], ["axis-modes", "--no-such-flag"], ["axis-latency", "--db", "x"], ["axis-modes", "--out", "x"],
    ["axis-modes", "--db"], ["axis-html", "--out"], ["axis-modes", "extra-positional"],
])
def test_unknown_report_or_flag_prints_usage_and_fails(args, capsys):
    code = run(args)

    out = capsys.readouterr().out
    assert code != 0 and "lms report" in out and "axis-modes" in out and "axis-latency" in out and "axis-html" in out


def test_axis_modes_cli_prints_the_header_and_tables(tmp_path, capsys):
    db = seed_db(tmp_path, [ev("t1", "Coach"), ev("t2", "Socratic", unit="PY-0.2")])

    assert run(["axis-modes", "--db", str(db)]) == 0
    out = capsys.readouterr().out

    assert "Weeks run Monday to Sunday, UTC." in out
    assert "Coach" in out and "Socratic" in out and "PY-0.2" in out and "2026-11-16" in out


def test_db_defaults_to_lms_db_path(tmp_path, monkeypatch, capsys):
    db = seed_db(tmp_path, [ev("t1", "Hybrid")])
    monkeypatch.setenv("LMS_DB_PATH", str(db))

    assert run(["axis-modes", "--json"]) == 0

    assert '"Hybrid"' in capsys.readouterr().out


def test_trace_dir_defaults_to_lms_trace_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LMS_TRACE_DIR", str(tmp_path / "somewhere"))

    assert run(["axis-latency"]) == 0

    assert "No traces recorded yet." in capsys.readouterr().out


def test_report_is_wired_into_the_lms_dispatcher(tmp_path, monkeypatch, capsys):
    import lms

    db = seed_db(tmp_path, [ev("t1")])
    monkeypatch.setattr(sys, "argv", ["lms", "report", "axis-modes", "--db", str(db)])

    lms.main()

    assert "Weeks run Monday to Sunday, UTC." in capsys.readouterr().out


def test_help_lists_the_report_command(monkeypatch, capsys):
    import lms

    monkeypatch.setattr(sys, "argv", ["lms", "--help"])

    lms.main()

    assert "lms report" in capsys.readouterr().out
