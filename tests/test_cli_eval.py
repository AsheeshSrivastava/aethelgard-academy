"""SPEC-30 tests, part 5: the `lms eval axis-obedience` command line.

Covers ADR-0037 section 2.5 / SPEC-30 R9 (command and options), R12 (MOCK_AI refusal, --replay) and section 3
(handler in src/lms/cli.py, a line in the `lms` dispatcher). Offline: `run_eval` is replaced by a recorder, except in the
two tests that use --replay or the MOCK_AI refusal, which never reach a model.

Names under test (SPEC-30 section 3 gives the handler's place; the rest is this suite's contract, see the phase 1 report):
  lms.cli.handle_eval_command(args, environ=None) -> int     args start with "axis-obedience"
  lms.cli.EVAL_USAGE                                          the usage text (holds "lms eval axis-obedience")
  The handler reaches `lms.adapters.ai.obedience.harness.run_eval` through the module, at call time, so a test can
  replace it. EvalOptions fields: profile, temperatures (tuple of float), modes, states, sets (tuples of str), quick,
  repeat, seed, run_name, out_dir, estimate, paid_ok, replay.
"""

import json
import sys
from pathlib import Path

import pytest

from obedience_corpus import MODES, STATES
from obedience_support import make_row

ALL_FLAGS = ["--profile", "--temperature", "--temperatures", "--modes", "--states", "--sets", "--quick", "--repeat",
             "--seed", "--run-name", "--out-dir", "--estimate", "--paid-ok", "--replay"]


@pytest.fixture
def recorder(monkeypatch):
    """Replace run_eval with a recorder; `recorder.code` is what it returns."""
    from lms.adapters.ai.obedience import harness

    class Recorder:
        code = 0

        def __init__(self):
            self.options = []

    rec = Recorder()

    def fake_run_eval(options, **kwargs):
        rec.options.append(options)
        return rec.code

    monkeypatch.setattr(harness, "run_eval", fake_run_eval)
    return rec


def handle(args, **kwargs):
    from lms.cli import handle_eval_command

    return handle_eval_command(args, **kwargs)


def test_eval_subcommand_and_flags(recorder, tmp_path):
    assert handle(["axis-obedience"]) == 0
    (defaults,) = recorder.options
    assert tuple(defaults.temperatures) == (0.0,) and defaults.seed == 29 and defaults.repeat == 1
    assert defaults.quick is False and defaults.estimate is False and defaults.paid_ok is False
    assert defaults.replay is None and defaults.run_name is None
    assert set(defaults.modes) == set(MODES) and set(defaults.states) == set(STATES)

    recorder.options.clear()
    args = ["axis-obedience", "--profile", "p1", "--temperature", "0.5", "--modes", "Socratic,Coach",
            "--states", "no_index,unavailable", "--sets", "pytest-docs,uv-docs", "--quick", "--repeat", "3",
            "--seed", "7", "--run-name", "r-1", "--out-dir", str(tmp_path / "o"), "--estimate", "--paid-ok",
            "--replay", str(tmp_path / "in.jsonl")]
    assert handle(args) == 0
    (options,) = recorder.options
    assert options.profile == "p1"
    assert tuple(options.temperatures) == (0.5,)
    assert tuple(options.modes) == ("Socratic", "Coach")
    assert tuple(options.states) == ("no_index", "unavailable")
    assert tuple(options.sets) == ("pytest-docs", "uv-docs")
    assert options.quick is True and options.repeat == 3 and options.seed == 7 and options.run_name == "r-1"
    assert Path(options.out_dir) == tmp_path / "o" and Path(options.replay) == tmp_path / "in.jsonl"
    assert options.estimate is True and options.paid_ok is True


def test_eval_comparison_flag_takes_a_list_of_temperatures(recorder):
    assert handle(["axis-obedience", "--temperatures", "0.0,0.2"]) == 0

    assert tuple(recorder.options[0].temperatures) == (0.0, 0.2)


def test_the_exit_code_of_the_run_is_returned(recorder):
    recorder.code = 3

    assert handle(["axis-obedience", "--quick"]) == 3


@pytest.mark.parametrize("args", [
    [],
    ["nonsense"],
    ["axis-obedience", "--no-such-flag"],
    ["axis-obedience", "extra-positional"],
    ["axis-obedience", "--repeat"],
    ["axis-obedience", "--repeat", "6"],
    ["axis-obedience", "--repeat", "0"],
    ["axis-obedience", "--repeat", "x"],
    ["axis-obedience", "--seed", "x"],
    ["axis-obedience", "--temperature", "abc"],
    ["axis-obedience", "--temperatures", "0.0,abc"],
    ["axis-obedience", "--out-dir"],
    ["axis-obedience", "--quick", "--bogus"],
])
def test_unknown_option_prints_usage_and_fails(recorder, capsys, args):
    code = handle(args)

    out = capsys.readouterr().out
    assert code != 0
    assert "lms eval axis-obedience" in out
    for flag in ALL_FLAGS:
        assert flag in out
    assert recorder.options == []  # nothing was run


def test_eval_is_wired_into_the_lms_dispatcher_and_help(recorder, monkeypatch, capsys):
    import lms

    monkeypatch.setattr(sys, "argv", ["lms", "eval", "axis-obedience", "--quick", "--seed", "5"])
    lms.main()
    assert recorder.options[0].quick is True and recorder.options[0].seed == 5

    recorder.code = 2
    monkeypatch.setattr(sys, "argv", ["lms", "eval", "axis-obedience"])
    with pytest.raises(SystemExit) as info:
        lms.main()
    assert info.value.code == 2

    for argv in (["lms", "eval"], ["lms", "eval", "bogus"]):
        monkeypatch.setattr(sys, "argv", argv)
        with pytest.raises(SystemExit) as info:
            lms.main()
        assert info.value.code not in (0, None)
        assert "lms eval axis-obedience" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["lms", "--help"])
    lms.main()
    assert "lms eval axis-obedience" in capsys.readouterr().out


def test_mock_ai_refusal_reaches_the_user_through_the_command(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("MOCK_AI", "true")

    code = handle(["axis-obedience", "--out-dir", str(tmp_path / "out")])

    assert code != 0
    assert "Set MOCK_AI=false to run against a real model. The checker alone runs with --replay." in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_replay_through_the_command_needs_no_model(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("MOCK_AI", "true")
    source = tmp_path / "replies.jsonl"
    rows = [make_row("q1", "Hybrid", "not_found"), make_row("q2", "Coach", "no_index")]
    source.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

    code = handle(["axis-obedience", "--replay", str(source), "--out-dir", str(tmp_path / "out"), "--run-name", "rp"])

    assert code == 0, capsys.readouterr().out
    assert (tmp_path / "out" / "rp" / "report.txt").is_file()
    assert (tmp_path / "out" / "rp" / "results.json").is_file()
