"""Tests for interactive runs over WebSocket (SPEC-12 section 7)."""

import time

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.interactive import InteractiveRun, RunLimits, safe_env, valid_start
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app


def make_client(limits=None):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo,
        runner=SubprocessRunner(),
        axis=MockAxisCompanion(),
        catalog=CurriculumCatalog(),
        run_limits=limits,
    )
    return TestClient(app), repo


def collect(ws, stdin=()):
    """Read events until exit, answering each awaiting_input from `stdin`."""
    answers = list(stdin)
    events = []
    while True:
        event = ws.receive_json()
        events.append(event)
        if event["type"] == "awaiting_input":
            if answers:
                ws.send_json({"type": "stdin", "data": answers.pop(0)})
        if event["type"] in ("exit", "error"):
            return events


def run(code, stdin=(), limits=None):
    client, _ = make_client(limits)
    with client.websocket_connect("/api/v1/runs") as ws:
        ws.send_json({"type": "start", "files": {"solution.py": code}, "entry": "solution.py"})
        return collect(ws, stdin)


def text(events, kind):
    return "".join(e["data"] for e in events if e["type"] == kind)


def test_output_and_exit():
    events = run("print('hello')")

    assert text(events, "stdout") == "hello\n"
    exit_event = events[-1]
    assert exit_event["type"] == "exit"
    assert exit_event["code"] == 0
    assert exit_event["timed_out"] is False
    assert exit_event["duration_ms"] >= 0


def test_program_pauses_at_input_and_resumes():
    events = run("name = input('Name: ')\nprint('Hello', name)", stdin=["Amara"])

    kinds = [e["type"] for e in events]
    assert kinds.index("awaiting_input") < kinds.index("exit")
    assert text(events, "stdout") == "Name: Hello Amara\n"


def test_prompt_arrives_before_awaiting_input():
    events = run("input('Name: ')", stdin=["x"])

    pause = next(i for i, e in enumerate(events) if e["type"] == "awaiting_input")
    assert text(events[:pause], "stdout") == "Name: "


def test_several_inputs():
    events = run("a = input()\nb = input()\nprint(a + b)", stdin=["1", "2"])

    assert [e["type"] for e in events].count("awaiting_input") == 2
    assert text(events, "stdout") == "12\n"


def test_errors_arrive_on_stderr():
    events = run("print(undefined_name)")

    assert "NameError" in text(events, "stderr")
    assert events[-1]["code"] != 0
    assert "lms_run_harness" not in text(events, "stderr")


def test_learner_cannot_fake_a_pause_with_printed_text():
    events = run("print('AWAITING_INPUT')\nprint('\\x01')")

    assert "awaiting_input" not in [e["type"] for e in events]


def test_learner_code_cannot_read_the_pause_token():
    events = run("import sys\nprint(sys.argv, sys.orig_argv)")

    assert len(text(events, "stdout")) < 60
    assert "\\x01" not in text(events, "stdout")


def test_wall_clock_limit_ends_a_program_waiting_for_input():
    events = run("input()", limits=RunLimits(wall_seconds=0.5))

    assert events[-1]["type"] == "exit"
    assert events[-1]["timed_out"] is True


def test_cpu_limit_ends_a_busy_loop():
    started = time.monotonic()

    events = run("while True:\n    pass", limits=RunLimits(cpu_seconds=0.3, wall_seconds=30))

    assert events[-1]["timed_out"] is True
    assert time.monotonic() - started < 15


def test_output_limit_stops_a_flood():
    events = run("while True:\n    print('x' * 1000)", limits=RunLimits(output_bytes=4000, wall_seconds=30))

    assert len(text(events, "stdout")) <= 4000
    assert "output limit" in text(events, "stderr").lower()
    assert events[-1]["timed_out"] is True


def test_network_is_blocked():
    events = run("import socket\nsocket.socket()")

    assert events[-1]["code"] != 0
    assert "network" in text(events, "stderr").lower()


def test_secrets_are_not_in_the_environment(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_API_KEY", "not-for-learners")

    events = run("import os\nprint(os.environ.get('LOCAL_LLM_API_KEY'))")

    assert text(events, "stdout") == "None\n"


def test_batch_runner_does_not_share_secrets_either(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_API_KEY", "not-for-learners")

    result = SubprocessRunner().execute("import os\nprint(os.environ.get('LOCAL_LLM_API_KEY'))")

    assert result.stdout.strip() == "None"


def test_safe_env_keeps_only_what_python_needs(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "x")

    assert "MY_SECRET" not in safe_env()


def test_runs_write_no_evidence():
    client, repo = make_client()
    with client.websocket_connect("/api/v1/runs") as ws:
        ws.send_json({"type": "start", "files": {"solution.py": "print(1)"}, "entry": "solution.py", "exercise_id": "x"})
        collect(ws)

    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_files_can_import_each_other():
    client, _ = make_client()
    with client.websocket_connect("/api/v1/runs") as ws:
        ws.send_json(
            {
                "type": "start",
                "files": {"solution.py": "import helper\nprint(helper.X)", "helper.py": "X = 5"},
                "entry": "solution.py",
            }
        )
        events = collect(ws)

    assert text(events, "stdout") == "5\n"


@pytest.mark.parametrize(
    "files, entry",
    [
        ({"../evil.py": "x"}, "../evil.py"),
        ({"a/b.py": "x"}, "a/b.py"),
        ({"notes.txt": "x"}, "notes.txt"),
        ({"solution.py": "x"}, "other.py"),
        ({}, "solution.py"),
        ({"solution.py": "x" * 2_000_000}, "solution.py"),
    ],
)
def test_bad_start_is_refused(files, entry):
    assert valid_start(files, entry) is not None
    client, _ = make_client()
    with client.websocket_connect("/api/v1/runs") as ws:
        ws.send_json({"type": "start", "files": files, "entry": entry})

        assert ws.receive_json()["type"] == "error"


def test_first_message_must_be_start():
    client, _ = make_client()
    with client.websocket_connect("/api/v1/runs") as ws:
        ws.send_json({"type": "stdin", "data": "x"})

        assert ws.receive_json()["type"] == "error"


def test_disconnecting_stops_the_program():
    client, _ = make_client()
    with client.websocket_connect("/api/v1/runs") as ws:
        ws.send_json({"type": "start", "files": {"solution.py": "input()"}, "entry": "solution.py"})
        assert ws.receive_json()["type"] == "awaiting_input"

    assert InteractiveRun.active_count() == 0
