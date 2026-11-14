# ADR 0036: The Docker runner is the default, and the app fails closed

- **Status:** Accepted (owner decision, 2026-11-14, independent-audit step A6)
- **Decider:** Owner (Asheesh Ranjan Srivastava)
- **Date:** 2026-11-14
- **Governed by:** ADR-0005 (container-isolated runners), SPEC-03, SPEC-12 section 7
- **Amends:** ADR-0005 limits (128 MB, 1 CPU) become 256 MB, 0.5 CPU. See section 2.4.

---

## 1. Context & Problem Statement

Until now `DockerRunner.execute()` never used Docker: it called the subprocess runner whether or not Docker was present, and `get_code_runner()` fell back to the subprocess runner without saying so. The subprocess runner is not a sandbox: learner code can read the host's files and use its network. The audit (2026-11-09) rated this as the blocking finding for letting anyone but the owner run code. A silent fallback is the worst form of it, because the deployment looks safe and is not.

## 2. Decision

1. **Default to Docker.** `LMS_RUNNER` is `docker` when unset. `get_code_runner()` returns a real `DockerRunner` that runs every learner program in an ephemeral container.
2. **Fail closed.** If Docker is missing, its daemon is down, or the image is absent, a run is refused with a clear error (HTTP 503 `Code runner unavailable`; a WebSocket `error` event). The code is never run another way. The app still starts, so lessons, progress and AXIS keep working. Start-up logs the active runner and whether it is reachable.
3. **Other modes are explicit.**
   - `LMS_RUNNER=subprocess`: the old behaviour, for development and CI. Logged as a warning at start-up. It is not a sandbox.
   - `LMS_RUNNER=auto`: Docker when reachable at start-up, else subprocess, with a warning. For a developer laptop only.
   - Any other value stops the app at start-up.
4. **Limits (one set, used by code, README and SPEC-03):** 256 MB memory with the same swap limit, 0.5 CPU, 64 processes, 64 open files, 1 MB file size, a 16 MB `noexec` `/tmp`, output capped at 64 KB, wall-clock timeout then `docker kill`. These replace the 128 MB and 1 CPU of ADR-0005, which left no room for the Python 3.14 interpreter plus a small data set, and which the README already contradicted.
5. **Interactive runs use the same container profile** (SPEC-12 section 7): same `input()` token protocol and `RunLimits`, so the browser sees the same events. Both kinds of run take a slot from the A4 cap.
6. **No image pulls at run time.** `--pull never`: a missing image is a deployment error with a clear fix (`docker pull`), not a hidden download that eats the run's time.

## 3. Consequences

- Positive: running strangers' code is possible once Docker is present. The protection is the container, not trust in the learner.
- Negative: a machine without Docker cannot run code unless the owner opts in with `LMS_RUNNER=subprocess`. CI and the Playwright server set that explicitly.
- Negative: each run pays container start-up (roughly 0.3 to 1 s). The timeout adds a fixed 3 s start-up allowance so a slow start does not fail a correct program.
- Residual risk: Docker shares the host kernel. Rootless Docker or gVisor is the next hardening step, not part of this change.
- The Docker CLI is the only integration point. Replacing it with the Docker API client later changes one module.

---

## 4. Amendment (2026-11-14, audit step A6b): hidden checks and `lms check`

- **Hidden checks are no longer written to the run folder.** They go to the harness on stdin and are compiled and wiped before the learner's module is imported (SPEC-03 section 2.4). Passive reads (files, cwd, `/proc/self/cmdline`, argv, environment, `linecache`) find nothing, in Docker and in the subprocess runner.
- **Plain limits:** a program written to attack the grader can still reach the checks, because they run in the same process as the learner's functions; and the subprocess runner can read the private answers folder because it runs as the server's user. Separate processes are the real fix and are not part of this change.
- **`lms check` follows `LMS_RUNNER`** like the server. With Docker down it refuses with a clear message instead of running the file unsandboxed.
