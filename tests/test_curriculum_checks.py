"""Tests for curriculum checks (SPEC-12 section 3.1)."""

import logging
from pathlib import Path
from typing import List

import pytest

from lms.adapters.curriculum.loader import (
    CurriculumCatalog,
    load_all_roadmaps,
    load_main_activities,
)
from lms.core.curriculum_checks import Severity, check_curriculum
from lms.core.models import ActivityType, ProficiencyLevel, TargetSkill, Unit


def unit(
    level: ProficiencyLevel = ProficiencyLevel.UNDERSTAND,
    methods: List[ActivityType] = None,
    unit_id: str = "PY-1.1",
    stage: int = 1,
) -> Unit:
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=stage,
        concept_line="Concept",
        target_skills=[TargetSkill(skill_id="CO-1", skill_name="CO-1", goal_level=level)],
        methods=methods or [ActivityType.EXPLAIN, ActivityType.PREDICT],
    )


def errors(units, **kwargs):
    return [f.code for f in check_curriculum(units, **kwargs) if f.severity == Severity.ERROR]


def warnings(units):
    return [f for f in check_curriculum(units) if f.severity == Severity.WARNING]


def test_apply_needs_a_perform_activity():
    assert errors([unit(ProficiencyLevel.APPLY)]) == ["apply-needs-perform"]
    assert (
        errors([unit(ProficiencyLevel.APPLY, [ActivityType.EXPLAIN, ActivityType.MODIFY])]) == []
    )


def test_adapt_needs_a_diagnose_activity():
    assert errors([unit(ProficiencyLevel.ADAPT, [ActivityType.EXPLAIN, ActivityType.MODIFY])]) == [
        "adapt-needs-diagnose"
    ]
    assert (
        errors([unit(ProficiencyLevel.ADAPT, [ActivityType.EXPLAIN, ActivityType.DEBUG_VALIDATE])])
        == []
    )


MAIN = {"CO-1": ActivityType.PREDICT}


def test_main_activity_satisfies_apply():
    assert errors([unit(ProficiencyLevel.APPLY)], main_activities=MAIN) == []


def test_main_activity_satisfies_adapt():
    assert errors([unit(ProficiencyLevel.ADAPT)], main_activities=MAIN) == []


def test_main_activity_missing_from_the_unit_does_not_help():
    other = unit(ProficiencyLevel.APPLY, [ActivityType.EXPLAIN, ActivityType.TRACE])

    assert errors([other], main_activities=MAIN) == ["apply-needs-perform"]


def test_understand_needs_nothing_more():
    assert errors([unit(ProficiencyLevel.UNDERSTAND)]) == []


def test_own_needs_a_stage_build():
    own = unit(ProficiencyLevel.OWN, [ActivityType.EXPLAIN, ActivityType.DEBUG_VALIDATE])

    assert errors([own]) == ["own-needs-stage-build"]
    assert errors([own], stages_with_build={("python", 1)}) == []
    assert errors([own], stages_with_build={("backend", 1)}) == ["own-needs-stage-build"]


def test_cold_check_needs_a_deterministic_activity():
    assert errors([unit(methods=[ActivityType.EXPLAIN, ActivityType.SPECIFY])]) == [
        "cold-check-not-graded"
    ]


@pytest.mark.parametrize("activity", [ActivityType.EVALUATE, ActivityType.DIRECT])
def test_fixed_answer_activities_can_carry_a_cold_check(activity):
    assert errors([unit(methods=[ActivityType.EXPLAIN, activity])]) == []


def test_finding_names_the_unit_and_skill():
    finding = check_curriculum([unit(ProficiencyLevel.APPLY)])[0]

    assert finding.unit_id == "PY-1.1"
    assert finding.skill_id == "CO-1"
    assert "CO-1" in finding.message


def test_stage_missing_an_evidence_category_is_a_warning():
    found = warnings([unit(methods=[ActivityType.EXPLAIN, ActivityType.PREDICT])])

    assert len(found) == 1
    assert found[0].code == "stage-missing-evidence"
    assert found[0].stage == 1
    assert "Perform / Solve" in found[0].message
    assert "Diagnose / Judge / Transfer" in found[0].message


def test_stage_covering_all_categories_across_units_has_no_warning():
    units = [
        unit(methods=[ActivityType.EXPLAIN, ActivityType.MODIFY], unit_id="PY-1.1"),
        unit(methods=[ActivityType.EXPLAIN, ActivityType.EVALUATE], unit_id="PY-1.2"),
    ]

    assert warnings(units) == []


def test_stages_are_checked_per_course():
    units = [
        unit(methods=[ActivityType.EXPLAIN, ActivityType.MODIFY], unit_id="PY-1.1"),
        unit(methods=[ActivityType.EXPLAIN, ActivityType.EVALUATE], unit_id="BE-1.1"),
    ]

    assert len(warnings(units)) == 2


def test_learning_method_table_gives_every_skill_a_main_activity():
    table = load_main_activities(Path("reference/Learning Method v2.md"))

    assert len(table) == 27
    assert table["CO-1"] == ActivityType.PREDICT
    assert table["CO-6"] == ActivityType.EXPLAIN
    assert table["VE-6"] == ActivityType.DEBUG_VALIDATE
    assert table["DE-5"] == ActivityType.DIRECT


def test_every_target_skill_in_the_roadmaps_has_a_main_activity():
    catalog = load_all_roadmaps(Path("reference"))
    targets = {s.skill_id for u in catalog.list_all_units() for s in u.target_skills}

    assert targets <= set(catalog.main_activities)


def test_missing_learning_method_file_gives_an_empty_table(tmp_path):
    assert load_main_activities(tmp_path / "missing.md") == {}


def test_empty_curriculum_has_no_findings():
    assert check_curriculum([]) == []


def test_load_records_findings_and_does_not_fail(caplog):
    with caplog.at_level(logging.WARNING, logger="lms.adapters.curriculum.loader"):
        catalog = load_all_roadmaps(Path("reference"))

    assert catalog.findings == check_curriculum(
        catalog.list_all_units(), main_activities=catalog.main_activities
    )
    assert "Curriculum checks" in caplog.text


def test_a_new_catalog_has_no_findings():
    assert CurriculumCatalog().findings == []


# Findings on the roadmaps after the ADR-0016 amendment (2026-10-31), reported to the
# owner. These counts may only go down: lower them when the curriculum is fixed.
KNOWN_FINDINGS = {
    "apply-needs-perform": 0,
    "adapt-needs-diagnose": 0,
    "cold-check-not-graded": 2,   # BE-7.1 and AI-0.1
    "own-needs-stage-build": 30,  # Clears when stage builds are curated
    "stage-missing-evidence": 0,
}


@pytest.mark.parametrize("code, limit", KNOWN_FINDINGS.items())
def test_real_roadmaps_add_no_new_findings(code, limit):
    catalog = load_all_roadmaps(Path("reference"))

    assert len([f for f in catalog.findings if f.code == code]) <= limit
