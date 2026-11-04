"""My skills: every framework skill once, by area, from the whole ledger (SPEC-12 section 6.1)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.models import ProficiencyLevel
from lms.core.skills_view import AREAS, build_skills_overview

from test_proficiency_view import NOW, make, supported_apply, unit

NAMES = {"CO-1": "Predict before running", "CO-2": "Trace state", "VE-4": "Read errors", "SP-1": "State the goal"}


def overview(entries, units=None):
    units = units or [unit("PY-1.1", {"CO-1": ProficiencyLevel.APPLY}), unit("BE-1.1", {"CO-1": ProficiencyLevel.ADAPT})]
    return build_skills_overview(NAMES, units, entries, NOW)


def row(view, skill_id):
    return next(s for a in view.areas for s in a.skills if s.skill_id == skill_id)


def test_skills_are_grouped_by_the_five_areas_in_framework_order():
    view = overview([])

    assert [a.area_id for a in view.areas] == [a for a in AREAS if any(s.startswith(a) for s in NAMES)]
    assert [s.skill_id for s in view.areas[0].skills] == ["CO-1", "CO-2"]
    assert view.areas[0].name == "Comprehend"


def test_every_skill_appears_once_even_if_not_started():
    view = overview([])

    assert sorted(s.skill_id for a in view.areas for s in a.skills) == sorted(NAMES)
    assert row(view, "SP-1").level is None and row(view, "SP-1").evidence == 0


def test_the_level_comes_from_all_evidence_across_courses():
    entries = supported_apply("CO-1", "PY-1.1")

    skill = row(overview(entries), "CO-1")

    assert skill.level is not None and skill.evidence == 2
    assert skill.last_seen == max(e.recorded_at for e in entries)


def test_practised_in_lists_units_with_evidence_in_first_seen_order():
    entries = [make("CO-1", "BE-1.1", days_ago=1), make("CO-1", "PY-1.1", days_ago=3), make("CO-1", "PY-1.1", days_ago=2)]

    assert row(overview(entries), "CO-1").practised_in == ["PY-1.1", "BE-1.1"]


def test_targeted_in_counts_units_per_course():
    assert row(overview([]), "CO-1").targeted_in == {"python": 1, "backend": 1}


def test_a_unit_reset_does_not_change_the_lifetime_level():
    """Reset markers belong to My progress only (ADR-0016 amendment, point 3)."""
    entries = supported_apply("CO-1", "PY-1.1")

    assert row(overview(entries), "CO-1").level == row(build_skills_overview(NAMES, [], entries, NOW), "CO-1").level


def test_the_api_returns_all_27_skills(tmp_path):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    repo.record_evidence(make("CO-1", "PY-0.1").model_copy(update={"learner_id": LOCAL_LEARNER_ID}))
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(),
                     catalog=load_all_roadmaps(Path("reference")), clock=lambda: NOW)

    body = TestClient(app).get("/api/v1/learners/me/skills").json()

    skills = [s for a in body["areas"] for s in a["skills"]]
    assert len(skills) == 27 and [a["area_id"] for a in body["areas"]] == ["CO", "SP", "BU", "VE", "DE"]
    co1 = next(s for s in skills if s["skill_id"] == "CO-1")
    assert co1["practised_in"] == ["PY-0.1"] and set(co1["targeted_in"]) == {"python", "backend", "ai-engineering"}
