"""Stage builds: the file format, the requirement checks and what a learner may see.

Governed by SPEC-15 and ADR-0016. No AI grades a build. Learner code runs only
through the ICodeRunner port, so it gets the same limits as any run.
"""

import ast
import io
import re
import secrets
import tokenize
from typing import Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lms.core.course_map import course_of
from lms.core.curriculum_checks import Finding, Severity
from lms.core.grading import Runner
from lms.core.models import Unit, stage_label

_EXERCISE_ID = re.compile(r"^([a-z-]+)/stage-(\d+)/build$")
_ERROR_LINE = re.compile(r"^[A-Za-z]+(Error|Exception): ")
_ASSERTION = "AssertionError: "


def exercise_id_of(course_id: str, stage: int) -> str:
    return f"{course_id}/stage-{stage}/build"


def scope_of(course_id: str, stage: int) -> str:
    """What a build's draft and served time are stored under, in place of a unit id."""
    return f"{course_id}/stage-{stage}"


def parse_exercise_id(exercise_id: str) -> Optional[Tuple[str, int]]:
    match = _EXERCISE_ID.match(exercise_id)
    return (match.group(1), int(match.group(2))) if match else None


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BuildFile(_Strict):
    path: str = Field(pattern=r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*$")
    starter: List[str]


class RequirementCheck(_Strict):
    kind: Literal[
        "comment_lines", "input_assignments", "fstring_prints", "file_contains", "ownership_note", "behaviour"
    ]
    min: Optional[int] = None
    min_chars: Optional[int] = None
    path: Optional[str] = None
    any: Optional[List[str]] = None
    function: Optional[str] = None


class Requirement(_Strict):
    id: str
    label: str
    unit_id: str
    check: RequirementCheck


class BuildProof(_Strict):
    skill_id: str
    unit_id: str
    label: str


class StageBuildSpec(_Strict):
    """A parsed build. It holds hidden checks, so it must never be returned to a learner."""

    schema_version: Literal[1]
    course_id: str
    stage: int
    title: str
    kind: Literal["script", "mini_project"]
    status: Literal["draft", "approved"]
    brief_markdown: str
    sample_run: List[str]
    entry: str
    files: List[BuildFile]
    requirements: List[Requirement]
    proves: List[BuildProof]
    checks_source: str

    @model_validator(mode="after")
    def _consistent(self) -> "StageBuildSpec":
        paths = {f.path for f in self.files}
        if self.entry not in paths:
            raise ValueError(f"entry '{self.entry}' must be one of the files")
        ids = [r.id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("requirement ids must be unique")
        behaviours = [r.check.function for r in self.requirements if r.check.kind == "behaviour"]
        if not behaviours:
            raise ValueError("a build needs at least one behaviour requirement")
        for function in behaviours:
            if f"def {function}(" not in self.checks_source:
                raise ValueError(f"checks.py has no function {function}")
        for requirement in self.requirements:
            check = requirement.check
            if check.kind == "file_contains" and check.path not in paths:
                raise ValueError(f"file_contains names {check.path}, which is not in files")
        return self


class PublicRequirement(BaseModel):
    id: str
    label: str
    unit_id: str


class StageBuild(BaseModel):
    """What a learner sees, built from a list of allowed fields (SPEC-15 section 3)."""

    exercise_id: str
    course_id: str
    stage: int
    stage_label: str                   # "Stage 4", "DSA 0"
    title: str
    kind: str
    status: str
    brief_markdown: str
    sample_run: List[str]
    entry: str
    files: List[BuildFile]
    requirements: List[PublicRequirement]
    proves: List[BuildProof]
    submitted: bool


def public_build(build: StageBuildSpec, submitted: bool) -> StageBuild:
    return StageBuild(
        exercise_id=exercise_id_of(build.course_id, build.stage),
        course_id=build.course_id,
        stage=build.stage,
        stage_label=stage_label(build.stage),
        title=build.title,
        kind=build.kind,
        status=build.status,
        brief_markdown=build.brief_markdown,
        sample_run=build.sample_run,
        entry=build.entry,
        files=build.files,
        requirements=[PublicRequirement(id=r.id, label=r.label, unit_id=r.unit_id) for r in build.requirements],
        proves=build.proves,
        submitted=submitted,
    )


class RequirementResult(BaseModel):
    id: str
    met: Optional[bool]                # None: a behaviour check that has not run yet
    detail: Optional[str] = None


def _comments(code: str) -> Set[str]:
    """Full comment lines, as far as the code can be read."""
    found: Set[str] = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.COMMENT and token.line.strip().startswith("#"):
                found.add(token.string.strip())
    except (tokenize.TokenError, SyntaxError):
        pass  # Half-written code still counts up to the point it can be read.
    return found


def _input_assignments(tree: ast.AST) -> int:
    def is_input(node: ast.AST) -> bool:
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"

    # The answer may be cleaned or converted on the same line: input().strip(), int(input()).
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and any(is_input(part) for part in ast.walk(node.value))
    )


def _fstring_prints(tree: ast.AST) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        and any(isinstance(argument, ast.JoinedStr) for argument in node.args)
    )


