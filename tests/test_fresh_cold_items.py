"""Unit Cold Check: unseen items first, failed next, passed last (ADR-0032, SPEC-16 section 2).

Uses the made-up items under tests/fixtures. TW-0.1 has CO-4: cold-explain-1..4 and
SP-4: cold-specify-1..2, so its round is explain-1, specify-1, explain-2.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.exercises import cold_history, cold_round, shown_cold_round
from lms.core.models import AssistanceLevel, EvidenceCategory, EvidenceEntry, EvidenceStrength
from made_up import right, wrong

T0 = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)
BASE = "/api/v1/learners/me"
UNIT = "TW-0.1"
E = [f"{UNIT}/cold-explain-{n}" for n in range(1, 5)]
S = [f"{UNIT}/cold-specify-{n}" for n in range(1, 3)]


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
    original = {u: list(s) for u, s in real_catalog.seeds.items()}
    yield real_catalog
    real_catalog.seeds = original


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def client(repo, catalog, clock):
    return TestClient(
        create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock, test_mode=False)
    )


def ids(seeds):
    return [s.seed_id for s in seeds]


def cold_entry(seed_id, passed=True, hours=0, **extra):
    fields = dict(
        learner_id=LOCAL_LEARNER_ID, unit_id=seed_id.split("/")[0], skill_id="CO-4",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG if passed else EvidenceStrength.WEAK,
        assistance_level=AssistanceLevel.NONE, demonstration_context="cold",
        recorded_at=T0 + timedelta(hours=hours), exercise_id=f"{seed_id}/v1", seed_id=seed_id, cold_check=True,
    )
    fields.update(extra)
    return EvidenceEntry(**fields)


# --- The round, as a pure function ---


def test_no_history_gives_todays_round(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]

    assert ids(cold_round(unit, seeds)) == [E[0], S[0], E[1]]
    assert cold_round(unit, seeds, {}, ()) == cold_round(unit, seeds)


def test_unseen_items_come_before_failed_ones(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]

    assert ids(cold_round(unit, seeds, {E[0]: False, S[0]: False})) == [E[1], S[1], E[2]]


def test_failed_items_come_before_passed_ones(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]
    history = {E[0]: True, E[1]: True, E[2]: False, E[3]: False, S[0]: True}

    assert ids(cold_round(unit, seeds, history)) == [E[2], S[1], E[3]]


def test_when_everything_was_answered_the_order_is_failed_then_passed_in_seed_order(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]
    history = {E[0]: True, E[1]: False, E[2]: True, E[3]: False, S[0]: True, S[1]: False}

    assert ids(cold_round(unit, seeds, history)) == [E[1], S[1], E[3]]


def test_an_item_already_in_the_round_keeps_its_place(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]
    history = {E[0]: False, E[1]: True}

    assert ids(cold_round(unit, seeds, history, in_round=[E[0], E[1]])) == [E[0], S[0], E[1]]


def test_the_round_is_deterministic_and_keeps_its_size(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]
    history = {E[1]: False}

    assert cold_round(unit, seeds, history) == cold_round(unit, seeds, history)
    assert len(cold_round(unit, seeds, history)) == len(cold_round(unit, seeds)) == 3


def test_a_unit_with_one_item_per_skill_never_changes(catalog):
    unit = catalog.get_unit("PY-0.1")
    seeds = [s for s in catalog.seeds["PY-0.1"] if s.seed_id.endswith(("cold-predict-1", "cold-trace-1", "cold-explain-1"))]
    plain = cold_round(unit, seeds)

    assert len(plain) == 3
    assert cold_round(unit, seeds, {s.seed_id: False for s in seeds}) == plain
    assert cold_round(unit, seeds, {s.seed_id: True for s in seeds}) == plain


def test_history_comes_from_unit_cold_check_answers_only():
    ledger = [
        cold_entry(E[0], True, hours=1),
        cold_entry(E[0], False, hours=2),  # The newest answer wins
        cold_entry(E[1], True, hours=1, review_kind="stage_review"),
        cold_entry(E[2], True, hours=1, cold_check=False),
        cold_entry(E[3], True, hours=1, unit_id="PY-0.1"),
    ]

    assert cold_history(ledger, UNIT) == {E[0]: False}


def test_the_ledger_is_not_changed_by_reading_it():
    ledger = [cold_entry(E[0], True)]
    before = [e.model_copy() for e in ledger]

    cold_history(ledger, UNIT)

    assert ledger == before


# --- Through the routes ---


def open_cold_check(repo):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, UNIT, T0 - 2 * DAY)


def run_round(client, right_seeds=()):
    """Answer every served item (right for the named seeds, wrong for the rest) until the round ends."""
    answered = []
    while True:
        res = client.get(f"{BASE}/units/{UNIT}/activities/cold_check/exercise")
        if res.status_code != 200:
            return answered
        exercise_id = res.json()["exercise_id"]
        seed_id = exercise_id.rsplit("/", 1)[0]
        fields = right(seed_id) if seed_id in right_seeds else wrong(seed_id)
        posted = client.post(f"{BASE}/attempts", json={"exercise_id": exercise_id, "activity": "cold_check", **fields})
        assert posted.status_code == 200, posted.text
        answered.append(seed_id)


def cold_state(client):
    return client.get(f"{BASE}/units/{UNIT}/cold-check").json()["state"]


def test_a_failed_round_is_replaced_by_unseen_items_then_repeats_when_none_are_left(client, repo, clock):
    open_cold_check(repo)

    assert run_round(client) == [E[0], S[0], E[1]]
    clock.now += DAY + timedelta(hours=1)
    assert run_round(client) == [E[2], S[1], E[3]]  # Every item is new
    clock.now += DAY + timedelta(hours=1)
    assert run_round(client) == [E[0], S[0], E[1]]  # None unseen: the failed ones return


def test_a_passed_item_stays_passed_and_the_round_can_complete(client, repo, clock):
    open_cold_check(repo)
    assert run_round(client, right_seeds=[E[0]]) == [E[0], S[0], E[1]]
    assert cold_state(client) == "failed_waiting"
    clock.now += DAY + timedelta(hours=1)

    second = run_round(client, right_seeds=[S[1], E[2]])

    assert second == [S[1], E[2]]  # The passed item is not asked again; two replacements
    assert cold_state(client) == "passed"


def test_the_failed_item_returns_only_when_its_skill_has_no_other_item(client, repo, clock, catalog):
    catalog.seeds[UNIT] = [s for s in catalog.seeds[UNIT] if s.seed_id not in (E[2], E[3], S[1])]
    open_cold_check(repo)

    first = run_round(client)
    clock.now += DAY + timedelta(hours=1)
    second = run_round(client)

    assert first == [E[0], S[0], E[1]]
    assert second == first  # CO-4 has two items, SP-4 one: nothing unseen is left


def test_a_unit_with_one_item_per_skill_behaves_as_before(client, repo, clock, catalog):
    catalog.seeds[UNIT] = [s for s in catalog.seeds[UNIT] if s.seed_id in (E[0], S[0])]
    open_cold_check(repo)

    first = run_round(client)
    clock.now += DAY + timedelta(hours=1)

    assert first == [E[0], S[0]]
    assert run_round(client) == first


def test_after_a_reset_items_passed_before_come_last(client, repo, clock):
    for hours, seed_id in enumerate([E[0], S[0], E[1]]):
        repo.record_evidence(cold_entry(seed_id, True, hours=hours - 10))
    repo.reset_unit(LOCAL_LEARNER_ID, UNIT, T0 - timedelta(hours=1))
    open_cold_check(repo)

    assert run_round(client) == [E[2], S[1], E[3]]


def test_items_failed_before_a_reset_still_come_after_unseen_ones(client, repo, clock):
    repo.record_evidence(cold_entry(E[0], False, hours=-10))
    repo.reset_unit(LOCAL_LEARNER_ID, UNIT, T0 - timedelta(hours=1))
    open_cold_check(repo)

    assert run_round(client)[0] == E[1]


def test_the_feedback_still_shows_the_round_that_failed(client, repo, clock):
    open_cold_check(repo)
    run_round(client, right_seeds=[E[0]])
    clock.now += DAY + timedelta(hours=1)

    rows = client.get(f"{BASE}/units/{UNIT}/cold-check/feedback").json()["items"]

    assert [r["passed"] for r in rows] == [True, False, False]
    assert [r["skill_id"] for r in rows] == ["CO-4", "SP-4", "CO-4"]


def test_the_feedback_follows_the_retry_once_it_starts(client, repo, clock):
    open_cold_check(repo)
    run_round(client, right_seeds=[E[0]])
    clock.now += DAY + timedelta(hours=1)
    first = client.get(f"{BASE}/units/{UNIT}/activities/cold_check/exercise").json()
    seed_id = first["exercise_id"].rsplit("/", 1)[0]
    client.post(f"{BASE}/attempts", json={"exercise_id": first["exercise_id"], "activity": "cold_check", **right(seed_id)})

    rows = client.get(f"{BASE}/units/{UNIT}/cold-check/feedback").json()["items"]

    # The kept pass, the item just passed, and the item still to answer.
    assert [r["passed"] for r in rows] == [True, True, None]


def test_the_feedback_after_a_reset_is_the_new_round(catalog):
    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]
    ledger = [cold_entry(E[0], True, hours=-5), cold_entry(S[0], True, hours=-4), cold_entry(E[1], True, hours=-3)]

    shown = shown_cold_round(unit, seeds, ledger, reset_at=T0)

    assert ids(shown) == [E[2], S[1], E[3]]
    assert ids(shown_cold_round(unit, seeds, ledger)) == [E[0], S[0], E[1]]


def test_the_stage_review_does_not_use_the_unit_round(catalog):
    from lms.core.exercises import spare_cold_items

    unit, seeds = catalog.get_unit(UNIT), catalog.seeds[UNIT]

    assert spare_cold_items(unit, seeds) == 3  # 6 approved items, a round of 3
