"""SPEC-29 tests, part D (backend): the thumbs signal, `axis_feedback` (R20 to R26).

Written before the code. Offline: a scripted companion behind the real routes, an in-memory repository.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from test_axis_stream import ScriptedCompanion, body, parse_sse

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.interaction_log import ClientEvent, InteractionEvent

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
INTERACTIONS = "/api/v1/learners/me/interactions"
TURN_ID = "01JCXYZABCDEFGHJKMNPQRSTVW"


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def repo():
    r = SQLiteLearnerRepository(db_path=":memory:")
    r.initialize()
    return r


def make_client(repo, catalog, axis=None, test_mode=None):
    return TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=axis or ScriptedCompanion(["Which ", "line?"]),
                                 catalog=catalog, clock=lambda: T0, test_mode=test_mode))


def ask(client, **extra):
    """One streamed AXIS turn; returns (turn id from the done event, the done event data)."""
    res = client.post("/api/v1/axis/stream", json=body(**extra))
    assert res.status_code == 200, res.text
    done = [data for event, data in parse_sse(res.text) if event == "done"]
    assert len(done) == 1
    return done[0].get("interaction_id"), done[0]


def vote(client, turn_id, value, **extra):
    return client.post(INTERACTIONS, json={"event_type": "axis_feedback", "payload": {"turn_id": turn_id, "vote": value}, **extra})


def events_of(repo, event_type, learner=LOCAL_LEARNER_ID):
    return [e for e in repo.get_interactions(learner) if e.event_type == event_type]


def table_counts(repo):
    conn = repo._get_conn()
    names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    return {n: conn.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0] for n in names}


# --- 1. The event type and its validation (R20, R21) ---


def test_axis_feedback_is_a_client_event_type():
    event = ClientEvent(event_type="axis_feedback", payload={"turn_id": TURN_ID, "vote": "up"})

    assert event.payload.turn_id == TURN_ID and event.payload.vote == "up"
    assert InteractionEvent(interaction_id="v-0000001", learner_id="me", recorded_at_ms=1, event_type="axis_feedback").event_type == "axis_feedback"


@pytest.mark.parametrize("payload", [{}, {"turn_id": TURN_ID}, {"vote": "up"}, {"turn_id": None, "vote": "up"}])
def test_vote_needs_turn_id_and_vote(payload):
    with pytest.raises(ValidationError):
        ClientEvent(event_type="axis_feedback", payload=payload)


@pytest.mark.parametrize("event_type", ["opened", "closed", "hint_viewed", "feedback_viewed", "feedback_disputed"])
def test_other_events_refuse_turn_id_and_vote(event_type):
    for payload in ({"turn_id": TURN_ID}, {"vote": "up"}, {"turn_id": TURN_ID, "vote": "up"}):
        with pytest.raises(ValidationError):
            ClientEvent(event_type=event_type, payload=payload)


@pytest.mark.parametrize("extra", [{"text": "hi"}, {"reason": "free text"}, {"seconds_open": 3}, {"step": "x"}, {"point": "p"}, {"anything": 1}])
def test_extra_payload_fields_are_still_refused(extra):
    with pytest.raises(ValidationError):
        ClientEvent(event_type="axis_feedback", payload={"turn_id": TURN_ID, "vote": "up", **extra})


@pytest.mark.parametrize("bad", [{"turn_id": "short", "vote": "up"}, {"turn_id": "has space in it", "vote": "up"}, {"turn_id": TURN_ID, "vote": "meh"},
                                 {"turn_id": TURN_ID, "vote": "UP"}, {"turn_id": TURN_ID, "vote": ""}, {"turn_id": "x" * 65, "vote": "up"}])
def test_bad_id_or_vote_is_422(repo, catalog, bad):
    client = make_client(repo, catalog)

    res = client.post(INTERACTIONS, json={"event_type": "axis_feedback", "payload": bad})

    assert res.status_code == 422 and events_of(repo, "axis_feedback") == []


# --- 2. The server checks the turn (R22) ---


def test_unknown_turn_is_404_and_writes_nothing(repo, catalog):
    client = make_client(repo, catalog)
    before = table_counts(repo)

    res = vote(client, TURN_ID, "up")

    assert res.status_code == 404 and res.headers["content-type"].startswith("application/problem+json")
    assert table_counts(repo) == before


def test_another_learners_turn_is_404(repo, catalog):
    repo.append_interaction(InteractionEvent(
        interaction_id=TURN_ID, learner_id="someone-else", recorded_at_ms=1, event_type="axis", payload={"mode": "Coach"}, unit_id="PY-0.1"))
    client = make_client(repo, catalog)

    res = vote(client, TURN_ID, "up")

    assert res.status_code == 404 and events_of(repo, "axis_feedback") == []


def test_a_non_axis_row_id_is_404(repo, catalog):
    client = make_client(repo, catalog)
    repo.append_interaction(InteractionEvent(
        interaction_id=TURN_ID, learner_id=LOCAL_LEARNER_ID, recorded_at_ms=1, event_type="run", payload={}, unit_id="PY-0.1"))

    assert vote(client, TURN_ID, "up").status_code == 404
    turn, _ = ask(client)
    assert vote(client, turn, "up").status_code == 204
    (row,) = events_of(repo, "axis_feedback")
    assert vote(client, row.interaction_id, "up").status_code == 404  # a vote row is not a turn


def test_a_blocked_turn_has_no_id_to_vote_on(repo, catalog):
    client = make_client(repo, catalog)

    res = client.post("/api/v1/axis/stream", json=body(exercise_id="PY-0.1/cold-predict-1/v1"))

    assert res.status_code == 403
    assert events_of(repo, "axis") == []


# --- 3. What gets written (R23, R24, R25) ---


def test_vote_row_has_its_own_id_and_copies_unit_and_activity(repo, catalog):
    client = make_client(repo, catalog)
    turn, _ = ask(client)
    (turn_row,) = events_of(repo, "axis")

    assert vote(client, turn, "up").status_code == 204

    (row,) = events_of(repo, "axis_feedback")
    assert row.interaction_id != turn and len(row.interaction_id) >= 8
    assert (row.unit_id, row.activity) == (turn_row.unit_id, turn_row.activity)
    assert row.payload == {"turn_id": turn, "vote": "up"}
    assert row.test_mode is False


def test_vote_row_follows_the_apps_test_mode(repo, catalog):
    client = make_client(repo, catalog, test_mode=True)
    turn, _ = ask(client)

    vote(client, turn, "down")

    (row,) = events_of(repo, "axis_feedback")
    assert row.test_mode is True


def test_client_supplied_unit_item_and_ids_are_ignored(repo, catalog):
    client = make_client(repo, catalog)
    turn, _ = ask(client)
    (turn_row,) = events_of(repo, "axis")

    res = vote(client, turn, "up", interaction_id=turn, unit_id="EVIL-9", activity="evil", item_id="evil-item")

    assert res.status_code == 204
    (row,) = events_of(repo, "axis_feedback")
    assert row.interaction_id != turn
    assert row.unit_id == turn_row.unit_id and row.activity == turn_row.activity and row.item_id is None
    assert len(events_of(repo, "axis")) == 1  # the turn's own row is untouched


def test_vote_never_touches_evidence_assistance_attempts_or_progress(repo, catalog):
    client = make_client(repo, catalog)
    turn, _ = ask(client, exercise_id="PY-0.1/predict-1/v1")  # a turn on an exercise logs assistance of its own
    before = table_counts(repo)
    ledger_before = repo.get_evidence_ledger(LOCAL_LEARNER_ID)

    for value in ("up", "down", "clear", "up"):
        assert vote(client, turn, value).status_code == 204

    after = table_counts(repo)
    assert after.pop("interaction_log") == before.pop("interaction_log") + 4
    assert after == before  # no other table changed: no evidence, assistance, attempt, progress or cold-check row
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == ledger_before


def test_votes_are_append_only_and_changeable(repo, catalog):
    client = make_client(repo, catalog)
    turn, _ = ask(client)

    for value in ("up", "down", "clear"):
        vote(client, turn, value)

    rows = sorted(events_of(repo, "axis_feedback"), key=lambda e: (e.recorded_at_ms, e.interaction_id))
    assert len(rows) == 3 and {r.payload["vote"] for r in rows} == {"up", "down", "clear"}
    assert len({r.interaction_id for r in rows}) == 3


def test_a_replayed_vote_post_adds_another_row_but_the_report_still_counts_once(repo, catalog):
    import lms.core.axis_report as report

    client = make_client(repo, catalog)
    turn, _ = ask(client)

    vote(client, turn, "up")
    vote(client, turn, "up")

    rep = report.aggregate_modes(list(repo.get_interactions(LOCAL_LEARNER_ID)))
    assert [r["up"] for r in rep["by_mode"] if r["mode"] == "Socratic"] == [1]


# --- 4. The turn id reaches the browser (R26) ---


def test_stream_done_event_carries_the_turn_interaction_id(repo, catalog):
    turn, done = ask(make_client(repo, catalog))

    assert isinstance(turn, str) and len(turn) >= 8
    assert set(done) >= {"assistance_level", "cited_concepts", "interaction_id"}


def test_done_interaction_id_equals_the_logged_axis_row_and_the_trace_root(repo, catalog, tmp_path):
    import lms.core.tracing as tracing
    from lms.adapters.observability.local_tracer import LocalTracer

    tracing.set_tracer(LocalTracer(tmp_path))
    try:
        turn, _ = ask(make_client(repo, catalog))
    finally:
        tracing.set_tracer(tracing.NoopTracer())

    (row,) = events_of(repo, "axis")
    spans = [json.loads(line) for line in (tmp_path / "axis-trace.jsonl").read_text(encoding="utf-8").splitlines()]
    root = next(s for s in spans if s["name"] == "axis_question" and s["parent_id"] is None)
    assert turn == row.interaction_id == root["attributes"]["interaction_id"]


def test_an_errored_stream_has_no_done_event_and_so_no_turn_id(repo, catalog):
    class Broken(MockAxisCompanion):
        def stream(self, query):
            raise RuntimeError("model down")

    res = make_client(repo, catalog, Broken()).post("/api/v1/axis/stream", json=body())

    assert [event for event, _ in parse_sse(res.text)][-1] == "error"
    assert not any("interaction_id" in data for _, data in parse_sse(res.text))


def test_consult_response_is_unchanged(repo, catalog):
    request = body()
    request.pop("page")

    res = make_client(repo, catalog).post("/api/v1/axis/consult", json=request)

    assert res.status_code == 200 and "interaction_id" not in res.json()


def test_the_votes_endpoint_still_accepts_the_other_client_events(repo, catalog):
    client = make_client(repo, catalog)

    res = client.post(INTERACTIONS, json={"event_type": "opened", "unit_id": "PY-0.1", "payload": {"seconds_open": 3}})

    assert res.status_code == 204 and len(events_of(repo, "opened")) == 1
