"""Tests for the unit round, stage review and rechecks (SPEC-16, ADR-0019)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog, load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.cold_check import ColdCheckTimer
from lms.core.curriculum_checks import check_curriculum
from lms.core.exercises import cold_round, seed_variants
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    TargetSkill,
    Unit,
)
from lms.core.review import (
    RECHECK,
    STAGE_REVIEW,
    ReviewItem,
    ReviewResult,
    ReviewState,
    build_is_open,
    due_reviews,
    plan_recheck,
    plan_stage_review,
    stage_review_status,
)

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)
BASE = "/api/v1/learners/me"
LEVELS = ProficiencyLevel


def unit(unit_id, skills, stage=0):
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=stage,
        concept_line="Concept",
        target_skills=[TargetSkill(skill_id=s, skill_name=s, goal_level=lvl) for s, lvl in skills],
        methods=[ActivityType.EXPLAIN, ActivityType.PREDICT],
    )


class Seed:
    """Only the fields the round planners read."""

    def __init__(self, seed_id, skill_id, eligible=True, approved=True):
        self.seed_id = seed_id
        self.skill_id = skill_id
        self.cold_check_eligible = eligible
        self.curator_approved = approved
        self.activity = ActivityType.PREDICT
        self.template = None
        self.level = LEVELS.UNDERSTAND
        self.item_type = "predict"
        self.body = {}
        self.topic = "a topic"


def seeds(*pairs):
    return [Seed(f"U/cold-{n}", skill) for n, skill in enumerate(pairs)]


# --- Unit round: 3 to 5 items ---


def test_round_takes_one_per_skill_then_fills_to_three():
    target = unit("PY-1.1", [("CO-1", LEVELS.APPLY), ("VE-6", LEVELS.APPLY)])

    chosen = cold_round(target, seeds("CO-1", "CO-1", "VE-6", "VE-6"))

    assert [s.skill_id for s in chosen] == ["CO-1", "VE-6", "CO-1"]


def test_round_stops_at_five_and_covers_skills_first():
    skills = [(f"CO-{n}", LEVELS.APPLY) for n in range(1, 7)]
    target = unit("PY-1.1", skills)

    chosen = cold_round(target, seeds(*[s for s, _ in skills]))

    assert [s.skill_id for s in chosen] == ["CO-1", "CO-2", "CO-3", "CO-4", "CO-5"]


def test_round_with_few_seeds_runs_what_it_has():
    target = unit("PY-1.1", [("CO-1", LEVELS.APPLY), ("VE-6", LEVELS.APPLY)])

    assert len(cold_round(target, seeds("CO-1"))) == 1


def test_round_ignores_unapproved_uneligible_and_other_skills():
    target = unit("PY-1.1", [("CO-1", LEVELS.APPLY)])
    pool = [Seed("a", "CO-1", approved=False), Seed("b", "CO-1", eligible=False), Seed("c", "VE-6")]

    assert cold_round(target, pool) == []


# --- Stage review planning ---


def plan(units, pools, seen=()):
    return plan_stage_review(units, pools, set(seen))


def test_plan_gives_two_per_unit_and_mixes_them():
    units = [unit("A-1", [("CO-1", LEVELS.UNDERSTAND)]), unit("A-2", [("VE-4", LEVELS.UNDERSTAND)])]
    pools = {"A-1": seeds("CO-1", "CO-1", "CO-1"), "A-2": seeds("VE-4", "VE-4", "VE-4")}

    items = plan(units, pools)

    assert [i.unit_id for i in items] == ["A-1", "A-2", "A-1", "A-2"]
    assert [i.position for i in items] == [0, 1, 2, 3]


def test_plan_covers_every_apply_skill_even_past_two():
    target = unit("A-1", [("CO-1", LEVELS.APPLY), ("CO-2", LEVELS.ADAPT), ("CO-3", LEVELS.APPLY)])

    items = plan([target], {"A-1": seeds("CO-1", "CO-2", "CO-3")})

    assert {i.skill_id for i in items} == {"CO-1", "CO-2", "CO-3"}


def test_plan_skips_what_the_learner_has_seen():
    target = unit("A-1", [("CO-1", LEVELS.APPLY)])
    pool = seeds("CO-1", "CO-1")

    items = plan([target], {"A-1": pool}, seen=[f"{pool[0].seed_id}/v1"])

    assert [i.exercise_id for i in items] == [f"{pool[1].seed_id}/v1"]


def test_plan_is_empty_when_everything_is_seen():
    target = unit("A-1", [("CO-1", LEVELS.APPLY)])
    pool = seeds("CO-1")

    assert plan([target], {"A-1": pool}, seen=[f"{pool[0].seed_id}/v1"]) == []


def test_plan_never_uses_an_unapproved_seed():
    target = unit("A-1", [("CO-1", LEVELS.APPLY)])

    assert plan([target], {"A-1": [Seed("x", "CO-1", approved=False)]}) == []


def test_recheck_plan_is_at_most_four_unseen_items_for_the_skill():
    pools = {"A-1": seeds("CO-1", "CO-1", "CO-1"), "A-2": [Seed(f"B/{n}", "CO-1") for n in range(3)] + [Seed("B/x", "VE-1")]}

    items = plan_recheck("CO-1", pools, {"U/cold-0/v1"})

    assert len(items) == 4
    assert "U/cold-0/v1" not in [i.exercise_id for i in items]
    assert {i.skill_id for i in items} == {"CO-1"}


# --- Stage review state ---


def status(pending=(), has_items=True, result=None, items=(), now=T0):
    return stage_review_status(list(pending), has_items, result, list(items), now)


def item(position=0, passed=None, unit_id="A-1"):
    return ReviewItem(position=position, exercise_id=f"x/{position}", unit_id=unit_id, skill_id="CO-1", passed=passed)


def test_state_not_ready_while_a_unit_is_pending():
    found = status(pending=["A-1"])

    assert found.state == ReviewState.NOT_READY
    assert found.pending_units == ["A-1"]


def test_state_unavailable_with_no_items():
    assert status(has_items=False).state == ReviewState.UNAVAILABLE


def test_state_available_when_all_units_passed():
    assert status().state == ReviewState.AVAILABLE


def test_state_failed_waits_a_day_and_names_units():
    result = ReviewResult(last_attempt_at=T0, passed=False)
    items = [item(0, True, "A-1"), item(1, False, "A-2")]

    found = status(result=result, items=items, now=T0 + timedelta(hours=23))

    assert found.state == ReviewState.FAILED_WAITING
    assert found.available_at == T0 + DAY
    assert found.failed_units == ["A-2"]


def test_state_available_again_after_the_delay():
    result = ReviewResult(last_attempt_at=T0, passed=False)

    assert status(result=result, items=[item(0, False)], now=T0 + DAY).state == ReviewState.AVAILABLE


def test_passed_stays_passed_after_a_unit_reset():
    result = ReviewResult(last_attempt_at=T0, passed=True)

    assert status(pending=["A-1"], result=result).state == ReviewState.PASSED


def test_status_counts_items_done():
    found = status(items=[item(0, True), item(1, None), item(2, False)])

    assert (found.items_total, found.items_done) == (3, 2)


@pytest.mark.parametrize(
    "state, is_open",
    [
        (ReviewState.PASSED, True),
        (ReviewState.UNAVAILABLE, True),
        (ReviewState.NOT_READY, False),
        (ReviewState.AVAILABLE, False),
        (ReviewState.FAILED_WAITING, False),
    ],
)
def test_build_gate(state, is_open):
    assert build_is_open(state) == is_open


# --- Due rechecks ---


def entry(skill="CO-1", kind=STAGE_REVIEW, strength=EvidenceStrength.STRONG, at=T0):
    return EvidenceEntry(
        learner_id="l",
        unit_id="A-1",
        skill_id=skill,
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=strength,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="x",
        recorded_at=at,
        cold_check=True,
        review_kind=kind,
    )


def due(ledger, finished=(), now=T0):
    return due_reviews(ledger, set(finished), now)


def test_nothing_due_before_seven_days():
    assert due([entry()], now=T0 + timedelta(days=6, hours=23)) == []


def test_seven_day_recheck_falls_due():
    found = due([entry()], now=T0 + timedelta(days=7))

    assert [(d.skill_id, d.days, d.due_at) for d in found] == [("CO-1", 7, T0 + timedelta(days=7))]


def test_thirty_day_waits_for_the_seven_day_one():
    assert [d.days for d in due([entry()], now=T0 + timedelta(days=40))] == [7]


def test_thirty_day_falls_due_after_the_seven_day_is_finished():
    finished = ["CO-1/7"]

    assert due([entry()], finished, now=T0 + timedelta(days=29)) == []
    assert [d.days for d in due([entry()], finished, now=T0 + timedelta(days=30))] == [30]


def test_all_finished_means_nothing_due():
    assert due([entry()], ["CO-1/7", "CO-1/30"], now=T0 + timedelta(days=99)) == []


def test_clock_starts_at_the_first_pass_only():
    ledger = [entry(at=T0 + timedelta(days=3)), entry(at=T0)]

    assert due(ledger, now=T0 + timedelta(days=7))[0].due_at == T0 + timedelta(days=7)


def test_failed_review_items_and_other_entries_start_no_clock():
    ledger = [entry(strength=EvidenceStrength.WEAK), entry(kind=None), entry(kind=RECHECK)]

    assert due(ledger, now=T0 + timedelta(days=99)) == []


def test_due_is_oldest_first():
    ledger = [entry("VE-1", at=T0 + DAY), entry("CO-1")]

    assert [d.skill_id for d in due(ledger, now=T0 + timedelta(days=9))] == ["CO-1", "VE-1"]


# --- Curriculum warning ---


def test_stage_with_no_spare_item_is_warned():
    target = unit("PY-0.1", [("CO-1", LEVELS.UNDERSTAND)])

    found = check_curriculum([target], seeds={"PY-0.1": seeds("CO-1")})

    assert "stage-review-short" in [f.code for f in found]


def test_stage_with_a_spare_item_per_unit_has_no_warning():
    target = unit("PY-0.1", [("CO-1", LEVELS.UNDERSTAND)])

    found = check_curriculum([target], seeds={"PY-0.1": seeds("CO-1", "CO-1", "CO-1", "CO-1")})

    assert "stage-review-short" not in [f.code for f in found]


# --- API ---


class FakeClock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


@pytest.fixture(scope="module")
def real_catalog():
    return load_all_roadmaps(Path("reference"))


def clone(seed, suffix):
    return seed.model_copy(update={"seed_id": f"{seed.seed_id}-{suffix}"})


@pytest.fixture
def catalog(real_catalog):
    """Stage 0 with one spare predict item per unit that has one, so a review can run."""
    extended = CurriculumCatalog()
    for stage_unit in real_catalog.get_stage_units(0):
        if stage_unit.unit_id.startswith("PY-"):
            extended.add_unit(stage_unit)
    extended.main_activities = real_catalog.main_activities
    extended.builds = real_catalog.builds
    extended.seeds = {u: list(s) for u, s in real_catalog.seeds.items()}
    for unit_id in ("PY-0.1", "PY-0.4"):
        spare = next(s for s in extended.seeds[unit_id] if s.seed_id.endswith("cold-predict-1"))
        extended.seeds[unit_id] += [clone(spare, name) for name in ("spare", "extra")]
    return extended


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def client(repo, catalog, clock):
    return TestClient(
        create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock)
    )


REVIEW = f"{BASE}/courses/python/stages/0/review"


def pass_units(repo, catalog):
    """Every unit passed, with its round's items seen."""
    for stage_unit in catalog.get_stage_units(0):
        repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, stage_unit.unit_id, T0 - 2 * DAY)
        repo.record_cold_check_attempt(LOCAL_LEARNER_ID, stage_unit.unit_id, True, T0 - DAY)
        for seed in cold_round(stage_unit, catalog.seeds.get(stage_unit.unit_id, [])):
            repo.set_current_exercise(LOCAL_LEARNER_ID, stage_unit.unit_id, "cold_check", f"{seed.seed_id}/v1", T0 - DAY)
            repo.clear_current_exercise(LOCAL_LEARNER_ID, stage_unit.unit_id, "cold_check")


