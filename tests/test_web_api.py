"""Tests for Web Platform API Gateway Endpoints.

Validates:
- GET /api/v1/concepts (search & list)
- POST /api/v1/explain (CO-6 evaluation & evidence logging)
- GET /api/v1/units/{unit_id} (full lesson metadata & concept check)
- GET / (serves HTML single-page platform shell)
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.concepts import ConceptCatalog
from lms.adapters.curriculum.loader import CurriculumCatalog, load_roadmap_from_file
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import create_app


@pytest.fixture
def test_client(tmp_path: Path):
    db_file = tmp_path / "test_web_lms.db"
    repo = SQLiteLearnerRepository(db_path=str(db_file))
    repo.initialize()

    runner = SubprocessRunner()
    axis = MockAxisCompanion()
    
    roadmap_path = Path("reference/Python Subject Roadmap v3.md")
    catalog = load_roadmap_from_file(roadmap_path) if roadmap_path.exists() else CurriculumCatalog()

    app = create_app(repo=repo, runner=runner, axis=axis, catalog=catalog)
    return TestClient(app), repo


def test_list_and_search_concepts(test_client):
    client, _ = test_client
    # List all
    res = client.get("/api/v1/concepts")
    assert res.status_code == 200
    concepts = res.json()
    assert len(concepts) >= 5
    ids = [c["concept_id"] for c in concepts]
    assert "built-in-input" in ids
    assert "sequential-execution" in ids

    # Search
    search_res = client.get("/api/v1/concepts?search=input")
    assert search_res.status_code == 200
    filtered = search_res.json()
    assert any("input" in c["name"].lower() for c in filtered)


def test_unit_full_metadata(test_client):
    client, _ = test_client
    res = client.get("/api/v1/units/PY-0.1")
    assert res.status_code == 200
    data = res.json()
    assert data["unit_id"] == "PY-0.1"
    # Should have lesson_markdown loaded from curriculum package
    assert data.get("lesson_markdown") is not None
    assert "Intake Reception Desk" in data["lesson_markdown"]


def test_explain_endpoint_solid(test_client):
    client, repo = test_client
    payload = {
        "unit_id": "PY-0.1",
        "explanation": "Statements execute top-to-bottom sequentially; input() returns unparsed string characters that must be converted before arithmetic.",
        "learner_id": "test_learner",
    }
    res = client.post("/api/v1/explain", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["unit_id"] == "PY-0.1"
    assert body["status"] == "Solid"
    assert body["evidence_logged"] is True

    # Check evidence logged in DB
    ledger = repo.get_evidence_ledger(learner_id="test_learner")
    assert len(ledger) >= 1
    assert ledger[0].skill_id == "CO-6"
    assert "Solid" in (ledger[0].observed_reasoning or "")


def test_explain_endpoint_shaky(test_client):
    client, repo = test_client
    payload = {
        "unit_id": "PY-0.1",
        "explanation": "Because it is code.",
        "learner_id": "test_learner_2",
    }
    res = client.post("/api/v1/explain", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["unit_id"] == "PY-0.1"
    assert body["status"] == "Shaky"
    assert body["evidence_logged"] is True


def test_execute_endpoint_with_stdin(test_client):
    client, _ = test_client
    code = (
        "name = input('Name: ')\n"
        "print(f'HELLO {name}')\n"
    )
    res = client.post(
        "/api/v1/execute",
        json={"code": code, "stdin_input": "Kofi Mensah\n"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "HELLO Kofi Mensah" in body["stdout"]


def test_explain_error_endpoint(test_client):
    client, _ = test_client
    payload = {
        "unit_id": "PY-0.1",
        "code": "pritn('Hello')",
        "error": "NameError: name 'pritn' is not defined",
        "learner_id": "test_learner",
    }
    res = client.post("/api/v1/explain-error", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "explanation" in data
    assert len(data["explanation"]) > 0




def test_serves_landing_page(test_client):
    client, _ = test_client
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Aethelgard Academy" in res.text
