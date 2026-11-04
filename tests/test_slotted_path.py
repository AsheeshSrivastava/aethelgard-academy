"""Tests for slotted units, stage ids, path order and Make credits (ADR-0020)."""

from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import (
    CurriculumCatalog,
    load_all_roadmaps,
    load_path_order,
    parse_unit_block,
)
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import create_app
from lms.cli import _get_default_catalog
from lms.core.cold_check import ColdCheckState
from lms.core.course_map import build_course_map, course_of, stages_in_path_order
from lms.core.curriculum_checks import Severity, check_curriculum
from lms.core.models import (
    ActivityType,
    MakeStep,
    ProficiencyLevel,
    ProgressionDecision,
    TargetSkill,
    Unit,
    slotted_stage,
    stage_label,
)

PYTHON_V4 = Path("reference/Python Subject Roadmap v4.md")
BACKEND_V3 = Path("reference/Backend Engineering Roadmap v3.md")
MAKE_UNITS = {
    "PY-1.2": "VE-6", "PY-1.7": "VE-6", "PY-1.8": "VE-1", "PY-1.4": "BU-1", "PY-2.1": "VE-6",
    "PY-2.2": "VE-1", "PY-2.3": "BU-2", "PY-2.4": "BU-4", "PY-3.1": "BU-2", "PY-3.2": "BU-1",
    "PY-3.4": "VE-1", "PY-4.2": "VE-1", "PY-4.3": "VE-6", "PY-5.2": "BU-4", "PY-5.4": "BU-1",
}


@pytest.fixture(scope="module")
def catalog() -> CurriculumCatalog:
    return load_all_roadmaps(Path("reference"))


def unit(unit_id: str, stage: int, methods=None, skill: str = "CO-1", make=None) -> Unit:
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=stage,
        concept_line="Concept",
        target_skills=[TargetSkill(skill_id=skill, skill_name=skill, goal_level=ProficiencyLevel.UNDERSTAND)],
        methods=methods or [ActivityType.EXPLAIN, ActivityType.PREDICT],
        make=make,
    )


# --- Courses ---


@pytest.mark.parametrize(
    "unit_id, course",
    [
        ("DSA-0.1", "python"),
        ("GIT-2.1", "python"),
        ("SD-1.4", "python"),
        ("AAE-0.7", "python"),
        ("NET-0.1", "backend"),
        ("DB-1.6", "backend"),
        ("PY-1.1", "python"),
        ("BE-2.1", "backend"),
        ("AI-0.1", "ai-engineering"),
        ("XX-1.1", None),
    ],
)
def test_course_of_covers_slotted_prefixes(unit_id, course):
    assert course_of(unit_id) == course


# --- Stage ids and labels ---


@pytest.mark.parametrize(
    "unit_id, roadmap_stage, stage",
    [("DSA-1.1", 1, 101), ("GIT-2.1", 2, 202), ("SD-0.1", 0, 300), ("AAE-0.1", 0, 400),
     ("NET-0.1", 0, 500), ("DB-1.1", 1, 601), ("PY-4.1", 4, 4), ("BE-11.1", 11, 11)],
)
def test_slotted_stage_ids(unit_id, roadmap_stage, stage):
    assert slotted_stage(unit_id, roadmap_stage) == stage


@pytest.mark.parametrize(
    "stage, label",
    [(4, "Stage 4"), (0, "Stage 0"), (17, "Stage 17"), (100, "DSA 0"), (101, "DSA 1"),
     (202, "GIT 2"), (301, "SD 1"), (400, "AAE 0"), (500, "NET 0"), (601, "DB 1")],
)
def test_stage_labels(stage, label):
    assert stage_label(stage) == label


# --- The whole path ---


def test_course_counts_with_slotted_units(catalog):
    counts = {
        course: (len(units), len({u.stage for u in units}))
        for course in ("python", "backend", "ai-engineering")
        for units in [catalog.get_course_units(course)]
    }

    assert counts == {"python": (111, 22), "backend": (98, 21), "ai-engineering": (81, 18)}
    assert len(catalog.list_all_units()) == 290


