"""POST /execute must not let a client pick any timeout. A huge value would let one request hold a
run slot (A4) for as long as the program runs. The server limit is 5 seconds, the same as RunLimits."""

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import MAX_EXECUTE_TIMEOUT_SECONDS, create_app


@pytest.fixture
def client():
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=CurriculumCatalog())
    return TestClient(app)


def post(client, **fields):
    return client.post("/api/v1/execute", json={"code": "print(1)", **fields})


def test_the_limit_is_the_servers_own_run_limit():
    assert MAX_EXECUTE_TIMEOUT_SECONDS == 5.0


@pytest.mark.parametrize("timeout", [5.1, 60, 1e9])
def test_a_timeout_above_the_limit_is_refused(client, timeout):
    assert post(client, timeout_seconds=timeout).status_code == 422


@pytest.mark.parametrize("timeout", [0, -1])
def test_a_timeout_of_zero_or_less_is_refused(client, timeout):
    assert post(client, timeout_seconds=timeout).status_code == 422


@pytest.mark.parametrize("fields", [{}, {"timeout_seconds": 1}, {"timeout_seconds": 5}])
def test_a_timeout_within_the_limit_runs(client, fields):
    response = post(client, **fields)
    assert response.status_code == 200
    assert response.json()["stdout"].strip() == "1"
