"""README checks on a stage build: plain Python, no AI (ADR-0024, SPEC-15 section 2.2)."""

import json
from pathlib import Path

import pytest

from lms.core.builds import StageBuildSpec, check_requirements

FOLDER = Path("curriculum/python/builds/stage-0")
CHECKS = "def check_sample_run():\n    pass\n"


def build(sections, path="README.md"):
    raw = json.loads((FOLDER / "build.json").read_text(encoding="utf-8"))
    raw["requirements"] = [
        {"id": "sample", "label": "s", "unit_id": "PY-0.4", "check": {"kind": "behaviour", "function": "check_sample_run"}},
        {"id": "readme", "label": "r", "unit_id": "PY-0.4", "check": {"kind": "markdown_sections", "path": path, "sections": sections}},
    ]
    return StageBuildSpec.model_validate({**raw, "checks_source": CHECKS})


def readme_result(spec, text):
    results = check_requirements(spec, {"checkin.py": "", "README.md": text}, "", None, False)
    return next(r for r in results if r.id == "readme")


RUN = {"heading": "How to run it", "min_words": 2, "any": ["python checkin.py"], "hint": "Give the command that runs it."}


def test_a_section_with_its_heading_words_and_command_is_met():
    result = readme_result(build([RUN]), "# Build\n\n## How to run it\n\nType python checkin.py in a terminal.\n")

    assert (result.met, result.detail) == (True, None)


def test_a_missing_heading_is_named():
    result = readme_result(build([RUN]), "# Build\n\nType python checkin.py\n")

    assert result.met is False and result.detail == "The heading 'How to run it' is missing."


def test_too_few_words_are_named():
    words = {"heading": "What this script does", "min_words": 5}

    result = readme_result(build([words]), "## What this script does\n\nMakes slips.\n")

    assert result.met is False and result.detail == "Write at least 5 words under 'What this script does'."


def test_the_hint_is_shown_when_the_text_is_missing():
    result = readme_result(build([RUN]), "## How to run it\n\nOpen it and press run.\n")

    assert result.met is False and result.detail == "Give the command that runs it."


def test_the_command_must_be_in_its_own_section():
    text = "## What this script does\n\nIt is run with python checkin.py by staff.\n\n## How to run it\n\nAsk the desk lead.\n"

    assert readme_result(build([RUN]), text).met is False


def test_headings_and_texts_ignore_case_and_heading_level():
    text = "### HOW TO RUN IT\n\nType Python Checkin.py now.\n"

    assert readme_result(build([RUN]), text).met is True


def test_words_under_the_next_heading_do_not_count():
    words = {"heading": "What this script does", "min_words": 5}
    text = "## What this script does\n\n## How to run it\n\none two three four five six\n"

    assert readme_result(build([words]), text).met is False


def test_a_markdown_check_must_name_a_file_of_the_build():
    with pytest.raises(ValueError, match="markdown_sections names NOTES.md"):
        build([RUN], path="NOTES.md")


# --- The Stage 0 build's own README rules ---


def stage_0():
    raw = json.loads((FOLDER / "build.json").read_text(encoding="utf-8"))
    return StageBuildSpec.model_validate({**raw, "checks_source": CHECKS + "def check_messy_input():\n    pass\n"})


def readme_results(text):
    results = check_requirements(stage_0(), {"checkin.py": "", "README.md": text}, "", None, False)
    return {r.id: (r.met, r.detail) for r in results if r.id.startswith("readme")}


GOOD = """# Stage 0 build

## What this script does

It asks a visitor for their name and service, cleans both, and prints a check-in slip.

## How to run it

Run python checkin.py and answer the two questions.

## What I checked myself

I typed a messy name like '  meera ' and the service 'SHELTER' and saw a clean slip.
"""


def test_a_good_readme_meets_every_readme_requirement():
    assert all(met for met, _ in readme_results(GOOD).values())
    assert len(readme_results(GOOD)) == 3


def test_the_owners_first_readme_gets_two_clear_details():
    """The README from the owner's screenshot, 2026-11-04."""
    first = (
        "# Stage 0 build\n\n## What this script does\n"
        "This script is use for creating Check-IN Slip for walkin customers\n\n"
        "## How to run it\n\n\n## What I checked myself\n\n"
    )

    results = readme_results(first)

    assert results["readme-does"] == (True, None)
    assert results["readme-run"][0] is False and "How to run it" in results["readme-run"][1]
    assert results["readme-checked"][0] is False and "What I checked myself" in results["readme-checked"][1]
