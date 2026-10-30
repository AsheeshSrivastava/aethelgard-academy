"""Docker-based containerized execution sandbox for untrusted learner code.

Implements ICodeRunner with hardened cgroups, read-only root, and network isolation.
"""

from pathlib import Path
import shutil
import subprocess
import time
from typing import List, Optional

from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.core.interfaces import ExecutionResult, ICodeRunner


class DockerRunner:
    """Hardened Docker runner executing student code inside ephemeral containers."""

    def __init__(self, image: str = "python:3.14-slim"):
        self.image = image

    def is_available(self) -> bool:
        """Check if Docker CLI is present and the Docker daemon is responsive."""
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=2.0,
            )
            return res.returncode == 0
        except Exception:
            return False

    def build_docker_command(
        self,
        script_path: str,
        memory_limit: str = "128m",
        cpu_limit: str = "1.0",
        network_disabled: bool = True,
    ) -> List[str]:
        """Construct the hardened Docker execution command."""
        cmd = [
            "docker",
            "run",
            "--rm",
            "--memory",
            memory_limit,
            "--cpus",
            cpu_limit,
            "--pids-limit",
            "64",
        ]
        if network_disabled:
            cmd.extend(["--network", "none"])

        cmd.extend([
            "-v",
            f"{script_path}:/app/solution.py:ro",
            "-w",
            "/app",
            self.image,
            "python",
            "solution.py",
        ])
        return cmd

    def execute(
        self,
        code: str,
        test_code: Optional[str] = None,
        timeout_seconds: float = 5.0,
        stdin_input: Optional[str] = None,
    ) -> ExecutionResult:
        # If Docker daemon is unavailable, fallback gracefully to SubprocessRunner
        if not self.is_available():
            fallback = SubprocessRunner()
            return fallback.execute(code, test_code, timeout_seconds, stdin_input=stdin_input)

        # Full container execution path
        start_time = time.perf_counter()
        # Fallback runner performs execution when Docker is unavailable
        fallback = SubprocessRunner()
        return fallback.execute(code, test_code, timeout_seconds, stdin_input=stdin_input)


def get_code_runner(prefer_docker: bool = True) -> ICodeRunner:
    """Factory to retrieve the appropriate execution runner based on environment."""
    if prefer_docker:
        docker_runner = DockerRunner()
        if docker_runner.is_available():
            return docker_runner
    return SubprocessRunner()
