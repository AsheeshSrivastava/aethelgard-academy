"""Tests for curriculum checks (SPEC-12 section 3.1)."""

import logging
from pathlib import Path
from typing import List

import pytest

from lms.adapters.curriculum.loader import CurriculumCatalog, load_all_roadmaps
from lms.core.curriculum_checks import Severity, check_curriculum
from lms.core.models import ActivityType, ProficiencyLevel, TargetSkill, Unit

EVERY_ACTIVITY = list(ActivityType)


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


def test_understand_needs_nothing_more():
    assert errors([unit(ProficiencyLevel.UNDERSTAND)]) == []


def test_own_needs_a_stage_build():
    own = unit(ProficiencyLevel.OWN, [ActivityType.EXPLAIN, ActivityType.DEBUG_VALIDATE])

    assert errors([own]) == ["own-needs-stage-build"]
    assert errors([own], stages_with_build={("python", 1)}) == []
    assert errors([own], stages_with_build={("backend", 1)}) == ["own-needs-stage-build"]


def test_cold_check_needs_a_deterministic_activity():
    assert errors([unit(methods=[ActivityType.EXPLAIN, ActivityType.EVALUATE])]) == [
        "cold-check-not-graded"
    ]


def test_finding_names_the_unit_and_skill():
    finding = check_curriculum([unit(ProficiencyLevel.APPLY)])[0]

    assert finding.unit_id == "PY-1.1"
    assert finding.skill_id == "CO-1"
    assert "CO-1" in finding.message


def test_stage_missing_an_activity_type_is_a_warning():
    found = warnings([unit(methods=[ActivityType.EXPLAIN, ActivityType.PREDICT])])

    assert len(found) == 1
    assert found[0].code == "stage-missing-activity"
    assert found[0].stage == 1
    assert "Modify" in found[0].message


def test_stage_using_every_activity_across_units_has_no_warning():
    units = [
        unit(methods=EVERY_ACTIVITY[:5], unit_id="PY-1.1"),
        unit(methods=[ActivityType.EXPLAIN, *EVERY_ACTIVITY[5:]], unit_id="PY-1.2"),
    ]

    assert warnings(units) == []


def test_stages_are_checked_per_course():
    units = [
        unit(methods=EVERY_ACTIVITY[:5], unit_id="PY-1.1"),
        unit(methods=[ActivityType.EXPLAIN, *EVERY_ACTIVITY[5:]], unit_id="BE-1.1"),
    ]

    assert len(warnings(units)) == 2


def test_empty_curriculum_has_no_findings():
    assert check_curriculum([]) == []


def test_load_records_findings_and_does_not_fail(caplog):
    with caplog.at_level(logging.WARNING, logger="lms.adapters.curriculum.loader"):
        catalog = load_all_roadmaps(Path("reference"))

    assert catalog.findings == check_curriculum(catalog.list_all_units())
    assert "Curriculum checks" in caplog.text


def test_a_new_catalog_has_no_findings():
    assert CurriculumCatalog().findings == []


# Findings on the roadmaps when the checks were introduced (2026-10-31), reported to
# the owner. These counts may only go down: lower them when the curriculum is fixed.
KNOWN_FINDINGS = {
    "apply-needs-perform": 54,
    "adapt-needs-diagnose": 61,
    "cold-check-not-graded": 41,
    "own-needs-stage-build": 30,
    "stage-missing-activity": 50,
}


@pytest.mark.parametrize("code, limit", KNOWN_FINDINGS.items())
def test_real_roadmaps_add_no_new_findings(code, limit):
    catalog = load_all_roadmaps(Path("reference"))

    assert len([f for f in catalog.findings if f.code == code]) <= limit
