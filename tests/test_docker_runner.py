"""Audit step A6: the Docker runner must really use Docker, and fail closed (ADR-0036, SPEC-03).

The docker CLI is mocked here: no Docker is needed. tests/test_docker_integration.py runs the
same behaviour against a real daemon where one is available.
"""

import io
import logging
import os
import subprocess
import sys
import threading
import time

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner import docker_cli
from lms.adapters.runner.docker_cli import RunnerUnavailable, docker_run_args
from lms.adapters.runner.docker_runner import DockerRunner, get_code_runner
from lms.adapters.runner.interactive import DockerInteractiveRun, InteractiveRun, RunLimits
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import create_app

REAL_POPEN = subprocess.Popen


class Sink(io.BytesIO):
    """stdin that remembers what was written to it after the writer closes it."""

    captured = b""

    def close(self):
        self.captured = self.getvalue()
        super().close()


class FakeProc:
    def __init__(self, stdout=b"", stderr=b"", returncode=0, hang=False):
        self.stdin = Sink()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.hang = hang
        self.killed = False

    def wait(self, timeout=None):
        if self.hang and not self.killed:
            raise subprocess.TimeoutExpired("docker", timeout)
        return self.returncode

    def poll(self):
        return None if (self.hang and not self.killed) else self.returncode

    def kill(self):
        self.killed = True


class Docker:
    """A stand-in for the docker CLI. Records every command and what was in the run folder."""

    def __init__(self, monkeypatch, proc=None, info_ok=True, has_cli=True, image_ok=True):
        self.calls = []  # every docker command line, in order
        self.popen_args = []
        self.mounted = {}  # file name -> text, read when `docker run` started
        self.proc = proc or FakeProc()
        self.info_ok = info_ok
        self.image_ok = image_ok
        monkeypatch.setattr(docker_cli.shutil, "which", lambda _name: "docker" if has_cli else None)
        monkeypatch.setattr(docker_cli.subprocess, "run", self._run)
        monkeypatch.setattr(docker_cli.subprocess, "Popen", self._popen)

    def _run(self, argv, **_kwargs):
        self.calls.append(list(argv))
        code = 1 if (argv[1] == "info" and not self.info_ok) or (argv[1:3] == ["image", "inspect"] and not self.image_ok) else 0
        return subprocess.CompletedProcess(argv, code, b"", b"")

    def _popen(self, argv, **kwargs):
        self.calls.append(list(argv))
        self.popen_args.append(list(argv))
        source = next(a for a in argv if a.startswith("type=bind")).split("source=")[1].split(",")[0]
        for name in os.listdir(source):
            self.mounted[name] = open(os.path.join(source, name), encoding="utf-8").read()
        self.source = source
        return self.proc

    def commands(self, verb):
        return [c for c in self.calls if len(c) > 1 and c[1] == verb]


@pytest.fixture
def docker(monkeypatch):
    return Docker(monkeypatch)


def flag_value(argv, flag):
    return argv[argv.index(flag) + 1]


# --- The command line ---


def test_the_command_has_every_hardening_flag():
    argv = docker_run_args("lms-run-x", "/tmp/run", ["python", "solution.py"])

    assert argv[:3] == ["docker", "run", "--rm"]
    assert flag_value(argv, "--name") == "lms-run-x"
    assert flag_value(argv, "--network") == "none"
    assert "--read-only" in argv
    assert flag_value(argv, "--tmpfs") == "/tmp:rw,noexec,nosuid,size=16m"
    assert flag_value(argv, "--user") == "65534:65534"
    assert flag_value(argv, "--cap-drop") == "ALL"
    assert flag_value(argv, "--security-opt") == "no-new-privileges"
    assert flag_value(argv, "--memory") == "256m"
    assert flag_value(argv, "--memory-swap") == "256m"
    assert flag_value(argv, "--cpus") == "0.5"
    assert flag_value(argv, "--pids-limit") == "64"
    assert flag_value(argv, "--pull") == "never"
    ulimits = [argv[i + 1] for i, a in enumerate(argv) if a == "--ulimit"]
    assert "nofile=64:64" in ulimits
    assert "fsize=1048576:1048576" in ulimits
    assert argv[-3:] == ["python:3.14-slim", "python", "solution.py"]


