"""Tests for Make items (Learning Method v2 Amendment A1.3, SPEC-13 playground)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.curriculum_checks import Severity, check_curriculum
from lms.core.exercises import parse_seed, to_exercise
from lms.core.models import ActivityType, MakeStep, ProficiencyLevel, TargetSkill, Unit

BASE = "/api/v1/learners/me"


def raw(make=True, starter=("# Write your program here.", ""), skill="VE-6", stem="build-1", unit_id="PY-1.2"):
    return {
        "schema_version": 2,
        "seed_id": f"{unit_id}/{stem}",
        "unit_id": unit_id,
        "activity": "Build",
        "skill_id": skill,
        "level": "Apply",
        "prompt_markdown": ["Write the program."],
        "cold_check_eligible": False,
        "curator_approved": True,
        "playground": {
            "starter": list(starter),
            "tasks": [{"id": "t1", "label": "Print the total"}],
            "reference_solution": ["print(int(input()) + 1)"],
            "hidden_checks": [
                "import subprocess, sys",
                "def test_adds_one():",
                "    out = subprocess.run([sys.executable, 'solution.py'], input='2', capture_output=True, text=True).stdout",
                "    assert out.strip() == '3'",
            ],
            "wrong_solution": ["print(input())"],
            "make": make,
        },
    }


def make_unit(make_skill="VE-6", with_make=True):
    return Unit(
        unit_id="PY-1.2",
        title="Numbers",
        stage=1,
        concept_line="Every value has a type.",
        target_skills=[
            TargetSkill(skill_id="CO-1", skill_name="CO-1", goal_level=ProficiencyLevel.APPLY),
            TargetSkill(skill_id="VE-6", skill_name="VE-6", goal_level=ProficiencyLevel.APPLY),
        ],
        methods=[ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.DEBUG_VALIDATE, ActivityType.BUILD],
        make=MakeStep(skill_id=make_skill, task="a tip calculator") if with_make else None,
    )


def findings(unit, seeds):
    return {(f.severity, f.code) for f in check_curriculum([unit], seeds={unit.unit_id: seeds})}


# --- The seed field ---


def test_a_make_item_is_read_and_shown_to_the_learner():
    seed = parse_seed(raw(), "build-1", "PY-1.2")

    assert seed.body["make"] is True
    assert to_exercise(seed, 1).playground.make is True


def test_an_ordinary_build_item_is_not_a_make_item():
    seed = parse_seed(raw(make=False), "build-1", "PY-1.2")

    assert to_exercise(seed, 1).playground.make is False


def test_the_hidden_parts_of_a_make_item_stay_hidden():
    shown = to_exercise(parse_seed(raw(), "build-1", "PY-1.2"), 1).model_dump_json()

    assert "reference_solution" not in shown and "hidden_checks" not in shown and "wrong_solution" not in shown


# --- The four rules ---


def test_a_blank_or_comment_only_starter_is_fine():
    seed = parse_seed(raw(starter=("# Tip calculator", "", "#   read two numbers")), "build-1", "PY-1.2")

    assert (Severity.ERROR, "make-starter-not-blank") not in findings(make_unit(), [seed])


def test_a_starter_with_code_is_an_error():
    seed = parse_seed(raw(starter=("# Tip calculator", "total = 0")), "build-1", "PY-1.2")

    assert (Severity.ERROR, "make-starter-not-blank") in findings(make_unit(), [seed])


def test_a_make_item_on_a_unit_without_a_make_step_is_an_error():
    seed = parse_seed(raw(), "build-1", "PY-1.2")

    assert (Severity.ERROR, "make-seed-unexpected") in findings(make_unit(with_make=False), [seed])


def test_a_make_item_crediting_another_skill_is_an_error():
    seed = parse_seed(raw(skill="CO-1"), "build-1", "PY-1.2")

    assert (Severity.ERROR, "make-seed-wrong-skill") in findings(make_unit(), [seed])


def test_a_make_unit_without_an_approved_make_item_is_warned():
    plain = parse_seed(raw(make=False), "build-1", "PY-1.2")

    assert (Severity.WARNING, "make-seed-missing") in findings(make_unit(), [plain])
    assert (Severity.WARNING, "make-seed-missing") in findings(make_unit(), [])


def test_an_approved_make_item_clears_the_warning():
    seed = parse_seed(raw(), "build-1", "PY-1.2")

    assert (Severity.WARNING, "make-seed-missing") not in findings(make_unit(), [seed])


def test_an_unapproved_make_item_still_leaves_the_warning():
    seed = parse_seed({**raw(), "curator_approved": False}, "build-1", "PY-1.2")

    assert (Severity.WARNING, "make-seed-missing") in findings(make_unit(), [seed])


def test_the_real_curriculum_has_no_make_errors(catalog):
    codes = [f.code for f in catalog.findings]

    assert "make-starter-not-blank" not in codes
    assert "make-seed-unexpected" not in codes
    assert "make-seed-wrong-skill" not in codes
    assert codes.count("make-seed-missing") <= 15


# --- Through the app: PY-1.2's Make step ---


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def client_and_repo(catalog):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, test_mode=False)
    return TestClient(app), repo


def make_seed(catalog):
    return next(s for s in catalog.seeds["PY-1.2"] if s.body.get("make"))


def test_py_1_2_offers_its_make_step_on_the_build_step(client_and_repo, catalog):
    client, _ = client_and_repo
    unit = client.get("/api/v1/units/PY-1.2").json()
    served = client.get(f"{BASE}/units/PY-1.2/activities/build/exercise").json()

    assert unit["make"]["skill_id"] == "VE-6"
    assert "build" in unit["activities"]
    assert served["playground"]["make"] is True
    assert all(line.strip() == "" or line.strip().startswith("#") for line in served["playground"]["starter"])


def test_the_reference_program_passes_and_credits_the_make_skill(client_and_repo, catalog):
    client, repo = client_and_repo
    served = client.get(f"{BASE}/units/PY-1.2/activities/build/exercise").json()
    code = "\n".join(make_seed(catalog).body["reference_solution"])

    res = client.post(f"{BASE}/attempts", json={"exercise_id": served["exercise_id"], "activity": "build", "files": {"solution.py": code}})

    assert res.json()["outcome"] == "passed", res.text
    [entry] = repo.get_evidence_ledger(LOCAL_LEARNER_ID)
    assert entry.skill_id == "VE-6"
    assert entry.activity == ActivityType.BUILD


def test_the_wrong_program_fails(client_and_repo, catalog):
    client, _ = client_and_repo
    served = client.get(f"{BASE}/units/PY-1.2/activities/build/exercise").json()
    code = "\n".join(make_seed(catalog).body["wrong_solution"])

    res = client.post(f"{BASE}/attempts", json={"exercise_id": served["exercise_id"], "activity": "build", "files": {"solution.py": code}})

    assert res.json()["outcome"] == "failed"