def answer(client, catalog, right=True):
    """Answer the next review item; a spare is a clone of a predict seed."""
    current = client.get(f"{REVIEW}/exercise")
    assert current.status_code == 200, current.text
    return send(client, catalog, current.json(), "stage_review", right)


def send(client, catalog, exercise, activity, right):
    unit_id = exercise["unit_id"]
    seed = next(s for s in catalog.seeds[unit_id] if exercise["exercise_id"].startswith(f"{s.seed_id}/"))
    return client.post(
        f"{BASE}/attempts",
        json={"exercise_id": exercise["exercise_id"], "activity": activity, **answer_for(seed, right)},
    )


def answer_for(seed, right):
    """A right or wrong answer for any Cold Check item type, from its answer key."""
    body = seed.body
    if seed.item_type == "trace":
        return {"trace_answers": body["expected_output"] if right else ["not the output"]}
    key = body["answer_key"]
    if seed.item_type == "debug_locate":
        return {"locate": key if right else {**key, "line": key["line"] + 1}}
    if right:
        return {"choice": key}
    keys = [o.get("key", o.get("id")) for o in body.get("options") or body.get("sentences")]
    return {"choice": next(k for k in keys if k != key)}


def state(client):
    return client.get(REVIEW).json()


def finish_review(client, catalog, right=True):
    while state(client)["state"] == "available":
        res = answer(client, catalog, right)
        assert res.status_code == 200, res.text


