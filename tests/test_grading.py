"""Tests for the deterministic grader (SPEC-13 section 4), using SPEC-13's own examples."""

import json
from pathlib import Path
import re

import pytest

from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.core.exercises import parse_seed
from lms.core.grading import Attempt, grade, spec_test_gate, structure_failures
from lms.core.models import EvidenceStrength
from lms.core.grading import evidence_strength
from lms.core.models import AssistanceLevel

RUNNER = SubprocessRunner()


def spec_seeds():
    text = Path("docs/specs/13-exercise-seed-format-spec.md").read_text(encoding="utf-8")
    worked = text.split("## 10. Worked example")[1].split("## 12. Acceptance")[0]
    raw_seeds = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", worked, re.S)]
    return {
        r["seed_id"]: parse_seed(r, r["seed_id"].split("/")[1], r["unit_id"]) for r in raw_seeds
    }


SEEDS = spec_seeds()


def attempt(seed, **fields):
    return Attempt(exercise_id=f"{seed.seed_id}/v1", activity=seed.activity.slug, **fields)


def run(seed_id, **fields):
    seed = SEEDS[seed_id]
    return grade(seed, attempt(seed, **fields), RUNNER)


def code(lines):
    return {"solution.py": "\n".join(lines)}


# --- Fixed answers ---


@pytest.mark.parametrize(
    "seed_id, right, wrong",
    [
        ("PY-0.1/predict-1", "A", "B"),
        ("PY-0.1/cold-explain-1", "C", "A"),
        ("PY-1.1/cold-explain-1", "B", "A"),
    ],
)
def test_choice_items(seed_id, right, wrong):
    assert run(seed_id, choice=right).passed is True
    assert run(seed_id, choice=wrong).passed is False


def test_reveal_has_the_answer_and_why():
    result = run("PY-0.1/predict-1", choice="B")

    assert result.reveal.correct == "A"
    assert result.reveal.why


def test_missing_answer_fails_cleanly():
    assert run("PY-0.1/predict-1").passed is False


def test_trace_compares_trimmed_lines():
    assert run("PY-0.1/trace-1", trace_answers=[" waiting ", "checked in"]).passed is True
    assert run("PY-0.1/trace-1", trace_answers=["waiting", "waiting"]).passed is False
    assert run("PY-0.1/trace-1", trace_answers=["waiting"]).passed is False


def test_debug_locate_needs_both_line_and_type():
    seed_id = "PY-0.4/cold-debug-validate-1"

    assert run(seed_id, locate={"line": 3, "error_type": "name"}).passed is True
    assert run(seed_id, locate={"line": 2, "error_type": "name"}).passed is False
    assert run(seed_id, locate={"line": 3, "error_type": "type"}).passed is False


def test_contract_needs_every_field_exact():
    seed_id = "PY-3.4/cold-specify-1"
    right = {"input_type": "str", "output_type": "int_none", "edge_cases": ["spaces", "empty", "letters"]}

    assert run(seed_id, fields=right).passed is True

    missed = run(seed_id, fields=right | {"edge_cases": ["empty", "letters"]})
    assert missed.passed is False
    assert (missed.score.passed, missed.score.total) == (2, 3)

    extra = run(seed_id, fields=right | {"edge_cases": ["empty", "letters", "spaces", "timeout"]})
    assert extra.passed is False


def test_plan_accepts_any_valid_order():
    seed_id = "PY-3.5/cold-decompose-1"

    assert run(seed_id, plan=["read", "validate", "format", "count", "print"]).passed is True
    assert run(seed_id, plan=["read", "validate", "count", "format", "print"]).passed is True


def test_plan_refuses_a_wrong_order_or_set():
    seed_id = "PY-3.5/cold-decompose-1"

    assert run(seed_id, plan=["validate", "read", "format", "count", "print"]).passed is False
    assert run(seed_id, plan=["read", "validate", "format", "count", "print", "email"]).passed is False
    assert run(seed_id, plan=["read", "validate", "format", "print"]).passed is False


# --- specify_by_tests ---


HEADER = ["from solution import desk_for", "", ""]


def spec_file(*lines):
    return "\n".join(HEADER + ["def test_x():"] + [f"    {line}" for line in lines])


def specify(tests):
    return run("PY-2.1/cold-specify-1", tests=tests)


def test_complete_spec_kills_every_mutant():
    seed = SEEDS["PY-2.1/cold-specify-1"]
    result = specify("\n".join(seed.body["sample_tests"]))

    assert result.passed is True
    assert (result.score.passed, result.score.total) == (4, 4)


def test_partial_spec_gets_a_partial_score():
    result = specify(spec_file("assert desk_for(18) == 'main'", "assert desk_for(65) == 'senior'"))

    assert result.passed is False
    assert (result.score.passed, result.score.total) == (2, 4)


def test_spec_that_contradicts_the_reference_gets_no_score():
    result = specify(spec_file("assert desk_for(18) == 'youth'"))

    assert result.passed is False
    assert result.score is None
    assert "correct" in result.feedback


def test_feedback_never_names_a_surviving_mutant():
    result = specify(spec_file("assert desk_for(18) == 'main'"))

    assert "m1" not in result.feedback and "m2" not in result.feedback
    assert result.reveal is None or "m2" not in str(result.reveal)


