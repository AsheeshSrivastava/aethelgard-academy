"""Interactive runs with live output and input() pausing.

Governed by SPEC-12 section 7 and ADR-0005. One run is one child process. Its
output arrives as events, and it stops when it hits a limit or the caller leaves.

The harness runs inside the child: it marks each input() call on stdout with a
random token, watches CPU time, and blocks Python sockets. This is not an OS
sandbox; hosting other people's code needs the Docker runner.
"""

from dataclasses import dataclass
import codecs
import os
from pathlib import Path
import queue
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, ClassVar, Dict, List, Optional, Set

MAX_SOURCE_CHARS = 512_000
_FILE_NAME = re.compile(r"^[A-Za-z0-9_-]+\.py$")
_ENV_ALLOWED = ("PATH", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG")

HARNESS = r'''
import builtins, os, runpy, socket, sys, threading, time, traceback



class _NoNetwork:
    def __init__(self, *args, **kwargs):
        raise OSError("Network access is disabled in this run.")


def _install(token, cpu_limit):
    """A closure, so learner code cannot reach the token through a global name."""

    def _input(prompt=""):
        sys.stdout.write(str(prompt))
        sys.stdout.write(token)
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not line:
            raise EOFError("EOF when reading a line")
        return line.rstrip("\n")

    def _watch_cpu():
        while True:
            time.sleep(0.05)
            if time.process_time() > cpu_limit:
                sys.stderr.write("\nStopped: the CPU time limit was reached.\n")
                sys.stderr.flush()
                os._exit(137)

    builtins.input = _input
    threading.Thread(target=_watch_cpu, daemon=True).start()


entry = sys.argv[2]
_install(sys.argv[1], float(sys.argv[3]))
sys.argv = [entry]
sys.orig_argv = [entry]
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(newline="\n")
sys.stderr.reconfigure(newline="\n")
socket.socket = _NoNetwork
try:
    runpy.run_path(entry, run_name="__main__")
except SystemExit:
    raise
except BaseException:
    kind, value, trace = sys.exc_info()
    traceback.print_exception(kind, value, trace.tb_next.tb_next if trace.tb_next else trace)
    sys.exit(1)
'''


@dataclass(frozen=True)
class RunLimits:
    cpu_seconds: float = 5.0
    wall_seconds: float = 120.0
    output_bytes: int = 64 * 1024


def safe_env() -> Dict[str, str]:
    """Only what Python needs. Learner code must never see keys or .env values."""
    env = {k: os.environ[k] for k in _ENV_ALLOWED if k in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def valid_start(files: Dict[str, str], entry: str) -> Optional[str]:
    """Why a start message must be refused, or None when it is fine."""
    if not files:
        return "A run needs at least one file."
    if any(not _FILE_NAME.match(name) for name in files):
        return "File names must be plain names ending in .py."
    if entry not in files:
        return "The entry file must be one of the files."
    if sum(len(source) for source in files.values()) > MAX_SOURCE_CHARS:
        return "The files are too large to run."
    return None


class InteractiveRun:
    """One running program. Read events with next_event(); stop it with stop()."""

    _active: ClassVar[Set["InteractiveRun"]] = set()

    def __init__(self, files: Dict[str, str], entry: str, limits: RunLimits = RunLimits()):
        self.limits = limits
        self._events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._token = f"\x01{secrets.token_hex(16)}\x02"
        self._output = 0
        self._timed_out = False
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self._dir = tempfile.TemporaryDirectory()

        for name, source in files.items():
            Path(self._dir.name, name).write_text(source, encoding="utf-8")
        harness = Path(self._dir.name, "lms_run_harness.py")
        harness.write_text(HARNESS, encoding="utf-8")

        self._process = subprocess.Popen(
            [sys.executable, "-u", str(harness), self._token, entry, str(limits.cpu_seconds)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._dir.name,
            env=safe_env(),
        )
        InteractiveRun._active.add(self)
        self._readers = [
            threading.Thread(target=self._read_stream, args=(self._process.stdout, "stdout"), daemon=True),
            threading.Thread(target=self._read_stream, args=(self._process.stderr, "stderr"), daemon=True),
        ]
        for reader in self._readers:
            reader.start()
        threading.Thread(target=self._wait, daemon=True).start()

    @classmethod
    def active_count(cls) -> int:
        return len(cls._active)

    def next_event(self, timeout: float) -> Optional[Dict[str, Any]]:
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_stdin(self, line: str) -> None:
        try:
            self._process.stdin.write((line + "\n").encode("utf-8"))
            self._process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass

    def stop(self) -> None:
        if self._process.poll() is None:
            self._process.kill()
        self._process.wait()
        InteractiveRun._active.discard(self)

    def _emit_output(self, kind: str, data: str) -> None:
        """Send output within the limit; past it, stop the program."""
        if not data:
            return
        with self._lock:
            room = self.limits.output_bytes - self._output
            sent = data[: max(room, 0)]
            self._output += len(data)
        if sent:
            self._events.put({"type": kind, "data": sent})
        if len(sent) < len(data) and not self._timed_out:
            self._timed_out = True
            self._events.put({"type": "stderr", "data": "\nStopped: the output limit was reached.\n"})
            self._process.kill()

    def _read_stream(self, stream: Any, kind: str) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        token = self._token
        pending = ""
        while True:
            chunk = os.read(stream.fileno(), 4096)
            if not chunk:
                break
            pending += decoder.decode(chunk)
            while token in pending:
                before, pending = pending.split(token, 1)
                self._emit_output(kind, before)
                self._events.put({"type": "awaiting_input"})
            # Hold back anything that could be the start of a token split across reads.
            keep = next((n for n in range(min(len(token) - 1, len(pending)), 0, -1) if token.startswith(pending[-n:])), 0)
            cut = len(pending) - keep
            self._emit_output(kind, pending[:cut])
            pending = pending[cut:]
        self._emit_output(kind, pending)

    def _wait(self) -> None:
        try:
            self._process.wait(timeout=self.limits.wall_seconds)
        except subprocess.TimeoutExpired:
            self._timed_out = True
            self._process.kill()
            self._process.wait()
        for reader in self._readers:
            reader.join(timeout=2)
        code = self._process.returncode
        InteractiveRun._active.discard(self)
        self._events.put(
            {
                "type": "exit",
                "code": code,
                "duration_ms": round((time.monotonic() - self._started) * 1000, 1),
                "timed_out": self._timed_out or code == 137,
            }
        )
        self._dir.cleanup()