def test_the_run_folder_is_mounted_read_only_and_no_host_variable_is_passed():
    argv = docker_run_args("lms-run-x", "/tmp/run", ["python", "solution.py"])

    mount = flag_value(argv, "--mount")
    assert mount == "type=bind,source=/tmp/run,target=/work,readonly"
    assert flag_value(argv, "-w") == "/work"
    env_values = [argv[i + 1] for i, a in enumerate(argv) if a == "-e"]
    assert all("=" in v for v in env_values), "-e NAME alone would copy a host variable into the container"
    assert not any(a in ("--privileged", "--env-file", "-v", "--volume") for a in argv)


def test_the_limits_in_the_code_match_the_docs():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = (root / "docs/specs/03-code-runner-and-sandbox-spec.md").read_text(encoding="utf-8")
    assert f"--memory {docker_cli.MEMORY_LIMIT} --memory-swap {docker_cli.MEMORY_LIMIT}" in spec
    assert f"--cpus {docker_cli.CPU_LIMIT}" in spec
    assert f"--pids-limit {docker_cli.PIDS_LIMIT}" in spec
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "256 MB" in readme and "0.5 CPU" in readme


# --- execute() ---


def test_execute_runs_the_code_in_a_container_not_in_a_subprocess(docker):
    docker.proc = FakeProc(stdout=b"hello\n")

    result = DockerRunner().execute("print('hello')")

    assert docker.popen_args, "no docker run was started"
    assert result.success and result.stdout == "hello\n" and result.exit_code == 0
    assert docker.mounted["solution.py"] == "print('hello')"
    assert docker.popen_args[0][-2:] == ["python", "solution.py"]


def test_test_code_runs_through_the_test_script_with_the_solution_beside_it(docker):
    DockerRunner().execute("def f():\n    return 1\n", test_code="def test_f():\n    assert f() == 1\n")

    assert docker.popen_args[0][-2:] == ["python", "run_tests.py"]
    assert "def f()" in docker.mounted["solution.py"]
    assert "def test_f" not in docker.mounted["run_tests.py"], "the checks go on stdin, never into the folder"
    assert b"def test_f" in docker.proc.stdin.captured


def test_extra_files_are_placed_beside_the_code(docker):
    DockerRunner().execute("import slip", files={"slip.py": "X = 1\n"})

    assert docker.mounted["slip.py"] == "X = 1\n"


@pytest.mark.parametrize("name", ["../evil.py", "solution.py", "a b.py", "notpython.txt"])
def test_a_bad_extra_file_name_is_refused_before_anything_starts(docker, name):
    with pytest.raises(ValueError):
        DockerRunner().execute("print(1)", files={name: "x"})
    assert not docker.popen_args


def test_stdin_reaches_the_container(docker):
    DockerRunner().execute("print(input())", stdin_input="Amara\n")

    assert docker.proc.stdin.captured == b"Amara\n"


def test_each_run_has_its_own_container_name(docker):
    runner = DockerRunner()
    runner.execute("print(1)")
    runner.execute("print(1)")

    names = {flag_value(c, "--name") for c in docker.popen_args}
    assert len(names) == 2 and all(n.startswith("lms-run-") for n in names)


def test_a_timeout_kills_the_container_and_reports_it(docker):
    docker.proc = FakeProc(hang=True)

    result = DockerRunner().execute("while True: pass", timeout_seconds=0.2)

    name = flag_value(docker.popen_args[0], "--name")
    assert ["docker", "kill", name] in docker.calls
    assert docker.proc.killed
    assert result.success is False and "timed out" in result.stderr.lower()
    assert result.exit_code == -1 and result.assertion_errors == ["Execution timed out"]


def test_the_container_and_the_folder_are_always_cleaned_up(docker):
    DockerRunner().execute("print(1)")
    name = flag_value(docker.popen_args[0], "--name")
    assert ["docker", "rm", "-f", name] in docker.calls
    assert not os.path.exists(docker.source)