def test_table_1_is_read_in_order():
    python = load_path_order(PYTHON_V4)
    backend = load_path_order(BACKEND_V3)

    assert (len(python), len(backend)) == (111, 98)
    assert python[:2] == ["PY-0.4", "PY-0.1"]
    assert python[23:25] == ["DSA-0.1", "DSA-0.2"]
    assert python[-1] == "PY-13.4"
    assert backend[0] == "NET-0.1"
    assert backend[6] == "BE-0.1"


def test_a_file_without_table_1_has_no_path(tmp_path):
    empty = tmp_path / "roadmap.md"
    empty.write_text("# Nothing here\n", encoding="utf-8")

    assert load_path_order(empty) == []
    assert load_path_order(tmp_path / "missing.md") == []


@pytest.mark.parametrize(
    "course, table", [("python", PYTHON_V4), ("backend", BACKEND_V3)]
)
def test_catalog_keeps_each_course_in_table_1_order(catalog, course, table):
    assert [u.unit_id for u in catalog.get_course_units(course)] == load_path_order(table)


def test_every_named_prerequisite_is_a_real_unit(catalog):
    known = {u.unit_id for u in catalog.list_all_units()}
    named = {
        p
        for u in catalog.list_all_units()
        for p in u.prerequisites
        if re.fullmatch(r"[A-Z]+-\d+(\.\d+)?", p)
    }

    assert not named - known
    assert catalog.validate_dag()


def test_slotted_stages_take_their_roadmap_titles(catalog):
    assert catalog.get_stage_titles("python")[100] == "Cost, sorting and search"
    assert catalog.get_stage_titles("python")[0] == "Running your first program"
    assert catalog.get_stage_titles("backend")[600] == "Relational model and SQL"


def test_python_stage_order_follows_table_1(catalog):
    assert stages_in_path_order(catalog.get_course_units("python")) == [
        0, 1, 2, 3, 100, 4, 200, 5, 6, 300, 7, 8, 101, 9, 10, 11, 201, 12, 301, 202, 400, 13,
    ]


def test_backend_stage_order_follows_table_1(catalog):
    assert stages_in_path_order(catalog.get_course_units("backend")) == [
        500, 0, 1, 2, 3, 4, 5, 600, 601, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
    ]


def test_a_slotted_stage_after_the_last_numbered_unit_stays_last():
    units = [unit("PY-1.1", 1), unit("DSA-0.1", 100)]

    assert stages_in_path_order(units) == [1, 100]


def test_units_without_slots_keep_number_order():
    assert stages_in_path_order([unit("AI-2.1", 2), unit("AI-0.1", 0)]) == [0, 2]


def test_course_map_uses_labels_and_path_order():
    units = [unit("PY-1.1", 1), unit("DSA-0.1", 100), unit("PY-2.1", 2)]

    stages = build_course_map(
        "python",
        units,
        {100: "Cost, sorting and search"},
        lambda _: ColdCheckState.PASSED,
        lambda _: ProgressionDecision.UNDECIDED,
    ).stages

    assert [s.stage for s in stages] == [1, 100, 2]
    assert [s.label for s in stages] == ["Stage 1", "DSA 0", "Stage 2"]
    assert stages[1].build.title == "DSA 0 build"


# --- API ---


@pytest.fixture
def client(catalog):
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    return TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog))


def test_course_map_route_shows_the_slotted_stage_in_place(client):
    stages = client.get("/api/v1/courses/python").json()["stages"]
    labels = [s["label"] for s in stages]

    assert labels.index("DSA 0") == labels.index("Stage 3") + 1
    assert labels.index("DSA 0") == labels.index("Stage 4") - 1
    dsa = stages[labels.index("DSA 0")]
    assert dsa["title"] == "Cost, sorting and search"
    assert [u["unit_id"] for u in dsa["units"]] == ["DSA-0.1", "DSA-0.2", "DSA-0.3", "DSA-0.4"]


