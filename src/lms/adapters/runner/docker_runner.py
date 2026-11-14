"""Docker-based sandbox for untrusted learner code (ICodeRunner).

Governed by ADR-0036 and SPEC-03. Each run is one ephemeral container with no network, a
read-only root, dropped privileges and memory, CPU, process and output limits.

The runner fails closed: when Docker cannot be used it raises RunnerUnavailable and runs
nothing. It never falls back to running the code on the host.
"""

import logging
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Any, Dict, List, Mapping, Optional

from lms.adapters.runner.docker_cli import (
    AVAILABILITY_TTL_SECONDS,
    IMAGE,
    MAX_OUTPUT_BYTES,
    STARTUP_ALLOWANCE_SECONDS,
    RunnerUnavailable,
    cli_env,
    docker_failure,
    docker_reachable,
    docker_run_args,
    kill_container,
    new_container_name,
    open_to_container,
    remove_container,
)
from lms.adapters.runner.interactive import DockerInteractiveRun, RunLimits
from lms.adapters.runner.subprocess_runner import SubprocessRunner, assertion_errors_from, build_test_script
from lms.core.interfaces import ExecutionResult, ICodeRunner, extra_file_problem

logger = logging.getLogger("lms.runner")
if not logger.handlers and not logging.getLogger().handlers:
    # Nothing else configures logging, and the start-up line saying which runner is active must be seen.
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

RUNNER_ENV = "LMS_RUNNER"
OUTPUT_LIMIT_NOTE = "\nStopped: the output limit was reached.\n"


class _Capture:
    """stdout and stderr together, never more than MAX_OUTPUT_BYTES in all."""

    def __init__(self) -> None:
        self.parts: Dict[str, bytearray] = {"out": bytearray(), "err": bytearray()}
        self.over = False
        self._total = 0
        self._lock = threading.Lock()

    def add(self, kind: str, data: bytes) -> bool:
        """Keep what fits. False once the limit has been passed."""
        with self._lock:
            room = MAX_OUTPUT_BYTES - self._total
            self.parts[kind].extend(data[: max(room, 0)])
            self._total += min(len(data), max(room, 0))
            if len(data) > room:
                self.over = True
            return not self.over

    def text(self, kind: str) -> str:
        return bytes(self.parts[kind]).decode("utf-8", errors="replace")


