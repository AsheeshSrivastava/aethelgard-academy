"""Audit step A4 (independent audit 2026-11-09): code runs must be capped. Each run is a process,
so without a cap a burst of /execute calls or run sockets can exhaust the machine. When every slot
is taken a new run is refused at once: HTTP 429 with Retry-After, or a WebSocket error message."""

import threading

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.run_slots import CappedRunner, RunBusy, RunSlots, max_runs_from_env
from lms.api.app import create_app
from lms.core.interfaces import ExecutionResult


class BlockingRunner:
    """A runner whose runs stay open until the test lets them finish."""

    def __init__(self):
        self.entered = threading.Semaphore(0)
        self.release = threading.Event()

    def execute(self, code, test_code=None, timeout_seconds=5.0, stdin_input=None, files=None):
        self.entered.release()
        self.release.wait(timeout=10)
        return ExecutionResult(success=True, stdout="ok", stderr="", exit_code=0, duration_ms=1)


def make_client(runner, max_runs):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo, runner=runner, axis=MockAxisCompanion(), catalog=CurriculumCatalog(), max_concurrent_runs=max_runs
    )
    return TestClient(app)


def start_blocked_run(client, runner):
    """Take one slot: a run that does not finish until runner.release is set."""
    result = {}

    def call():
        result["response"] = client.post("/api/v1/execute", json={"code": "print(1)"})

    thread = threading.Thread(target=call)
    thread.start()
    assert runner.entered.acquire(timeout=5), "the run never started"
    return thread, result


def test_slots_hand_out_at_most_the_limit_and_take_a_slot_back_when_released():
    slots = RunSlots(2)
    assert slots.try_acquire() and slots.try_acquire()
    assert not slots.try_acquire()
    slots.release()
    assert slots.try_acquire()


def test_a_limit_below_one_is_refused():
    with pytest.raises(ValueError):
        RunSlots(0)


def test_execute_answers_429_when_every_slot_is_taken():
    runner = BlockingRunner()
    client = make_client(runner, max_runs=1)
    thread, first = start_blocked_run(client, runner)
    try:
        busy = client.post("/api/v1/execute", json={"code": "print(2)"})
        assert busy.status_code == 429
        assert busy.headers["content-type"].startswith("application/problem+json")
        assert int(busy.headers["retry-after"]) >= 1
    finally:
        runner.release.set()
        thread.join(timeout=10)
    assert first["response"].status_code == 200
    assert client.post("/api/v1/execute", json={"code": "print(3)"}).status_code == 200


def test_a_slot_is_given_back_when_the_runner_raises():
    class Failing:
        def execute(self, **kwargs):
            raise RuntimeError("runner broke")

    client = make_client(Failing(), max_runs=1)
    quiet = TestClient(client.app, raise_server_exceptions=False)
    assert quiet.post("/api/v1/execute", json={"code": "x"}).status_code == 500
    assert quiet.post("/api/v1/execute", json={"code": "x"}).status_code == 500  # not 429


def test_a_run_socket_gets_an_error_message_when_every_slot_is_taken():
    runner = BlockingRunner()
    client = make_client(runner, max_runs=1)
    thread, _ = start_blocked_run(client, runner)
    try:
        with client.websocket_connect("/api/v1/runs") as ws:
            ws.send_json({"type": "start", "files": {"solution.py": "print(1)"}, "entry": "solution.py"})
            event = ws.receive_json()
        assert event["type"] == "error"
        assert "busy" in event["message"].lower()
    finally:
        runner.release.set()
        thread.join(timeout=10)


def test_a_finished_run_socket_gives_its_slot_back():
    client = make_client(BlockingRunner(), max_runs=1)
    for _ in range(2):
        with client.websocket_connect("/api/v1/runs") as ws:
            ws.send_json({"type": "start", "files": {"solution.py": "print(1)"}, "entry": "solution.py"})
            events = []
            for _ in range(50):  # bounded: a stuck run fails the test instead of hanging CI
                events.append(ws.receive_json())
                if events[-1]["type"] in ("exit", "error"):
                    break
        assert events[-1]["type"] == "exit", events


def test_the_capped_runner_refuses_when_full_and_gives_the_slot_back_after_an_error():
    class Broken:
        def execute(self, **kwargs):
            raise RuntimeError("boom")

    slots = RunSlots(1)
    capped = CappedRunner(Broken(), slots)
    with pytest.raises(RuntimeError):
        capped.execute(code="x")
    assert slots.try_acquire()  # the failed run gave its slot back
    with pytest.raises(RunBusy):
        capped.execute(code="x")


@pytest.mark.parametrize("raw, expected", [("", 4), ("7", 7), ("0", 4), ("-2", 4), ("abc", 4), ("\u00b2", 4)])
def test_the_limit_comes_from_the_environment_and_a_bad_value_falls_back(monkeypatch, raw, expected):
    monkeypatch.setenv("LMS_MAX_CONCURRENT_RUNS", raw)
    assert max_runs_from_env() == expected
