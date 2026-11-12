"""A repeated concept check counts once, and the next-step wording (ADR-0016 amendment G, SPEC-12 section 6)."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import count
from typing import Optional

from lms.core.cold_check import ColdCheckState, ColdCheckStatus
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
    TargetSkill,
    Unit,
)
from lms.core.proficiency import DEFAULT_CONFIG, consecutive_shaky_checks, decide_skill, estimate_skill
from lms.core.proficiency_view import build_proficiency_view

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
_n = count(1)


def check(
    strength: EvidenceStrength = EvidenceStrength.STRONG,
    unit_id: str = "PY-0.1",
    hours_ago: float = 1,
    exercise_id: Optional[str] = "PY-0.1/explain/v1",
) -> EvidenceEntry:
    """A CO-6 concept check as `POST /explain` records it."""
    return EvidenceEntry(
        learner_id="l",
        unit_id=unit_id,
        skill_id="CO-6",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=strength,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="concept check",
        recorded_at=NOW - timedelta(hours=hours_ago, seconds=next(_n)),
        exercise_id=exercise_id,
    )


def other(skill_id: str = "CO-1", exercise_id: Optional[str] = None, hours_ago: float = 1, **extra) -> EvidenceEntry:
    fields = dict(
        learner_id="l",
        unit_id="PY-0.1",
        skill_id=skill_id,
        evidence_category=EvidenceCategory.PERFORM_SOLVE,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="task",
        recorded_at=NOW - timedelta(hours=hours_ago, seconds=next(_n)),
        exercise_id=exercise_id,
    )
    fields.update(extra)
    return EvidenceEntry(**fields)


# --- Item 1: a repeated concept check counts once ---


def test_the_same_concept_check_twice_counts_once():
    est = estimate_skill([check(hours_ago=3), check(hours_ago=1)], "CO-6", now=NOW)

    assert len(est.qualifying_entry_ids) == 1


def test_old_rows_without_an_id_count_once_per_unit():
    est = estimate_skill([check(hours_ago=3, exercise_id=None), check(hours_ago=1, exercise_id=None)], "CO-6", now=NOW)

    assert len(est.qualifying_entry_ids) == 1


def test_an_old_row_and_a_new_row_of_one_unit_are_the_same_check():
    est = estimate_skill([check(hours_ago=3, exercise_id=None), check(hours_ago=1)], "CO-6", now=NOW)

    assert len(est.qualifying_entry_ids) == 1


def test_concept_checks_of_different_units_count_separately():
    entries = [
        check(unit_id="PY-0.1", exercise_id=None, hours_ago=3),
        check(unit_id="PY-0.2", exercise_id="PY-0.2/explain/v1", hours_ago=1),
    ]

    assert len(estimate_skill(entries, "CO-6", now=NOW).qualifying_entry_ids) == 2


def test_the_newest_answer_to_a_repeated_check_is_the_one_kept():
    solid_then_shaky = [check(hours_ago=3), check(EvidenceStrength.WEAK, hours_ago=1)]
    shaky_then_solid = [check(EvidenceStrength.WEAK, hours_ago=3), check(hours_ago=1)]

    assert estimate_skill(solid_then_shaky, "CO-6", now=NOW).level is None
    assert estimate_skill(shaky_then_solid, "CO-6", now=NOW).level == ProficiencyLevel.UNDERSTAND


def test_a_repeated_check_cannot_be_the_second_piece_of_support():
    entries = [check(hours_ago=3), check(hours_ago=1)]
    decision = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-6", now=NOW)

    assert "1 more exercise" in decision.reason


def test_a_shaky_run_still_counts_every_attempt_for_rebuild():
    entries = [check(EvidenceStrength.WEAK, hours_ago=2), check(EvidenceStrength.WEAK, hours_ago=1)]

    assert consecutive_shaky_checks(entries, "PY-0.1") == 2


def test_other_entries_without_an_id_are_not_merged():
    est = estimate_skill([other(hours_ago=3), other(hours_ago=1)], "CO-1", now=NOW)

    assert len(est.qualifying_entry_ids) == 2


# --- Item 2: next-step wording ---


def test_one_short_and_no_cold_check_is_one_task():
    reason = decide_skill(ProficiencyLevel.UNDERSTAND, [other()], "CO-1", now=NOW).reason

    assert reason == (
        "Understand is provisional: it needs 1 more exercise at Understand, and it must be a passed Cold Check."
    )


def test_two_short_and_no_cold_check_names_one_as_the_cold_check():
    config = replace(DEFAULT_CONFIG, supported_min_entries=3)
    reason = decide_skill(ProficiencyLevel.UNDERSTAND, [other()], "CO-1", now=NOW, config=config).reason

    assert reason == (
        "Understand is provisional: it needs 2 more exercises at Understand; one must be a passed Cold Check."
    )


def test_enough_exercises_but_no_cold_check_names_only_the_cold_check():
    entries = [other(exercise_id="a", hours_ago=2), other(exercise_id="b", hours_ago=1)]
    reason = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-1", now=NOW).reason

    assert reason == "Understand is provisional: it needs a passed Cold Check."


def test_a_passed_cold_check_alone_needs_one_more_exercise():
    reason = decide_skill(ProficiencyLevel.UNDERSTAND, [other(cold_check=True)], "CO-1", now=NOW).reason

    assert reason == "Understand is provisional: it needs 1 more exercise at Understand."


def test_a_weak_streak_is_added_after_the_cold_check_wording():
    entries = [
        other(exercise_id="a", hours_ago=3),
        other(exercise_id="b", hours_ago=1, evidence_strength=EvidenceStrength.WEAK),
    ]
    reason = decide_skill(ProficiencyLevel.UNDERSTAND, entries, "CO-1", now=NOW).reason

    assert reason == (
        "Understand is provisional: it needs 1 more exercise at Understand, and it must be a passed Cold Check, "
        "and a strong attempt after your last weak one."
    )


def unit(methods=(ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.TRACE)) -> Unit:
    return Unit(
        unit_id="PY-0.1",
        title="PY-0.1",
        stage=0,
        concept_line="Concept",
        target_skills=[TargetSkill(skill_id="CO-1", skill_name="CO-1", goal_level=ProficiencyLevel.UNDERSTAND)],
        methods=list(methods),
    )


def next_message(entries, state=ColdCheckState.NOT_READY, resets=None):
    view = build_proficiency_view(
        [unit()], entries, lambda _: ColdCheckStatus(state=state), now=NOW, resets=resets or {}
    )
    return view.next_action.message


def test_a_closed_cold_check_says_how_many_activities_open_it():
    message = next_message([other(activity=ActivityType.PREDICT)])

    assert message.endswith(" Do this unit's 2 remaining activities to open its Cold Check.")


def test_one_remaining_activity_is_singular():
    entries = [other(activity=ActivityType.PREDICT, exercise_id="a"), check()]

    assert next_message(entries).endswith(" Do this unit's 1 remaining activity to open its Cold Check.")


def test_after_a_reset_every_activity_counts_as_remaining():
    entries = [other(activity=ActivityType.PREDICT, exercise_id="a", hours_ago=5), check(hours_ago=5)]
    reset = {"PY-0.1": NOW - timedelta(hours=2)}
    # After the reset the unit has no evidence, so it is Undecided and asks for no Cold Check yet.
    assert "open its Cold Check" not in next_message(entries, resets=reset)
    # New evidence after the reset: two activities still to redo.
    entries.append(other(activity=ActivityType.PREDICT, exercise_id="b", hours_ago=1))
    assert next_message(entries, resets=reset).endswith(
        " Do this unit's 2 remaining activities to open its Cold Check."
    )


def test_an_open_cold_check_adds_nothing():
    message = next_message([other(activity=ActivityType.PREDICT)], state=ColdCheckState.AVAILABLE)

    assert "open its Cold Check" not in message
