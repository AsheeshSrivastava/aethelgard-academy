"""Tests for assembling ProficiencyView from the ledger (SPEC-12 section 6, ADR-0016)."""

from datetime import datetime, timedelta, timezone
from itertools import count
from typing import Dict, List, Optional

from lms.core.cold_check import ColdCheckState, ColdCheckStatus
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    ProgressionDecision,
    TargetSkill,
    Unit,
)
from lms.core.proficiency import (
    Confidence,
    consecutive_shaky_checks,
    evidence_counts,
)
from lms.core.proficiency_view import build_proficiency_view, first_unfinished_unit

NOW = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
_ids = count(1)


def make(
    skill_id: str = "CO-1",
    unit_id: str = "PY-1.1",
    category: EvidenceCategory = EvidenceCategory.PERFORM_SOLVE,
    strength: EvidenceStrength = EvidenceStrength.STRONG,
    days_ago: float = 1,
    **overrides,
) -> EvidenceEntry:
    n = next(_ids)
    fields = dict(
        learner_id="learner_001",
        unit_id=unit_id,
        skill_id=skill_id,
        evidence_category=category,
        evidence_strength=strength,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="Task",
        recorded_at=NOW - timedelta(days=days_ago),
        exercise_id=f"ex-{n}",
    )
    fields.update(overrides)
    return EvidenceEntry(**fields)


def shaky(unit_id: str = "PY-1.1", days_ago: float = 1) -> EvidenceEntry:
    return make(
        "CO-6",
        unit_id,
        EvidenceCategory.EXPLAIN_REASON,
        EvidenceStrength.WEAK,
        days_ago,
        exercise_id=None,
    )


def solid(unit_id: str = "PY-1.1", days_ago: float = 1) -> EvidenceEntry:
    return make("CO-6", unit_id, EvidenceCategory.EXPLAIN_REASON, days_ago=days_ago, exercise_id=None)


def unit(
    unit_id: str = "PY-1.1",
    targets: Optional[Dict[str, ProficiencyLevel]] = None,
    methods: Optional[List[ActivityType]] = None,
) -> Unit:
    targets = targets if targets is not None else {"CO-1": ProficiencyLevel.APPLY}
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=1,
        concept_line="Concept",
        target_skills=[
            TargetSkill(skill_id=s, skill_name=s, goal_level=level) for s, level in targets.items()
        ],
        methods=methods or [ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.DEBUG_VALIDATE],
    )


def statuses(**by_unit: ColdCheckState):
    """Cold Check lookup; unit ids are given with underscores, e.g. PY_1_1."""
    states = {k.replace("_", "-", 1).replace("_", "."): v for k, v in by_unit.items()}

    def lookup(unit_id: str) -> ColdCheckStatus:
        return ColdCheckStatus(state=states.get(unit_id, ColdCheckState.NOT_READY))

    return lookup


def supported_apply(skill_id: str = "CO-1", unit_id: str = "PY-1.1") -> List[EvidenceEntry]:
    return [make(skill_id, unit_id, days_ago=3), make(skill_id, unit_id, days_ago=2, cold_check=True)]


def view(units, entries, cold=None):
    return build_proficiency_view(units, entries, cold or statuses(), now=NOW)


# --- consecutive_shaky_checks ---


def test_counts_consecutive_shaky_checks_for_the_unit():
    assert consecutive_shaky_checks([shaky(days_ago=3), shaky(days_ago=2)], "PY-1.1") == 2


def test_solid_check_ends_the_shaky_run():
    entries = [shaky(days_ago=4), solid(days_ago=3), shaky(days_ago=2)]
    assert consecutive_shaky_checks(entries, "PY-1.1") == 1


def test_shaky_checks_in_another_unit_do_not_count():
    assert consecutive_shaky_checks([shaky("PY-1.2"), shaky("PY-1.2", 2)], "PY-1.1") == 0


def test_a_failed_co6_predict_is_not_a_concept_check():
    wrong_predict = make(
        "CO-6",
        category=EvidenceCategory.EXPLAIN_REASON,
        strength=EvidenceStrength.WEAK,
        activity=ActivityType.PREDICT,
    )
    assert consecutive_shaky_checks([wrong_predict], "PY-1.1") == 0


