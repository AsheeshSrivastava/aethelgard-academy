"""Curriculum guards from Learning Method v2 Amendment A1: entry, one rung, volume, awareness (SPEC-02, SPEC-13)."""

from lms.adapters.curriculum.loader import parse_topics, parse_unit_block
from lms.core.curriculum_checks import Severity, check_curriculum
from lms.core.exercises import parse_seed
from lms.core.models import ActivityType, MakeStep, ProficiencyLevel, TargetSkill, Unit, UnitTopic

U, A, D, OWN = ProficiencyLevel.UNDERSTAND, ProficiencyLevel.APPLY, ProficiencyLevel.ADAPT, ProficiencyLevel.OWN


def unit(unit_id="PY-1.2", targets=None, stage=1, topics=(), make=None) -> Unit:
    targets = targets or {"CO-1": U}
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=stage,
        concept_line="Concept",
        target_skills=[TargetSkill(skill_id=s, skill_name=s, goal_level=g) for s, g in targets.items()],
        methods=[ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.BUILD],
        topics=list(topics),
        make=make,
    )


def seed(n=1, unit_id="PY-1.2", topic="integers", cold=False, approved=True, make=False):
    if make:
        raw = {
            "activity": "Build",
            "skill_id": "CO-1",
            "playground": {
                "starter": ["# blank"],
                "reference_solution": ["print(1)"],
                "hidden_checks": ["def test_x():", "    pass"],
                "wrong_solution": ["print(2)"],
                "make": True,
            },
        }
    else:
        raw = {
            "activity": "Predict",
            "skill_id": "CO-1",
            "predict": {
                "code": ["print(1)"],
                "stdin": "",
                "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
                "answer_key": "A",
                "why": ["It prints 1."],
            },
        }
    raw.update(
        schema_version=2,
        seed_id=f"{unit_id}/item-{n}",
        unit_id=unit_id,
        level="Understand",
        prompt_markdown=["What prints?"],
        cold_check_eligible=cold,
        curator_approved=approved,
    )
    if topic is not None:
        raw["topic"] = topic
    return parse_seed(raw, f"item-{n}", unit_id)


def codes(findings, *wanted):
    return [f.code for f in findings if f.code in wanted]


# --- A1.1 entry rule and A1.2 one-rung rule, over the whole path ---


def test_a_skill_entering_at_adapt_is_an_error():
    findings = check_curriculum([unit("PY-1.2", {"CO-1": D})])

    entry = [f for f in findings if f.code == "skill-enters-above-apply"]
    assert len(entry) == 1 and entry[0].severity == Severity.ERROR
    assert entry[0].skill_id == "CO-1" and entry[0].unit_id == "PY-1.2"


def test_a_skill_entering_at_apply_is_fine():
    assert codes(check_curriculum([unit("PY-1.2", {"CO-1": A})]), "skill-enters-above-apply") == []


def test_a_jump_of_two_rungs_is_an_error_and_names_both_units():
    findings = check_curriculum([unit("PY-1.2", {"CO-1": U}), unit("PY-1.7", {"CO-1": D})])

    jump = [f for f in findings if f.code == "skill-skips-a-rung"]
    assert len(jump) == 1 and jump[0].severity == Severity.ERROR
    assert jump[0].unit_id == "PY-1.7" and "PY-1.2" in jump[0].message


def test_one_rung_at_a_time_and_going_down_are_fine():
    path = [
        unit("PY-1.2", {"CO-1": U}),
        unit("PY-1.7", {"CO-1": A}),
        unit("PY-1.8", {"CO-1": U}),
        unit("PY-2.1", {"CO-1": A}),
        unit("PY-2.2", {"CO-1": D}),
        unit("PY-2.3", {"CO-1": OWN}),
    ]

    assert codes(check_curriculum(path), "skill-enters-above-apply", "skill-skips-a-rung") == []


def test_the_rung_is_measured_from_the_last_unit_that_targets_the_skill():
    path = [unit("PY-1.2", {"CO-1": U}), unit("PY-1.7", {"BU-1": U}), unit("PY-1.8", {"CO-1": A})]

    assert codes(check_curriculum(path), "skill-skips-a-rung") == []


KNOWN_JUMPS = {
    ("PY-11.4", "DE-6"), ("PY-12.1", "CO-5"), ("PY-12.4", "BU-1"), ("PY-12.4", "VE-1"), ("PY-13.3", "VE-4"),
    ("NET-0.2", "CO-6"), ("BE-15.1", "DE-6"), ("BE-17.2", "BU-3"), ("AI-17.4", "DE-5"),
}


def test_the_nine_known_jumps_in_the_roadmaps_stay_flagged():
    """Owner, 2026-11-04 (work sequence 1.4, option C): left as they are, but always reported."""
    from pathlib import Path

    from lms.adapters.curriculum.loader import load_all_roadmaps

    findings = load_all_roadmaps(Path("reference")).findings
    jumps = {(f.unit_id, f.skill_id) for f in findings if f.code == "skill-skips-a-rung"}

    assert jumps == KNOWN_JUMPS
    assert all(f.severity == Severity.ERROR for f in findings if f.code == "skill-skips-a-rung")