@pytest.mark.parametrize(
    "source",
    [
        "\n".join(HEADER + ["def test_x():", "    assert 'x' not in open('solution.py').read()"]),
        "import os\n" + spec_file("assert desk_for(1)"),
        "\n".join(HEADER + ["def test_x():", "    desk_for(1)"]),
        "\n".join(HEADER + ["def test_x():", "    assert desk_for.__code__.co_consts"]),
        "\n".join(HEADER + ["def test_x():", "    import os", "    assert os"]),
        "\n".join(HEADER + ["x = 1", "def test_x():", "    assert desk_for(1)"]),
        "def test_x(:",
        "",
    ],
)
def test_static_gate_refuses_anything_but_tests(source):
    assert spec_test_gate(source, "desk_for") is False
    assert specify(source).passed is False


def test_refused_tests_never_reach_the_sandbox():
    calls = []

    class Spy:
        def execute(self, code, test_code=None, timeout_seconds=5.0, stdin_input=None):
            calls.append(test_code)
            return RUNNER.execute(code, test_code=test_code)

    seed = SEEDS["PY-2.1/cold-specify-1"]
    cheat = "\n".join(HEADER + ["def test_x():", "    assert open('solution.py').read()"])

    result = grade(seed, attempt(seed, tests=cheat), Spy())

    assert result.passed is False
    assert calls == []


def test_static_gate_allows_pytest_raises():
    source = "import pytest\n" + "\n".join(
        HEADER + ["def test_x():", "    with pytest.raises(ValueError):", "        desk_for(1)"]
    )

    assert spec_test_gate(source, "desk_for") is True


def test_a_test_that_hangs_does_not_hang_the_grader():
    result = specify(spec_file("while desk_for(1) != 'never':", "    pass", "assert True"))

    assert result.passed is False


# --- decompose_code and sandboxed code ---


DECOMPOSE = "PY-3.5/cold-decompose-2"


def test_decompose_code_passes_with_good_structure():
    seed = SEEDS[DECOMPOSE]

    assert run(DECOMPOSE, files=code(seed.body["reference_solution"])).passed is True


def test_decompose_code_fails_when_only_behaviour_is_right():
    seed = SEEDS[DECOMPOSE]
    result = run(DECOMPOSE, files=code(seed.body["wrong_solution"]))

    assert result.passed is False
    assert any(not c.passed for c in result.checks)


def test_structure_check_rules():
    rules = ("main", 2, 4)
    good = "def a():\n    pass\ndef b():\n    pass\ndef main():\n    a()\n    b()\n"

    assert structure_failures(good, *rules) == []
    assert "too few helpers" in structure_failures("def a():\n    pass\ndef main():\n    a()\n", *rules)
    assert "helper not called" in structure_failures(
        "def a():\n    pass\ndef b():\n    pass\ndef main():\n    a()\n", *rules
    )
    assert "function too long" in structure_failures(
        "def a():\n    pass\ndef b():\n    pass\ndef main():\n    a()\n    b()\n    x = 1\n    y = 2\n    z = 3\n",
        *rules,
    )
    assert "no entry function" in structure_failures("def a():\n    pass\n", *rules)
    assert "cannot be parsed" in structure_failures("def (:", *rules)


def test_structure_check_never_runs_the_code(tmp_path):
    marker = tmp_path / "ran.txt"
    source = f"open({str(marker)!r}, 'w').write('x')\ndef main():\n    pass\n"

    structure_failures(source, "main", 0, 8)

    assert not marker.exists()


def test_hidden_checks_grade_a_debug_fix():
    fixed = ["citizen = input()", "print('Registering', citizen)"]
    broken = ["citizen = input()", "print('Registering', citizn)"]
    seed = parse_seed(
        json.loads(Path("curriculum/python/py-0.4/exercises/debug-validate-1.json").read_text(encoding="utf-8")),
        "debug-validate-1",
        "PY-0.4",
    )

    assert grade(seed, attempt(seed, files=code(fixed)), RUNNER).passed is True
    assert grade(seed, attempt(seed, files=code(broken)), RUNNER).passed is False


def test_empty_submission_fails_cleanly():
    assert run(DECOMPOSE).passed is False


# --- Evidence strength (SPEC-12 section 5) ---


@pytest.mark.parametrize(
    "item_type, passed, prior, assistance, cold, expected",
    [
        ("predict", True, 0, AssistanceLevel.NONE, False, EvidenceStrength.STRONG),
        ("predict", False, 0, AssistanceLevel.NONE, False, EvidenceStrength.WEAK),
        ("debug", True, 2, AssistanceLevel.NONE, False, EvidenceStrength.MODERATE),
        ("trace", True, 0, AssistanceLevel.NONE, False, EvidenceStrength.MODERATE),
        ("trace", True, 0, AssistanceLevel.NONE, True, EvidenceStrength.STRONG),
        ("predict", True, 0, AssistanceLevel.SUPPLIED_REASONING, False, EvidenceStrength.WEAK),
        ("predict", True, 0, AssistanceLevel.SMALL_HINT, False, EvidenceStrength.STRONG),
    ],
)
def test_evidence_strength(item_type, passed, prior, assistance, cold, expected):
    assert evidence_strength(item_type, passed, prior, assistance, cold) == expected
