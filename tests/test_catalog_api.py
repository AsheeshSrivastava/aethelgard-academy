"""Tests for loading all three roadmaps and the catalog routes (SPEC-12 sections 2, 3)."""

from datetime import datetime, timezone
from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import (
    CurriculumCatalog,
    load_all_roadmaps,
    parse_prerequisites_string,
    parse_unit_block,
)
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.models import ACTIVITY_BY_SLUG, ActivityType, ProficiencyLevel, TargetSkill, Unit

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def full_catalog() -> CurriculumCatalog:
    return load_all_roadmaps(Path("reference"))


def make_client(catalog: CurriculumCatalog):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=lambda: T0
    )
    return TestClient(app), repo


@pytest.fixture
def client(full_catalog):
    return make_client(full_catalog)[0]


def make_unit(unit_id: str, stage: int, methods=None) -> Unit:
    return Unit(
        unit_id=unit_id,
        title=f"Title {unit_id}",
        stage=stage,
        concept_line="Concept",
        target_skills=[
            TargetSkill(skill_id="CO-1", skill_name="CO-1", goal_level=ProficiencyLevel.APPLY)
        ],
        methods=methods or [ActivityType.EXPLAIN, ActivityType.PREDICT],
    )


def small_catalog() -> CurriculumCatalog:
    catalog = CurriculumCatalog()
    catalog.add_unit(make_unit("PY-1.1", 1))
    catalog.add_unit(make_unit("PY-1.2", 1))
    catalog.add_unit(make_unit("PY-2.1", 2))
    return catalog


# --- Parsing ---


def test_parser_reads_non_python_unit_ids():
    block = """
#### BE-2.4 Read and use the generated OpenAPI contract (new unit)
- **The concept (Explain):** The contract is generated.
- **Target skills:** CO-3 to Apply; VE-1 to Adapt
- **Methods:** Explain → Trace → Evaluate
"""
    unit = parse_unit_block(block, stage=2)

    assert unit.unit_id == "BE-2.4"
    assert unit.title == "Read and use the generated OpenAPI contract"
    assert [s.skill_id for s in unit.target_skills] == ["CO-3", "VE-1"]


def test_prerequisites_keep_units_and_drop_soft_and_link_notes():
    text = "AI-0.1; PY-8.2, PY-8.4 (Python through Stage 8); soft: BE-5.1 (typed client); link: Networking"

    assert parse_prerequisites_string(text) == ["AI-0.1", "PY-8.2", "PY-8.4"]


# --- Loading ---


@pytest.mark.parametrize(
    "prefix, units, stages",
    [("PY-", 79, 14), ("BE-", 79, 18), ("AI-", 81, 18)],
)
def test_all_roadmaps_load_with_their_counts(full_catalog, prefix, units, stages):
    loaded = [u for u in full_catalog.list_all_units() if u.unit_id.startswith(prefix)]

    assert len(loaded) == units
    assert len({u.stage for u in loaded}) == stages


def test_every_unit_has_skills_and_methods(full_catalog):
    for unit in full_catalog.list_all_units():
        assert unit.target_skills, unit.unit_id
        assert unit.methods[0] == ActivityType.EXPLAIN, unit.unit_id


def test_full_prerequisite_graph_is_acyclic(full_catalog):
    assert full_catalog.validate_dag()


def test_lesson_packages_still_overlay(full_catalog):
    assert full_catalog.get_unit("PY-0.1").lesson_markdown is not None


# --- Unit.activities ---


def test_activities_start_with_video_explain_and_end_with_cold_check():
    unit = make_unit(
        "PY-1.1", 1, [ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.DEBUG_VALIDATE]
    )

    assert unit.activities == [
        "video",
        "explain",
        "predict",
        "debug-validate",
        "playground",
        "cold_check",
    ]


@pytest.mark.parametrize("activity", [ActivityType.MODIFY, ActivityType.BUILD])
def test_graded_playground_activities_add_no_separate_step(activity):
    unit = make_unit("PY-1.1", 1, [ActivityType.EXPLAIN, activity])

    assert unit.activities == ["video", "explain", activity.slug, "cold_check"]


def test_every_activity_slug_maps_back_to_its_type():
    assert ACTIVITY_BY_SLUG["debug-validate"] == ActivityType.DEBUG_VALIDATE
    assert {a: ACTIVITY_BY_SLUG[a.slug] for a in ActivityType} == {a: a for a in ActivityType}


def test_activities_are_safe_in_urls(full_catalog):
    for unit in full_catalog.list_all_units():
        assert all(re.fullmatch(r"[a-z_-]+", a) for a in unit.activities), unit.unit_id


def test_unit_route_returns_activities(client):
    body = client.get("/api/v1/units/PY-0.4").json()

    assert body["activities"][:2] == ["video", "explain"]
    assert body["activities"][-1] == "cold_check"


# --- Courses ---


def test_courses_lists_the_three_courses_with_counts(client):
    res = client.get("/api/v1/courses")

    assert res.status_code == 200
    counts = {c["course_id"]: (c["stage_count"], c["unit_count"]) for c in res.json()}
    assert counts == {"python": (22, 111), "backend": (21, 98), "ai-engineering": (18, 81)}
    assert all(c["title"] and c["summary"] for c in res.json())


