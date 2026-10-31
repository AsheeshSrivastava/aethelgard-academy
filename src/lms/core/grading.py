"""Deterministic grading of attempts.

Governed by:
- SPEC-13 section 4 (grading rules per item type)
- SPEC-12 section 5 (Attempts and Evidence)
- ADR-0016 amendments B and C: no AI grades an exercise.

Fixed answers and code structure are checked here. Learner code runs only through
the ICodeRunner port, so it gets the same limits as any run.
"""

import ast
from typing import Dict, List, Optional, Protocol, Tuple

from pydantic import BaseModel, ConfigDict

from lms.core.exercises import ExerciseSeed
from lms.core.models import AssistanceLevel, EvidenceStrength

_FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "getattr", "globals"}


class Locate(BaseModel):
    line: int
    error_type: str


class Attempt(BaseModel):
    # Unknown fields are refused, so a client cannot send strength or assistance.
    model_config = ConfigDict(extra="forbid")

    exercise_id: str
    activity: str
    choice: Optional[str] = None
    trace_answers: Optional[List[str]] = None
    locate: Optional[Locate] = None
    files: Optional[Dict[str, str]] = None
    tests: Optional[str] = None
    fields: Optional[Dict[str, object]] = None
    plan: Optional[List[str]] = None
    ownership_note: Optional[str] = None


class Check(BaseModel):
    label: str
    passed: bool
    detail: Optional[str] = None


class Score(BaseModel):
    passed: int
    total: int


class Reveal(BaseModel):
    correct: object
    why: List[str] = []


class GradeResult(BaseModel):
    passed: bool
    feedback: str
    checks: Optional[List[Check]] = None
    score: Optional[Score] = None
    reveal: Optional[Reveal] = None


class Runner(Protocol):
    def execute(self, code: str, test_code: Optional[str] = None, timeout_seconds: float = 5.0, stdin_input: Optional[str] = None):
        ...


def _submitted_code(attempt: Attempt) -> str:
    files = attempt.files or {}
    return files.get("solution.py") or next(iter(files.values()), "")


def _verdict(passed: bool, reveal: Optional[Reveal] = None) -> GradeResult:
    return GradeResult(passed=passed, feedback="Correct." if passed else "Not this time.", reveal=reveal)


def _grade_key(seed: ExerciseSeed, attempt: Attempt) -> GradeResult:
    key = seed.body["answer_key"]
    return _verdict(attempt.choice == key, Reveal(correct=key, why=seed.body.get("why", [])))


def _grade_trace(seed: ExerciseSeed, attempt: Attempt) -> GradeResult:
    expected = seed.body["expected_output"]
    given = [line.strip() for line in attempt.trace_answers or []]
    return _verdict(given == [line.strip() for line in expected], Reveal(correct=expected))


def _grade_locate(seed: ExerciseSeed, attempt: Attempt) -> GradeResult:
    key = seed.body["answer_key"]
    picked = attempt.locate
    passed = picked is not None and picked.line == key["line"] and picked.error_type == key["error_type"]
    return _verdict(passed, Reveal(correct=key, why=seed.body["why"]))


def _grade_contract(seed: ExerciseSeed, attempt: Attempt) -> GradeResult:
    key = seed.body["answer_key"]
    given = attempt.fields or {}

    def exact(field_id: str) -> bool:
        answer, picked = key[field_id], given.get(field_id)
        if isinstance(answer, list):
            return isinstance(picked, list) and set(map(str, picked)) == set(answer)
        return picked == answer

    right = sum(1 for field_id in key if exact(field_id))
    return GradeResult(
        passed=right == len(key),
        feedback=f"{right} of {len(key)} fields are right.",
        score=Score(passed=right, total=len(key)),
        reveal=Reveal(correct=key, why=seed.body["why"]),
    )


def _grade_plan(seed: ExerciseSeed, attempt: Attempt) -> GradeResult:
    body = seed.body
    plan = attempt.plan or []
    right_set = set(plan) == set(body["needed"]) and len(plan) == len(set(plan))
    position = {step: i for i, step in enumerate(plan)}
    right_order = right_set and all(position[a] < position[b] for a, b in body["order_constraints"])
    if not right_set:
        feedback = "The chosen steps are not right yet."
    else:
        feedback = "Correct." if right_order else "The steps are right, but the order is not."
    return GradeResult(
        passed=right_order,
        feedback=feedback,
        reveal=Reveal(correct=body["needed"], why=body.get("why", [])),
    )


def _run_checks(runner: Runner, code: str, hidden_checks: List[str]) -> Tuple[bool, str]:
    result = runner.execute(code=code, test_code="\n".join(hidden_checks))
    return result.success, "; ".join(result.assertion_errors) or result.stderr[-300:]