# --- evidence_counts ---


def test_evidence_counts_group_by_category():
    entries = [
        make(category=EvidenceCategory.EXPLAIN_REASON),
        make(category=EvidenceCategory.PERFORM_SOLVE),
        make(category=EvidenceCategory.PERFORM_SOLVE),
        make(category=EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER),
        make("CO-2", category=EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER),
    ]
    assert evidence_counts(entries, "CO-1", now=NOW) == {
        EvidenceCategory.EXPLAIN_REASON: 1,
        EvidenceCategory.PERFORM_SOLVE: 2,
        EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER: 1,
    }


def test_evidence_counts_use_the_recency_window():
    assert evidence_counts([make(days_ago=91)], "CO-1", now=NOW)[EvidenceCategory.PERFORM_SOLVE] == 0


# --- Skills and units ---


def test_no_evidence_is_undecided():
    result = view([unit()], [])

    row = result.skills[0]
    assert row.skill_id == "CO-1"
    assert row.target_level == ProficiencyLevel.APPLY
    assert row.current_level is None
    assert row.confidence is None
    assert row.decision == ProgressionDecision.UNDECIDED
    assert row.evidence_counts.perform == 0
    assert result.units[0].decision == ProgressionDecision.UNDECIDED


def test_two_entries_with_a_cold_check_are_supported_and_progress():
    entries = supported_apply()
    result = view([unit()], entries)

    row = result.skills[0]
    assert row.current_level == ProficiencyLevel.APPLY
    assert row.confidence == Confidence.SUPPORTED
    assert row.decision == ProgressionDecision.PROGRESS
    assert row.evidence_counts.perform == 2
    assert set(row.entry_ids) == {e.entry_id for e in entries}
    assert row.reason


def test_two_entries_without_a_cold_check_stay_provisional():
    result = view([unit()], [make(days_ago=3), make(days_ago=2)])

    assert result.skills[0].confidence == Confidence.PROVISIONAL
    assert result.skills[0].decision == ProgressionDecision.STRENGTHEN


def test_unit_decision_is_the_weakest_of_its_skills():
    u = unit(targets={"CO-1": ProficiencyLevel.APPLY, "CO-2": ProficiencyLevel.APPLY})
    result = view([u], supported_apply("CO-1"))

    assert result.units[0].decision == ProgressionDecision.UNDECIDED


def test_each_unit_is_decided_against_its_own_target():
    units = [
        unit("PY-1.1", {"CO-1": ProficiencyLevel.UNDERSTAND}),
        unit("PY-1.2", {"CO-1": ProficiencyLevel.APPLY}),
        unit("PY-1.3", {"CO-1": ProficiencyLevel.ADAPT}),
    ]
    result = view(units, supported_apply())

    assert [u.decision for u in result.units] == [
        ProgressionDecision.ACCELERATE,
        ProgressionDecision.PROGRESS,
        ProgressionDecision.STRENGTHEN,
    ]


def test_skill_row_shows_the_highest_target_in_scope():
    units = [
        unit("PY-1.1", {"CO-1": ProficiencyLevel.UNDERSTAND}),
        unit("PY-1.2", {"CO-1": ProficiencyLevel.ADAPT}),
        unit("PY-1.3", {"CO-1": ProficiencyLevel.APPLY}),
    ]
    result = view(units, supported_apply())

    assert len(result.skills) == 1
    assert result.skills[0].target_level == ProficiencyLevel.ADAPT
    assert result.skills[0].decision == ProgressionDecision.STRENGTHEN


def test_shaky_concept_checks_rebuild_the_unit_and_its_skill_row():
    entries = supported_apply() + [shaky(days_ago=1.5), shaky(days_ago=1)]
    result = view([unit()], entries)

    assert result.units[0].decision == ProgressionDecision.REBUILD
    assert result.skills[0].decision == ProgressionDecision.REBUILD