def _parse(code: str) -> Tuple[Optional[ast.AST], Optional[str]]:
    try:
        return ast.parse(code), None
    except SyntaxError as error:
        return None, f"The file has a syntax error on line {error.lineno}."
    except ValueError:
        return None, "The file cannot be read as Python."


def _failure_detail(result, token_seen: bool) -> str:
    lines = result.stderr.strip().splitlines()
    if "timed out" in result.stderr:
        return "The script did not finish in time. Is it stuck in a loop?"
    for line in reversed(lines):
        if line.startswith(_ASSERTION):
            return line[len(_ASSERTION) :]
    if lines and _ERROR_LINE.match(lines[-1]):
        return lines[-1]
    return "The script stopped before the check could finish."


def _run_behaviour(build: StageBuildSpec, code: str, function: str, runner: Runner) -> Tuple[bool, Optional[str]]:
    """Exit code 0 alone proves nothing, so the check must also print a token it could not guess."""
    token = f"build-check-{secrets.token_hex(16)}"
    test_code = (
        f"{build.checks_source}\n\n"
        f"def test_requirement():\n"
        f"    {function}()\n"
        f'    print("{token}")\n'
    )
    result = runner.execute(code=code, test_code=test_code)
    token_seen = token in result.stdout
    if result.success and token_seen:
        return True, None
    return False, _failure_detail(result, token_seen)


def _check_one(
    requirement: Requirement,
    build: StageBuildSpec,
    files: Mapping[str, str],
    note: Optional[str],
    runner: Runner,
    run_checks: bool,
) -> RequirementResult:
    check = requirement.check
    code = files.get(build.entry, "")

    def result(met: Optional[bool], detail: Optional[str] = None) -> RequirementResult:
        return RequirementResult(id=requirement.id, met=met, detail=detail)

    if check.kind == "ownership_note":
        return result(len((note or "").strip()) >= (check.min_chars or 0))
    if check.kind == "file_contains":
        content = files.get(check.path or "", "")
        return result(any(text in content for text in check.any or []))
    if check.kind == "comment_lines":
        entry = next(f for f in build.files if f.path == build.entry)
        new_comments = _comments(code) - _comments("\n".join(entry.starter))
        return result(len(new_comments) >= (check.min or 0))
    if check.kind == "behaviour":
        if not run_checks:
            return result(None)
        return result(*_run_behaviour(build, code, check.function or "", runner))

    tree, problem = _parse(code)
    if tree is None:
        return result(False, problem)
    count = _input_assignments(tree) if check.kind == "input_assignments" else _fstring_prints(tree)
    return result(count >= (check.min or 0))


def check_requirements(
    build: StageBuildSpec,
    files: Mapping[str, str],
    ownership_note: Optional[str],
    runner: Runner,
    run_checks: bool,
) -> List[RequirementResult]:
    """Every requirement, in order. `run_checks` False skips the checks that run code."""
    return [_check_one(r, build, files, ownership_note, runner, run_checks) for r in build.requirements]


def check_builds(builds: Mapping[Tuple[str, int], StageBuildSpec], units: Sequence[Unit]) -> List[Finding]:
    """SPEC-15 section 5."""
    findings: List[Finding] = []
    for (course_id, stage), build in builds.items():
        in_stage = {u.unit_id: u for u in units if course_of(u.unit_id) == course_id and u.stage == stage}

        def report(code: str, message: str) -> None:
            findings.append(
                Finding(severity=Severity.ERROR, code=code, message=message, course_id=course_id, stage=stage)
            )

        named = [r.unit_id for r in build.requirements] + [p.unit_id for p in build.proves]
        for unit_id in sorted(set(named) - set(in_stage)):
            report("build-unit-unknown", f"{course_id} stage {stage} build names {unit_id}, which is not in the stage.")
        for proof in build.proves:
            unit = in_stage.get(proof.unit_id)
            if unit and proof.skill_id not in {s.skill_id for s in unit.target_skills}:
                report("build-skill-unknown", f"{proof.skill_id} is not a target skill of {proof.unit_id}.")
    return findings
