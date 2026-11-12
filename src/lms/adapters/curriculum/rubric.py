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
from lms.core.exercises import MAX_CONCEPT_PROMPTS
from lms.core.proficiency import concept_check_id

RUBRIC_FILE = "concept_check.json"
PUBLIC_RUBRIC_FIELDS = ("rubric", "solid_keywords", "ideas", "variants")
_UNIT = re.compile(r"^[A-Za-z]+-\d+(?:\.\d+)*$")




def load_rubric(answers_dir: Optional[Path], unit_id: str, prompt_no: int = 1) -> Optional[Rubric]:
    """The private rubric of a unit's prompt `v<prompt_no>`, or None when there is none or it is unusable.

    `v1` is the file's own `ideas`; `v2` and `v3` sit under `variants` (ADR-0032).
    """
    if answers_dir is None or not _UNIT.match(unit_id or ""):
        return None
    course = course_of(unit_id.upper())
    if course is None:
        return None
    path = Path(answers_dir) / course / unit_id.lower() / RUBRIC_FILE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if prompt_no != 1:
            variants = raw.get("variants") if isinstance(raw, dict) else None
            raw = variants.get(f"v{prompt_no}") if isinstance(variants, dict) else None
        return parse_rubric(raw, unit_id.upper())
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
        more = check.get("more_prompts", [])
        if not isinstance(more, list) or not all(isinstance(p, str) and p.strip() for p in more):
            findings.append(
                Finding(
                    severity=Severity.ERROR, code="concept-check-bad-prompts",
                    message=f"{unit_id} more_prompts must be a list of non-empty texts.",
                    unit_id=unit_id, course_id=course,
                )
            )
            more = []
        if 1 + len(more) > MAX_CONCEPT_PROMPTS:
            findings.append(
                Finding(
                    severity=Severity.ERROR, code="concept-check-too-many-prompts",
                    message=f"{unit_id} has {1 + len(more)} concept check prompts; the most is {MAX_CONCEPT_PROMPTS}.",
                    unit_id=unit_id, course_id=course,
                )
            )
        if "prompt" not in check:
            continue
        for number in range(1, min(1 + len(more), MAX_CONCEPT_PROMPTS) + 1):
            if load_rubric(answers_dir, unit_id, number) is None:
                findings.append(
                    Finding(
                        severity=Severity.WARNING, code="concept-check-rubric-missing",
                        message=(
                            f"{concept_check_id(unit_id, number)} has a concept check prompt but no private rubric, "
                            "so it is not judged."
                        ),
                        unit_id=unit_id, course_id=course,
                    )
                )
    return findings
