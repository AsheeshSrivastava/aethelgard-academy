"""Tests for the whole-ledger proficiency estimator (ADR-0016)."""

from datetime import datetime, timedelta, timezone

from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    ProgressionDecision,
)
from lms.core.proficiency import (
    Confidence,
    EstimatorConfig,
    decide_skill,
    decide_unit,
    estimate_skill,
)

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
_counter = 0


def make(
    category=EvidenceCategory.PERFORM_SOLVE,
    strength=EvidenceStrength.STRONG,
    assistance=AssistanceLevel.NONE,
    *,
    days_ago=1.0,
    exercise_id=None,
    activity=None,
    cold_check=False,
    skill_id="CO-1",
):
    global _counter
    _counter += 1
    return EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id=skill_id,
        evidence_category=category,
        evidence_strength=strength,
        assistance_level=assistance,
        demonstration_context="test",
        recorded_at=NOW - timedelta(days=days_ago, seconds=-_counter),
        exercise_id=exercise_id or f"ex-{_counter}",
        activity=activity,
        cold_check=cold_check,
    )


def weak(days_ago=0.5, **kw):
    return make(strength=EvidenceStrength.WEAK, days_ago=days_ago, **kw)


# --- The decision asks about the target level -------------------------------


def test_a_provisional_top_rung_does_not_hide_proven_rungs_above_the_goal():
    # ADR-0016 amendment H: Apply is proven above the Understand goal, so Accelerate; Adapt is only seen once.
    config = EstimatorConfig(main_activities={"CO-2": ActivityType.TRACE})
    trace = dict(skill_id="CO-2", activity=ActivityType.TRACE)
    entries = [
        make(EvidenceCategory.EXPLAIN_REASON, EvidenceStrength.MODERATE, days_ago=3, **trace),
        make(EvidenceCategory.EXPLAIN_REASON, days_ago=2, cold_check=True, **trace),
    ]

    d = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-2", now=NOW, config=config)

    assert d.estimate.level == ProficiencyLevel.ADAPT
    assert d.estimate.confidence == Confidence.PROVISIONAL
    assert d.decision == ProgressionDecision.ACCELERATE


def test_supported_above_the_target_still_accelerates():
    entries = [make(days_ago=3), make(days_ago=2, cold_check=True)]

    d = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-1", now=NOW)

    assert d.decision == ProgressionDecision.ACCELERATE


def test_a_weak_entry_blocks_support_at_every_level():
    entries = [make(days_ago=4), make(days_ago=3, cold_check=True), weak(days_ago=1)]

    d = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-1", now=NOW)

    assert d.decision == ProgressionDecision.STRENGTHEN


# --- Amendment E: evidence counts per seed ----------------------------------


def seeded(seed_id, days_ago, strength=EvidenceStrength.STRONG, cold_check=False):
    entry = make(strength=strength, days_ago=days_ago, cold_check=cold_check)
    return entry.model_copy(update={"seed_id": seed_id})


def test_name_variants_of_a_seed_count_once():
    est = estimate_skill([seeded("s1", 3), seeded("s1", 2, cold_check=True)], "CO-1", now=NOW)

    assert len(est.qualifying_entry_ids) == 1
    assert est.confidence == Confidence.PROVISIONAL


def test_different_seeds_count_separately():
    est = estimate_skill([seeded("s1", 3), seeded("s2", 2, cold_check=True)], "CO-1", now=NOW)

    assert est.confidence == Confidence.SUPPORTED


def test_the_newest_result_for_a_seed_is_the_one_kept():
    entries = [seeded("s1", 3, EvidenceStrength.WEAK), seeded("s1", 2, EvidenceStrength.MODERATE)]

    est = estimate_skill(entries, "CO-1", now=NOW)

    assert est.level == ProficiencyLevel.APPLY
    assert est.weak_streak == 0


# --- Amendment A: a skill's main activity counts for Apply and Adapt --------

MAIN = EstimatorConfig(main_activities={"CO-1": ActivityType.PREDICT})


def predict(strength=EvidenceStrength.MODERATE, assistance=AssistanceLevel.NONE, **kw):
    return make(EvidenceCategory.EXPLAIN_REASON, strength, assistance, activity=ActivityType.PREDICT, **kw)


def test_main_activity_reaches_apply():
    assert estimate_skill([predict()], "CO-1", now=NOW, config=MAIN).level == ProficiencyLevel.APPLY


def test_without_the_mapping_the_original_rule_applies():
    assert estimate_skill([predict()], "CO-1", now=NOW).level == ProficiencyLevel.UNDERSTAND


def test_a_helper_activity_does_not_count_as_the_main_activity():
    entry = make(EvidenceCategory.EXPLAIN_REASON, activity=ActivityType.TRACE)

    assert estimate_skill([entry], "CO-1", now=NOW, config=MAIN).level == ProficiencyLevel.UNDERSTAND


def test_main_activity_of_another_skill_does_not_count():
    config = EstimatorConfig(main_activities={"CO-2": ActivityType.PREDICT})

    assert estimate_skill([predict()], "CO-1", now=NOW, config=config).level == ProficiencyLevel.UNDERSTAND


