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
            script_path.write_text(code, encoding="utf-8")

            if test_code:
                # Write separate test harness file that safely imports solution
                test_script = (
                    "import sys\n"
                    "import builtins\n"
                    "from pathlib import Path\n"
                    "sys.path.insert(0, '.')\n"
                    "# Provide default input mock during import to prevent hanging on top-level input()\n"
                    "_orig_input = builtins.input\n"
                    "builtins.input = lambda *args, **kwargs: 'Amara Okafor'\n"
                    "try:\n"
                    "    from solution import *\n"
                    "except Exception:\n"
                    "    pass\n"
                    "builtins.input = _orig_input\n\n"
                    f"{test_code}\n\n"
                    "# --- Auto-invoke test functions ---\n"
                    "for _name, _fn in list(locals().items()):\n"
                    "    if _name.startswith('test_') and callable(_fn):\n"
                    "        _fn()\n"
                )
                runner_script = tmppath / "run_tests.py"
                runner_script.write_text(test_script, encoding="utf-8")
                target_to_run = runner_script
            else:
                target_to_run = script_path

            try:
                proc = subprocess.run(
                    [sys.executable, str(target_to_run)],
                    input="",
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
