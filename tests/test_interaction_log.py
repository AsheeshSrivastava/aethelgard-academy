"""Tests for the interaction log (ADR-0022)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.interaction_log import (
    MAX_PAYLOAD_CHARS,
    MAX_TEXT_CHARS,
    InteractionEvent,
    clean_payload,
    new_ulid,
)

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
BASE = "/api/v1/learners/me"
SESSION = "01J9ZK3Y4D8Q2W6X0SESSION01"
ID = "01J9ZK3Y4D8Q2W6X0ANSWER001"


# --- The core rules ---


def test_ulids_are_26_characters_and_sort_by_time():
    early, late = new_ulid(1_000), new_ulid(2_000)

    assert len(early) == len(late) == 26
    assert early < late
    assert new_ulid(1_000) != new_ulid(1_000)


def test_long_text_is_cut_and_marked():
    cleaned = clean_payload({"code": "x" * (MAX_TEXT_CHARS + 10)})

    assert len(cleaned["code"]) <= MAX_TEXT_CHARS + 20
    assert cleaned["code"].endswith("…[truncated]")


def test_secret_looking_keys_are_redacted_at_any_depth():
    cleaned = clean_payload({"api_key": "abc", "nested": {"Token": "t", "password_hint": "p"}, "answer": "A"})

    assert cleaned == {"api_key": "[redacted]", "nested": {"Token": "[redacted]", "password_hint": "[redacted]"}, "answer": "A"}


def test_a_payload_over_the_total_cap_is_replaced_by_a_marker():
    big = {f"part{i}": "y" * (MAX_TEXT_CHARS - 1) for i in range(6)}

    cleaned = clean_payload(big)

    assert cleaned["truncated"] is True
    assert len(str(cleaned)) < MAX_PAYLOAD_CHARS


# --- Storage ---


def event(**fields):
    base = dict(
        interaction_id=new_ulid(1_000),
        learner_id="l",
        recorded_at_ms=1_000,
        event_type="opened",
        payload={},
    )
    return InteractionEvent(**{**base, **fields})


def test_the_log_is_append_only_and_idempotent():
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    first = event(payload={"n": 1})

    repo.append_interaction(first)
    repo.append_interaction(first.model_copy(update={"payload": {"n": 2}}))

    stored = repo.get_interactions("l")
    assert len(stored) == 1
    assert stored[0].payload == {"n": 1}


def test_old_ledger_rows_have_no_links(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE evidence_ledger (entry_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL, unit_id TEXT NOT NULL,"
            " skill_id TEXT NOT NULL, evidence_category TEXT NOT NULL, evidence_strength TEXT NOT NULL,"
            " assistance_level TEXT NOT NULL, demonstration_context TEXT NOT NULL, observed_reasoning TEXT,"
            " recorded_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO evidence_ledger VALUES ('e1','l','PY-0.1','CO-1','Explain / Reason','Strong','none','old',NULL,?)",
            (T0.isoformat(),),
        )
    repo = SQLiteLearnerRepository(db_path=str(path))
    repo.initialize()

    old = repo.get_evidence_ledger("l")[0]
    assert old.interaction_id is None and old.attempt_id is None


# --- The app ---


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def client(repo, catalog, clock):
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock, test_mode=False)
    return TestClient(app, headers={"X-Session-Id": SESSION})


def log(repo, event_type=None):
    found = repo.get_interactions(LOCAL_LEARNER_ID)
    return [e for e in found if event_type is None or e.event_type == event_type]


def serve(client, unit="PY-0.4", activity="predict"):
    return client.get(f"{BASE}/units/{unit}/activities/{activity}/exercise").json()


def test_an_answer_is_logged_exactly_and_linked_to_its_evidence(client, repo):
    current = serve(client)
    res = client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "predict", "choice": "B", "interaction_id": ID})

    [answer] = log(repo, "answer_submitted")
    [entry] = repo.get_evidence_ledger(LOCAL_LEARNER_ID)
    assert answer.interaction_id == ID == entry.interaction_id
    assert answer.payload["answer"] == {"choice": "B"}
    assert answer.payload["outcome"] == res.json()["outcome"]
    assert answer.payload["evidence_entry_id"] == entry.entry_id
    assert answer.attempt_id == entry.attempt_id
    assert answer.attempt_id.startswith(f"{current['exercise_id']}@")
    assert (answer.unit_id, answer.activity, answer.item_id) == ("PY-0.4", "predict", current["exercise_id"])
    assert answer.session_id == SESSION


def test_a_repeated_submit_is_logged_once(client, repo):
    current = serve(client)
    body = {"exercise_id": current["exercise_id"], "activity": "predict", "choice": "A", "interaction_id": ID}
    client.post(f"{BASE}/attempts", json=body)
    client.post(f"{BASE}/attempts", json=body)

    assert len(log(repo, "answer_submitted")) == 1


def test_a_refused_answer_is_logged_with_why_and_its_id_stays_free(client, repo):
    serve(client)
    client.post(f"{BASE}/attempts", json={"exercise_id": "PY-0.4/predict-9/v1", "activity": "predict", "choice": "A", "interaction_id": ID})

    [refused] = log(repo, "answer_submitted")
    assert refused.payload["status"] in (404, 409)
    assert refused.interaction_id != ID


def test_an_answer_without_an_id_still_gets_one(client, repo):
    current = serve(client)
    client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "predict", "choice": "A"})

    [answer] = log(repo, "answer_submitted")
    [entry] = repo.get_evidence_ledger(LOCAL_LEARNER_ID)
    assert len(answer.interaction_id) == 26
    assert entry.interaction_id == answer.interaction_id


def test_a_cold_check_answer_is_logged_with_its_round(client, repo, clock):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-0.4", T0 - timedelta(days=2))
    current = serve(client, activity="cold_check")
    client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "cold_check", "choice": "A", "interaction_id": ID})

    [answer] = log(repo, "answer_submitted")
    assert answer.payload["answer"] == {"choice": "A"}
    assert answer.attempt_id == f"PY-0.4/cold_check@{(T0 - timedelta(days=2)).isoformat()}"


def test_concept_check_regenerate_reset_and_verify_are_logged(client, repo):
    client.post("/api/v1/explain", json={"unit_id": "PY-0.1", "explanation": "statements run in order"})
    serve(client)
    client.post(f"{BASE}/units/PY-0.4/activities/predict/exercises:regenerate")
    client.post(f"{BASE}/units/PY-0.4/playground:verify", json={"code": "print('hi')"})
    client.post(f"{BASE}/units/PY-0.4/reset")

    kinds = [e.event_type for e in log(repo)]
    assert {"concept_check", "regenerate", "verify", "reset"} <= set(kinds)
    [check] = log(repo, "concept_check")
    assert check.payload["explanation"] == "statements run in order"
    [verify] = log(repo, "verify")
    assert verify.payload["code"] == "print('hi')"
    assert "passed" in verify.payload


def test_an_axis_question_and_answer_are_logged(client, repo):
    client.post("/api/v1/axis/consult", json={"unit_id": "PY-0.1", "mode": "Socratic", "current_activity": "Predict", "user_prompt": "Why?"})

    [axis] = log(repo, "axis")
    assert axis.payload["question"] == "Why?"
    assert axis.payload["mode"] == "Socratic"
    assert axis.payload["answer"]


def test_client_events_are_allow_listed(client, repo):
    ok = client.post(f"{BASE}/interactions", json={"event_type": "opened", "unit_id": "PY-0.1", "activity": "predict"})
    bad_type = client.post(f"{BASE}/interactions", json={"event_type": "answer_submitted"})
    bad_field = client.post(f"{BASE}/interactions", json={"event_type": "opened", "payload": {"x": "y"}})

    assert ok.status_code == 204
    assert bad_type.status_code == 422
    assert bad_field.status_code == 422
    assert [e.event_type for e in log(repo)] == ["opened"]


def test_a_malformed_session_header_is_dropped(repo, catalog, clock):
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock)
    TestClient(app, headers={"X-Session-Id": "bad header!"}).post(f"{BASE}/interactions", json={"event_type": "opened"})

    assert log(repo)[0].session_id is None


def test_a_failed_log_write_never_breaks_learning(client, repo, monkeypatch):
    def broken(_event):
        raise RuntimeError("disk full")

    monkeypatch.setattr(repo, "append_interaction", broken)
    current = serve(client)

    res = client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "predict", "choice": "A"})

    assert res.status_code == 200
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 1


def test_export_returns_the_learners_own_log_newest_first(client, repo, clock):
    client.post(f"{BASE}/interactions", json={"event_type": "opened"})
    clock.now = T0 + timedelta(seconds=5)
    client.post(f"{BASE}/interactions", json={"event_type": "closed", "payload": {"seconds_open": 5}})
    repo.append_interaction(event(learner_id="someone_else"))

    body = client.get(f"{BASE}/interactions").json()

    assert [e["event_type"] for e in body] == ["closed", "opened"]


def test_test_mode_is_tagged_on_log_rows(repo, catalog, clock):
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock, test_mode=True)
    TestClient(app).post(f"{BASE}/interactions", json={"event_type": "opened"})

    assert log(repo)[0].test_mode is True
