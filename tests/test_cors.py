"""Tests for CORS origins (ADR-0015 decision 5)."""

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import create_app


def allowed_origin_header(origin: str):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=CurriculumCatalog()
    )
    res = TestClient(app).get("/api/v1/health", headers={"Origin": origin})
    return res.headers.get("access-control-allow-origin")


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_vite_dev_server_is_allowed_by_default(monkeypatch, origin):
    monkeypatch.delenv("LMS_ALLOWED_ORIGINS", raising=False)

    assert allowed_origin_header(origin) == origin


def test_other_origins_are_refused_by_default(monkeypatch):
    monkeypatch.delenv("LMS_ALLOWED_ORIGINS", raising=False)

    assert allowed_origin_header("https://evil.example") is None


def test_env_replaces_the_default_origins(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_ORIGINS", "https://a.example, https://b.example")

    assert allowed_origin_header("https://a.example") == "https://a.example"
    assert allowed_origin_header("https://b.example") == "https://b.example"
    assert allowed_origin_header("http://localhost:5173") is None


def test_wildcard_in_env_is_never_honoured(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_ORIGINS", "*, https://a.example")

    assert allowed_origin_header("https://evil.example") is None
    assert allowed_origin_header("https://a.example") == "https://a.example"