def test_review_not_ready_until_units_pass(client):
    assert state(client)["state"] == "not_ready"
    assert client.get(f"{REVIEW}/exercise").status_code == 423


def test_unknown_stage_is_404(client):
    assert client.get(f"{BASE}/courses/python/stages/9/review").status_code == 404
    assert client.get(f"{BASE}/courses/cooking/stages/0/review").status_code == 404


def test_passing_the_review_opens_the_build(client, repo, catalog):
    pass_units(repo, catalog)
    assert state(client)["state"] == "available"
    assert client.get("/api/v1/courses/python/stages/0/build").status_code == 423

    finish_review(client, catalog)

    assert state(client)["state"] == "passed"
    assert client.get("/api/v1/courses/python/stages/0/build").status_code == 200


def test_course_map_reports_the_review_state_and_lock(client, repo, catalog):
    pass_units(repo, catalog)

    build = client.get("/api/v1/courses/python").json()["stages"][0]["build"]

    assert build["locked"] is True
    assert build["pending_units"] == []
    assert build["review_state"] == "available"


def test_course_map_plans_a_review_only_where_spare_items_exist(client, repo, catalog):
    planned = client.get("/api/v1/courses/python").json()["stages"][0]["build"]

    assert planned["review_planned"] is True
    assert planned["review_state"] == "not_ready"

    catalog.seeds = {}
    assert client.get("/api/v1/courses/python").json()["stages"][0]["build"]["review_planned"] is False


