"""Tests for loading and validating SPEC-13 exercise seeds."""

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from conftest import real_content
from lms.adapters.curriculum.loader import load_all_roadmaps, load_seeds
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.core.curriculum_checks import Severity, check_curriculum
from lms.core.exercises import (
    public_and_private,
    SeedError,
    choose_next,
    fill_slots,
    parse_seed,
    pool_for,
    seed_variants,
    to_exercise,
)
from lms.core.models import ActivityType, ProficiencyLevel, TargetSkill, Unit


def raw_seed(**overrides) -> dict:
    fields = dict(
        schema_version=2,
        seed_id="PY-1.1/predict-1",
        unit_id="PY-1.1",
        activity="Predict",
        skill_id="CO-1",
        level="Understand",
        prompt_markdown=["What prints?"],
        cold_check_eligible=False,
        curator_approved=True,
        predict={
            "code": ["print(1)"],
            "stdin": "",
            "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
            "answer_key": "A",
            "why": ["It prints 1."],
        },
    )
    fields.update(overrides)
    return fields


def parse(**overrides):
    return parse_seed(raw_seed(**overrides), file_stem="predict-1", unit_id="PY-1.1")


def unit(targets=None, methods=None, unit_id="PY-1.1") -> Unit:
    targets = targets or {"CO-1": ProficiencyLevel.UNDERSTAND}
    return Unit(
        unit_id=unit_id,
        title=unit_id,
        stage=1,
        concept_line="Concept",
        target_skills=[TargetSkill(skill_id=s, skill_name=s, goal_level=g) for s, g in targets.items()],
        methods=methods or [ActivityType.EXPLAIN, ActivityType.PREDICT],
    )


def codes(findings):
    return [f.code for f in findings]


MAIN = {"CO-1": ActivityType.PREDICT, "CO-6": ActivityType.EXPLAIN}


# --- Parsing ---


def test_valid_seed_parses():
    seed = parse()

    assert seed.activity == ActivityType.PREDICT
    assert seed.item_type == "predict"
    assert seed.body["answer_key"] == "A"


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"schema_version": 1}, "schema_version"),
        ({"seed_id": "PY-1.1/other"}, "seed_id"),
        ({"unit_id": "PY-1.2"}, "unit_id"),
        ({"activity": "Dance"}, "activity"),
        ({"level": "Expert"}, "level"),
        ({"prompt_markdown": "text"}, "prompt_markdown"),
    ],
)
def test_bad_fields_give_a_clear_error(overrides, message):
    with pytest.raises(SeedError, match=message):
        parse(**overrides)


def test_seed_needs_exactly_one_body_block():
    with pytest.raises(SeedError, match="body block"):
        parse(trace={"code": [], "input": "", "expected_output": []})

    raw = raw_seed()
    del raw["predict"]
    with pytest.raises(SeedError, match="body block"):
        parse_seed(raw, file_stem="predict-1", unit_id="PY-1.1")


def test_body_block_must_suit_the_activity():
    with pytest.raises(SeedError, match="not allowed"):
        parse(activity="Trace")


def test_body_block_needs_its_required_fields():
    body = raw_seed()["predict"]
    del body["answer_key"]

    with pytest.raises(SeedError, match="answer_key"):
        parse(predict=body)


def test_answer_key_must_match_an_option():
    body = raw_seed()["predict"] | {"answer_key": "Z"}

    with pytest.raises(SeedError, match="answer_key"):
        parse(predict=body)


def test_plan_order_constraints_must_use_needed_steps():
    plan = {
        "steps": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}],
        "needed": ["a"],
        "order_constraints": [["a", "b"]],
    }

    with pytest.raises(SeedError, match="order_constraints"):
        parse(activity="Decompose", predict=None, decompose_plan=plan)


def test_undefined_slot_is_an_error():
    body = raw_seed()["predict"] | {"stdin": "{{person}}"}

    with pytest.raises(SeedError, match="person"):
        parse(predict=body)


def test_unused_slot_is_an_error():
    template = {"slots": {"person": {"kind": "name", "values": ["A"]}}}

    with pytest.raises(SeedError, match="person"):
        parse(template=template)


# --- Loading files ---


def answers(root: Path) -> Path:
    return root.parent / f"{root.name}-answers"


