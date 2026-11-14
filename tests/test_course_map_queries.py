"""Audit step A3 (independent audit 2026-11-09): the course map must not query the database once
per unit. The full roadmaps hold hundreds of units, so a per-unit query (about 373 in the audit)
makes a page load slow. The number of queries must stay small and not grow with the unit count."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.review import STAGE_REVIEW, stage_scope

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
MAX_QUERIES = 12
DAY = timedelta(days=1)


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


def counted_client(catalog):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(
        repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=lambda: T0
    )
    statements: list[str] = []
    repo._get_conn().set_trace_callback(statements.append)
    return TestClient(app), statements, repo


def course_with_most_units(catalog):
    return max(
        ("python", "backend", "ai"),
        key=lambda c: len(catalog.get_course_units(c)),
    )


def test_the_course_map_uses_a_small_fixed_number_of_queries(catalog):
    client, statements, _ = counted_client(catalog)
    course = course_with_most_units(catalog)
    assert len(catalog.get_course_units(course)) > 50

    statements.clear()
    response = client.get(f"/api/v1/courses/{course}")

    assert response.status_code == 200
    selects = [s for s in statements if s.lstrip().upper().startswith(("SELECT", "INSERT", "UPDATE"))]
    assert len(selects) <= MAX_QUERIES, f"{len(selects)} queries for one course map"


def add_progress(repo, course, units):
    """Clocks started on every unit, rounds passed on every second one, and one stage review result."""
    for number, unit in enumerate(units):
        repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, unit.unit_id, T0 - 2 * DAY)
        if number % 2 == 0:
            repo.record_cold_check_attempt(LOCAL_LEARNER_ID, unit.unit_id, True, T0 - DAY)
    repo.record_review_result(LOCAL_LEARNER_ID, STAGE_REVIEW, stage_scope(course, units[0].stage), True, T0 - DAY)


def test_the_query_count_stays_small_for_a_learner_with_progress(catalog):
    client, statements, repo = counted_client(catalog)
    course = course_with_most_units(catalog)
    add_progress(repo, course, catalog.get_course_units(course))

    statements.clear()
    response = client.get(f"/api/v1/courses/{course}")

    assert response.status_code == 200
    queries = [s for s in statements if s.lstrip().upper().startswith(("SELECT", "INSERT", "UPDATE"))]
    assert len(queries) <= MAX_QUERIES, f"{len(queries)} queries for one course map"


def test_the_course_map_shows_the_cold_check_progress_the_learner_made(catalog):
    client, _, repo = counted_client(catalog)
    course = course_with_most_units(catalog)
    units = catalog.get_course_units(course)
    before = client.get(f"/api/v1/courses/{course}").json()
    add_progress(repo, course, units)
    after = client.get(f"/api/v1/courses/{course}").json()

    assert before != after
    assert client.get(f"/api/v1/courses/{course}").json() == after
