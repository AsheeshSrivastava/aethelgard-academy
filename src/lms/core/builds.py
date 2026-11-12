"""Stage builds: the file format, the requirement checks and what a learner may see.

Governed by SPEC-15 and ADR-0016. No AI grades a build. Learner code runs only
through the ICodeRunner port, so it gets the same limits as any run.
"""

import ast
import io
import re
import secrets
import tokenize
from typing import Dict, List, Literal, Mapping, Optional, Sequence, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lms.core.course_map import STAGE_BUILD_MATURITY, Maturity, course_of
from lms.core.curriculum_checks import Finding, Severity
from lms.core.grading import Runner
from lms.core.interfaces import extra_file_problem
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


class SectionRule(_Strict):
    """One section of a Markdown file the learner writes (ADR-0024)."""

    heading: str
    min_words: int = 0
    any: Optional[List[str]] = None
    hint: Optional[str] = None


class RequirementCheck(_Strict):
    kind: Literal[
        "comment_lines", "input_assignments", "fstring_prints", "file_contains", "ownership_note", "behaviour",
        "markdown_sections", "readme_sample_run", "review_note",
    ]
    min: Optional[int] = None
    min_chars: Optional[int] = None
    path: Optional[str] = None
    any: Optional[List[str]] = None
    function: Optional[str] = None
    sections: Optional[List[SectionRule]] = None
    heading: Optional[str] = None      # readme_sample_run: the section that holds the pasted run


class Requirement(_Strict):
    id: str
    label: str
    unit_id: str
    skills: List[str] = Field(default_factory=list)  # the proves skills this requirement earns (ADR-0030)
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
    maturity: Maturity = STAGE_BUILD_MATURITY
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
        if self.maturity != STAGE_BUILD_MATURITY:
            raise ValueError(f"a stage build is {STAGE_BUILD_MATURITY} (ADR-0018), not {self.maturity}")
        paths = {f.path for f in self.files}
        if len(paths) != len(self.files):
            raise ValueError("file paths must be unique")
        for path in sorted(paths - {self.entry}):
            problem = extra_file_problem(path) if path.endswith(".py") else None
            if problem:
                raise ValueError(problem)
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
            if check.kind in ("file_contains", "markdown_sections", "readme_sample_run") and check.path not in paths:
                raise ValueError(f"{check.kind} names {check.path}, which is not in files")
            if check.kind == "markdown_sections" and not check.sections:
                raise ValueError("markdown_sections needs at least one section")
            if check.kind == "readme_sample_run" and not check.heading:
                raise ValueError("readme_sample_run needs a heading")
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
    stage_label: str                   # "Module 4", "DSA 0" (ADR-0027)
    title: str
    kind: str
    maturity: Maturity
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
        maturity=build.maturity,
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


def other_python_files(build: StageBuildSpec, files: Mapping[str, str]) -> Dict[str, str]:
    """The build's own .py files besides the entry, as the learner has them (else the starter).

    Only files the build declares are taken, so a request cannot place a file of its own choosing.
    """
    return {
        f.path: files.get(f.path, "\n".join(f.starter))
        for f in build.files
        if f.path.endswith(".py") and f.path != build.entry
    }


def _run_behaviour(
    build: StageBuildSpec, code: str, files: Mapping[str, str], function: str, runner: Runner
) -> Tuple[bool, Optional[str]]:
    """Exit code 0 alone proves nothing, so the check must also print a token it could not guess."""
    token = f"build-check-{secrets.token_hex(16)}"
    test_code = (
        f"{build.checks_source}\n\n"
        f"def test_requirement():\n"
        f"    {function}()\n"
        f'    print("{token}")\n'
    )
    result = runner.execute(code=code, test_code=test_code, files=other_python_files(build, files))
    token_seen = token in result.stdout
    if result.success and token_seen:
        return True, None
    return False, _failure_detail(result, token_seen)


_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
_FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def _sections_of(text: str) -> Dict[str, str]:
    """Each Markdown heading's text (lower case) and the text under it, up to the next heading."""
    sections: Dict[str, str] = {}
    current: Optional[str] = None
    fence: Optional[str] = None        # A "#" line inside a code block is text, not a heading.
    for line in text.splitlines():
        marker = _FENCE.match(line)
        if marker:
            fence = None if fence == marker.group(1) else (fence or marker.group(1))
        match = None if (fence or marker) else _HEADING.match(line)
        if match:
            current = match.group(1).strip().lower()
            sections.setdefault(current, "")
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def _markdown_sections(text: str, rules: Sequence[SectionRule]) -> Tuple[bool, Optional[str]]:
    """ADR-0024: plain checks on a Markdown file; the detail names the first unmet rule."""
    sections = _sections_of(text)
    for rule in rules:
        body = sections.get(rule.heading.strip().lower())
        if body is None:
            return False, f"The heading '{rule.heading}' is missing."
        if len(body.split()) < rule.min_words:
            return False, f"Write at least {rule.min_words} words under '{rule.heading}'."
        if rule.any and not any(t.lower() in body.lower() for t in rule.any):
            return False, rule.hint or f"'{rule.heading}' needs one of: {', '.join(rule.any)}."
    return True, None


def _input_prompts(tree: ast.AST) -> List[str]:
    """The text of each input("...") call, in code order. Read from the code; nothing runs."""
    found = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            found.append((node.lineno, node.col_offset, node.args[0].value))
    return [text for _, _, text in sorted(found) if text.strip()]