def test_shaky_checks_elsewhere_do_not_rebuild_this_unit():
    entries = supported_apply() + [shaky("PY-9.9", 1.5), shaky("PY-9.9", 1)]

    assert view([unit()], entries).units[0].decision == ProgressionDecision.PROGRESS


# --- first_unfinished_unit ---


def test_first_unfinished_unit_for_a_fresh_learner_is_the_first_unit():
    units = [unit("PY-1.1"), unit("PY-1.2")]

    assert first_unfinished_unit(units, [], now=NOW).unit_id == "PY-1.1"


def test_finished_units_are_passed_over():
    units = [unit("PY-1.1", {"CO-1": ProficiencyLevel.APPLY}), unit("PY-1.2", {"CO-2": ProficiencyLevel.APPLY})]

    assert first_unfinished_unit(units, supported_apply(), now=NOW).unit_id == "PY-1.2"


def test_nothing_unfinished_gives_none():
    assert first_unfinished_unit([unit()], supported_apply(), now=NOW) is None
    assert first_unfinished_unit([], [], now=NOW) is None


# --- next_action ---


def test_no_units_means_no_next_action():
    assert view([], []).next_action is None


def test_all_units_done_means_no_next_action():
    assert view([unit()], supported_apply()).next_action is None


def test_fresh_learner_starts_with_explain_in_the_first_unit():
    action = view([unit("PY-1.1"), unit("PY-1.2")], []).next_action

    assert action.unit_id == "PY-1.1"
    assert action.skill_id == "CO-1"
    assert action.activity == "explain"
    assert action.decision == ProgressionDecision.UNDECIDED
    assert action.message


def test_next_activity_is_the_first_one_not_yet_tried():
    entries = [solid(), make(activity=ActivityType.PREDICT, category=EvidenceCategory.EXPLAIN_REASON)]

    assert view([unit()], entries).next_action.activity == "debug & validate"


def test_finished_units_are_skipped():
    units = [unit("PY-1.1", {"CO-1": ProficiencyLevel.APPLY}), unit("PY-1.2", {"CO-2": ProficiencyLevel.APPLY})]

    assert view(units, supported_apply()).next_action.unit_id == "PY-1.2"


def test_rebuild_points_back_to_explain():
    entries = [
        solid(days_ago=5),
        make(activity=ActivityType.PREDICT, days_ago=4),
        shaky(days_ago=2),
        shaky(days_ago=1),
    ]
    action = view([unit()], entries).next_action

    assert action.decision == ProgressionDecision.REBUILD
    assert action.activity == "explain"


def test_available_cold_check_is_the_next_action():
    entries = [make(days_ago=3)]
    action = view([unit()], entries, statuses(PY_1_1=ColdCheckState.AVAILABLE)).next_action

    assert action.activity == "cold_check"


def test_a_waiting_cold_check_does_not_block_the_next_unit():
    units = [unit("PY-1.1"), unit("PY-1.2")]
    action = view(units, [make(days_ago=3)], statuses(PY_1_1=ColdCheckState.WAITING)).next_action

    assert action.unit_id == "PY-1.2"


def test_everything_waiting_means_no_next_action():
    assert view([unit()], [make()], statuses(PY_1_1=ColdCheckState.WAITING)).next_action is None


def test_after_a_failed_cold_check_the_learner_practises_the_unit():
    tried = [
        solid(days_ago=5),
        make(activity=ActivityType.PREDICT, days_ago=4, category=EvidenceCategory.EXPLAIN_REASON),
        make(activity=ActivityType.DEBUG_VALIDATE, days_ago=3),
        make(strength=EvidenceStrength.WEAK, cold_check=True, days_ago=1),
    ]
    action = view([unit()], tried, statuses(PY_1_1=ColdCheckState.FAILED_WAITING)).next_action

    assert action.decision == ProgressionDecision.STRENGTHEN
    assert action.activity == "debug & validate"


def test_a_unit_without_target_skills_is_listed_but_gives_no_next_action():
    result = view([unit("PY-1.1", {})], [])

    assert result.units[0].decision == ProgressionDecision.UNDECIDED
    assert result.next_action is None