# --- A1.6 practice volume ---


def test_a_stage_0_to_5_unit_with_few_items_gets_a_warning():
    findings = check_curriculum([unit()], seeds={"PY-1.2": [seed(n) for n in range(7)]})

    low = [f for f in findings if f.code == "practice-volume-low"]
    assert len(low) == 1 and low[0].severity == Severity.WARNING
    assert "7" in low[0].message and "15" in low[0].message


def test_fifteen_approved_items_are_enough():
    findings = check_curriculum([unit()], seeds={"PY-1.2": [seed(n) for n in range(15)]})

    assert codes(findings, "practice-volume-low") == []


def test_unapproved_items_do_not_count():
    seeds = [seed(n) for n in range(14)] + [seed(99, approved=False)]

    assert codes(check_curriculum([unit()], seeds={"PY-1.2": seeds}), "practice-volume-low") == ["practice-volume-low"]


def test_later_stages_need_eight():
    later = unit("PY-6.1", stage=6)

    assert codes(check_curriculum([later], seeds={"PY-6.1": [seed(n, "PY-6.1") for n in range(8)]}), "practice-volume-low") == []
    assert codes(check_curriculum([later], seeds={"PY-6.1": [seed(n, "PY-6.1") for n in range(7)]}), "practice-volume-low") == [
        "practice-volume-low"
    ]


def test_a_unit_with_no_content_yet_gets_no_volume_warning():
    assert codes(check_curriculum([unit()], seeds={}), "practice-volume-low", "make-volume-low") == []


def test_a_make_unit_needs_three_make_items():
    make_unit = unit(make=MakeStep(skill_id="CO-1", task="a calculator"))
    seeds = [seed(n) for n in range(14)] + [seed(90, make=True)]

    findings = check_curriculum([make_unit], seeds={"PY-1.2": seeds})

    assert codes(findings, "make-volume-low") == ["make-volume-low"]
    assert codes(findings, "practice-volume-low") == []


# --- A1.4 awareness topics ---


def test_topics_are_read_with_their_awareness_mark():
    topics = parse_topics("integers; `None`; `math` module basics (new); `decimal` for exact values such as money (awareness, new); locks (awareness)")

    assert topics == [
        UnitTopic(name="integers"),
        UnitTopic(name="`None`"),
        UnitTopic(name="`math` module basics"),
        UnitTopic(name="`decimal` for exact values such as money", awareness=True),
        UnitTopic(name="locks", awareness=True),
    ]


def test_a_topic_named_as_awareness_counts_as_one():
    assert parse_topics("persistence awareness; awareness of users") == [
        UnitTopic(name="persistence awareness", awareness=True),
        UnitTopic(name="awareness of users"),
    ]


def test_a_unit_block_carries_its_topics():
    block = "#### PY-1.2 Numbers\n- **Target skills:** CO-1 to Apply\n- **Topics:** integers; locks (awareness)\n"

    assert [t.name for t in parse_unit_block(block, 1).topics] == ["integers", "locks"]


def test_a_cold_check_item_on_an_awareness_topic_is_an_error():
    topics = [UnitTopic(name="integers"), UnitTopic(name="locks", awareness=True)]

    findings = check_curriculum([unit(topics=topics)], seeds={"PY-1.2": [seed(topic="locks", cold=True)]})

    hit = [f for f in findings if f.code == "cold-check-awareness-topic"]
    assert len(hit) == 1 and hit[0].severity == Severity.ERROR and "locks" in hit[0].message


def test_a_practice_item_on_an_awareness_topic_is_a_warning():
    topics = [UnitTopic(name="locks", awareness=True)]

    findings = check_curriculum([unit(topics=topics)], seeds={"PY-1.2": [seed(topic="locks")]})

    assert [(f.code, f.severity) for f in findings if f.code == "exercise-awareness-topic"] == [
        ("exercise-awareness-topic", Severity.WARNING)
    ]


def test_topics_match_whatever_the_case():
    topics = [UnitTopic(name="Locks", awareness=True)]

    findings = check_curriculum([unit(topics=topics)], seeds={"PY-1.2": [seed(topic="locks", cold=True)]})

    assert codes(findings, "cold-check-awareness-topic") == ["cold-check-awareness-topic"]


def test_a_seed_must_name_a_topic_of_its_unit():
    topics = [UnitTopic(name="integers")]
    seeds = [seed(1, topic=None), seed(2, topic="floats"), seed(3, topic="integers")]

    findings = check_curriculum([unit(topics=topics)], seeds={"PY-1.2": seeds})

    assert codes(findings, "seed-topic-missing", "seed-topic-unknown") == ["seed-topic-missing", "seed-topic-unknown"]
    assert all(f.severity == Severity.ERROR for f in findings if f.code in ("seed-topic-missing", "seed-topic-unknown"))
