"""The code-run WebSocket refuses foreign Origins and Hosts (SPEC-12 section 7, ADR-0015 amendment).

A browser always sends Origin on a WebSocket handshake and never lets a web page change it, so
checking it stops any website from driving the runner. The Host check stops DNS rebinding.
"""

import pytest
from starlette.websockets import WebSocketDisconnect

from lms.api.app import allowed_hosts, origin_allowed

from test_runs_ws import make_client

START = {"type": "start", "files": {"solution.py": "print('hi')"}, "entry": "solution.py"}


def connect(client, headers):
    return client.websocket_connect("/api/v1/runs", headers=headers)


def refused(client, headers):
    with pytest.raises(WebSocketDisconnect):
        with connect(client, headers) as ws:
            ws.send_json(START)
            ws.receive_json()


def accepted(client, headers):
    with connect(client, headers) as ws:
        ws.send_json(START)
        events = []
        while True:
            event = ws.receive_json()
            events.append(event)
            if event["type"] in ("exit", "error"):
                return events


def test_foreign_origin_is_refused():
    client, _ = make_client()
    refused(client, {"origin": "https://evil.example"})


def test_foreign_origin_on_localhost_port_is_refused():
    client, _ = make_client()
    refused(client, {"origin": "http://localhost:9999"})


def test_null_origin_is_refused():
    client, _ = make_client()
    refused(client, {"origin": "null"})


def test_allowed_origin_connects():
    client, _ = make_client()
    events = accepted(client, {"origin": "http://localhost:5173"})
    assert events[-1]["type"] == "exit"


def test_own_origin_connects(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "localhost")
    client, _ = make_client()
    events = accepted(client, {"origin": "http://localhost:8000", "host": "localhost:8000"})
    assert events[-1]["type"] == "exit"


def test_own_origin_over_https_connects(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "localhost")
    client, _ = make_client()
    events = accepted(client, {"origin": "https://localhost:8000", "host": "localhost:8000"})
    assert events[-1]["type"] == "exit"


def test_origin_on_another_port_of_the_same_host_is_refused(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "localhost")
    client, _ = make_client()
    refused(client, {"origin": "http://localhost:9999", "host": "localhost:8000"})


def test_foreign_origin_with_no_host_is_refused():
    assert not origin_allowed("https://evil.example", None)
    assert not origin_allowed("null", "")


def test_missing_origin_connects_for_non_browser_clients():
    # The CLI and tests are not browsers and send no Origin. Only browsers are the threat here.
    client, _ = make_client()
    assert accepted(client, {})[-1]["type"] == "exit"


def test_foreign_host_is_refused(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "localhost,127.0.0.1")
    client, _ = make_client()
    refused(client, {"host": "evil.example", "origin": "http://evil.example"})


def test_foreign_host_with_allowed_origin_is_refused(monkeypatch):
    # DNS rebinding: the page's origin is the attacker's name, so the Host is what gives it away.
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "localhost,127.0.0.1")
    client, _ = make_client()
    refused(client, {"host": "rebind.example:8000", "origin": "http://localhost:5173"})


def test_foreign_host_is_refused_on_http_too(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "localhost,127.0.0.1")
    client, _ = make_client()
    assert client.get("/api/v1/health", headers={"host": "evil.example"}).status_code == 400
    assert client.get("/api/v1/health", headers={"host": "localhost:8000"}).status_code == 200


def test_allowed_hosts_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("LMS_ALLOWED_HOSTS", raising=False)
    assert allowed_hosts() == ["localhost", "127.0.0.1"]


def test_allowed_hosts_ignores_wildcard(monkeypatch):
    monkeypatch.setenv("LMS_ALLOWED_HOSTS", "*, lms.example.org")
    assert allowed_hosts() == ["lms.example.org"]


# --- Cross-site writes over HTTP (ADR-0015 5b, SPEC-12 section 2) ---

WRITE_PATH = "/api/v1/execute"
WRITE_BODY = {"code": "print(1)", "test_code": "", "timeout_seconds": 5}


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_cross_site_write_is_refused(method):
    client, _ = make_client()
    response = client.request(method, WRITE_PATH, json=WRITE_BODY, headers={"origin": "https://evil.example"})
    assert response.status_code == 403
    assert response.headers["content-type"].startswith("application/problem+json")


def test_cross_site_reset_is_refused():
    client, _ = make_client()
    response = client.post(
        "/api/v1/learners/me/units/any-unit/reset", headers={"origin": "https://evil.example"}
    )
    assert response.status_code == 403
    # Same call with no Origin reaches the route (a different answer), so the 403 came from the check.
    assert client.post("/api/v1/learners/me/units/any-unit/reset").status_code != 403


def test_write_from_an_allowed_origin_is_not_blocked():
    client, _ = make_client()
    response = client.post(WRITE_PATH, json=WRITE_BODY, headers={"origin": "http://localhost:5173"})
    assert response.status_code != 403


def test_write_with_no_origin_is_not_blocked():
    client, _ = make_client()
    assert client.post(WRITE_PATH, json=WRITE_BODY).status_code != 403


def test_cross_site_read_and_preflight_reach_the_normal_layers():
    client, _ = make_client()
    evil = {"origin": "https://evil.example"}
    assert client.get("/api/v1/health", headers=evil).status_code == 200
    preflight = client.options(
        WRITE_PATH, headers={**evil, "access-control-request-method": "POST"}
    )
    assert preflight.status_code == 400  # CORS layer refuses it; our check never answers 403 here


def test_vite_dev_shape_is_allowed():
    # Vite proxies with the browser's Host (localhost:5173) and its own Origin (a different spelling).
    client, _ = make_client()
    headers = {"origin": "http://127.0.0.1:5173", "host": "localhost:5173"}
    assert client.post(WRITE_PATH, json=WRITE_BODY, headers=headers).status_code != 403


def test_empty_or_wildcard_only_hosts_fall_back_to_loopback(monkeypatch):
    for value in ("*", ""):
        monkeypatch.setenv("LMS_ALLOWED_HOSTS", value)
        assert allowed_hosts() == ["localhost", "127.0.0.1"]