class DockerRunner:
    """Runs student code in an ephemeral, locked-down Docker container."""

    def __init__(self, image: str = IMAGE):
        self.image = image
        self._checked_at: Optional[float] = None
        self._reachable = False

    def is_available(self) -> bool:
        """Ask Docker now (the answer is remembered for a few seconds)."""
        self._reachable = docker_reachable(self.image)
        self._checked_at = time.monotonic()
        return self._reachable

    def require_available(self) -> None:
        fresh = self._checked_at is not None and time.monotonic() - self._checked_at < AVAILABILITY_TTL_SECONDS
        if not (self._reachable if fresh else self.is_available()):
            raise RunnerUnavailable("Docker is not reachable: the docker CLI or its daemon is not running.")

    def start_interactive(self, files: Dict[str, str], entry: str, limits: RunLimits = RunLimits()) -> DockerInteractiveRun:
        """An interactive run (SPEC-12 section 7) in a container, with the same events as a local run."""
        self.require_available()
        return DockerInteractiveRun(files, entry, limits, image=self.image)

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
        self.require_available()
        started = time.perf_counter()

        with tempfile.TemporaryDirectory(prefix="lms-run-") as folder:
            folder_path = Path(folder)
            (folder_path / "solution.py").write_text(code, encoding="utf-8")
            for name, source in extra.items():
                (folder_path / name).write_text(source, encoding="utf-8")
            script = "solution.py"
            if test_code:
                (folder_path / "run_tests.py").write_text(build_test_script(test_code), encoding="utf-8")
                script = "run_tests.py"
            open_to_container(folder)

            name = new_container_name()
            argv = docker_run_args(name, folder, ["python", script], self.image)
            capture = _Capture()
            timed_out = False
            proc = subprocess.Popen(
                argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=cli_env()
            )
            try:
                threads = self._start_pipes(proc, name, capture, stdin_input or "")
                try:
                    proc.wait(timeout=timeout_seconds + STARTUP_ALLOWANCE_SECONDS)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    kill_container(name)
                    proc.kill()
                    proc.wait()
                for thread in threads:
                    thread.join(timeout=5)
            finally:
                if proc.poll() is None:  # an error got us here with the container still running
                    kill_container(name)
                    proc.kill()
                remove_container(name)

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        if timed_out:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {timeout_seconds:.1f}s. Check for an infinite loop or blocking call.",
                exit_code=-1,
                duration_ms=duration_ms,
                assertion_errors=["Execution timed out"],
            )

        stdout, stderr, exit_code = capture.text("out"), capture.text("err"), proc.returncode
        if exit_code == 125:
            reason = docker_failure(stderr)
            if reason:
                raise RunnerUnavailable(reason)
        if capture.over:
            stderr += OUTPUT_LIMIT_NOTE
        return ExecutionResult(
            success=exit_code == 0 and not capture.over,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            assertion_errors=assertion_errors_from(stderr),
        )

    def _start_pipes(self, proc: Any, name: str, capture: _Capture, stdin_text: str) -> List[threading.Thread]:
        """Feed stdin and read both output streams, each on its own thread so none can block another."""

        def feed() -> None:
            try:
                proc.stdin.write(stdin_text.encode("utf-8"))
            except (BrokenPipeError, OSError, ValueError):
                pass
            finally:
                try:
                    proc.stdin.close()
                except (BrokenPipeError, OSError, ValueError):
                    pass

        def drain(stream: Any, kind: str) -> None:
            stopped = False
            while True:
                chunk = stream.read1(8192)
                if not chunk:
                    return
                if not capture.add(kind, chunk) and not stopped:
                    stopped = True  # keep reading so the pipe empties, but stop the program
                    kill_container(name)
                    proc.kill()

        threads = [
            threading.Thread(target=feed, daemon=True),
            threading.Thread(target=drain, args=(proc.stdout, "out"), daemon=True),
            threading.Thread(target=drain, args=(proc.stderr, "err"), daemon=True),
        ]
        for thread in threads:
            thread.start()
        return threads


def get_code_runner(mode: Optional[str] = None) -> ICodeRunner:
    """The runner for this deployment. `mode` is LMS_RUNNER when None. There is no silent fallback.

    docker (default): DockerRunner. If Docker is down, runs are refused (fail closed).
    subprocess:       SubprocessRunner. Explicit opt-in for development and CI. Not a sandbox.
    auto:             DockerRunner if Docker answers now, else SubprocessRunner, with a warning.
    """
    chosen = (mode if mode is not None else os.environ.get(RUNNER_ENV, "")).strip().lower() or "docker"
    if chosen not in ("docker", "subprocess", "auto"):
        raise ValueError(f"{RUNNER_ENV}={chosen!r} is not one of: docker, subprocess, auto.")

    if chosen == "subprocess":
        logger.warning(
            "Code runner: subprocess (%s=subprocess). This is NOT a sandbox. Use it only for development or CI.",
            RUNNER_ENV,
        )
        return SubprocessRunner()

    docker_runner = DockerRunner()
    if docker_runner.is_available():
        logger.info("Code runner: docker (reachable, image %s).", docker_runner.image)
        return docker_runner
    if chosen == "auto":
        logger.warning(
            "Code runner: auto found no reachable Docker, so it uses the subprocess runner. NOT a sandbox."
        )
        return SubprocessRunner()
    logger.error(
        "Code runner: docker is UNAVAILABLE (cli missing, daemon down or image not pulled: docker pull %s). Learner code will be refused until "
        "Docker is running. Set %s=subprocess to run code unsandboxed in development.",
        docker_runner.image,
        RUNNER_ENV,
    )
    return docker_runner