def _grade_hidden_checks(seed: ExerciseSeed, attempt: Attempt, runner: Runner) -> GradeResult:
    passed, detail = _run_checks(runner, _submitted_code(attempt), seed.body["hidden_checks"])
    return GradeResult(
        passed=passed,
        feedback="All checks passed." if passed else "Some checks failed.",
        checks=[Check(label="Hidden checks", passed=passed)],
    )


def structure_failures(source: str, entry: str, min_helpers: int, max_lines: int) -> List[str]:
    """SPEC-13 decompose_code structure check. Parses the code and never runs it."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ["cannot be parsed"]
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    if entry not in functions:
        return ["no entry function"]
    helpers = [name for name in functions if name != entry]
    called = {
        n.func.id
        for n in ast.walk(functions[entry])
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    failures = []
    if len(helpers) < min_helpers:
        failures.append("too few helpers")
    if any(h not in called for h in helpers):
        failures.append("helper not called")
    if any(f.end_lineno - f.lineno + 1 > max_lines for f in functions.values()):
        failures.append("function too long")
    return failures


def _grade_decompose_code(seed: ExerciseSeed, attempt: Attempt, runner: Runner) -> GradeResult:
    body = seed.body
    source = _submitted_code(attempt)
    structure = body["structure"]
    failures = structure_failures(
        source, body["entry_function"], structure["min_helpers"], structure["max_lines_per_function"]
    )
    behaves, _ = _run_checks(runner, source, body["hidden_checks"]) if source else (False, "")
    return GradeResult(
        passed=behaves and not failures,
        feedback="Correct." if behaves and not failures else "Not this time.",
        checks=[
            Check(label="Behaviour tests", passed=behaves),
            Check(label="Structure", passed=not failures, detail=", ".join(failures) or None),
        ],
    )


def spec_test_gate(source: str, function_name: str) -> bool:
    """SPEC-13 specify_by_tests step 1: the file may only test. Parsed, never run."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.Import):
            if [a.name for a in node.names] != ["pytest"]:
                return False
        elif isinstance(node, ast.ImportFrom):
            if node.module != "solution" or [a.name for a in node.names] != [function_name]:
                return False
        elif not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            return False

    has_check = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and (node.id in _FORBIDDEN_NAMES or node.id.startswith("__")):
            return False
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in tree.body:
            return False
        if isinstance(node, ast.Assert) or (isinstance(node, ast.Attribute) and node.attr == "raises"):
            has_check = True
    return has_check


def _grade_specify_by_tests(seed: ExerciseSeed, attempt: Attempt, runner: Runner) -> GradeResult:
    body = seed.body
    tests = attempt.tests or ""
    if not spec_test_gate(tests, body["function_name"]):
        return GradeResult(passed=False, feedback="Your file may only contain tests with assert or pytest.raises.")
    tests_lines = tests.splitlines()
    fits, _ = _run_checks(runner, "\n".join(body["reference"]), tests_lines)
    if not fits:
        return GradeResult(passed=False, feedback="Your tests fail on a correct program, so they describe the wrong behaviour.")
    killed = sum(
        1
        for mutant in body["mutants"]
        if not _run_checks(runner, "\n".join(mutant["code"]), tests_lines)[0]
    )
    total = len(body["mutants"])
    return GradeResult(
        passed=killed == total,
        feedback=f"Your tests caught {killed} of {total} faulty programs.",
        score=Score(passed=killed, total=total),
    )


def grade(seed: ExerciseSeed, attempt: Attempt, runner: Runner) -> GradeResult:
    """Grade one attempt. `seed` must already have its name slots filled."""
    item = seed.item_type
    if item in ("predict", "choice", "explain_spot_flaw", "explain_model_choice"):
        return _grade_key(seed, attempt)
    if item == "trace":
        return _grade_trace(seed, attempt)
    if item == "debug_locate":
        return _grade_locate(seed, attempt)
    if item == "specify_contract":
        return _grade_contract(seed, attempt)
    if item == "decompose_plan":
        return _grade_plan(seed, attempt)
    if item == "specify_by_tests":
        return _grade_specify_by_tests(seed, attempt, runner)
    if item == "decompose_code":
        return _grade_decompose_code(seed, attempt, runner)
    return _grade_hidden_checks(seed, attempt, runner)


def highest_assistance(levels: List[AssistanceLevel]) -> AssistanceLevel:
    """The strongest help logged. Enum order runs from none to supplied reasoning."""
    order = list(AssistanceLevel)
    return max(levels, key=order.index, default=AssistanceLevel.NONE)


def evidence_strength(
    item_type: str, passed: bool, prior_attempts: int, assistance: AssistanceLevel, cold_check: bool
) -> EvidenceStrength:
    """SPEC-12 section 5. Supplied reasoning always forces Weak (ADR-0009)."""
    if not passed or assistance == AssistanceLevel.SUPPLIED_REASONING:
        return EvidenceStrength.WEAK
    if cold_check:
        return EvidenceStrength.STRONG
    if item_type == "trace" or prior_attempts > 0:
        return EvidenceStrength.MODERATE
    return EvidenceStrength.STRONG
