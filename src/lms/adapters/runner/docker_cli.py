"""The Docker command line for learner code, shared by one-shot and interactive runs.

Governed by ADR-0036 and SPEC-03 section 2.1. Every limit is a named constant here so that the
code, the README and the spec say the same thing (a test compares them).

Only the `docker` CLI is used. Nothing from the host environment is copied into a container:
there is no `-e NAME` (which would copy a host value) and no `--env-file`.
"""

import os
import shutil
import subprocess
import uuid
from typing import List, Optional, Sequence

IMAGE = "python:3.14-slim"
MEMORY_LIMIT = "256m"  # --memory-swap is set to the same value, so there is no swap
CPU_LIMIT = "0.5"
PIDS_LIMIT = 64
NOFILE_LIMIT = 64
FSIZE_LIMIT_BYTES = 1024 * 1024
TMPFS = "/tmp:rw,noexec,nosuid,size=16m"
WORKDIR = "/work"
CONTAINER_USER = "65534:65534"  # nobody:nogroup
NAME_PREFIX = "lms-run-"

MAX_OUTPUT_BYTES = 64 * 1024
STARTUP_ALLOWANCE_SECONDS = 3.0  # container start-up must not eat the learner's time limit
AVAILABILITY_TTL_SECONDS = 5.0
CLI_TIMEOUT_SECONDS = 15.0

_CONTAINER_ENV = ("PYTHONIOENCODING=utf-8", "PYTHONUTF8=1", "PYTHONDONTWRITEBYTECODE=1")
# What the docker CLI itself needs to find its daemon and config. None of it enters a container.
_CLI_ENV = (
    "PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "SYSTEMROOT", "SYSTEMDRIVE",
    "WINDIR", "TEMP", "TMP", "XDG_RUNTIME_DIR", "XDG_CONFIG_HOME", "LANG",
)


class RunnerUnavailable(Exception):
    """Learner code cannot be run safely right now. The code was not run in any other way."""


def cli_env() -> dict:
    """The environment of the docker CLI process: what it needs, plus its own DOCKER_* settings."""
    env = {k: os.environ[k] for k in _CLI_ENV if k in os.environ}
    env.update({k: v for k, v in os.environ.items() if k.startswith("DOCKER_")})
    return env


def new_container_name() -> str:
    return f"{NAME_PREFIX}{uuid.uuid4().hex}"


def docker_run_args(name: str, folder: str, command: Sequence[str], image: str = IMAGE) -> List[str]:
    """The `docker run` command line for one learner program. `folder` is mounted read-only."""
    if "," in folder or "\n" in folder:
        raise ValueError("The run folder path cannot be mounted safely.")
    args = [
        "docker", "run", "--rm", "-i",
        "--name", name,
        "--pull", "never",
        "--network", "none",
        "--read-only",
        "--tmpfs", TMPFS,
        "--user", CONTAINER_USER,
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", MEMORY_LIMIT,
        "--memory-swap", MEMORY_LIMIT,
        "--cpus", CPU_LIMIT,
        "--pids-limit", str(PIDS_LIMIT),
        "--ulimit", f"nofile={NOFILE_LIMIT}:{NOFILE_LIMIT}",
        "--ulimit", f"fsize={FSIZE_LIMIT_BYTES}:{FSIZE_LIMIT_BYTES}",
        "--mount", f"type=bind,source={folder},target={WORKDIR},readonly",
        "-w", WORKDIR,
    ]
    for item in _CONTAINER_ENV:
        args.extend(["-e", item])
    args.append(image)
    args.extend(command)
    return args


def open_to_container(folder: str) -> None:
    """A temp folder is private to the server's user (mode 700). The container user is a different
    user, so let it read the folder. It still cannot write: the mount is read-only."""
    if os.name == "nt":
        return
    os.chmod(folder, 0o755)
    for entry in os.scandir(folder):
        os.chmod(entry.path, 0o644)


def docker_reachable(image: str = IMAGE) -> bool:
    """True when the docker CLI exists, its daemon answers and the image is installed."""
    if not shutil.which("docker"):
        return False
    try:
        for command in (["docker", "info"], ["docker", "image", "inspect", image]):
            if subprocess.run(command, capture_output=True, timeout=5.0, env=cli_env()).returncode != 0:
                return False
        return True
    except Exception:
        return False


def kill_container(name: str) -> None:
    """Best effort: stop a container that may already be gone."""
    try:
        subprocess.run(["docker", "kill", name], capture_output=True, timeout=CLI_TIMEOUT_SECONDS, env=cli_env())
    except Exception:
        pass


def remove_container(name: str) -> None:
    """Best effort: make sure no container is left behind."""
    try:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=CLI_TIMEOUT_SECONDS, env=cli_env())
    except Exception:
        pass


def docker_failure(stderr: str) -> Optional[str]:
    """When `docker run` failed in Docker itself (not in the learner's program), why. Else None."""
    text = stderr.strip()
    if not (
        text.startswith("docker:")
        or "Error response from daemon" in text
        or "Cannot connect to the Docker daemon" in text
    ):
        return None
    if "No such image" in text or "Unable to find image" in text:
        return f"The image {IMAGE} is not installed. Run: docker pull {IMAGE}"
    return f"Docker could not start the run: {text.splitlines()[0][:300]}"