def test_cleanup_still_happens_when_the_run_blows_up(docker, monkeypatch):
    docker.proc.wait = lambda timeout=None: (_ for _ in ()).throw(RuntimeError("boom"))

    with pytest.raises(RuntimeError):
        DockerRunner().execute("print(1)")

    name = flag_value(docker.popen_args[0], "--name")
    assert ["docker", "rm", "-f", name] in docker.calls
    assert not os.path.exists(docker.source)


def test_output_is_capped_at_64_kb_and_the_container_is_killed(docker):
    docker.proc = FakeProc(stdout=b"x" * 300_000)

    result = DockerRunner().execute("while True: print('x'*100)")

    assert len(result.stdout.encode()) <= 64 * 1024
    assert "output limit" in result.stderr.lower()
    name = flag_value(docker.popen_args[0], "--name")
    assert ["docker", "kill", name] in docker.calls


def test_failed_assertions_are_listed(docker):
    docker.proc = FakeProc(stderr=b"Traceback\nAssertionError: 1 != 2\n", returncode=1)

    result = DockerRunner().execute("x", test_code="def test_a():\n    assert 1 == 2\n")

    assert result.success is False
    assert any("AssertionError" in e for e in result.assertion_errors)


# --- Fail closed (the audit finding) ---


def test_without_the_docker_cli_nothing_runs(monkeypatch):
    docker = Docker(monkeypatch, has_cli=False)

    with pytest.raises(RunnerUnavailable):
        DockerRunner().execute("print('should not run')")
    assert not docker.popen_args


def test_with_the_daemon_down_nothing_runs(monkeypatch):
    docker = Docker(monkeypatch, info_ok=False)

    with pytest.raises(RunnerUnavailable):
        DockerRunner().execute("print('should not run')")
    assert not docker.popen_args


def test_it_never_falls_back_to_the_subprocess_runner(monkeypatch):
    Docker(monkeypatch, info_ok=False)

    def boom(*_a, **_k):
        raise AssertionError("learner code was run outside Docker")

    monkeypatch.setattr(SubprocessRunner, "execute", boom)
    with pytest.raises(RunnerUnavailable):
        DockerRunner().execute("print(1)")


def test_a_missing_image_is_an_unavailable_runner_not_a_failed_program(docker):
    docker.proc = FakeProc(stderr=b"docker: Error response from daemon: No such image: python:3.14-slim.\n", returncode=125)

    with pytest.raises(RunnerUnavailable) as caught:
        DockerRunner().execute("print(1)")
    assert "docker pull" in str(caught.value)


def test_a_learner_program_that_exits_125_is_still_a_program_result(docker):
    docker.proc = FakeProc(stderr=b"", returncode=125)

    result = DockerRunner().execute("import sys; sys.exit(125)")

    assert result.exit_code == 125 and result.success is False


def test_availability_is_not_asked_for_on_every_run(docker):
    runner = DockerRunner()
    runner.execute("print(1)")
    runner.execute("print(1)")

    assert len(docker.commands("info")) == 1


# --- get_code_runner ---


def test_the_default_is_docker_even_when_docker_is_down(monkeypatch):
    Docker(monkeypatch, info_ok=False)
    monkeypatch.delenv("LMS_RUNNER", raising=False)

    assert isinstance(get_code_runner(), DockerRunner)


def test_subprocess_is_an_explicit_opt_in_and_warns(monkeypatch, caplog):
    monkeypatch.setenv("LMS_RUNNER", "subprocess")
    with caplog.at_level(logging.INFO):
        runner = get_code_runner()

    assert isinstance(runner, SubprocessRunner)
    assert "not a sandbox" in caplog.text.lower()


def test_auto_uses_docker_only_when_it_is_reachable(monkeypatch, caplog):
    Docker(monkeypatch, info_ok=False)
    monkeypatch.setenv("LMS_RUNNER", "auto")
    with caplog.at_level(logging.INFO):
        assert isinstance(get_code_runner(), SubprocessRunner)
    assert "warning" in " ".join(r.levelname.lower() for r in caplog.records)

    Docker(monkeypatch, info_ok=True)
    assert isinstance(get_code_runner(), DockerRunner)


def test_an_unknown_mode_stops_the_app(monkeypatch):
    monkeypatch.setenv("LMS_RUNNER", "dokcer")
    with pytest.raises(ValueError):
        get_code_runner()


