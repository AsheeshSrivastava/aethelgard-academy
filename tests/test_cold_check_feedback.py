"""Tests for Cold Check feedback, option A (ADR-0022 section 2.5)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.exercises import SeedError, cold_round, parse_seed

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
BASE = "/api/v1/learners/me"
UNIT = "PY-0.4"
FEEDBACK = f"{BASE}/units/{UNIT}/cold-check/feedback"


# --- The seed field ---


def raw_seed(**extra):
    return {
        "schema_version": 2,
        "seed_id": "PY-0.4/cold-predict-9",
        "unit_id": "PY-0.4",
        "activity": "Predict",
        "skill_id": "CO-1",
        "level": "Understand",
        "prompt_markdown": ["What prints?"],
        "cold_check_eligible": True,
        "curator_approved": True,
        "predict": {"code": ["print(1)"], "stdin": "", "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}], "answer_key": "A", "why": ["It prints 1."]},
        **extra,
    }


def test_a_seed_reads_its_hint_and_approval():
    seed = parse_seed(raw_seed(hint="Comments never run.", hint_approved=True), "cold-predict-9", "PY-0.4")

    assert (seed.hint, seed.hint_approved) == ("Comments never run.", True)


def test_a_seed_without_a_hint_has_none_and_is_not_approved():
    seed = parse_seed(raw_seed(), "cold-predict-9", "PY-0.4")

    assert (seed.hint, seed.hint_approved) == (None, False)


@pytest.mark.parametrize("bad", ["", "x" * 301, 42])
def test_a_bad_hint_is_refused(bad):
    with pytest.raises(SeedError):
        parse_seed(raw_seed(hint=bad), "cold-predict-9", "PY-0.4")


# --- The route ---


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


@pytest.fixture(scope="module")
def real_catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def catalog(real_catalog):
    """A copy whose seeds the tests may change."""
    copy = real_catalog
    original = {u: list(s) for u, s in real_catalog.seeds.items()}
    yield copy
    copy.seeds = original


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
    return TestClient(app)


def round_seeds(catalog):
    return cold_round(catalog.get_unit(UNIT), catalog.seeds[UNIT])


def answer_for(seed, right):
    body = seed.body
    if seed.item_type == "trace":
        return {"trace_answers": body["expected_output"] if right else ["nope"]}
    key = body["answer_key"]
    if seed.item_type == "debug_locate":
        return {"locate": key if right else {**key, "line": key["line"] % len(body["broken_code"]) + 1}}
    if right:
        return {"choice": key}
    return {"choice": next(o["key"] for o in body["options"] if o["key"] != key)}


def take_round(client, catalog, right_first):
    """Answer the whole round: the first item as told, the rest wrong."""
    answered = []
    for n, _ in enumerate(round_seeds(catalog)):
        current = client.get(f"{BASE}/units/{UNIT}/activities/cold_check/exercise").json()
        seed = next(s for s in catalog.seeds[UNIT] if current["exercise_id"].startswith(f"{s.seed_id}/"))
        given = answer_for(seed, right_first if n == 0 else False)
        client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "cold_check", **given})
        answered.append((seed, given))
    return answered


def open_cold_check(repo):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, UNIT, T0 - timedelta(days=2))


def test_before_any_attempt_items_are_not_answered(client, repo, catalog):
    open_cold_check(repo)

    items = client.get(FEEDBACK).json()["items"]

    assert len(items) == len(round_seeds(catalog))
    assert all(i["passed"] is None and i["your_answer"] is None for i in items)


def test_a_failed_round_shows_your_answer_skill_and_practice_but_not_the_worked_answer(client, repo, catalog):
    open_cold_check(repo)
    answered = take_round(client, catalog, right_first=False)

    items = client.get(FEEDBACK).json()["items"]

    first_seed, first_answer = answered[0]
    first = items[0]
    assert first["passed"] is False
    assert first["skill_id"] == first_seed.skill_id
    assert first["skill_name"] != first_seed.skill_id
    assert first["your_answer"]
    assert first["worked"] is None
    assert first["practice_activity"] in {"predict", "debug-validate"}
    for item in items:
        assert item["worked"] is None
        assert "why" not in str(item["your_answer"])


def test_a_choice_answer_reads_back_as_the_chosen_option(client, repo, catalog):
    open_cold_check(repo)
    answered = take_round(client, catalog, right_first=False)

    items = client.get(FEEDBACK).json()["items"]

    for (seed, given), item in zip(answered, items):
        if "choice" in given:
            text = next(o["text"] for o in seed.body["options"] if o["key"] == given["choice"])
            assert item["your_answer"] == f"{given['choice']}. {text}"


def test_a_passed_item_shows_its_worked_answer(client, repo, catalog):
    open_cold_check(repo)
    answered = take_round(client, catalog, right_first=True)

    first = client.get(FEEDBACK).json()["items"][0]

    assert first["passed"] is True
    assert first["worked"]["why"] == answered[0][0].body.get("why", [])


def test_a_retry_shows_the_newest_result(client, repo, catalog, clock):
    open_cold_check(repo)
    take_round(client, catalog, right_first=False)
    assert client.get(FEEDBACK).json()["items"][0]["passed"] is False

    clock.now = T0 + timedelta(days=1, hours=1)
    current = client.get(f"{BASE}/units/{UNIT}/activities/cold_check/exercise").json()
    seed = next(s for s in catalog.seeds[UNIT] if current["exercise_id"].startswith(f"{s.seed_id}/"))
    # With a spare item for the skill (ADR-0032) the failed item is swapped for a fresh one,
    # so the retry may serve a different seed; the feedback must show the newest result either way.
    client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "cold_check", **answer_for(seed, True)})

    first = client.get(FEEDBACK).json()["items"][0]
    assert first["passed"] is True
    assert first["worked"] is not None


def test_an_unapproved_hint_is_never_shown(client, repo, catalog):
    seeds = catalog.seeds[UNIT]
    catalog.seeds[UNIT] = [s.model_copy(update={"hint": "Look at line order.", "hint_approved": False}) for s in seeds]
    open_cold_check(repo)
    take_round(client, catalog, right_first=False)

    assert all(i["hint"] is None for i in client.get(FEEDBACK).json()["items"])


def test_an_approved_hint_shows_for_a_failed_item_only(client, repo, catalog):
    seeds = catalog.seeds[UNIT]
    catalog.seeds[UNIT] = [s.model_copy(update={"hint": "Look at line order.", "hint_approved": True}) for s in seeds]
    open_cold_check(repo)
    take_round(client, catalog, right_first=True)

    items = client.get(FEEDBACK).json()["items"]

    assert items[0]["hint"] is None
    assert all(i["hint"] == "Look at line order." for i in items[1:])


def test_a_hint_never_leaves_the_server_with_the_item(client, repo, catalog):
    seeds = catalog.seeds[UNIT]
    catalog.seeds[UNIT] = [s.model_copy(update={"hint": "SECRET-HINT", "hint_approved": True}) for s in seeds]
    open_cold_check(repo)

    served = client.get(f"{BASE}/units/{UNIT}/activities/cold_check/exercise")

    assert "SECRET-HINT" not in served.text


def test_unknown_unit_is_404(client):
    assert client.get(f"{BASE}/units/PY-99.9/cold-check/feedback").status_code == 404