def test_a_build_page_uses_the_stage_label(client, repo, catalog):
    pass_units(repo, catalog)
    finish_review(client, catalog)

    assert client.get("/api/v1/courses/python/stages/0/build").json()["stage_label"] == "Stage 0"


def test_stage_with_no_items_opens_the_build_as_before(client, repo, catalog):
    # Keep only what each unit's own round uses, so no spare item is left for a review.
    catalog.seeds = {
        u: [s for s in ss if not s.cold_check_eligible or s in cold_round(catalog.get_unit(u), ss)]
        for u, ss in catalog.seeds.items()
        if catalog.get_unit(u)
    }
    pass_units(repo, catalog)

    assert state(client)["state"] == "unavailable"
    assert client.get(f"{REVIEW}/exercise").status_code == 404
    assert client.get("/api/v1/courses/python/stages/0/build").status_code == 200


def test_review_items_are_mixed_and_write_cold_evidence(client, repo, catalog):
    pass_units(repo, catalog)

    first = client.get(f"{REVIEW}/exercise").json()
    res = send(client, catalog, first, "stage_review", True)
    second = client.get(f"{REVIEW}/exercise").json()

    assert res.status_code == 200
    assert first["unit_id"] != second["unit_id"]
    written = repo.get_evidence_ledger(LOCAL_LEARNER_ID)[-1]
    assert written.cold_check is True
    assert written.review_kind == "stage_review"
    assert written.evidence_strength == EvidenceStrength.STRONG
    assert written.assistance_level == AssistanceLevel.NONE


def test_review_round_is_stable_across_requests(client, repo, catalog):
    pass_units(repo, catalog)

    assert client.get(f"{REVIEW}/exercise").json() == client.get(f"{REVIEW}/exercise").json()


