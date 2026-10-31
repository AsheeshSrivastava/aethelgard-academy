"""Tests for the exercise, reset, state and draft routes (SPEC-12 sections 4 and 4.1)."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.exercises import HIDDEN_REQUIRED, parse_seed, seed_variants, to_exercise
from lms.core.models import (
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)
BASE = "/api/v1/learners/me"
HIDDEN_KEYS = {key for keys in HIDDEN_REQUIRED.values() for key in keys} | {"line_states"}


class FakeClock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now

    def advance(self, delta):
        self.now += delta


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


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
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=clock
    )
    return TestClient(app)


def exercise_url(unit, activity):
    return f"{BASE}/units/{unit}/activities/{activity}/exercise"


def regenerate_url(unit, activity):
    return f"{BASE}/units/{unit}/activities/{activity}/exercises:regenerate"


def get_exercise(client, unit="PY-0.1", activity="predict"):
    res = client.get(exercise_url(unit, activity))
    assert res.status_code == 200, res.text
    return res.json()


def assert_problem(res, status):
    assert res.status_code == status, res.text
    assert res.headers["content-type"].startswith("application/problem+json")


def complete_unit(repo, clock, unit="PY-0.1"):
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, unit, clock())


def all_keys(value):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key
            yield from all_keys(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from all_keys(inner)


# --- Getting an exercise ---


def test_first_exercise_is_the_first_seed(client):
    body = get_exercise(client)

    assert body["exercise_id"] == "PY-0.1/predict-1/v1"
    assert body["unit_id"] == "PY-0.1"
    assert body["activity"] == "predict"
    assert body["origin"] == "authored"
    assert body["variant_no"] == 1
    assert body["item_type"] == "predict"
    assert "Amara Okafor" in body["prompt_markdown"]
    assert len(body["predict"]["options"]) == 4


def test_slots_are_filled_in(client):
    assert "{{" not in json.dumps(get_exercise(client))


def test_same_exercise_is_served_until_regenerated(client):
    assert get_exercise(client) == get_exercise(client)


def test_slug_with_a_hyphen_works(client):
    assert get_exercise(client, "PY-0.4", "debug-validate")["item_type"] == "debug"


def test_explain_serves_the_concept_check_prompt_only(client):
    body = get_exercise(client, "PY-0.1", "explain")

    assert body["item_type"] == "concept_check"
    assert "Explain in your own words" in body["prompt_markdown"]
    assert "solid_keywords" not in json.dumps(body)
    assert "rubric" not in json.dumps(body)


def test_playground_serves_the_starter(client):
    body = get_exercise(client, "PY-0.4", "playground")

    assert body["item_type"] == "playground"
    assert any("clean_name" in line for line in body["playground"]["starter"])


def test_video_has_no_exercise(client):
    assert_problem(client.get(exercise_url("PY-0.1", "video")), 404)


def test_activity_outside_the_unit_is_not_found(client):
    assert_problem(client.get(exercise_url("PY-0.1", "direct")), 404)
    assert_problem(client.get(exercise_url("PY-0.1", "nonsense")), 404)


def test_unknown_unit_is_not_found(client):
    assert_problem(client.get(exercise_url("PY-99.9", "predict")), 404)


def test_unit_with_no_seed_is_not_found(client):
    assert_problem(client.get(exercise_url("PY-1.2", "predict")), 404)


def test_exercises_are_per_learner(client, repo):
    repo.set_current_exercise("someone_else", "PY-0.1", "predict", "PY-0.1/predict-2/v2", served_at=T0)

    assert get_exercise(client)["exercise_id"] == "PY-0.1/predict-1/v1"


# --- Hidden fields ---


def walk_everything(client, repo, clock, catalog):
    """Every exercise any learner could be served: all units, activities and variants."""
    served = []
    for unit_id in catalog.seeds:
        unit = catalog.get_unit(unit_id)
        repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, unit_id, clock() - 2 * DAY)
        for activity in unit.activities:
            if activity == "video":
                continue
            res = client.get(exercise_url(unit_id, activity))
            assert res.status_code == 200, (unit_id, activity, res.text)
            served.append(res)
            if activity == "explain":
                continue
            if activity == "cold_check":
                for skill in unit.target_skills[1:]:
                    previous = unit.target_skills[unit.target_skills.index(skill) - 1]
                    repo.record_cold_item(LOCAL_LEARNER_ID, unit_id, previous.skill_id, True, clock())
                    res = client.get(exercise_url(unit_id, activity))
                    assert res.status_code == 200, (unit_id, activity, res.text)
                    served.append(res)
                continue
            for _ in range(8):
                res = client.post(regenerate_url(unit_id, activity))
                assert res.status_code == 200, (unit_id, activity, res.text)
                served.append(res)
    return served


def test_no_hidden_field_appears_in_any_response(client, repo, clock, catalog):
    served = walk_everything(client, repo, clock, catalog)
    ids = {res.json()["exercise_id"] for res in served}

    for res in served:
        assert not HIDDEN_KEYS & set(all_keys(res.json())), res.text
        assert "cold_check_eligible" not in res.text
        assert "curator_approved" not in res.text

    expected = {
        f"{seed.seed_id}/v{n}"
        for seeds in catalog.seeds.values()
        for seed in seeds
        for n, _ in seed_variants(seed)
    }
    assert expected <= ids


def test_no_hidden_value_appears_in_any_response(client, repo, clock, catalog):
    served = " ".join(res.text for res in walk_everything(client, repo, clock, catalog))

    for seeds in catalog.seeds.values():
        for seed in seeds:
            for why in seed.body.get("why", []):
                assert why not in served, seed.seed_id
            for line in seed.body.get("expected_output", []):
                if len(line) > 3:
                    assert f'"{line}"' not in served, seed.seed_id
            reference = seed.body.get("reference_solution")
            if reference:
                assert json.dumps(reference) not in served, seed.seed_id


def spec_seeds():
    text = Path("docs/specs/13-exercise-seed-format-spec.md").read_text(encoding="utf-8")
    worked = text.split("## 10. Worked example")[1].split("## 12. Acceptance")[0]
    raw_seeds = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", worked, re.S)]
    return [parse_seed(r, r["seed_id"].split("/")[1], r["unit_id"]) for r in raw_seeds]


@pytest.mark.parametrize("seed", spec_seeds(), ids=lambda s: s.seed_id)
def test_every_item_type_strips_its_hidden_fields(seed):
    for n, variant in seed_variants(seed):
        exercise = to_exercise(variant, n).model_dump(exclude_none=True)

        assert not HIDDEN_KEYS & set(all_keys(exercise))


def test_spec_examples_cover_every_item_type_with_a_seed_form():
    types = {s.item_type for s in spec_seeds()}

    assert types == set(HIDDEN_REQUIRED) - {"playground", "debug", "choice"}


def test_plan_steps_are_not_served_in_the_curators_order():
    seed = next(s for s in spec_seeds() if s.item_type == "decompose_plan")

    steps = [s.id for s in to_exercise(seed, 1).decompose_plan.steps]

    assert steps != [s["id"] for s in seed.body["steps"]]
    assert sorted(steps) == sorted(s["id"] for s in seed.body["steps"])


# --- Regenerate ---


def regenerate(client, unit="PY-0.1", activity="predict"):
    res = client.post(regenerate_url(unit, activity))
    assert res.status_code == 200, res.text
    return res.json()


def test_regenerate_gives_the_next_unseen_variant(client):
    first = get_exercise(client)

    assert regenerate(client)["exercise_id"] != first["exercise_id"]


def test_regenerate_replaces_the_current_exercise(client):
    regenerated = regenerate(client)

    assert get_exercise(client) == regenerated


def test_regenerate_walks_every_variant_before_repeating(client):
    get_exercise(client)
    ids = {regenerate(client)["exercise_id"] for _ in range(5)}

    assert len(ids) == 5


def test_exhausted_pool_reuses_the_oldest_seen(client):
    first = get_exercise(client)["exercise_id"]
    for _ in range(5):
        regenerate(client)

    assert regenerate(client)["exercise_id"] == first


def test_explain_cannot_be_regenerated(client):
    assert_problem(client.post(regenerate_url("PY-0.1", "explain")), 409)


def test_video_cannot_be_regenerated(client):
    assert_problem(client.post(regenerate_url("PY-0.1", "video")), 404)


# --- Cold Check ---


def test_cold_check_is_locked_before_completion(client):
    assert_problem(client.get(exercise_url("PY-0.1", "cold_check")), 423)


def test_cold_check_is_locked_during_the_wait_then_opens(client, repo, clock):
    complete_unit(repo, clock)
    assert_problem(client.get(exercise_url("PY-0.1", "cold_check")), 423)

    clock.advance(DAY - timedelta(seconds=1))
    assert_problem(client.get(exercise_url("PY-0.1", "cold_check")), 423)

    clock.advance(timedelta(seconds=1))
    body = get_exercise(client, "PY-0.1", "cold_check")
    assert body["exercise_id"].startswith("PY-0.1/cold-")


def test_cold_check_stays_locked_after_a_fail_until_the_new_time(client, repo, clock):
    complete_unit(repo, clock)
    clock.advance(DAY)
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-0.1", passed=False, attempted_at=clock())

    assert_problem(client.get(exercise_url("PY-0.1", "cold_check")), 423)

    clock.advance(DAY)
    assert client.get(exercise_url("PY-0.1", "cold_check")).status_code == 200


def test_passed_cold_check_is_a_conflict(client, repo, clock):
    complete_unit(repo, clock)
    clock.advance(DAY)
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-0.1", passed=True, attempted_at=clock())

    assert_problem(client.get(exercise_url("PY-0.1", "cold_check")), 409)


def test_cold_check_regenerate_needs_an_attempt_on_the_current_variant(client, repo, clock):
    complete_unit(repo, clock)
    clock.advance(DAY)
    first = get_exercise(client, "PY-0.1", "cold_check")

    assert_problem(client.post(regenerate_url("PY-0.1", "cold_check")), 409)

    clock.advance(timedelta(hours=1))
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-0.1", passed=False, attempted_at=clock())
    clock.advance(DAY)
    second = regenerate(client, "PY-0.1", "cold_check")
    assert second["exercise_id"] == first["exercise_id"]  # CO-1 has one Cold Check seed

    assert_problem(client.post(regenerate_url("PY-0.1", "cold_check")), 409)


def test_cold_check_seeds_are_not_served_in_normal_steps(client):
    get_exercise(client)
    ids = {regenerate(client)["exercise_id"] for _ in range(7)}

    assert not any("cold" in i for i in ids)


def test_unit_without_cold_check_seeds_is_not_found(client, repo, clock):
    complete_unit(repo, clock, "PY-1.2")
    clock.advance(DAY)

    assert_problem(client.get(exercise_url("PY-1.2", "cold_check")), 404)


# --- Reset, state and drafts ---


def make_evidence():
    return EvidenceEntry(
        learner_id=LOCAL_LEARNER_ID,
        unit_id="PY-0.1",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="Task",
    )


def test_reset_clears_the_unit_but_never_the_ledger(client, repo, clock):
    repo.record_evidence(make_evidence())
    complete_unit(repo, clock)
    regenerate(client)
    state_url = f"{BASE}/units/PY-0.1/state"
    client.put(state_url, json={"step": "predict", "done_steps": ["video"]})
    exercise_id = get_exercise(client)["exercise_id"]
    client.put(f"{BASE}/drafts/{exercise_id}", json={"files": {"solution.py": "x"}})

    res = client.post(f"{BASE}/units/PY-0.1/reset")

    assert res.status_code == 204
    assert client.get(state_url).json() == {"step": None, "done_steps": []}
    assert client.get(f"{BASE}/drafts/{exercise_id}").json() == {"files": {}}
    assert client.get(f"{BASE}/units/PY-0.1/cold-check").json()["state"] == "not_ready"
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == 1


def test_reset_unknown_unit_is_not_found(client):
    assert_problem(client.post(f"{BASE}/units/PY-99.9/reset"), 404)


def test_state_defaults_then_round_trips(client):
    url = f"{BASE}/units/PY-0.1/state"

    assert client.get(url).json() == {"step": None, "done_steps": []}
    assert client.put(url, json={"step": "trace", "done_steps": ["video", "explain"]}).status_code == 200
    assert client.get(url).json() == {"step": "trace", "done_steps": ["video", "explain"]}


def test_state_refuses_steps_outside_the_unit(client):
    url = f"{BASE}/units/PY-0.1/state"

    assert_problem(client.put(url, json={"step": "direct", "done_steps": []}), 422)
    assert_problem(client.put(url, json={"step": "trace", "done_steps": ["nonsense"]}), 422)


def test_state_unknown_unit_is_not_found(client):
    assert_problem(client.get(f"{BASE}/units/PY-99.9/state"), 404)


def test_draft_round_trips(client):
    exercise_id = get_exercise(client, "PY-0.4", "debug-validate")["exercise_id"]
    url = f"{BASE}/drafts/{exercise_id}"

    assert client.get(url).json() == {"files": {}}
    assert client.put(url, json={"files": {"solution.py": "print(1)"}}).status_code == 204
    assert client.get(url).json() == {"files": {"solution.py": "print(1)"}}


def test_draft_for_the_playground_works(client):
    url = f"{BASE}/drafts/PY-0.4/playground/v1"

    assert client.put(url, json={"files": {"solution.py": "x"}}).status_code == 204


def test_draft_for_an_unknown_exercise_is_not_found(client):
    assert_problem(
        client.put(f"{BASE}/drafts/PY-0.1/nothing/v1", json={"files": {"a.py": "x"}}), 404
    )


def test_oversized_draft_is_refused(client):
    url = f"{BASE}/drafts/PY-0.1/playground/v1"

    assert_problem(client.put(url, json={"files": {"a.py": "x" * 300_000}}), 413)


def test_new_routes_appear_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert f"/api/v1/learners/me/units/{{unit_id}}/activities/{{activity}}/exercise" in paths
    assert f"/api/v1/learners/me/units/{{unit_id}}/activities/{{activity}}/exercises:regenerate" in paths