def _first_code_block(body: str) -> Optional[List[str]]:
    lines: List[str] = []
    fence: Optional[str] = None
    for line in body.splitlines():
        marker = _FENCE.match(line)
        if marker and fence is None:
            fence = marker.group(1)
        elif marker and fence == marker.group(1):
            return lines
        elif fence:
            lines.append(line)
    return lines if fence else None


def _split_transcript(lines: Sequence[str], prompts: Sequence[str]) -> Tuple[List[str], List[str]]:
    """Typed values and expected output lines (SPEC-15 section 9.2).

    The next unused prompt, in code order, marks a typed line. Once every prompt is used, the rest
    is output, so a slip line that starts like a prompt ("Name: Meera") is not mistaken for typing.
    """
    typed: List[str] = []
    output: List[str] = []
    for line in lines:
        if not line.strip():
            continue
        if len(typed) < len(prompts):
            full = prompts[len(typed)]
            prompt = full.rstrip()
            if line.lstrip().startswith(prompt):
                rest = line.lstrip()[len(prompt):]
                typed.append(rest[1:] if full.endswith(" ") and rest.startswith(" ") else rest)
                continue
        output.append(line.strip())
    return typed, output


def _first_missing_line(stdout: str, expected: Sequence[str], prompts: Sequence[str]) -> Optional[str]:
    """The first expected line the script's output lacks, in order. Prompts print without a newline
    when input is piped, so a line may follow one or more of them."""
    lead = "|".join(re.escape(p.rstrip()) for p in sorted(set(prompts), key=len, reverse=True))
    lead_part = f"(?:(?:{lead})[ \\t]*)*" if lead else ""
    cursor = 0
    for line in expected:
        pattern = re.compile(rf"^[ \t]*{lead_part}{re.escape(line)}[ \t]*\r?$", re.MULTILINE)
        match = pattern.search(stdout, cursor)
        if not match:
            return line
        cursor = match.end()
    return None


def _readme_sample_run(
    build: StageBuildSpec, check: RequirementCheck, files: Mapping[str, str], runner: Runner
) -> Tuple[bool, Optional[str]]:
    """SPEC-15 section 9.2: the README's pasted run must be what the script really does."""
    heading = check.heading or ""
    body = _sections_of(files.get(check.path or "", "")).get(heading.strip().lower())
    block = _first_code_block(body) if body is not None else None
    if block is None:
        return False, f"Paste one real run inside a code block under '{heading}'."
    code = files.get(build.entry, "")
    tree, problem = _parse(code)
    if tree is None:
        return False, problem
    prompts = _input_prompts(tree)
    typed, expected = _split_transcript(block, prompts)
    if not typed:
        return False, "Show what you typed: start each typed line with the question your script asks."
    if not expected:
        return False, "Show what the script printed after you typed."
    result = runner.execute(code=code, stdin_input="\n".join(typed) + "\n", files=other_python_files(build, files))
    if not result.success:
        return False, "The script stopped before the sample run finished."
    missing = _first_missing_line(result.stdout, expected, prompts)
    if missing is not None:
        # A line that starts like a prompt is often the typing of a second pasted run (owner 1A, 2026-11-09).
        if any(missing.startswith(p.rstrip()) for p in prompts):
            return False, f"Your script did not print: `{missing}`. If you pasted more than one run, keep just one."
        return False, f"Your script did not print: `{missing}`"
    return True, None


def _check_one(
    requirement: Requirement,
    build: StageBuildSpec,
    files: Mapping[str, str],
    note: Optional[str],
    runner: Runner,
    run_checks: bool,
    review: Optional[str] = None,
) -> RequirementResult:
    check = requirement.check
    code = files.get(build.entry, "")

    def result(met: Optional[bool], detail: Optional[str] = None) -> RequirementResult:
        return RequirementResult(id=requirement.id, met=met, detail=detail)

    if check.kind == "ownership_note":
        return result(len((note or "").strip()) >= (check.min_chars or 0))
    if check.kind == "review_note":
        return result(len((review or "").strip()) >= (check.min_chars or 0))
    if check.kind == "readme_sample_run":
        if not run_checks:
            return result(None)
        return result(*_readme_sample_run(build, check, files, runner))
    if check.kind == "file_contains":
        content = files.get(check.path or "", "")
        return result(any(text in content for text in check.any or []))
    if check.kind == "markdown_sections":
        return result(*_markdown_sections(files.get(check.path or "", ""), check.sections or []))
    if check.kind == "comment_lines":
        entry = next(f for f in build.files if f.path == build.entry)
        new_comments = _comments(code) - _comments("\n".join(entry.starter))
        return result(len(new_comments) >= (check.min or 0))
    if check.kind == "behaviour":
        if not run_checks:
            return result(None)
        return result(*_run_behaviour(build, code, files, check.function or "", runner))

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
    review_note: Optional[str] = None,
) -> List[RequirementResult]:
    """Every requirement, in order. `run_checks` False skips the checks that run code."""
    return [_check_one(r, build, files, ownership_note, runner, run_checks, review_note) for r in build.requirements]


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

        # ADR-0030: a proved skill must be earned by a requirement, and a requirement may only earn proved skills.
        proved = {p.skill_id for p in build.proves}
        earned = {skill for r in build.requirements for skill in r.skills}
        for skill_id in sorted(proved - earned):
            report("build-proof-unearned", f"The build proves {skill_id}, but no requirement earns it.")
        for requirement in build.requirements:
            for skill_id in sorted(set(requirement.skills) - proved):
                report(
                    "build-skill-unproved",
                    f"Requirement {requirement.id} names {skill_id}, which the build does not prove.",
                )
    return findings