def test_failed_review_waits_names_units_and_hides_the_answer(client, repo, catalog, clock):
    pass_units(repo, catalog)
    res = answer(client, catalog, right=False)
    assert "reveal" not in res.json()
    finish_review(client, catalog)

    found = state(client)

    assert found["state"] == "failed_waiting"
    assert len(found["failed_units"]) == 1
    assert client.get(f"{REVIEW}/exercise").status_code == 423
    assert client.get("/api/v1/courses/python/stages/0/build").status_code == 423


def test_retry_after_a_day_brings_back_only_failed_items_with_a_new_one(client, repo, catalog, clock):
    pass_units(repo, catalog)
    wrong = client.get(f"{REVIEW}/exercise").json()
    send(client, catalog, wrong, "stage_review", False)
    finish_review(client, catalog)
    total = state(client)["items_total"]

    clock.now = T0 + DAY

    retry = client.get(f"{REVIEW}/exercise").json()
    assert retry["unit_id"] == wrong["unit_id"]
    assert retry["exercise_id"] != wrong["exercise_id"]
    assert state(client)["items_done"] == total - 1
    assert send(client, catalog, retry, "stage_review", True).status_code == 200
    assert state(client)["state"] == "passed"


def test_attempt_must_be_the_next_item(client, repo, catalog):
    pass_units(repo, catalog)
    current = client.get(f"{REVIEW}/exercise").json()
    answer(client, catalog)

    res = client.post(f"{BASE}/attempts", json={"exercise_id": current["exercise_id"], "activity": "stage_review", "choice": "A"})

    assert res.status_code == 409


def test_a_later_item_cannot_be_answered_first(client, repo, catalog):
    pass_units(repo, catalog)
    client.get(f"{REVIEW}/exercise")
    later = repo.get_review_items(LOCAL_LEARNER_ID, STAGE_REVIEW, "python/0")[1]

    res = client.post(f"{BASE}/attempts", json={"exercise_id": later.exercise_id, "activity": "stage_review", "choice": "A"})

    assert res.status_code == 409
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_unit_round_of_three_needs_every_item_and_retries_only_the_failed_one(client, repo, catalog, clock):
    spare = next(s for s in catalog.seeds["PY-0.4"] if s.seed_id.endswith("cold-predict-1"))
    catalog.seeds["PY-0.4"] = [spare, clone(spare, "two"), clone(spare, "three")]
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-0.4", T0 - 2 * DAY)
    route = f"{BASE}/units/PY-0.4/activities/cold_check/exercise"
    cold = f"{BASE}/units/PY-0.4/cold-check"

    first = client.get(route).json()
    send(client, catalog, first, "cold_check", False)
    assert client.get(cold).json()["state"] == "available"
    send(client, catalog, client.get(route).json(), "cold_check", True)
    assert client.get(cold).json()["state"] == "available"
    send(client, catalog, client.get(route).json(), "cold_check", True)
    assert client.get(cold).json()["state"] == "failed_waiting"

    clock.now = T0 + DAY
    retry = client.get(route).json()

    assert retry["exercise_id"] == first["exercise_id"]
    send(client, catalog, retry, "cold_check", True)
    assert client.get(cold).json()["state"] == "passed"


def test_attempt_outside_a_round_is_refused(client, repo, catalog):
    pass_units(repo, catalog)

    res = client.post(f"{BASE}/attempts", json={"exercise_id": "PY-0.1/cold-predict-1-spare/v1", "activity": "stage_review", "choice": "A"})

    assert res.status_code == 409


def test_passed_review_refuses_more_exercises(client, repo, catalog):
    pass_units(repo, catalog)
    finish_review(client, catalog)

    assert client.get(f"{REVIEW}/exercise").status_code == 409


def test_axis_is_refused_on_a_review_item(client, repo, catalog):
    pass_units(repo, catalog)
    current = client.get(f"{REVIEW}/exercise").json()

    res = client.post(
        "/api/v1/axis/consult",
        json={
            "unit_id": current["unit_id"],
            "mode": "Socratic",
            "current_activity": "Predict",
            "user_prompt": "Help",
            "exercise_id": current["exercise_id"],
        },
    )

    assert res.status_code == 403


