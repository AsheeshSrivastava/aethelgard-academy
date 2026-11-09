"""Quick checks and step diagrams in Explain parts (SPEC-19 sections 2 and 3, ADR-0029).

A `quickcheck` block in `lesson.md` is public: id, question, options. Its key (answer, why)
lives in the private answers folder (ADR-0021):
`<answers dir>/<course>/<unit folder>/quick_checks.json`. A `steps` block is public and only
checked for shape here; the browser draws it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from lms.core.course_map import course_of
from lms.core.curriculum_checks import Finding, Severity

QUICK_CHECKS_FILE = "quick_checks.json"
PRIVATE_KEYS = ("answer", "why")
OPTION_LETTERS = "ABCD"

_BLOCK = re.compile(r"^```(quickcheck|steps)[ \t]*\n(.*?)\n```[ \t]*$", re.M | re.S)
_ID = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
_UNIT = re.compile(r"^[A-Za-z]+-\d+(?:\.\d+)*$")
_STEP_KEYS = ("title", "code", "result", "note")


@dataclass
class QuickCheck:
    id: str
    question: str
    options: Dict[str, str]
    leaked: List[str] = field(default_factory=list)


@dataclass
class QuickCheckKey:
    answer: str
    why: str


def _blocks(markdown: str, language: str) -> List[str]:
    return [body for lang, body in _BLOCK.findall(markdown or "") if lang == language]


def _pairs(block: str) -> List[Tuple[str, str]]:
    """`key: value` lines, split at the first ": "; blank lines are ignored."""
    pairs = []
    for line in block.splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(": ")
        if not sep:
            key, value = line.rstrip(":"), ""
        pairs.append((key.strip(), value.strip()))
    return pairs


def _parse_one(block: str) -> Tuple[Optional[QuickCheck], Optional[str]]:
    values: Dict[str, str] = {}
    for key, value in _pairs(block):
        if key not in ("id", "question", *OPTION_LETTERS, *PRIVATE_KEYS):
            return None, f"unknown key '{key}'"
        values[key] = value
    check_id = values.get("id", "")
    if not _ID.match(check_id):
        return None, "needs an id of lowercase letters, digits, '.' and '-'"
    if not values.get("question"):
        return None, f"{check_id} needs a question"
    letters = [letter for letter in OPTION_LETTERS if letter in values]
    if not 2 <= len(letters) <= 4 or "".join(letters) != OPTION_LETTERS[: len(letters)]:
        return None, f"{check_id} needs 2 to 4 options, A, B, C, D in order"
    if any(not values[letter] for letter in letters):
        return None, f"{check_id} has an empty option"
    leaked = [key for key in PRIVATE_KEYS if key in values]
    return QuickCheck(check_id, values["question"], {letter: values[letter] for letter in letters}, leaked), None


def parse_quick_checks(markdown: str) -> Tuple[List[QuickCheck], List[str]]:
    """Every valid `quickcheck` block, and a problem line for each invalid or repeated one."""
    checks: List[QuickCheck] = []
    problems: List[str] = []
    for block in _blocks(markdown, "quickcheck"):
        check, problem = _parse_one(block)
        if problem:
            problems.append(f"quickcheck {problem}")
        elif any(other.id == check.id for other in checks):
            problems.append(f"quickcheck id {check.id} is repeated")
        else:
            checks.append(check)
    return checks, problems


def steps_block_problems(block: str) -> List[str]:
    """Why a `steps` block is invalid (SPEC-19 section 2); empty when it is fine."""
    steps = 0
    captions = 0
    for key, _ in _pairs(block):
        if key == "caption":
            captions += 1
        elif key == "title":
            steps += 1
        elif key in _STEP_KEYS:
            if steps == 0:
                return [f"'{key}' comes before the first title"]
        else:
            return [f"unknown key '{key}'"]
    if captions > 1:
        return ["more than one caption"]
    if not 2 <= steps <= 5:
        return [f"needs 2 to 5 steps, has {steps}"]
    return []


def load_quick_check_key(answers_dir: Optional[Path], unit_id: str, check_id: str) -> Optional[QuickCheckKey]:
    """The private key of one quick check, or None when there is none or it is unusable."""
    if answers_dir is None or not _UNIT.match(unit_id or ""):
        return None
    course = course_of(unit_id.upper())
    if course is None:
        return None
    path = Path(answers_dir) / course / unit_id.lower() / QUICK_CHECKS_FILE
    try:
        entry = json.loads(path.read_text(encoding="utf-8")).get(check_id)
    except (OSError, ValueError, AttributeError):
        return None
    if not isinstance(entry, dict):
        return None
    answer, why = entry.get("answer"), entry.get("why")
    if not (isinstance(answer, str) and answer in OPTION_LETTERS and isinstance(why, str) and why.strip()):
        return None
    return QuickCheckKey(answer=answer, why=why.strip())


def check_explain_blocks(curriculum_dir: Path, answers_dir: Optional[Path]) -> List[Finding]:
    """Findings for every lesson's `steps` and `quickcheck` blocks (SPEC-19 sections 2 and 3)."""
    findings: List[Finding] = []
    missing = Severity.ERROR if answers_dir is not None else Severity.WARNING

    for lesson in sorted(Path(curriculum_dir).glob("*/*/lesson.md")):
        unit_id, course = lesson.parent.name.upper(), lesson.parent.parent.name
        text = lesson.read_text(encoding="utf-8")

        def add(severity: Severity, code: str, message: str) -> None:
            findings.append(Finding(severity=severity, code=code, message=message, unit_id=unit_id, course_id=course))

        for block in _blocks(text, "steps"):
            for problem in steps_block_problems(block):
                add(Severity.WARNING, "explain-steps-invalid", f"{unit_id}: a steps block {problem}.")

        checks, problems = parse_quick_checks(text)
        for problem in problems:
            add(Severity.WARNING, "explain-quickcheck-invalid", f"{unit_id}: {problem}.")
        for check in checks:
            if check.leaked:
                add(
                    Severity.ERROR, "quickcheck-answers-public",
                    f"{unit_id}: quick check {check.id} holds {', '.join(check.leaked)} in the public lesson.",
                )
            key = load_quick_check_key(answers_dir, unit_id, check.id)
            if key is None or key.answer not in check.options:
                add(missing, "quickcheck-answers-missing", f"{unit_id}: quick check {check.id} has no usable private key.")
    return findings
