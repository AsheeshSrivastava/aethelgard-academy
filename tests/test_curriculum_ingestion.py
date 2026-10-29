from pathlib import Path
import pytest
from lms.core.models import ActivityType, ProficiencyLevel, TargetSkill, Unit
from lms.adapters.curriculum.loader import (
    CurriculumCatalog,
    load_roadmap_from_file,
    parse_methods_string,
    parse_prerequisites_string,
    parse_skills_string,
    parse_unit_block,
)


def test_parse_skills_string():
    skills_text = "CO-1 to Understand; VE-4 to Understand"
    targets = parse_skills_string(skills_text)
    assert len(targets) == 2
    assert targets[0].skill_id == "CO-1"
    assert targets[0].goal_level == ProficiencyLevel.UNDERSTAND
    assert targets[1].skill_id == "VE-4"
    assert targets[1].goal_level == ProficiencyLevel.UNDERSTAND


def test_parse_methods_string():
    methods_text = "Explain → Predict → Debug & Validate"
    methods = parse_methods_string(methods_text)
    assert methods == [
        ActivityType.EXPLAIN,
        ActivityType.PREDICT,
        ActivityType.DEBUG_VALIDATE,
    ]


def test_parse_prerequisites_string():
    assert parse_prerequisites_string("None") == []
    assert parse_prerequisites_string("PY-0.4") == ["PY-0.4"]
    assert parse_prerequisites_string("PY-1.2, PY-1.7") == ["PY-1.2", "PY-1.7"]


def test_parse_unit_block():
    block = """
#### PY-0.4 Run a first program (new unit)

- **Objective:** Can set up and run a Python program, give it text input and output, and read a first error message.
- **The concept (Explain):** A program is text that the Python interpreter reads and runs from top to bottom.
- **Target skills:** CO-1 to Understand; VE-4 to Understand
- **Methods:** Explain → Predict → Debug & Validate
- **Outcome (measured at unit end):** CO-1: predicts the output of a 5-line script.
- **Topics:** print(); input(); comments
- **Prerequisites:** None | **Importance:** Foundational | **Integration link:** Entire Python roadmap
"""
    unit = parse_unit_block(block, stage=0)
    assert unit.unit_id == "PY-0.4"
    assert unit.title == "Run a first program"
    assert unit.stage == 0
    assert unit.concept_line == "A program is text that the Python interpreter reads and runs from top to bottom."
    assert len(unit.target_skills) == 2
    assert len(unit.methods) == 3
    assert unit.prerequisites == []


def test_load_full_python_roadmap():
    roadmap_path = Path("reference/Python Subject Roadmap v3.md")
    assert roadmap_path.exists(), "Reference roadmap file must exist"

    catalog = load_roadmap_from_file(roadmap_path)
    units = catalog.list_all_units()

    # There are over 25 units in the Python Subject Roadmap v3
    assert len(units) >= 25

    # Check that PY-0.4 exists
    py_04 = catalog.get_unit("PY-0.4")
    assert py_04 is not None
    assert py_04.unit_id == "PY-0.4"
    assert py_04.methods[0] == ActivityType.EXPLAIN

    # Check stage 0 units
    stage_0_units = catalog.get_stage_units(stage=0)
    assert len(stage_0_units) >= 3

    # Check that DAG is valid (no circular prerequisites)
    assert catalog.validate_dag() is True
