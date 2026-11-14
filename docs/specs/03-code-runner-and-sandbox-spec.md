# Specification 03: Code Execution Sandbox & Runner Specification

- **Status:** Accepted (2026-11-09, by the owner, as built). Was a draft.
- **Governed By:** 
  - `ADR-0005: Defer Kubernetes in Favor of Container-Isolated Runners`
  - `docs/specs/01-lesson-and-curriculum-spec.md` Section 3.2
- **Domain:** Untrusted Code Execution, Security Isolation & Assertion Verification
- **Date:** 2026-10-30

---

## 1. Purpose & Architectural Context

Learners write and execute untrusted Python code to fulfill unit requirements.
Because this code originates from learners (or AI-generated snippets), the execution runtime must be **strictly bounded and secured** against:
1. Infinite loops (resource hogging).
2. Memory exhaustion (OOM attacks).
3. Network egress / crypto-mining / data exfiltration.
4. Host filesystem tampering.

---

## 2. Hardened Sandbox Constraints

### 2.1 Production Docker Runner (`DockerRunner`)
Governed by ADR-0036. Every learner program, interactive or not, runs in its own ephemeral container made with `docker run`:

* **Image:** `python:3.14-slim`, `--pull never` (a missing image is a deployment error, never a hidden download).
* **Network:** `--network none`.
* **Quotas (one set, shared with README):** `--memory 256m --memory-swap 256m` (no swap), `--cpus 0.5`, `--pids-limit 64`, `--ulimit nofile=64:64`, `--ulimit fsize=1048576:1048576`.
* **Filesystem:** `--read-only` root; `--tmpfs /tmp:rw,noexec,nosuid,size=16m`; the run folder is bind-mounted read-only at `/work` (`--mount type=bind,...,readonly`), the working directory.
* **Privilege:** `--user 65534:65534`, `--cap-drop ALL`, `--security-opt no-new-privileges`.
* **Environment:** no host variable is passed. Only `PYTHONIOENCODING`, `PYTHONUTF8`, `PYTHONDONTWRITEBYTECODE` are set in the container.
* **Name:** unique per run (`lms-run-<uuid4 hex>`), used to kill and remove it.
* **Wall-clock timeout:** `timeout_seconds` plus a 3 s start-up allowance, then `docker kill <name>`. The result is the same timed-out result as the subprocess runner.
* **Output:** stdout and stderr together are capped at 64 KB; past the cap the container is killed and the output ends with a stop note.
* **Cleanup:** whatever happens (success, timeout, crash, cap), the container is removed (`docker rm -f`) and the temp folder deleted.
* **Inputs:** `code`, `test_code`, `stdin_input` and extra `files` behave as in `SubprocessRunner`; extra file names are checked with `extra_file_problem` (a bad name raises `ValueError`).
* **Interactive runs** (SPEC-12 section 7): `DockerInteractiveRun` starts the same container with `-i` and the same harness. The `input()` token protocol, event types and `RunLimits` (CPU, wall, output) are unchanged. Stop, wall-clock expiry and the output limit all end with `docker kill` and `docker rm -f`.

### 2.2 Local / Offline Subprocess Runner (`SubprocessRunner`)
* **Not a sandbox.** Development and CI only, selected explicitly with `LMS_RUNNER=subprocess`.
* Python `subprocess.run` with a strict timeout, a temp directory that is deleted afterwards, and a cleaned environment (no keys or `.env` values).

### 2.3 Fail closed
If Docker cannot be used (CLI missing, daemon down, image absent), `DockerRunner` raises `RunnerUnavailable` and runs nothing. The API answers HTTP 503 (`Code runner unavailable`), or a WebSocket `error` event. It never runs the code another way. The run slot taken for the attempt is given back.

### 2.4 Hidden checks (audit step A6b, ADR-0036 amendment)
Hidden checks are answer material, so the learner's program must not be able to read them.

* `run_tests.py` is fixed text (`check_harness.HARNESS`) with no checks in it. It is the only extra file in the run folder.
* The checks (`test_code`) are sent as the first line of stdin (JSON `{"checks": ...}`). The learner's own `stdin_input` follows that line. `ICodeRunner.execute()` is unchanged.
* The harness reads that line a byte at a time (no stdio buffer keeps a copy), compiles it under the file name `<hidden-checks>`, wipes the bytes, and only then imports `solution`. So the checks are not in a file, in `argv`, in the environment, in `/proc/self/cmdline`, or in `linecache`, and a traceback shows no check source line.
* `DockerRunner` and `SubprocessRunner` use the same harness.
* **Names and scope.** The checks run with the names they always had: `sys`, `builtins`, `Path` and `__name__ == "__main__"`. A `SystemExit` raised while importing the learner's module no longer skips the checks.
* **Feedback.** A failing traceback has no check source line. So a check should carry a message (`assert f(2) == 4, "f(2) should be 4"`): a bare `assert` now reports only `AssertionError`. This is deliberate, because that source line was the leak.
* **Still open.** A learner program that calls `os._exit(0)` at import ends the run with exit code 0 before any check runs, so it passes. This is old behaviour. A completion sentinel from the harness would close it.
* **What this does not close.** The compiled checks and the learner's functions run in one Python process. A program written to attack the grader can still walk the calling frames, at import time or while a check runs, or scan its own memory (a test run found one residue copy of the check text there). Fully closing it needs the learner's code and the checks in separate processes. That is future work.
* **What the subprocess runner cannot guarantee.** It runs as the server's user, on the host, so a learner's program can read anything that user can read, including the private answers folder (`LMS_ANSWERS_DIR`). Hiding the checks from the program is only meaningful in Docker.
* `lms check` uses `get_code_runner()` and follows `LMS_RUNNER`. With Docker down it refuses with a message that names `docker pull` and `LMS_RUNNER=subprocess`.

---

## 3. Data Contract (`ExecutionResult`)

```python
class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    assertion_errors: List[str] = []
```

### 3.1 Verification & Assertion Injection
When `test_code` is provided:
1. The student's code is written to `solution.py`.
2. The verification test code is sent on stdin to the harness (section 2.4).
3. The runner executes a deterministic assertion harness (`run_tests.py`); the checks reach it on stdin, never as a file (section 2.4).
4. If an `AssertionError` is raised, it is parsed and extracted into `assertion_errors`.

---

## 4. Runner Factory (no silent fallback)

```python
def get_code_runner(mode: Optional[str] = None) -> ICodeRunner:
    """mode is LMS_RUNNER when None: docker (default) | subprocess | auto."""
```

| `LMS_RUNNER` | Result |
| :--- | :--- |
| unset or `docker` | `DockerRunner`. If Docker is unreachable, start-up logs an error and every run is refused (section 2.3). |
| `subprocess` | `SubprocessRunner`, with a start-up warning that it is not a sandbox. |
| `auto` | `DockerRunner` when Docker is reachable at start-up, else `SubprocessRunner` with a warning. |
| anything else | `ValueError`: the app does not start. |

The chosen runner and its availability are logged once at start-up.

---

## 5. Non-Functional Requirements (NFRs)

1. **Sub-second Execution:** For non-looping code, execution round-trip must complete in $< 800$ms.
2. **Deterministic Cleanup:** Every temp file and container must be destroyed even if execution aborts, times out, or crashes.
3. **No Zombie Containers:** Container names are unique; `--rm` is set and `docker rm -f` runs in a `finally` block.
4. **Start-up allowance:** Container start-up (about 0.3 to 1 s) is outside the sub-second target in NFR 1; that target applies to the subprocess runner.