def test_unit_route_gives_the_stage_label_and_make_step(client):
    body = client.get("/api/v1/units/PY-1.2").json()

    assert body["stage_label"] == "Stage 1"
    assert body["make"]["skill_id"] == "VE-6"
    assert body["make"]["task"].startswith("a tip calculator")
    assert client.get("/api/v1/units/DSA-0.1").json()["stage_label"] == "DSA 0"


# --- Make step credits ---


def test_make_is_read_from_the_outcome_line():
    block = """
#### PY-2.2 Iteration
- **The concept (Explain):** A loop repeats.
- **Target skills:** VE-1 to Adapt; CO-1 to Adapt
- **Methods:** Explain → Predict → Build
- **Outcome (measured at unit end):** Make (VE-1): a batch summary with checks. CO-1: predicts the output.
"""
    assert parse_unit_block(block, stage=2).make == MakeStep(
        skill_id="VE-1", task="a batch summary with checks."
    )


def test_a_unit_with_no_make_step_has_none():
    block = """
#### PY-1.1 Names
- **The concept (Explain):** A name points to an object.
- **Target skills:** CO-1 to Apply
- **Methods:** Explain → Predict
- **Outcome (measured at unit end):** CO-1: predicts state changes.
"""
    assert parse_unit_block(block, stage=1).make is None


def test_the_fifteen_make_steps_credit_the_approved_skills(catalog):
    credits = {u.unit_id: u.make.skill_id for u in catalog.list_all_units() if u.make}

    assert credits == MAKE_UNITS


def test_every_make_step_keeps_its_wording_and_build_method(catalog):
    for unit_id in MAKE_UNITS:
        found = catalog.get_unit(unit_id)
        assert found.make.task, unit_id
        assert ActivityType.BUILD in found.methods, unit_id
        assert found.make.skill_id in {s.skill_id for s in found.target_skills}, unit_id


def codes(findings):
    return [f.code for f in findings if f.severity == Severity.ERROR]


def test_make_credit_outside_the_targets_is_an_error():
    bad = unit(
        "PY-1.1", 1, [ActivityType.EXPLAIN, ActivityType.BUILD], make=MakeStep(skill_id="VE-6", task="x")
    )

    assert codes(check_curriculum([bad])) == ["make-credit-invalid"]


def test_make_without_a_build_method_is_an_error():
    bad = unit("PY-1.1", 1, make=MakeStep(skill_id="CO-1", task="x"))

    assert codes(check_curriculum([bad])) == ["make-credit-invalid"]


def test_build_seed_crediting_another_skill_is_an_error():
    make = MakeStep(skill_id="CO-1", task="x")
    target = unit("PY-1.1", 1, [ActivityType.EXPLAIN, ActivityType.BUILD], make=make)
    target.target_skills.append(
        TargetSkill(skill_id="VE-6", skill_name="VE-6", goal_level=ProficiencyLevel.UNDERSTAND)
    )
    seed = SimpleSeed("make-1", "VE-6")

    found = check_curriculum([target], seeds={"PY-1.1": [seed]})

    assert "make-seed-wrong-skill" in codes(found)


class SimpleSeed:
    """Only the fields the seed checks read."""

    def __init__(self, seed_id: str, skill_id: str) -> None:
        self.seed_id = seed_id
        self.skill_id = skill_id
        self.activity = ActivityType.BUILD
        self.level = ProficiencyLevel.UNDERSTAND
        self.cold_check_eligible = False
        self.curator_approved = True
        self.template = None
        self.item_type = "playground"
        self.body = {}


# --- Old roadmaps ---


def test_cli_catalog_reads_the_new_roadmaps_and_slotted_units():
    catalog = _get_default_catalog()

    assert catalog.get_unit("PY-1.9") is not None
    assert catalog.get_unit("DSA-0.1") is not None