def test_course_map_shape(client):
    body = client.get("/api/v1/courses/python").json()

    assert set(body) == {"course", "stages"}
    assert body["course"]["course_id"] == "python"
    assert set(body["stages"][0]) == {"stage", "label", "title", "units", "build"}
    assert set(body["stages"][0]["units"][0]) == {
        "unit_id",
        "title",
        "concept_line",
        "target_skills",
        "authored",
        "decision",
        "cold_check_state",
    }
    assert set(body["stages"][0]["units"][0]["target_skills"][0]) == {
        "skill_id",
        "skill_name",
        "goal_level",
    }
    assert set(body["stages"][0]["build"]) == {
        "title", "kind", "locked", "pending_units", "authored", "status", "review_state",
    }


def stage_by_number(body, stage: int):
    return next(s for s in body["stages"] if s["stage"] == stage)


def test_course_map_lists_numbered_stages_in_order_with_units_in_teaching_order(client):
    body = client.get("/api/v1/courses/backend").json()

    assert [s["stage"] for s in body["stages"] if s["stage"] < 100] == list(range(18))
    assert [u["unit_id"] for u in stage_by_number(body, 11)["units"]][:2] == ["BE-11.1", "BE-11.2"]


def test_stage_title_comes_from_the_roadmap(client):
    body = client.get("/api/v1/courses/backend").json()

    assert stage_by_number(body, 0)["title"] == "Backend service mental model"
    assert stage_by_number(body, 11)["title"] == "Backend testing"


def test_stage_without_a_roadmap_title_falls_back_to_its_number():
    client, _ = make_client(small_catalog())

    body = client.get("/api/v1/courses/python").json()

    assert body["stages"][0]["title"] == "Stage 1"


def test_python_stages_have_the_approved_titles(client):
    stages = client.get("/api/v1/courses/python").json()["stages"]
    titles = [s["title"] for s in stages if s["stage"] < 100]

    assert titles == [
        "Running your first program",
        "Values, text and collections",
        "Conditions, loops and control flow",
        "Functions and decomposition",
        "Errors, validation and failure contracts",
        "Modules, packages and project structure",
        "Classes and object design",
        "Iterators, decorators and type contracts",
        "Files, data and external services",
        "Testing, debugging and runtime evidence",
        "Environments, packaging and quality gates",
        "Concurrency and async",
        "Working in existing codebases",
        "Owning a Python subsystem",
    ]


def test_authored_marks_units_with_a_lesson_package(client):
    body = client.get("/api/v1/courses/python").json()
    stage_0 = {u["unit_id"]: u["authored"] for u in body["stages"][0]["units"]}
    stage_1 = body["stages"][1]["units"]

    assert stage_0 == {"PY-0.4": True, "PY-0.1": True, "PY-0.3": True}
    assert stage_1[0]["authored"] is False


def test_unknown_course_is_a_problem_response(client):
    res = client.get("/api/v1/courses/cooking")

    assert res.status_code == 404
    assert res.headers["content-type"].startswith("application/problem+json")


def test_build_is_locked_until_every_unit_passed_its_cold_check():
    client, repo = make_client(small_catalog())

    def stage_1_build():
        return client.get("/api/v1/courses/python").json()["stages"][0]["build"]

    assert stage_1_build()["locked"] is True
    assert stage_1_build()["pending_units"] == ["PY-1.1", "PY-1.2"]

    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.1", T0)
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-1.1", passed=True, attempted_at=T0)
    assert stage_1_build()["pending_units"] == ["PY-1.2"]

    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.2", T0)
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-1.2", passed=True, attempted_at=T0)
    assert stage_1_build() == {
        "title": "Stage 1 build",
        "kind": "script",
        "locked": False,
        "pending_units": [],
        "review_state": "unavailable",
        "authored": False,
        "status": None,
    }


def test_build_lock_ignores_other_learners_cold_checks():
    client, repo = make_client(small_catalog())
    repo.mark_unit_activities_completed("someone_else", "PY-1.1", T0)
    repo.record_cold_check_attempt("someone_else", "PY-1.1", passed=True, attempted_at=T0)

    build = client.get("/api/v1/courses/python").json()["stages"][0]["build"]

    assert "PY-1.1" in build["pending_units"]


def test_failed_cold_check_keeps_the_build_locked():
    client, repo = make_client(small_catalog())
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-2.1", T0)
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-2.1", passed=False, attempted_at=T0)

    build = client.get("/api/v1/courses/python").json()["stages"][1]["build"]

    assert build["locked"] is True


# --- What the frontend shows for the learner ---


def test_course_map_units_carry_the_learners_decision_and_cold_check():
    client, repo = make_client(small_catalog())
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-1.1", T0)

    unit = client.get("/api/v1/courses/python").json()["stages"][0]["units"][0]

    assert unit["decision"] == "Undecided"
    assert unit["cold_check_state"] == "waiting"


def test_skill_names_come_from_the_learning_method(client):
    unit = client.get("/api/v1/courses/python").json()["stages"][0]["units"][0]
    skill = client.get("/api/v1/units/PY-0.1").json()["target_skills"][0]

    assert unit["target_skills"][0]["skill_name"] == "Predict before running"
    assert skill["skill_name"] == "Predict before running"


def test_proficiency_rows_carry_the_skill_name(client):
    rows = client.get("/api/v1/learners/me/proficiency?course_id=python&stage=0").json()["skills"]

    assert next(r for r in rows if r["skill_id"] == "CO-1")["skill_name"] == "Predict before running"


# --- Old shell and identity ---


def test_units_can_be_filtered_by_course(client):
    units = client.get("/api/v1/units?course_id=python").json()

    assert len(units) == 111
    assert client.get("/api/v1/units?course_id=cooking").status_code == 404


def test_learners_me(client):
    assert client.get("/api/v1/learners/me").json() == {
        "learner_id": LOCAL_LEARNER_ID,
        "display_name": "Local learner",
        "auth_mode": "local-single",
    }