def test_unit_reset_keeps_a_passed_review(client, repo, catalog):
    pass_units(repo, catalog)
    finish_review(client, catalog)

    client.post(f"{BASE}/units/PY-0.1/reset")

    assert state(client)["state"] == "passed"
    assert client.get("/api/v1/courses/python/stages/0/build").status_code == 200


def add_recheck_spares(catalog):
    for unit_id in ("PY-0.1", "PY-0.4"):
        spare = next(s for s in catalog.seeds[unit_id] if s.seed_id.endswith("cold-predict-1"))
        catalog.seeds[unit_id] += [clone(spare, f"later{n}") for n in range(3)]


def test_recheck_falls_due_runs_and_finishes(client, repo, catalog, clock):
    pass_units(repo, catalog)
    finish_review(client, catalog)
    add_recheck_spares(catalog)
    assert client.get(f"{BASE}/reviews/due").json() == []

    clock.now = T0 + timedelta(days=7)
    due_now = client.get(f"{BASE}/reviews/due").json()

    assert [d["skill_id"] for d in due_now] == ["CO-1"]
    assert due_now[0]["days"] == 7
    assert 2 <= due_now[0]["items"] <= 4
    assert due_now[0]["skill_name"] != "CO-1"

    route = f"{BASE}/reviews/CO-1/7/exercise"
    for _ in range(due_now[0]["items"]):
        res = send(client, catalog, client.get(route).json(), "recheck", True)
        assert res.status_code == 200, res.text

    assert client.get(f"{BASE}/reviews/due").json() == []
    assert client.get(route).status_code == 404
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID)[-1].review_kind == "recheck"


def test_failed_recheck_finishes_and_resets_nothing(client, repo, catalog, clock):
    pass_units(repo, catalog)
    finish_review(client, catalog)
    add_recheck_spares(catalog)
    clock.now = T0 + timedelta(days=7)
    items = client.get(f"{BASE}/reviews/due").json()[0]["items"]

    for _ in range(items):
        send(client, catalog, client.get(f"{BASE}/reviews/CO-1/7/exercise").json(), "recheck", False)

    assert client.get(f"{BASE}/reviews/due").json() == []
    assert state(client)["state"] == "passed"
    assert client.get("/api/v1/units/PY-0.1").status_code == 200


def test_recheck_not_yet_due_is_refused(client, repo, catalog):
    pass_units(repo, catalog)
    finish_review(client, catalog)
    add_recheck_spares(catalog)

    assert client.get(f"{BASE}/reviews/CO-1/7/exercise").status_code == 404


def test_due_recheck_with_no_unseen_item_is_left_out(client, repo, catalog, clock):
    pass_units(repo, catalog)
    finish_review(client, catalog)
    for unit_id, unit_seeds in catalog.seeds.items():
        repo.set_current_exercise(LOCAL_LEARNER_ID, unit_id, "cold_check", "x", T0)
        for seed in unit_seeds:
            for n, _ in seed_variants(seed):
                repo.set_current_exercise(LOCAL_LEARNER_ID, unit_id, "cold_check", f"{seed.seed_id}/v{n}", T0)

    clock.now = T0 + timedelta(days=7)

    assert client.get(f"{BASE}/reviews/due").json() == []


# --- Storage ---


def test_old_cold_item_column_is_migrated(tmp_path):
    import sqlite3

    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE cold_check_item (learner_id TEXT NOT NULL, unit_id TEXT NOT NULL, skill_id TEXT NOT NULL,"
            " passed INTEGER NOT NULL, attempted_at TEXT NOT NULL, PRIMARY KEY (learner_id, unit_id, skill_id))"
        )
    repo = SQLiteLearnerRepository(db_path=str(path))
    repo.initialize()
    repo.initialize()

    repo.record_cold_item("l", "u", "u/cold-1", True, T0)

    assert repo.get_cold_items("l", "u") == {"u/cold-1": True}


def test_review_kind_survives_the_ledger(repo):
    repo.record_evidence(entry(kind=RECHECK).model_copy(update={"learner_id": "l"}))

    assert repo.get_evidence_ledger("l")[0].review_kind == RECHECK


def test_timer_type_is_untouched():
    assert ColdCheckTimer(learner_id="l", unit_id="u", completed_at=T0).last_attempt_passed is None
