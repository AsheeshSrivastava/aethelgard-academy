"""The run_tests.py harness, shared by the Docker and subprocess runners (SPEC-03 section 2.4).

The hidden checks are answer material. They must not sit in a file the learner's program can
open. So run_tests.py is fixed text with no checks in it. The checks arrive as the first line
of stdin (JSON), are compiled, and are dropped as text *before* the learner's module is
imported. They are compiled under the name "<hidden-checks>", so a traceback or linecache has
no source line to show. Whatever stdin_input the caller gave follows the checks line.

What this closes: the learner's program cannot open a file, read the working folder, argv,
the environment, /proc/self/cmdline or linecache and find the checks.
What it does not close: the checks and the learner's functions run in one Python process, so a
program written to attack the grader (walk the calling frames, at import time or while a check
runs, or scan its own memory) could still see the compiled checks. Only a separate process can fix that.
"""

import json

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
    code = compile(json.loads(raw)["checks"], "<hidden-checks>", "exec")
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


_main()
'''


def check_stdin(checks: str, stdin_input: str | None) -> str:
    """What to send on stdin: the checks as one JSON line, then the learner's own input."""
    return json.dumps({"checks": checks}) + "\n" + (stdin_input or "")