def test_entry_without_an_activity_uses_the_original_rule():
    entry = make(EvidenceCategory.EXPLAIN_REASON, activity=None)

    assert estimate_skill([entry], "CO-1", now=NOW, config=MAIN).level == ProficiencyLevel.UNDERSTAND


def test_apply_keeps_its_assistance_limit():
    entry = predict(assistance=AssistanceLevel.STRUCTURAL_DIRECTION)

    assert estimate_skill([entry], "CO-1", now=NOW, config=MAIN).level is None


def test_adapt_on_main_activity_needs_strong():
    assert estimate_skill([predict()], "CO-1", now=NOW, config=MAIN).level != ProficiencyLevel.ADAPT


def test_adapt_on_main_activity_keeps_its_assistance_limit():
    entry = predict(EvidenceStrength.STRONG, AssistanceLevel.SMALL_HINT)

    assert estimate_skill([entry], "CO-1", now=NOW, config=MAIN).level == ProficiencyLevel.APPLY


def test_one_strong_main_activity_entry_reaches_adapt_but_stays_provisional():
    est = estimate_skill([predict(EvidenceStrength.STRONG)], "CO-1", now=NOW, config=MAIN)

    assert est.level == ProficiencyLevel.ADAPT
    assert est.confidence == Confidence.PROVISIONAL


def test_main_activity_does_not_reach_own():
    entries = [predict(EvidenceStrength.STRONG), predict(EvidenceStrength.STRONG)]

    assert estimate_skill(entries, "CO-1", now=NOW, config=MAIN).level == ProficiencyLevel.ADAPT


def test_supplied_reasoning_never_qualifies_through_the_main_activity():
    entry = predict(EvidenceStrength.STRONG, AssistanceLevel.SUPPLIED_REASONING)

    assert estimate_skill([entry], "CO-1", now=NOW, config=MAIN).level is None


def test_main_activity_with_a_cold_check_supports_the_target():
    entries = [predict(days_ago=3), predict(days_ago=2, cold_check=True)]

    decision = decide_skill(ProficiencyLevel.APPLY, entries, "CO-1", now=NOW, config=MAIN)

    assert decision.estimate.confidence == Confidence.SUPPORTED
    assert decision.decision == ProgressionDecision.PROGRESS


# --- 2.3 Level rules -------------------------------------------------------


def test_no_evidence_gives_no_level():
    est = estimate_skill([], "CO-1", now=NOW)
    assert est.level is None
    assert est.confidence is None