def write_seed(root: Path, unit_folder: str, name: str, raw: dict) -> None:
    """Write the public file and, beside it, the private half (ADR-0021 amendment)."""
    public, private = public_and_private(raw)
    for base, data in ((root, public), (answers(root), private)):
        folder = base / "python" / unit_folder / "exercises"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def test_load_seeds_groups_them_by_unit(tmp_path):
    write_seed(tmp_path, "py-1.1", "predict-1", raw_seed())

    seeds, problems = load_seeds(tmp_path, answers(tmp_path))

    assert [s.seed_id for s in seeds["PY-1.1"]] == ["PY-1.1/predict-1"]
    assert problems == []


def test_bad_seed_is_reported_and_skipped(tmp_path):
    write_seed(tmp_path, "py-1.1", "predict-1", raw_seed())
    write_seed(tmp_path, "py-1.1", "predict-2", raw_seed())
    folder = tmp_path / "python" / "py-1.1" / "exercises"
    (folder / "predict-3.json").write_text("{not json", encoding="utf-8")

    seeds, problems = load_seeds(tmp_path, answers(tmp_path))

    assert [s.seed_id for s in seeds["PY-1.1"]] == ["PY-1.1/predict-1"]
    assert [p.code for p in problems] == ["seed-invalid", "seed-invalid"]
    assert problems[0].severity == Severity.ERROR
    assert "predict-2" in problems[0].message
    assert "predict-3" in problems[1].message


def test_all_stage_0_seeds_load_cleanly():
    with real_content():
        catalog = load_all_roadmaps(Path("reference"))

    assert {u: len(s) for u, s in catalog.seeds.items()} == {"PY-0.1": 9, "PY-0.2": 8, "PY-0.3": 9, "PY-0.4": 10, "PY-1.2": 1, "TW-0.1": 14, "TW-0.2": 16}
    assert [f for f in catalog.findings if f.code.startswith("seed-")] == []


# --- Rule 11 and unit rules ---


def test_target_skill_without_a_cold_check_seed_is_a_warning():
    found = check_curriculum([unit()], main_activities=MAIN, seeds={})

    missing = [f for f in found if f.code == "cold-check-seed-missing"]
    assert len(missing) == 1
    assert missing[0].severity == Severity.WARNING
    assert missing[0].skill_id == "CO-1"


def test_approved_cold_check_seed_satisfies_the_skill():
    seeds = {"PY-1.1": [parse(cold_check_eligible=True)]}

    assert "cold-check-seed-missing" not in codes(check_curriculum([unit()], main_activities=MAIN, seeds=seeds))


def test_unapproved_cold_check_seed_does_not_count():
    seeds = {"PY-1.1": [parse(cold_check_eligible=True, curator_approved=False)]}

    assert "cold-check-seed-missing" in codes(check_curriculum([unit()], main_activities=MAIN, seeds=seeds))


def test_cold_check_seed_must_use_the_skills_main_activity():
    seeds = {"PY-1.1": [parse(cold_check_eligible=True, skill_id="CO-6")]}
    target = unit({"CO-6": ProficiencyLevel.UNDERSTAND})

    found = codes(check_curriculum([target], main_activities=MAIN, seeds=seeds))

    assert "seed-not-main-activity" in found
    assert "cold-check-seed-missing" in found


def test_seed_must_fit_its_unit():
    seeds = {"PY-1.1": [parse(skill_id="VE-1")]}

    assert "seed-wrong-skill" in codes(check_curriculum([unit()], seeds=seeds))

    seeds = {"PY-1.1": [parse(level="Apply")]}
    assert "seed-wrong-level" in codes(check_curriculum([unit()], seeds=seeds))

    seeds = {"PY-1.1": [parse()]}
    other = unit(methods=[ActivityType.EXPLAIN, ActivityType.TRACE])
    assert "seed-wrong-activity" in codes(check_curriculum([other], seeds=seeds))


def test_real_stage_0_skills_all_have_a_cold_check_seed():
    with real_content():
        catalog = load_all_roadmaps(Path("reference"))
    stage_0 = {"PY-0.4", "PY-0.1", "PY-0.3"}

    # Volume is known to be short until Stage 0 is topped up (work sequence 4.3).
    assert [f for f in catalog.findings if f.unit_id in stage_0 and f.code != "practice-volume-low"] == []


# --- Variants ---


TEMPLATE = {"slots": {"person": {"kind": "name", "values": ["Amara", "Kofi"]}}}


def templated():
    body = raw_seed()["predict"] | {"stdin": "{{person}}"}
    return parse(predict=body, template=TEMPLATE)


