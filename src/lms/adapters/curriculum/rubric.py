"""The private concept-check rubric (SPEC-18 section 1, ADR-0021).

`<answers dir>/<course>/<unit folder>/concept_check.json` holds the required ideas.
The public `meta.json` keeps only the prompt.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from lms.core.course_map import course_of
from lms.core.ai_judgement import Rubric, RubricError, parse_rubric
from lms.core.curriculum_checks import Finding, Severity

RUBRIC_FILE = "concept_check.json"
PUBLIC_RUBRIC_FIELDS = ("rubric", "solid_keywords", "ideas")
_UNIT = re.compile(r"^[A-Za-z]+-\d+(?:\.\d+)*$")




def load_rubric(answers_dir: Optional[Path], unit_id: str) -> Optional[Rubric]:
    """The unit's private rubric, or None when there is none or it is unusable."""
    if answers_dir is None or not _UNIT.match(unit_id or ""):
        return None
    course = course_of(unit_id.upper())
    if course is None:
        return None
    path = Path(answers_dir) / course / unit_id.lower() / RUBRIC_FILE
    try:
        return parse_rubric(json.loads(path.read_text(encoding="utf-8")), unit_id.upper())
    except (OSError, ValueError, RubricError):
        return None


def check_concept_checks(curriculum_dir: Path, answers_dir: Optional[Path]) -> List[Finding]:
    """`concept-check-answers-public` (error) and `concept-check-rubric-missing` (warning)."""
    findings: List[Finding] = []
    for meta_file in sorted(Path(curriculum_dir).glob("*/*/meta.json")):
        unit_id = meta_file.parent.name.upper()
        try:
            check = json.loads(meta_file.read_text(encoding="utf-8")).get("concept_check")
        except (OSError, ValueError):
            continue
        if not isinstance(check, dict):
            continue
        course = meta_file.parent.parent.name
        leaked = [f for f in PUBLIC_RUBRIC_FIELDS if f in check]
        if leaked:
            findings.append(
                Finding(
                    severity=Severity.ERROR, code="concept-check-answers-public",
                    message=f"{unit_id} holds {', '.join(leaked)} in the public concept check.",
                    unit_id=unit_id, course_id=course,
                )
            )
        if "prompt" in check and load_rubric(answers_dir, unit_id) is None:
            findings.append(
                Finding(
                    severity=Severity.WARNING, code="concept-check-rubric-missing",
                    message=f"{unit_id} has a concept check prompt but no private rubric, so it is not judged.",
                    unit_id=unit_id, course_id=course,
                )
            )
    return findings
