"""The run_tests.py harness, shared by the Docker and subprocess runners (SPEC-03 section 2.4).

The hidden checks are answer material. They must not sit in a file the learner's program can
open. So run_tests.py is fixed text with no checks in it. The checks arrive as the first line
of stdin (JSON), are compiled, and are dropped as text *before* the learner's module is
imported. They are compiled under the name "<hidden-checks>", so a traceback or linecache has
no source line to show. Whatever stdin_input the caller gave follows the checks line.
The line also carries a per-run completion token that the harness prints after the last check (ADR-0036 amendment 5).

What this closes: the learner's program cannot open a file, read the working folder, argv,
the environment, /proc/self/cmdline or linecache and find the checks.
What it does not close: the checks and the learner's functions run in one Python process, so a
program written to attack the grader (walk the calling frames, at import time or while a check
runs, or scan its own memory) could still see the compiled checks. Only a separate process can fix that.
"""

import json
import secrets

from lms.core.interfaces import ExecutionResult

HARNESS = r'''import builtins
import json
import os
import sys
from pathlib import Path


def _read_checks_line():
    """Read the first stdin line a byte at a time, so no stdio buffer keeps a copy, and return it
    as a bytearray the caller can wipe."""
    line = bytearray()
    while True:
        byte = os.read(0, 1)
        if not byte or byte == b"\n":
            return line
        line += byte


def _main():
    raw = _read_checks_line()
    payload = json.loads(raw)
    code = compile(payload["checks"], "<hidden-checks>", "exec")
    token = payload["token"]
    del payload
    for i in range(len(raw)):
        raw[i] = 0
    del raw
    sys.path.insert(0, ".")
    # The names the checks always had when they ran as the script itself.
    scope = {"__name__": "__main__", "sys": sys, "builtins": builtins, "Path": Path}
    real_input = builtins.input
    builtins.input = lambda *args, **kwargs: "Amara Okafor"  # a top-level input() must not hang the import
    try:
        exec("from solution import *", scope)
    except BaseException:  # includes SystemExit: sys.exit(0) at import must not skip the checks
        pass
    builtins.input = real_input
    exec(code, scope)
    for name, check in list(scope.items()):
        if name.startswith("test_") and callable(check):
            check()
    # The last thing the harness does. A program that ends the run early (os._exit(0)) never gets here.
    sys.stdout.write("\n" + token + "\n")
    sys.stdout.flush()


_main()
'''


def new_token() -> str:
    """A fresh random completion token for one run. It is never reused and never shown to the learner."""
    return "lms-complete-" + secrets.token_hex(16)


def check_stdin(checks: str, stdin_input: str | None, token: str) -> str:
    """What to send on stdin: the checks and the run's token as one JSON line, then the learner's own input."""
    return json.dumps({"checks": checks, "token": token}) + "\n" + (stdin_input or "")


def with_completion(result: ExecutionResult, token: str) -> ExecutionResult:
    """Exit code 0 alone proves nothing. A checked run succeeds only if the harness printed its token.

    The token line is removed from stdout, so the learner never sees it (SPEC-03 section 2.4).
    """
    framed = f"\n{token}\n"
    finished = framed in result.stdout
    update = {"stdout": result.stdout.replace(framed, "")}
    if result.success and not finished:
        update["success"] = False
        update["stderr"] = result.stderr + "The program ended before the checks finished.\n"
    return result.model_copy(update=update)
