import pytest
from datetime import datetime
from lms.core.models import (
    ProficiencyLevel,
    EvidenceCategory,
    EvidenceStrength,
    AssistanceLevel,
    ProgressionDecision,
    ActivityType,
    TargetSkill,
    ConceptCheck,
    DataContext,
    ConceptWikiLink,
    MediaAsset,
    Unit,
    EvidenceEntry,
)

def test_target_skill_validation():
    skill = TargetSkill(
        skill_id="CO-1",
        skill_name="Predict before running",
        goal_level=ProficiencyLevel.UNDERSTAND,
    )
    assert skill.skill_id == "CO-1"
    assert skill.goal_level == ProficiencyLevel.UNDERSTAND

def test_unit_creation_with_prerequisites_and_carry_forward():
    context = DataContext(
        description="User registration dictionary state",
        state_payload={"name": "Alice", "age": 28, "city": "Ranchi"},
        source_unit_id="PY-1.1",
    )
    unit = Unit(
        unit_id="PY-1.2",
        title="Numbers, booleans and None",
        stage=1,
        concept_line="Values have types that dictate valid operations",
        target_skills=[
            TargetSkill(
                skill_id="CO-1",
                skill_name="Predict before running",
                goal_level=ProficiencyLevel.APPLY,
            )
        ],
        methods=[ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.DEBUG_VALIDATE],
        prerequisites=["PY-1.1"],
        carry_forward=context,
        wiki_links=[
            ConceptWikiLink(concept_name="Type Casting", wiki_slug="concepts/python/type-casting")
        ],
    )
    assert unit.unit_id == "PY-1.2"
    assert unit.prerequisites == ["PY-1.1"]
    assert unit.carry_forward is not None
    assert unit.carry_forward.state_payload["name"] == "Alice"
    assert len(unit.methods) == 3

def test_concept_check_soft_gate():
    # Soft gate allows "Shaky" without blocking
    check = ConceptCheck(
        concept_line="Variables bind names to values in memory",
        status="Shaky",
        learner_explanation="Variables are like boxes where code puts text",
        example="name = 'Alice'",
        non_example="print('Alice')",
        ai_feedback="Good start, but remember Python variables are labels pointing to objects, not fixed boxes.",
    )
    assert check.status == "Shaky"
    assert check.learner_explanation is not None

def test_evidence_entry_schema():
    entry = EvidenceEntry(
        learner_id="learner_001",
        unit_id="PY-1.2",
        skill_id="CO-1",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="PY-1.2 Predict activity: predicted output without running",
        observed_reasoning="Learner predicted TypeError on '25' + 5 correctly",
    )
    assert entry.learner_id == "learner_001"
    assert entry.evidence_strength == EvidenceStrength.STRONG
    assert entry.assistance_level == AssistanceLevel.NONE
    assert isinstance(entry.recorded_at, datetime)


def test_unit_media_assets_and_extensibility():
    video = MediaAsset(
        media_id="vid-py-1.2-01",
        kind="video",
        title="Walkthrough: Values, Types and Mutability",
        url="https://cdn.example.org/videos/py-1.2.mp4",
        duration_seconds=345,
        timestamps=[
            {"time": "00:30", "topic": "Integers and Floats"},
            {"time": "02:15", "topic": "Boolean Truthiness"},
        ],
    )
    unit = Unit(
        unit_id="PY-1.2",
        title="Numbers, booleans and None",
        stage=1,
        concept_line="Values have types that dictate valid operations",
        target_skills=[
            TargetSkill(skill_id="CO-1", skill_name="Predict", goal_level=ProficiencyLevel.APPLY)
        ],
        methods=[ActivityType.EXPLAIN],
        media=[video],
    )
    assert len(unit.media) == 1
    assert unit.media[0].media_id == "vid-py-1.2-01"
    assert unit.media[0].duration_seconds == 345
    assert unit.media[0].timestamps[1]["topic"] == "Boolean Truthiness"

