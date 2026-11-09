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
* **Base Image:** `python:3.14-slim` (minimal attack surface).
* **Network Isolation:** `--network none` (zero internet access).
* **Resource Quotas (Cgroups):**
  * Memory: `--memory 128m` (strict 128 megabytes cap).
  * CPU: `--cpus 1.0` (maximum 1 physical CPU core).
  * PIDs: `--pids-limit 64` (prevents fork bombs).
* **Filesystem Security:**
  * Root filesystem mounted read-only: `--read-only`.
  * Ephemeral temp volume for execution: `--tmpfs /tmp:rw,size=16m,noexec`.
* **Execution Timeout:** Strict 5.0 seconds maximum wall-clock time.

### 2.2 Local / Offline Subprocess Runner (`SubprocessRunner`)
* Used for instant offline development and local environments where the Docker daemon is inactive.
* Employs Python `subprocess.run` with:
  * Strict `timeout=5.0`.
  * AST import validation (disallowing dangerous OS/sys calls when untrusted mode is active).
  * Isolated temp directory cleanup.

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
2. The verification test code is written to `test_solution.py`.
3. The runner executes `pytest` or a deterministic assertion harness.
4. If an `AssertionError` is raised, it is parsed and extracted into `assertion_errors`.

---

## 4. Runner Factory & Fallback Strategy

```python
def get_code_runner(prefer_docker: bool = True) -> ICodeRunner:
    """Factory that returns DockerRunner if daemon is running, else SubprocessRunner."""
```

---

## 5. Non-Functional Requirements (NFRs)

1. **Sub-second Execution:** For non-looping code, execution round-trip must complete in $< 800$ms.
2. **Deterministic Cleanup:** Every temp file and container must be destroyed even if execution aborts, times out, or crashes.
3. **No Zombie Containers:** Container names must be unique UUIDs with `--rm` enabled to ensure automatic cleanup.
