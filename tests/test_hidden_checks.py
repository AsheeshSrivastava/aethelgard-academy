"""Audit step A6b: hidden checks must not be readable by the learner's program (ADR-0036 amendment, SPEC-03 2.4).

Before: the hidden test code was written to run_tests.py beside the learner's file, so the
learner's program could open() it. Now the checks arrive on stdin, are compiled, and are gone
as text before the learner's module is imported. The Docker runner uses the same harness; its
isolation is tested in tests/test_docker_integration.py.
"""

import json
import logging


from lms.adapters.runner.check_harness import HARNESS, check_stdin
from lms.adapters.runner.docker_runner import DockerRunner
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.cli import handle_verify_command

from test_docker_runner import Docker  # the mocked docker CLI of the A6 tests

MARKER = "HIDDEN-MARKER-7f3a9c"
HIDDEN = f"# {MARKER}\ndef test_double():\n    assert double(2) == 4, 'double(2) should be 4'\n"
SNOOP = """
import glob, os, sys, linecache
needle = 'HIDDEN-MARKER-' + '7f3a9c'  # built at run time, so this file does not contain it
found = []
for path in glob.glob('*') + glob.glob('/work/*') + ['run_tests.py']:
    try:
        if needle in open(path, encoding='utf-8', errors='replace').read():
            found.append(path)
    except OSError:
        pass
for name in ('cmdline', 'environ'):
    try:
        if needle.encode() in open('/proc/self/' + name, 'rb').read():
            found.append('/proc/self/' + name)
    except OSError:
        pass
if any(needle in a for a in sys.argv) or any(needle in v for v in os.environ.values()):
    found.append('argv-or-env')
if any(needle in (linecache.getline(f, n) or '') for f in ('<hidden-checks>', 'run_tests.py') for n in range(1, 8)):
    found.append('linecache')
print('FOUND', found)

def double(x):
    return x * 2
"""


def test_the_harness_is_fixed_text_that_holds_no_checks():
    assert MARKER not in HARNESS
    assert "os.read(0, 1)" in HARNESS and "<hidden-checks>" in HARNESS


def test_the_checks_travel_on_the_first_stdin_line_then_the_learner_input_follows():
    payload = check_stdin(HIDDEN, "Amara\n")

    first, rest = payload.split("\n", 1)
    assert json.loads(first) == {"checks": HIDDEN}
    assert rest == "Amara\n"


def test_the_subprocess_runner_hides_the_checks_from_the_learner_program():
    result = SubprocessRunner().execute(SNOOP, test_code=HIDDEN)

    assert result.success, result.stderr
    assert "FOUND []" in result.stdout, result.stdout


def test_the_checks_still_run_and_still_fail_a_wrong_answer():
    wrong = "def double(x):\n    return x + 3\n"

    result = SubprocessRunner().execute(wrong, test_code=HIDDEN)

    assert result.success is False
    assert any("double(2) should be 4" in line for line in result.assertion_errors)
    assert MARKER not in result.stderr and "assert double(2)" not in result.stderr, "no check source in the output"


def test_checks_see_learner_input_and_real_input_still_works_after_import():
    code = "def ask():\n    return input('? ')\nname = input('top level? ')\n"
    hidden = "def test_ask():\n    assert ask() == 'Zed'\n"

    result = SubprocessRunner().execute(code, test_code=hidden, stdin_input="Zed\n")

    assert result.success, result.stderr


def test_docker_runner_puts_no_check_code_in_the_run_folder(monkeypatch):
    docker = Docker(monkeypatch)

    DockerRunner().execute("def double(x):\n    return x * 2\n", test_code=HIDDEN, stdin_input="Zed\n")

    assert MARKER not in "".join(docker.mounted.values())
    assert docker.mounted["run_tests.py"] == HARNESS
    sent = docker.proc.stdin.captured.decode()
    assert json.loads(sent.split("\n", 1)[0]) == {"checks": HIDDEN}
    assert sent.endswith("\nZed\n")


def test_docker_runner_without_checks_sends_only_the_learner_input(monkeypatch):
    docker = Docker(monkeypatch)

    DockerRunner().execute("print(input())", stdin_input="Amara\n")

    assert docker.proc.stdin.captured == b"Amara\n"
    assert "run_tests.py" not in docker.mounted


# --- lms check follows LMS_RUNNER (A6b item 2) ---


def make_unit(tmp_path):
    folder = tmp_path / "PY-0.1"
    folder.mkdir()
    (folder / "solution.py").write_text("print('hi')\n", encoding="utf-8")
    return tmp_path


def test_lms_check_refuses_with_a_clear_message_when_docker_is_down(monkeypatch, tmp_path, caplog):
    Docker(monkeypatch, info_ok=False)
    monkeypatch.setenv("LMS_RUNNER", "docker")
    ran = []
    monkeypatch.setattr(SubprocessRunner, "execute", lambda *a, **k: ran.append(1))

    with caplog.at_level(logging.INFO):
        result = handle_verify_command("PY-0.1", make_unit(tmp_path))

    assert result["success"] is False
    assert "Docker" in result["message"] and "LMS_RUNNER=subprocess" in result["message"]
    assert not ran, "the learner's file must not run outside Docker"


def test_lms_check_uses_the_subprocess_runner_only_when_asked(monkeypatch, tmp_path):
    monkeypatch.setenv("LMS_RUNNER", "subprocess")

    result = handle_verify_command("PY-0.1", make_unit(tmp_path))

    assert "Docker" not in result.get("message", "")
    assert result["message"] != "Verification failed."


def test_lms_check_runs_in_a_container_when_docker_is_the_runner(monkeypatch, tmp_path):
    docker = Docker(monkeypatch)
    monkeypatch.setenv("LMS_RUNNER", "docker")

    handle_verify_command("PY-0.1", make_unit(tmp_path))

    assert docker.popen_args, "no container was started"


# --- Review follow-ups: the checks keep the names they always had, and a learner cannot skip them ---


def test_checks_still_see_sys_path_builtins_and_main_as_before():
    hidden = (
        "def test_names():\n"
        "    assert sys.version_info[0] == 3\n"
        "    assert Path('x').name == 'x'\n"
        "    assert builtins.len([1]) == 1\n"
        "    assert __name__ == '__main__'\n"
    )

    result = SubprocessRunner().execute("x = 1\n", test_code=hidden)

    assert result.success, result.stderr


def test_a_program_that_calls_sys_exit_at_import_does_not_skip_the_checks():
    code = "import sys\nsys.exit(0)\ndef double(x):\n    return x * 2\n"

    result = SubprocessRunner().execute(code, test_code=HIDDEN)

    assert result.success is False, "the checks never ran but the run passed"
