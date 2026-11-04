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


# --- Multi-file runs (SPEC-15 section 2.4, phase 2 step 2.2) ---

HELPER = 'def slip_line(name):\n    return f"Name: {name}"\n'


def test_subprocess_runner_lets_the_entry_import_another_file():
    code = "from slip import slip_line\nprint(slip_line('Amara'))\n"

    result = SubprocessRunner().execute(code=code, files={"slip.py": HELPER})

    assert result.success is True
    assert result.stdout.strip() == "Name: Amara"


def test_subprocess_runner_checks_can_reach_another_file():
    code = "from slip import slip_line\n"
    test_code = "def test_line():\n    assert slip_line('Kofi') == 'Name: Kofi'\n"

    result = SubprocessRunner().execute(code=code, test_code=test_code, files={"slip.py": HELPER})

    assert result.success is True


def test_without_extra_files_an_import_of_one_fails():
    result = SubprocessRunner().execute(code="from slip import slip_line\n")

    assert result.success is False
    assert "ModuleNotFoundError" in result.stderr


@pytest.mark.parametrize("name", ["../evil.py", "sub/mod.py", "solution.py", "run_tests.py", "notes.txt", "my-mod.py", ".py"])
def test_subprocess_runner_refuses_a_file_name_it_cannot_place_safely(name):
    with pytest.raises(ValueError):
        SubprocessRunner().execute(code="print(1)", files={name: "x = 1"})
