"""Audit step A6: the Docker runner against a real Docker daemon (ADR-0036).

Runs only where `docker` answers and the python:3.14-slim image is already pulled; everywhere
else (CI included) it is skipped. Run it by hand with:  uv run pytest -m docker -q
"""

import os
from pathlib import Path
import shutil
import subprocess
import time

import pytest

from lms.adapters.runner.docker_cli import IMAGE
from lms.adapters.runner.docker_runner import DockerRunner
from lms.adapters.runner.interactive import RunLimits


def docker_ready() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True, timeout=15).returncode == 0
    except Exception:
        return False


pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(not docker_ready(), reason=f"Docker is not reachable or {IMAGE} is not pulled"),
]


def leftover_containers() -> str:
    out = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=lms-run-", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=15
    )
    return out.stdout.strip()


@pytest.fixture
def runner():
    return DockerRunner()


def test_a_plain_program_runs_and_prints(runner):
    result = runner.execute("print('hello from docker')")
    assert result.success and result.stdout.strip() == "hello from docker"


def test_input_comes_from_stdin(runner):
    result = runner.execute("print('Hi ' + input())", stdin_input="Amara\n")
    assert result.stdout.strip() == "Hi Amara"


def test_tests_run_against_the_solution(runner):
    result = runner.execute(
        "def double(x):\n    return x * 2\n",
        test_code="def test_double():\n    assert double(2) == 5, 'wrong'\n",
    )
    assert result.success is False and result.assertion_errors


def test_extra_files_can_be_imported(runner):
    result = runner.execute("from slip import X\nprint(X)", files={"slip.py": "X = 41 + 1\n"})
    assert result.stdout.strip() == "42"


def test_the_network_is_blocked(runner):
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 80), timeout=2)\n"
        "    print('CONNECTED')\n"
        "except OSError as e:\n"
        "    print('BLOCKED')\n"
    )
    assert runner.execute(code, timeout_seconds=10).stdout.strip() == "BLOCKED"


def test_writes_are_blocked_except_in_tmp(runner):
    code = (
        "for path in ('/work/x.txt', '/etc/x.txt', '/usr/x.txt'):\n"
        "    try:\n"
        "        open(path, 'w').write('x'); print('WROTE', path)\n"
        "    except OSError:\n"
        "        print('BLOCKED', path)\n"
        "open('/tmp/ok.txt', 'w').write('x'); print('TMP OK')\n"
    )
    out = runner.execute(code).stdout
    assert "WROTE" not in out and out.count("BLOCKED") == 3 and "TMP OK" in out


def test_files_in_tmp_cannot_be_executed(runner):
    code = (
        "import os, shutil, subprocess\n"
        "shutil.copy('/bin/true', '/tmp/t')\nos.chmod('/tmp/t', 0o755)\n"
        "try:\n    subprocess.run(['/tmp/t']); print('EXECUTED')\nexcept OSError:\n    print('NOEXEC')\n"
    )
    assert runner.execute(code).stdout.strip() == "NOEXEC"


def test_the_program_is_not_root_and_has_no_capabilities(runner):
    out = runner.execute("import os\nprint(os.getuid())\nprint(open('/proc/self/status').read())").stdout
    assert out.splitlines()[0] == "65534"
    assert "CapEff:\t0000000000000000" in out


def test_memory_is_limited(runner):
    result = runner.execute("data = bytearray(900 * 1024 * 1024)\nprint('ALLOCATED')", timeout_seconds=20)
    assert "ALLOCATED" not in result.stdout and result.success is False


def test_a_fork_bomb_is_contained(runner):
    code = (
        "import os, time\n"
        "made = 0\n"
        "try:\n"
        "    while True:\n"
        "        if os.fork() == 0:\n"
        "            time.sleep(30); os._exit(0)\n"
        "        made += 1\n"
        "except OSError:\n"
        "    print('LIMIT', made, flush=True)\n"
        "    os._exit(0)\n"
    )
    result = runner.execute(code, timeout_seconds=15)
    assert "LIMIT" in result.stdout, result
    assert int(result.stdout.split()[1]) < 64
    time.sleep(1)
    assert leftover_containers() == ""


def test_an_infinite_loop_times_out_and_leaves_no_container(runner):
    started = time.monotonic()
    result = runner.execute("while True:\n    pass\n", timeout_seconds=1.0)

    assert result.success is False and "timed out" in result.stderr.lower()
    assert time.monotonic() - started < 15
    assert leftover_containers() == ""


def test_output_is_capped(runner):
    result = runner.execute("while True:\n    print('x' * 1000)\n", timeout_seconds=10)
    assert len(result.stdout.encode()) <= 64 * 1024
    assert leftover_containers() == ""