def test_seed_without_slots_has_one_variant():
    assert [n for n, _ in seed_variants(parse())] == [1]


def test_each_slot_value_is_a_variant():
    variants = seed_variants(templated())

    assert [n for n, _ in variants] == [1, 2]
    assert [v.body["stdin"] for _, v in variants] == ["Amara", "Kofi"]


def test_fill_slots_reaches_nested_text():
    assert fill_slots({"a": ["{{x}} b"], "c": {"d": "{{x}}"}}, {"x": "y"}) == {"a": ["y b"], "c": {"d": "y"}}


def test_normal_pool_leaves_out_cold_check_seeds():
    normal = parse()
    cold = parse_seed(
        raw_seed(seed_id="PY-1.1/cold-predict-1", cold_check_eligible=True),
        file_stem="cold-predict-1",
        unit_id="PY-1.1",
    )

    assert pool_for([normal, cold], "predict") == ["PY-1.1/predict-1/v1"]
    assert pool_for([normal, cold], "cold_check") == ["PY-1.1/cold-predict-1/v1"]


def test_cold_check_pool_needs_approval():
    cold = parse(cold_check_eligible=True, curator_approved=False)

    assert pool_for([cold], "cold_check") == []


def test_choose_next_prefers_the_first_unseen():
    assert choose_next(["a", "b", "c"], seen=["a"], current="a") == "b"


def test_choose_next_reuses_the_oldest_seen_when_exhausted():
    assert choose_next(["a", "b", "c"], seen=["b", "a", "c"], current="c") == "b"


def test_choose_next_never_repeats_the_current_when_it_has_a_choice():
    assert choose_next(["a", "b"], seen=["a", "b"], current="a") == "b"


def test_choose_next_with_one_item_stays_on_it():
    assert choose_next(["a"], seen=["a"], current="a") == "a"


# --- Every real seed against real Python (SPEC-13 section 8, rule 5) ---


def run_python(code, stdin):
    return subprocess.run(
        [sys.executable, "-c", "\n".join(code)], input=stdin, capture_output=True, text=True, timeout=30
    )


def all_variants():
    with real_content():
        catalog = load_all_roadmaps(Path("reference"))
    return [
        (variant.seed_id, n, variant)
        for seeds in catalog.seeds.values()
        for seed in seeds
        for n, variant in seed_variants(seed)
    ]


VARIANTS = all_variants()


def passes(code, checks):
    return SubprocessRunner().execute("\n".join(code), test_code="\n".join(checks)).success


@pytest.mark.parametrize("seed_id, n, seed", [v for v in VARIANTS if v[2].item_type == "predict"])
def test_predict_key_matches_real_output(seed_id, n, seed):
    output = run_python(seed.body["code"], seed.body["stdin"] + "\n").stdout.rstrip("\n")

    assert [o["key"] for o in seed.body["options"] if o["text"] == output] == [seed.body["answer_key"]]


@pytest.mark.parametrize("seed_id, n, seed", [v for v in VARIANTS if v[2].item_type == "trace"])
def test_trace_output_matches_real_output(seed_id, n, seed):
    output = run_python(seed.body["code"], seed.body["input"]).stdout

    assert output.splitlines() == seed.body["expected_output"]


@pytest.mark.parametrize("seed_id, n, seed", [v for v in VARIANTS if v[2].item_type == "debug"])
def test_debug_seed_separates_right_from_wrong(seed_id, n, seed):
    checks = seed.body["hidden_checks"]

    assert passes(seed.body["reference_solution"], checks)
    assert not passes(seed.body["broken_code"], checks)
    assert not passes(seed.body["wrong_solution"], checks)


@pytest.mark.parametrize("seed_id, n, seed", [v for v in VARIANTS if v[2].item_type == "debug_locate"])
def test_debug_locate_key_matches_the_real_error(seed_id, n, seed):
    result = run_python(seed.body["broken_code"], seed.body["stdin"] + "\n")
    line = int(re.findall(r'File "<string>", line (\d+)', result.stderr)[-1])
    kind = result.stderr.strip().splitlines()[-1].split(":")[0]
    key = seed.body["answer_key"]
    label = next(o["text"] for o in seed.body["error_types"] if o["key"] == key["error_type"])

    assert result.returncode != 0
    assert line == key["line"]
    assert label.startswith(kind + ":")


def test_real_exercises_build():
    for _, n, seed in VARIANTS:
        assert to_exercise(seed, n).exercise_id == f"{seed.seed_id}/v{n}"