def test_start_up_logs_the_active_runner(monkeypatch, caplog):
    Docker(monkeypatch, info_ok=False)
    monkeypatch.delenv("LMS_RUNNER", raising=False)
    with caplog.at_level(logging.INFO):
        get_code_runner()

    assert "docker" in caplog.text.lower() and "unavailable" in caplog.text.lower()


# --- Interactive runs ---


def python_stand_in(script):
    """Replace `docker run ...` with a real process, so the event reader has real pipes."""

    def popen(argv, **kwargs):
        popen.argv = list(argv)
        return REAL_POPEN([sys.executable, "-u", "-c", script], **{k: v for k, v in kwargs.items() if k != "cwd"})

    return popen


def drain(run, limit=10):
    events, end = [], time.monotonic() + limit
    while time.monotonic() < end:
        event = run.next_event(0.1)
        if event is not None:
            events.append(event)
            if event["type"] == "exit":
                return events
    raise AssertionError(f"no exit event; got {events}")


def test_interactive_runs_use_the_same_container_profile(monkeypatch):
    docker = Docker(monkeypatch)
    stand_in = python_stand_in("print('hi')")
    monkeypatch.setattr(docker_cli.subprocess, "Popen", stand_in)

    run = DockerRunner().start_interactive({"solution.py": "print('hi')"}, "solution.py", RunLimits())
    events = drain(run)

    argv = stand_in.argv
    assert flag_value(argv, "--network") == "none" and "--read-only" in argv
    assert flag_value(argv, "--user") == "65534:65534" and flag_value(argv, "--cap-drop") == "ALL"
    assert "-i" in argv
    assert argv[-6:-3] == ["python", "-u", "/work/lms_run_harness.py"]
    assert [e for e in events if e["type"] == "stdout"][0]["data"].strip() == "hi"
    assert events[-1]["code"] == 0
    name = flag_value(argv, "--name")
    assert ["docker", "rm", "-f", name] in docker.calls


def test_stopping_an_interactive_run_kills_and_removes_the_container(monkeypatch):
    docker = Docker(monkeypatch)
    stand_in = python_stand_in("import time; time.sleep(30)")
    monkeypatch.setattr(docker_cli.subprocess, "Popen", stand_in)

    run = DockerRunner().start_interactive({"solution.py": "x = 1"}, "solution.py", RunLimits())
    run.stop()
    events = drain(run)

    name = flag_value(stand_in.argv, "--name")
    assert ["docker", "kill", name] in docker.calls
    assert ["docker", "rm", "-f", name] in docker.calls
    assert events[-1]["type"] == "exit"


def test_the_wall_clock_limit_kills_the_container(monkeypatch):
    docker = Docker(monkeypatch)
    stand_in = python_stand_in("import time; time.sleep(30)")
    monkeypatch.setattr(docker_cli.subprocess, "Popen", stand_in)

    run = DockerRunner().start_interactive({"solution.py": "x = 1"}, "solution.py", RunLimits(wall_seconds=0.3))
    events = drain(run)

    assert events[-1]["timed_out"] is True
    assert ["docker", "kill", flag_value(stand_in.argv, "--name")] in docker.calls


def test_interactive_input_still_uses_the_token_protocol(monkeypatch):
    Docker(monkeypatch)
    # The stand-in is the real harness, so the token round trip is the real one.
    from lms.adapters.runner import interactive

    def source_of(argv):
        return next(a for a in argv if a.startswith("type=bind")).split("source=")[1].split(",")[0]

    def popen(argv, **kwargs):
        popen.argv = list(argv)
        folder = source_of(argv)
        harness_args = argv[argv.index("-u") + 2 :]
        rest = {k: v for k, v in kwargs.items() if k != "cwd"}
        return REAL_POPEN([sys.executable, "-u", os.path.join(folder, "lms_run_harness.py"), *harness_args], cwd=folder, **rest)

    monkeypatch.setattr(docker_cli.subprocess, "Popen", popen)
    run = DockerRunner().start_interactive(
        {"solution.py": "name = input('Name? ')\nprint('Hi ' + name)\n"}, "solution.py", interactive.RunLimits()
    )
    events = []
    end = time.monotonic() + 10
    while time.monotonic() < end:
        event = run.next_event(0.1)
        if event is None:
            continue
        events.append(event)
        if event["type"] == "awaiting_input":
            run.send_stdin("Amara")
        if event["type"] == "exit":
            break

    assert any(e["type"] == "awaiting_input" for e in events)
    assert "Hi Amara" in "".join(e.get("data", "") for e in events if e["type"] == "stdout")


