"""Data-based build feedback, layer 1 (SPEC-15 section 10). Offline: no model, no network."""

import json

from lms.core.builds import RequirementResult, StageBuildSpec
from lms.core.build_feedback import build_feedback_points
from test_stage_build import FOLDER

README_OK = (
    "## What it does\n\nThis script greets a visitor and prints a check-in slip for them.\n\n"
    "## How to run it\n\nRun `uv run checkin.py` in the folder.\n"
)


def spec():
    raw = json.loads((FOLDER / "build.json").read_text(encoding="utf-8"))
    raw["requirements"] = [
        {"id": "behaviour", "label": "Script behaves", "unit_id": "PY-0.4",
         "check": {"kind": "behaviour", "function": "check_it"}},
        {"id": "sections", "label": "README answers the checklist points", "unit_id": "TW-0.1",
         "check": {"kind": "markdown_sections", "path": "README.md", "sections": [
             {"heading": "What it does", "min_words": 8}, {"heading": "How to run it", "min_words": 4},
             {"heading": "Limits", "min_words": 4}]}},
        {"id": "run", "label": "README's sample run is real", "unit_id": "TW-0.1",
         "check": {"kind": "readme_sample_run", "path": "README.md", "heading": "A sample run"}},
        {"id": "review", "label": "Review note written", "unit_id": "TW-0.1",
         "check": {"kind": "review_note", "min_chars": 20}},
    ]
    return StageBuildSpec.model_validate({**raw, "checks_source": "def check_it():\n    pass\n"})


def points(results, files=None, note=""):
    return build_feedback_points(spec(), files or {"README.md": README_OK}, results, note)


R = RequirementResult


def test_every_point_says_what_the_rule_looked_for():
    pts = points([R(id="behaviour", met=False), R(id="sections", met=False), R(id="run", met=False),
                  R(id="review", met=False)])
    looked = {p.requirement_id: p.looked_for for p in pts}
    assert "'What it does' with at least 8 words" in looked["sections"]
    assert "'Limits' with at least 4 words" in looked["sections"]
    assert "under 'A sample run'" in looked["run"]
    assert "at least 20 characters" in looked["review"]


def test_a_miss_is_worded_as_the_check_not_finding_it_not_as_the_learner_being_wrong():
    pts = points([R(id="behaviour", met=True), R(id="sections", met=False), R(id="run", met=None), R(id="review", met=True)])
    miss = next(p for p in pts if p.status == "not_met")
    assert miss.found.startswith("The check did not find what it looks for.")
    assert not any(w in miss.found.lower() for w in ("wrong", "bad", "error in your"))



def test_one_point_per_requirement_not_met_first_then_not_checked_then_met():
    pts = points([R(id="behaviour", met=True), R(id="sections", met=True), R(id="run", met=None), R(id="review", met=False)])
    assert [(p.requirement_id, p.status) for p in pts] == [
        ("review", "not_met"), ("run", "not_checked"), ("behaviour", "met"), ("sections", "met")]


def test_the_check_detail_is_the_found_fact_and_where_names_the_section():
    pts = points([R(id="behaviour", met=True), R(id="sections", met=True), R(id="run", met=False, detail="Your script did not print: `Hi`"),
                  R(id="review", met=True)])
    run = next(p for p in pts if p.requirement_id == "run")
    assert run.found.endswith("Your script did not print: `Hi`")
    assert run.where == 'README.md, "A sample run"'
    assert run.why == "README's sample run is real"


def test_missing_sections_are_named_with_word_counts():
    pts = points([R(id="behaviour", met=True), R(id="sections", met=False, detail="x"), R(id="run", met=None), R(id="review", met=True)])
    found = next(p for p in pts if p.requirement_id == "sections").found
    assert "What it does: 12 words (needs 8)" in found
    assert "Limits: missing" in found


def test_review_note_reports_its_length_and_the_minimum():
    pts = points([R(id="behaviour", met=True), R(id="sections", met=True), R(id="run", met=None), R(id="review", met=False)], note="  short ")
    assert next(p for p in pts if p.requirement_id == "review").found.endswith("The note has 5 characters (needs 20).")


def test_a_pointer_is_never_code_or_a_fix():
    pts = points([R(id="behaviour", met=False), R(id="sections", met=False), R(id="run", met=False), R(id="review", met=False)])
    for p in pts:
        assert "```" not in p.look and p.look


def test_same_inputs_give_the_same_points():
    results = [R(id="behaviour", met=True), R(id="sections", met=False), R(id="run", met=None), R(id="review", met=True)]
    assert points(results) == points(results)