def test_moderate_explain_entry_reaches_understand_only():
    est = estimate_skill([make(EvidenceCategory.EXPLAIN_REASON, EvidenceStrength.MODERATE)], "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.UNDERSTAND


def test_perform_entry_reaches_apply():
    est = estimate_skill([make(EvidenceCategory.PERFORM_SOLVE, EvidenceStrength.MODERATE)], "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.APPLY


def test_structural_help_does_not_qualify():
    est = estimate_skill([make(assistance=AssistanceLevel.STRUCTURAL_DIRECTION)], "CO-1", now=NOW)
    assert est.level is None


def test_supplied_reasoning_never_raises_a_level():
    est = estimate_skill(
        [make(strength=EvidenceStrength.STRONG, assistance=AssistanceLevel.SUPPLIED_REASONING)], "CO-1", now=NOW
    )
    assert est.level is None


def test_insufficient_entries_are_ignored():
    est = estimate_skill([make(strength=EvidenceStrength.INSUFFICIENT)], "CO-1", now=NOW)
    assert est.level is None
    assert est.confidence is None


def test_adapt_needs_strong_diagnose_and_a_lower_apply_entry():
    diagnose = make(EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER, EvidenceStrength.STRONG, AssistanceLevel.SYNTAX_LOOKUP)
    assert estimate_skill([diagnose], "CO-1", now=NOW).level == ProficiencyLevel.UNDERSTAND
    est = estimate_skill([make(), diagnose], "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.ADAPT


def test_adapt_rejects_small_hint():
    diagnose = make(EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER, EvidenceStrength.STRONG, AssistanceLevel.SMALL_HINT)
    assert estimate_skill([make(), diagnose], "CO-1", now=NOW).level == ProficiencyLevel.APPLY


def test_own_needs_unassisted_strong_build():
    diagnose = make(EvidenceCategory.DIAGNOSE_JUDGE_TRANSFER)
    build = make(activity=ActivityType.BUILD)
    assert estimate_skill([make(), diagnose, build], "CO-1", now=NOW).level == ProficiencyLevel.OWN
    hinted_build = make(activity=ActivityType.BUILD, assistance=AssistanceLevel.SMALL_HINT)
    assert estimate_skill([make(), diagnose, hinted_build], "CO-1", now=NOW).level == ProficiencyLevel.ADAPT


def test_only_entries_for_the_skill_count():
    est = estimate_skill([make(skill_id="BU-1")], "CO-1", now=NOW)
    assert est.level is None


# --- 2.2 Window and duplicates -----------------------------------------------


def test_entries_older_than_90_days_are_ignored():
    est = estimate_skill([make(days_ago=91)], "CO-1", now=NOW)
    assert est.level is None


def test_only_last_10_entries_count():
    old_good = make(days_ago=5)
    newer = [make(EvidenceCategory.EXPLAIN_REASON, days_ago=4 - i * 0.1) for i in range(10)]
    est = estimate_skill([old_good, *newer], "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.UNDERSTAND


def test_window_size_is_configurable():
    cfg = EstimatorConfig(window_entries=20)
    old_good = make(days_ago=5)
    newer = [make(EvidenceCategory.EXPLAIN_REASON, days_ago=4 - i * 0.1) for i in range(10)]
    assert estimate_skill([old_good, *newer], "CO-1", now=NOW, config=cfg).level == ProficiencyLevel.APPLY


def test_repeating_the_same_exercise_counts_once():
    first = make(exercise_id="ex-same", cold_check=True, days_ago=2)
    repeat = make(exercise_id="ex-same", days_ago=1)
    est = estimate_skill([first, repeat], "CO-1", now=NOW)
    assert est.confidence == Confidence.PROVISIONAL
    assert est.qualifying_entry_ids == [repeat.entry_id]


# --- 2.4 Confidence ----------------------------------------------------------


def test_single_qualifying_entry_is_provisional():
    est = estimate_skill([make()], "CO-1", now=NOW)
    assert est.confidence == Confidence.PROVISIONAL


def test_two_entries_without_cold_check_stay_provisional():
    est = estimate_skill([make(days_ago=2), make()], "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.APPLY
    assert est.confidence == Confidence.PROVISIONAL


def test_two_entries_with_a_passed_cold_check_are_supported():
    est = estimate_skill([make(days_ago=2), make(cold_check=True)], "CO-1", now=NOW)
    assert est.confidence == Confidence.SUPPORTED


def test_one_newer_weak_entry_makes_level_provisional_without_lowering_it():
    entries = [make(days_ago=3), make(cold_check=True, days_ago=2), weak()]
    est = estimate_skill(entries, "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.APPLY
    assert est.confidence == Confidence.PROVISIONAL


def test_two_consecutive_newer_weak_entries_lower_the_level_by_one():
    entries = [make(days_ago=3), make(cold_check=True, days_ago=2), weak(0.6), weak(0.5)]
    est = estimate_skill(entries, "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.UNDERSTAND
    assert est.confidence == Confidence.PROVISIONAL


def test_a_good_entry_between_weak_ones_breaks_the_streak():
    entries = [make(days_ago=3), make(cold_check=True, days_ago=2), weak(0.7), make(days_ago=0.6), weak(0.5)]
    est = estimate_skill(entries, "CO-1", now=NOW)
    assert est.level == ProficiencyLevel.APPLY


# --- 2.5 Decisions -------------------------------------------------------------


def test_undecided_without_evidence():
    d = decide_skill(ProficiencyLevel.APPLY, [], "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.UNDECIDED


def test_progress_when_target_met_and_supported():
    d = decide_skill(ProficiencyLevel.APPLY, [make(days_ago=2), make(cold_check=True)], "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.PROGRESS
    assert len(d.entry_ids) == 2


def test_strengthen_when_target_met_but_provisional():
    d = decide_skill(ProficiencyLevel.APPLY, [make()], "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.STRENGTHEN
    assert "provisional" in d.reason.lower()


def test_strengthen_when_one_level_below_target():
    d = decide_skill(ProficiencyLevel.APPLY, [make(EvidenceCategory.EXPLAIN_REASON)], "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.STRENGTHEN


def test_accelerate_when_above_target_and_supported():
    entries = [make(days_ago=2), make(cold_check=True, days_ago=1.5), make(EvidenceCategory.EXPLAIN_REASON)]
    d = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.ACCELERATE


def test_weak_entries_without_qualifying_evidence_strengthen():
    d = decide_skill(ProficiencyLevel.APPLY, [weak()], "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.STRENGTHEN


def test_rebuild_after_three_weak_entries_and_no_qualifying_entry():
    d = decide_skill(ProficiencyLevel.APPLY, [weak(0.7), weak(0.6), weak(0.5)], "CO-1", now=NOW)
    assert d.decision == ProgressionDecision.REBUILD


def test_rebuild_after_two_consecutive_shaky_concept_checks():
    d = decide_skill(ProficiencyLevel.APPLY, [make()], "CO-1", now=NOW, consecutive_shaky=2)
    assert d.decision == ProgressionDecision.REBUILD


def test_unit_decision_is_the_weakest_skill_decision():
    progress = decide_skill(ProficiencyLevel.APPLY, [make(days_ago=2), make(cold_check=True)], "CO-1", now=NOW)
    undecided = decide_skill(ProficiencyLevel.APPLY, [], "CO-2", now=NOW)
    strengthen = decide_skill(ProficiencyLevel.APPLY, [make(skill_id="CO-6")], "CO-6", now=NOW)
    assert decide_unit([progress, undecided]) == ProgressionDecision.UNDECIDED
    assert decide_unit([progress, undecided, strengthen]) == ProgressionDecision.STRENGTHEN
    assert decide_unit([]) == ProgressionDecision.UNDECIDED
