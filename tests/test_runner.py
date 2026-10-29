import pytest
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.adapters.runner.docker_runner import DockerRunner, get_code_runner
from lms.core.interfaces import ExecutionResult, ICodeRunner


def test_subprocess_runner_happy_path():
    runner = SubprocessRunner()
    code = "print('Hello from the LMS Sandbox!')"
    result = runner.execute(code=code)

    assert result.success is True
    assert "Hello from the LMS Sandbox!" in result.stdout
    assert result.exit_code == 0
    assert result.assertion_errors == []


def test_subprocess_runner_syntax_error():
    runner = SubprocessRunner()
    code = "def broken_code(\n  print('missing colon')"
    result = runner.execute(code=code)

    assert result.success is False
    assert result.exit_code != 0
    assert "SyntaxError" in result.stderr


def test_subprocess_runner_with_passing_assertions():
    runner = SubprocessRunner()
    code = "def add(a, b):\n    return a + b\n"
    test_code = "assert add(2, 3) == 5\nassert add(-1, 1) == 0\n"

    result = runner.execute(code=code, test_code=test_code)
    assert result.success is True
    assert result.assertion_errors == []


def test_subprocess_runner_with_failing_assertions():
    runner = SubprocessRunner()
    code = "def add(a, b):\n    return a - b\n"  # Buggy implementation
    test_code = "assert add(2, 3) == 5\n"

    result = runner.execute(code=code, test_code=test_code)
    assert result.success is False
    assert len(result.assertion_errors) > 0
    assert "AssertionError" in result.stderr or len(result.assertion_errors) > 0


def test_subprocess_runner_timeout_infinite_loop():
    runner = SubprocessRunner()
    code = "while True:\n    pass\n"

    # Set short timeout to verify timeout defense
    result = runner.execute(code=code, timeout_seconds=1.0)
    assert result.success is False
    assert "timed out" in result.stderr.lower()


def test_docker_runner_command_generation():
    docker_runner = DockerRunner()
    cmd = docker_runner.build_docker_command(
        script_path="/tmp/test.py",
        memory_limit="128m",
        cpu_limit="1.0",
        network_disabled=True,
    )
    # Verify strict security flags
    assert "--network" in cmd
    assert "none" in cmd
    assert "--memory" in cmd
    assert "128m" in cmd
    assert "--cpus" in cmd
    assert "1.0" in cmd


def test_get_code_runner_factory():
    runner = get_code_runner()
    # Must implement ICodeRunner protocol
    assert hasattr(runner, "execute")
