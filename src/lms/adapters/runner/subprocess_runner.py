"""Subprocess implementation of ICodeRunner.

Provides fast, local, offline code execution and test verification
with strict timeout boundaries and error handling.
"""

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import List, Optional

from lms.core.interfaces import ExecutionResult


class SubprocessRunner:
    """Runs student code and test assertions locally via isolated subprocess."""

    def execute(
        self, code: str, test_code: Optional[str] = None, timeout_seconds: float = 5.0
    ) -> ExecutionResult:
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            script_path = tmppath / "solution.py"

            if test_code:
                # Combine solution code with test assertions
                full_script = f"{code}\n\n# --- Verification Assertions ---\n{test_code}"
            else:
                full_script = code

            script_path.write_text(full_script, encoding="utf-8")

            try:
                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=tmpdir,
                )
                duration_ms = (time.perf_counter() - start_time) * 1000

                stdout = proc.stdout
                stderr = proc.stderr
                exit_code = proc.returncode
                success = exit_code == 0

                assertion_errors: List[str] = []
                if "AssertionError" in stderr:
                    for line in stderr.splitlines():
                        if "AssertionError" in line or "assert " in line:
                            assertion_errors.append(line.strip())

                return ExecutionResult(
                    success=success,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    duration_ms=round(duration_ms, 2),
                    assertion_errors=assertion_errors,
                )

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