def test_interactive_start_is_refused_when_docker_is_down(monkeypatch):
    docker = Docker(monkeypatch, info_ok=False)

    with pytest.raises(RunnerUnavailable):
        DockerRunner().start_interactive({"solution.py": "x = 1"}, "solution.py", RunLimits())
    assert not docker.popen_args


def test_the_local_interactive_run_is_still_a_plain_subprocess():
    assert not issubclass(InteractiveRun, DockerInteractiveRun)
    assert issubclass(DockerInteractiveRun, InteractiveRun)


# --- Through the API ---


class DownRunner:
    def execute(self, *args, **kwargs):
        raise RunnerUnavailable("Docker is not reachable.")

    def start_interactive(self, *args, **kwargs):
        raise RunnerUnavailable("Docker is not reachable.")


def make_client(runner, max_runs=1):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo, runner=runner, axis=MockAxisCompanion(), catalog=CurriculumCatalog(), max_concurrent_runs=max_runs
    )
    return TestClient(app)


def test_execute_answers_503_when_the_runner_is_down():
    response = make_client(DownRunner()).post("/api/v1/execute", json={"code": "print(1)"})

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "Traceback" not in response.text and "Docker is not reachable" not in response.text


def test_a_run_socket_gets_an_error_and_gives_its_slot_back():
    client = make_client(DownRunner(), max_runs=1)

    for _ in range(2):  # a second try would be "busy" if the first leaked its slot
        with client.websocket_connect("/api/v1/runs") as ws:
            ws.send_json({"type": "start", "files": {"solution.py": "print(1)"}, "entry": "solution.py"})
            message = ws.receive_json()
        assert message["type"] == "error"
        assert "busy" not in message["message"].lower()


def test_a_docker_run_socket_takes_a_slot_like_any_other_run():
    class Slow:
        def __init__(self):
            self.started = threading.Event()

        def execute(self, *a, **k):
            raise AssertionError

        def start_interactive(self, files, entry, limits):
            self.started.set()
            return _Endless()

    class _Endless:
        stopped = False

        def next_event(self, timeout):
            time.sleep(min(timeout, 0.05))
            return None

        def send_stdin(self, line):
            pass

        def stop(self):
            _Endless.stopped = True

    runner = Slow()
    client = make_client(runner, max_runs=1)
    with client.websocket_connect("/api/v1/runs") as first:
        first.send_json({"type": "start", "files": {"solution.py": "x = 1"}, "entry": "solution.py"})
        assert runner.started.wait(5)
        with client.websocket_connect("/api/v1/runs") as second:
            second.send_json({"type": "start", "files": {"solution.py": "x = 1"}, "entry": "solution.py"})
            assert "busy" in second.receive_json()["message"].lower()


def test_a_missing_image_refuses_interactive_runs_before_anything_starts(monkeypatch):
    docker = Docker(monkeypatch, image_ok=False)

    with pytest.raises(RunnerUnavailable):
        DockerRunner().start_interactive({"solution.py": "x = 1"}, "solution.py", RunLimits())
    with pytest.raises(RunnerUnavailable):
        DockerRunner().execute("print(1)")
    assert not docker.popen_args


def test_the_interactive_output_limit_kills_the_container(monkeypatch):
    docker = Docker(monkeypatch)
    script = "import sys\nwhile True:\n    sys.stdout.write('x' * 1000)\n    sys.stdout.flush()"
    stand_in = python_stand_in(script)
    monkeypatch.setattr(docker_cli.subprocess, "Popen", stand_in)

    run = DockerRunner().start_interactive({"solution.py": "x = 1"}, "solution.py", RunLimits(output_bytes=2000))
    drain(run)

    assert ["docker", "kill", flag_value(stand_in.argv, "--name")] in docker.calls
