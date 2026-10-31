"""Stage builds from curriculum/<course>/builds/stage-<n>/ (SPEC-15).

A bad build is reported as a finding and skipped; it never stops the app.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import ValidationError

from lms.core.builds import StageBuildSpec
from lms.core.curriculum_checks import Finding, Severity


class BuildError(ValueError):
    """Says what is wrong with a build."""


def parse_build(folder: Path) -> StageBuildSpec:
    raw = json.loads((folder / "build.json").read_text(encoding="utf-8"))
    checks = folder / "checks.py"
    if not checks.exists():
        raise BuildError("checks.py is missing")
    try:
        build = StageBuildSpec.model_validate({**raw, "checks_source": checks.read_text(encoding="utf-8")})
    except ValidationError as error:
        raise BuildError(str(error)) from error

    course_folder, stage_folder = folder.parent.parent.name, folder.name
    if (build.course_id, f"stage-{build.stage}") != (course_folder, stage_folder):
        raise BuildError(f"course_id and stage must match the folder {course_folder}/builds/{stage_folder}")
    return build


def load_builds(curriculum_dir: Path) -> Tuple[Dict[Tuple[str, int], StageBuildSpec], List[Finding]]:
    builds: Dict[Tuple[str, int], StageBuildSpec] = {}
    problems: List[Finding] = []
    for path in sorted(curriculum_dir.glob("*/builds/stage-*/build.json")):
        folder = path.parent
        try:
            build = parse_build(folder)
            builds[(build.course_id, build.stage)] = build
        except ValueError as error:  # BuildError, bad JSON, or a file that is not UTF-8
            name = f"{folder.parent.parent.name}/{folder.name}"
            problems.append(Finding(severity=Severity.ERROR, code="build-invalid", message=f"{name}: {error}"))
    return builds, problems
