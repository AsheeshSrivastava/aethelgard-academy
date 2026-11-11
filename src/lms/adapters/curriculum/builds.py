"""Stage builds from curriculum/<course>/builds/stage-<n>/ (SPEC-15).

Hidden checks live outside the public tree, in the folder named by LMS_ANSWERS_DIR
(ADR-0021). Without it, a build grades with its public practice checks and says so.

A bad build is reported as a finding and skipped; it never stops the app.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError

from lms.core.builds import StageBuildSpec
from lms.core.curriculum_checks import Finding, Severity

ANSWERS_ENV = "LMS_ANSWERS_DIR"
CURRICULUM_ENV = "LMS_CURRICULUM_DIR"
PRACTICE_CHECKS = "practice_checks.py"
ANSWER_FILES = ("checks.py", "solution.py")


class BuildError(ValueError):
    """Says what is wrong with a build."""


REPO_ROOT = Path(__file__).resolve().parents[4]
SIBLING_ANSWERS = REPO_ROOT.parent / "lms-answers"


def answers_dir_from_env() -> Optional[Path]:
    """LMS_ANSWERS_DIR if set; otherwise the sibling lms-answers folder, if it exists (ADR-0021 amendment)."""
    value = os.environ.get(ANSWERS_ENV, "").strip()
    if value:
        return Path(value)
    return SIBLING_ANSWERS if SIBLING_ANSWERS.is_dir() else None


def curriculum_dir_from_env(default: Path) -> Path:
    """LMS_CURRICULUM_DIR if set; otherwise the default. Tests point it at made-up items."""
    value = os.environ.get(CURRICULUM_ENV, "").strip()
    return Path(value) if value else default


def _checks_file(folder: Path, answers_dir: Optional[Path]) -> Path:
    """The hidden checks when an answers folder is set, never falling back; else the practice checks."""
    if answers_dir is None:
        checks = folder / PRACTICE_CHECKS
    else:
        checks = answers_dir / folder.parent.parent.name / "builds" / folder.name / "checks.py"
    if not checks.exists():
        where = ANSWERS_ENV if answers_dir is not None else "the build folder"
        raise BuildError(f"{checks.name} is missing from {where}")
    return checks


def parse_build(folder: Path, answers_dir: Optional[Path] = None) -> StageBuildSpec:
    raw = json.loads((folder / "build.json").read_text(encoding="utf-8"))
    checks = _checks_file(folder, answers_dir)
    try:
        build = StageBuildSpec.model_validate({**raw, "checks_source": checks.read_text(encoding="utf-8")})
    except ValidationError as error:
        raise BuildError(str(error)) from error

    course_folder, stage_folder = folder.parent.parent.name, folder.name
    if (build.course_id, f"stage-{build.stage}") != (course_folder, stage_folder):
        raise BuildError(f"course_id and stage must match the folder {course_folder}/builds/{stage_folder}")
    return build


def load_builds(
    curriculum_dir: Path, answers_dir: Optional[Path] = None
) -> Tuple[Dict[Tuple[str, int], StageBuildSpec], List[Finding]]:
    builds: Dict[Tuple[str, int], StageBuildSpec] = {}
    problems: List[Finding] = []
    for path in sorted(curriculum_dir.glob("*/builds/stage-*/build.json")):
        folder = path.parent
        name = f"{folder.parent.parent.name}/{folder.name}"
        for leaked in ANSWER_FILES:
            if (folder / leaked).exists():
                problems.append(Finding(
                    severity=Severity.ERROR, code="build-answers-public",
                    message=f"{name}: {leaked} is in the public tree; move it to {ANSWERS_ENV}.",
                ))
        try:
            build = parse_build(folder, answers_dir)
            builds[(build.course_id, build.stage)] = build
        except ValueError as error:  # BuildError, bad JSON, or a file that is not UTF-8
            problems.append(Finding(severity=Severity.ERROR, code="build-invalid", message=f"{name}: {error}"))
            continue
        if answers_dir is None:
            problems.append(Finding(
                severity=Severity.WARNING, code="build-practice-checks",
                message=f"{name}: {ANSWERS_ENV} is not set, so this build grades with its public practice checks.",
                course_id=build.course_id, stage=build.stage,
            ))
    return builds, problems
