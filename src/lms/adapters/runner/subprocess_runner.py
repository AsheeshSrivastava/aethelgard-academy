"""Subprocess implementation of ICodeRunner.

Provides fast, local, offline code execution and test verification
with strict timeout boundaries and error handling.
"""

from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import List, Mapping, Optional

from lms.adapters.runner.check_harness import HARNESS, check_stdin, new_token, with_completion
from lms.adapters.runner.interactive import safe_env
from lms.core.interfaces import ExecutionResult, extra_file_problem


def assertion_errors_from(stderr: str) -> List[str]:
    """The failed-assertion lines of a traceback."""
    if "AssertionError" not in stderr:
        return []
    return [line.strip() for line in stderr.splitlines() if "AssertionError" in line or "assert " in line]


class SubprocessRunner:
    """Runs student code and test assertions locally via isolated subprocess."""

    def execute(
        self,
        code: str,
        test_code: Optional[str] = None,
        timeout_seconds: float = 5.0,
        stdin_input: Optional[str] = None,
        files: Optional[Mapping[str, str]] = None,
    ) -> ExecutionResult:
        extra = dict(files or {})
        for name in extra:
            problem = extra_file_problem(name)
            if problem:
                raise ValueError(problem)
        token = new_token()
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            script_path = tmppath / "solution.py"
            script_path.write_text(code, encoding="utf-8")
            for name, source in extra.items():
                (tmppath / name).write_text(source, encoding="utf-8")

            if test_code:
                # The harness is fixed text. The hidden checks go in on stdin, never to disk (SPEC-03 2.4).
                runner_script = tmppath / "run_tests.py"
                runner_script.write_text(HARNESS, encoding="utf-8")
                target_to_run = runner_script
            else:
                target_to_run = script_path

            try:
                proc = subprocess.run(
                    [sys.executable, str(target_to_run)],
                    input=check_stdin(test_code, stdin_input, token) if test_code else (stdin_input or ""),
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=tmpdir,
                    env=safe_env(),
                )
                duration_ms = (time.perf_counter() - start_time) * 1000

                stdout = proc.stdout
                stderr = proc.stderr
                exit_code = proc.returncode
                success = exit_code == 0

                assertion_errors = assertion_errors_from(stderr)

                result = ExecutionResult(
                    success=success,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    duration_ms=round(duration_ms, 2),
                    assertion_errors=assertion_errors,
                )
                return with_completion(result, token) if test_code else result

            except subprocess.TimeoutExpired:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution timed out after {timeout_seconds:.1f}s. Check for an infinite loop or blocking call.",
                    exit_code=-1,
                    duration_ms=round(duration_ms, 2),
                    assertion_errors=["Execution timed out"],
                )
