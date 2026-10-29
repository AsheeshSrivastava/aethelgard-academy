from fastapi.testclient import TestClient
import pytest
from lms.api.app import create_app
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.runner.subprocess_runner import SubprocessRunner


@pytest.fixture
def client():
    # Dependency injection for test isolation
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    runner = SubprocessRunner()
    axis = MockAxisCompanion()

    app = create_app(repo=repo, runner=runner, axis=axis)
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_units(client):
    response = client.get("/api/v1/units")
    assert response.status_code == 200
    units = response.json()
    assert len(units) >= 25


def test_list_units_by_stage(client):
    response = client.get("/api/v1/units?stage=0")
    assert response.status_code == 200
    units = response.json()
    assert all(u["stage"] == 0 for u in units)


def test_get_unit_detail(client):
    response = client.get("/api/v1/units/PY-0.4")
    assert response.status_code == 200
    data = response.json()
    assert data["unit_id"] == "PY-0.4"
    assert "Run a first program" in data["title"]
    assert len(data["methods"]) > 0


def test_get_unit_not_found(client):
    response = client.get("/api/v1/units/PY-999.9")
    assert response.status_code == 404


def test_execute_code(client):
    payload = {
        "code": "print('Gateway code execution verified')",
        "test_code": None,
        "timeout_seconds": 5.0,
    }
    response = client.post("/api/v1/execute", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "Gateway code execution verified" in res["stdout"]


def test_axis_consult_socratic(client):
    payload = {
        "learner_id": "student_api_01",
        "unit_id": "PY-1.2",
        "mode": "Socratic",
        "current_activity": "Predict",
        "user_prompt": "What does '10' + 5 do?",
        "learner_code": "x = '10' + 5",
    }
    response = client.post("/api/v1/axis/consult", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "?" in res["reply"]
    assert len(res["cited_concepts"]) > 0


def test_learner_progress_and_ledger(client):
    learner_id = "test_user_42"

    # Save progress
    progress_payload = {"unit_id": "PY-0.4", "status": "Completed"}
    post_res = client.post(f"/api/v1/learners/{learner_id}/progress", json=progress_payload)
    assert post_res.status_code == 200
    assert post_res.json()["success"] is True

    # Query ledger (initially empty)
    ledger_res = client.get(f"/api/v1/learners/{learner_id}/ledger")
    assert ledger_res.status_code == 200
    assert isinstance(ledger_res.json(), list)