def test_no_host_environment_or_files_are_visible(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("LMS_A6_SECRET", "do-not-leak")
    host_file = tmp_path / "host-secret.txt"
    host_file.write_text("secret", encoding="utf-8")
    code = (
        "import os\n"
        "print('SECRET' if any('do-not-leak' in v for v in os.environ.values()) else 'NO-ENV-LEAK')\n"
        f"print('FILE' if os.path.exists({str(host_file)!r}) else 'NO-HOST-FILE')\n"
        f"print('REPO' if os.path.exists({str(Path(__file__).resolve().parents[1])!r}) else 'NO-REPO')\n"
        "print(sorted(os.listdir('/work')))\n"
    )
    out = runner.execute(code).stdout.split("\n")
    assert out[:3] == ["NO-ENV-LEAK", "NO-HOST-FILE", "NO-REPO"]
    assert out[3] == "['run_tests.py', 'solution.py']" or out[3] == "['solution.py']"


def test_interactive_input_round_trip_and_cleanup(runner):
    run = runner.start_interactive(
        {"solution.py": "name = input('Name? ')\nprint('Hi ' + name)\n"}, "solution.py", RunLimits(wall_seconds=30)
    )
    seen, deadline = [], time.monotonic() + 40
    while time.monotonic() < deadline:
        event = run.next_event(0.2)
        if event is None:
            continue
        seen.append(event)
        if event["type"] == "awaiting_input":
            run.send_stdin("Amara")
        if event["type"] == "exit":
            break
    assert "Hi Amara" in "".join(e.get("data", "") for e in seen if e["type"] == "stdout")
    assert seen[-1]["code"] == 0
    assert leftover_containers() == ""


def test_stopping_an_interactive_run_removes_the_container(runner):
    run = runner.start_interactive({"solution.py": "import time\ntime.sleep(60)\n"}, "solution.py", RunLimits())
    time.sleep(2)
    run.stop()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and leftover_containers():
        time.sleep(0.5)
    assert leftover_containers() == ""


def test_the_interactive_wall_clock_limit_kills_the_container(runner):
    run = runner.start_interactive(
        {"solution.py": "while True:\n    pass\n"}, "solution.py", RunLimits(wall_seconds=2, cpu_seconds=60)
    )
    deadline, last = time.monotonic() + 30, None
    while time.monotonic() < deadline:
        event = run.next_event(0.2)
        if event and event["type"] == "exit":
            last = event
            break
    assert last and last["timed_out"] is True
    assert leftover_containers() == ""


def test_the_environment_variable_of_the_cli_does_not_reach_the_container(runner):
    assert "LMS_RUNNER" not in runner.execute("import os\nprint(dict(os.environ))").stdout
    assert os.environ.get("PATH")



# --- A6b: the learner's program cannot find the hidden checks (ADR-0036 amendment, SPEC-03 2.4) ---

HIDDEN_MARKER = "HIDDEN-MARKER-7f3a9c"
HIDDEN_CHECKS = f"# {HIDDEN_MARKER}\ndef test_double():\n    assert double(2) == 4, 'double(2) should be 4'\n"

SNOOP = """
import glob, linecache, os, sys
needle = 'HIDDEN-MARKER-' + '7f3a9c'  # built at run time, so this file does not contain it
paths = glob.glob('/work/*') + glob.glob('/tmp/*') + glob.glob('*') + ['run_tests.py']
for root, _dirs, names in os.walk('/proc/self', onerror=lambda e: None):
    if root.count('/') <= 3:
        paths += [os.path.join(root, n) for n in names if n in ('cmdline', 'environ', 'status')]
found = []
for path in paths:
    try:
        if needle.encode() in open(path, 'rb').read():
            found.append(path)
    except OSError:
        pass
if any(needle in a for a in sys.argv) or any(needle in v for v in os.environ.values()):
    found.append('argv-or-env')
if any(needle in linecache.getline(f, n) for f in ('<hidden-checks>', 'run_tests.py') for n in range(1, 8)):
    found.append('linecache')
print('FOUND', found)
def double(x):
    return x * 2
"""


def test_the_learner_cannot_find_the_hidden_checks_in_files_proc_argv_or_env(runner):
    result = runner.execute(SNOOP, test_code=HIDDEN_CHECKS)

    assert result.success, result
    assert "FOUND []" in result.stdout, result.stdout


def test_the_run_folder_holds_only_the_harness_and_the_learner_files(runner):
    code = "import os\nprint(sorted(os.listdir('/work')))\ndef double(x):\n    return x * 2\n"

    result = runner.execute(code, test_code=HIDDEN_CHECKS)

    assert "['run_tests.py', 'solution.py']" in result.stdout


def test_hidden_checks_still_grade_in_the_container(runner):
    right = runner.execute("def double(x):\n    return x * 2\n", test_code=HIDDEN_CHECKS)
    wrong = runner.execute("def double(x):\n    return x + 3\n", test_code=HIDDEN_CHECKS)

    assert right.success is True
    assert wrong.success is False and any("double(2) should be 4" in e for e in wrong.assertion_errors)
    assert HIDDEN_MARKER not in wrong.stderr and "assert double(2)" not in wrong.stderr
