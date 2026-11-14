"""Audit step A5 (independent audit 2026-11-09): importing lms.api.app must do no work. The module
used to end with `app = create_app()`, so any import (a test, a script, openapi dump) opened the
database, read the curriculum and built the AI router. The server now starts through a factory."""

import subprocess
import sys

import lms
from lms.api import app as app_module


def test_importing_the_module_builds_no_app_and_creates_no_database(tmp_path):
    code = (
        "import sys, lms.api.app as m; "
        "print(hasattr(m, 'app')); print('lms.api.app' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={"PATH": "", "LMS_DB_PATH": str(tmp_path / "lms_state.db")},
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False", "True"]
    assert list(tmp_path.iterdir()) == []  # no database, no other file


def test_the_module_has_no_module_level_app():
    assert not hasattr(app_module, "app")


def test_a_factory_for_the_server_builds_a_working_app(tmp_path, monkeypatch):
    monkeypatch.setenv("LMS_DB_PATH", str(tmp_path / "lms_state.db"))
    application = app_module.create_default_app()
    assert application.title


def test_serve_starts_uvicorn_in_factory_mode(monkeypatch):
    calls = []
    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(sys, "argv", ["lms", "serve", "--port", "8123"])
    lms.main()

    (args, kwargs), = calls
    assert args == ("lms.api.app:create_default_app",)
    assert kwargs["factory"] is True
    assert kwargs["port"] == 8123
