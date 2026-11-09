"""README work on a build (SPEC-15 section 9, ADR-0028): the sample run check, the review note,
the AXIS draft and the course map for stages with no build."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers.router import DraftFailed
from lms.adapters.curriculum.builds import load_builds
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.builds import StageBuildSpec, check_requirements
from test_stage_build import (
    BUILD,
    FOLDER,
    ME,
    NOTE,
    REVIEW,
    T0,
    EXERCISE,
    pass_cold_checks,
)

DRAFT = f"{ME}/build:draft-readme"

# A small script of our own, with a prompt, a typed answer and a line that starts like the prompt.
SCRIPT = (
    'name = input("Name: ")\n'
    'print("Hello")\n'
    'print(f"Name: {name.strip().title()}")\n'
    'print("Bye")\n'
)
GOOD_RUN = "Name:   ada \n\nHello\nName: Ada\nBye"


def readme(run):
    return f"## A sample run\n\n```\n{run}\n```\n"


def spec():
    raw = json.loads((FOLDER / "build.json").read_text(encoding="utf-8"))
    raw["requirements"] = [
        {"id": "sample", "label": "s", "unit_id": "PY-0.4", "check": {"kind": "behaviour", "function": "check_sample_run"}},
        {"id": "run", "label": "r", "unit_id": "PY-0.4",
         "check": {"kind": "readme_sample_run", "path": "README.md", "heading": "A sample run"}},
        {"id": "review", "label": "n", "unit_id": "PY-0.4", "check": {"kind": "review_note", "min_chars": 20}},
    ]
    return StageBuildSpec.model_validate({**raw, "checks_source": "def check_sample_run():\n    pass\n"})


def run_check(files, runner=None, run_checks=True):
    results = check_requirements(spec(), files, "", runner or SubprocessRunner(), run_checks)
    return next(r for r in results if r.id == "run")


# --- readme_sample_run ---


def test_a_real_sample_run_is_met():
    result = run_check({"checkin.py": SCRIPT, "README.md": readme(GOOD_RUN)})

    assert (result.met, result.detail) == (True, None)


def test_a_run_that_is_not_in_a_code_block_is_not_met():
    result = run_check({"checkin.py": SCRIPT, "README.md": "## A sample run\n\nName: ada\nHello\n"})

    assert result.met is False
    assert result.detail == "Paste one real run inside a code block under 'A sample run'."


def test_a_missing_section_is_not_met():
    result = run_check({"checkin.py": SCRIPT, "README.md": "## Limits\n\nNothing here at all.\n"})

    assert result.met is False and "code block" in result.detail


def test_the_first_line_the_script_did_not_print_is_named():
    result = run_check({"checkin.py": SCRIPT, "README.md": readme("Name: ada\nHello\nName: ADA\nBye")})

    assert result.met is False
    assert result.detail == "Your script did not print: `Name: ADA`"


def test_lines_must_come_in_order():
    result = run_check({"checkin.py": SCRIPT, "README.md": readme("Name: ada\nBye\nHello")})

    assert result.met is False and result.detail == "Your script did not print: `Hello`"


def test_a_script_error_is_a_plain_message():
    broken = 'name = input("Name: ")\nprint(1 / 0)\n'

    result = run_check({"checkin.py": broken, "README.md": readme("Name: ada\nHello")})

    assert result.met is False
    assert result.detail == "The script stopped before the sample run finished."


def test_asking_for_more_than_the_run_shows_stops_the_script():
    more = 'a = input("Name: ")\nb = input("Age: ")\nprint(a, b)\n'

    result = run_check({"checkin.py": more, "README.md": readme("Name: ada\nada")})

    assert result.met is False and "stopped" in result.detail


def test_a_run_with_no_typed_line_is_not_met():
    result = run_check({"checkin.py": SCRIPT, "README.md": readme("Hello\nBye")})

    assert result.met is False and "what you typed" in result.detail


def test_a_run_with_no_output_line_is_not_met():
    result = run_check({"checkin.py": SCRIPT, "README.md": readme("Name: ada")})

    assert result.met is False and "printed" in result.detail


def test_a_script_with_no_prompt_text_has_no_typed_line():
    result = run_check({"checkin.py": "print(input())\n", "README.md": readme("ada\nada")})

    assert result.met is False and "what you typed" in result.detail


def test_a_syntax_error_is_reported_not_raised():
    result = run_check({"checkin.py": "name = (\n", "README.md": readme(GOOD_RUN)})

    assert result.met is False and "syntax error" in result.detail


def test_the_sample_run_runs_code_so_typing_leaves_it_unchecked():
    class Boom:
        def execute(self, *args, **kwargs):
            raise AssertionError("no code may run while the learner types")

    result = run_check({"checkin.py": SCRIPT, "README.md": readme(GOOD_RUN)}, runner=Boom(), run_checks=False)

    assert result.met is None


def test_prompts_are_read_from_the_code_without_running_it():
    guarded = 'import os\nos._exit(3)\nname = input("Name: ")\n'

    result = run_check({"checkin.py": guarded, "README.md": readme("Name: ada\nHello")})

    assert result.met is False  # it was run, and stopped; reading the prompts did not need a run


# --- review_note ---


def review(note):
    results = check_requirements(spec(), {"checkin.py": SCRIPT, "README.md": ""}, "", None, False, note)
    return next(r for r in results if r.id == "review")


def test_a_review_note_of_enough_characters_is_met():
    assert review(REVIEW).met is True


@pytest.mark.parametrize("note", [None, "", "short", " " * 40])
def test_a_missing_short_or_blank_review_note_is_not_met(note):
    assert review(note).met is False


# --- build.json ---


def test_the_build_loads_with_the_five_readme_headings_and_no_findings():
    builds, problems = load_builds(Path("curriculum"), None)

    assert [p.code for p in problems] == ["build-practice-checks"]
    build = builds[("python", 0)]
    starter = next(f for f in build.files if f.path == "README.md").starter
    headings = [line[3:] for line in starter if line.startswith("## ")]
    assert headings == ["What it does", "What you need first", "How to run it", "A sample run", "Limits"]
    kinds = {r.id: r.check.kind for r in build.requirements}
    assert kinds["readme-sections"] == "markdown_sections"
    assert kinds["readme-run"] == "markdown_sections"
    assert kinds["readme-sample"] == "readme_sample_run"
    assert kinds["review"] == "review_note"
    assert not {"readme-does", "readme-checked"} & set(kinds)


# --- The API ---


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


def make_client(repo, catalog, axis=None):
    return TestClient(
        create_app(repo=repo, runner=SubprocessRunner(), axis=axis or MockAxisCompanion(), catalog=catalog, clock=lambda: T0)
    )


@pytest.fixture
def client(repo, catalog):
    return make_client(repo, catalog)


def test_the_draft_is_locked_until_the_build_opens(client):
    res = client.post(DRAFT, json={"files": {}})

    assert res.status_code == 423


def test_an_unknown_stage_has_no_draft(client):
    assert client.post("/api/v1/learners/me/courses/python/stages/99/build:draft-readme", json={"files": {}}).status_code == 404


def test_the_mock_draft_has_the_five_headings_the_real_entry_and_the_paste_placeholder(client, repo):
    pass_cold_checks(repo)

    res = client.post(DRAFT, json={"files": {"checkin.py": "name = input('Name: ')\n"}})

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "drafted"
    assert body["model"]
    headings = [line[3:] for line in body["markdown"].splitlines() if line.startswith("## ")]
    assert headings == ["What it does", "What you need first", "How to run it", "A sample run", "Limits"]
    assert "uv run checkin.py" in body["markdown"]
    assert "(paste a real run here)" in body["markdown"]


def test_the_draft_is_logged_as_a_document_draft_and_is_not_help_on_the_build(client, repo):
    pass_cold_checks(repo)
    client.get(BUILD)

    client.post(DRAFT, json={"files": {}})

    events = [e for e in repo.get_interactions(LOCAL_LEARNER_ID) if e.event_type == "document_draft"]
    assert len(events) == 1
    assert events[0].payload["course_id"] == "python" and events[0].payload["stage"] == 0
    assert events[0].item_id is None and events[0].activity is None
    assert EXERCISE not in json.dumps(events[0].payload)
    served = repo.get_current_exercise(LOCAL_LEARNER_ID, "python/stage-0", "build").served_at
    assert repo.get_assistance_levels(LOCAL_LEARNER_ID, EXERCISE, served) == []


def test_a_failed_draft_is_a_plain_error_and_nothing_is_filled_in(repo, catalog):
    class Failing(MockAxisCompanion):
        def draft_readme(self, entry, code, brief):
            raise DraftFailed("AXIS could not draft the README right now.")

    client = make_client(repo, catalog, Failing())
    pass_cold_checks(repo)

    res = client.post(DRAFT, json={"files": {}})

    assert res.status_code == 502
    assert res.json()["detail"] == "AXIS could not draft the README right now."
    assert "markdown" not in res.json()


def test_a_companion_that_cannot_draft_says_so(repo, catalog):
    class NoDrafts:
        pass

    client = make_client(repo, catalog, NoDrafts())
    pass_cold_checks(repo)

    assert client.post(DRAFT, json={"files": {}}).status_code == 503


def test_an_oversized_draft_request_is_refused(client, repo):
    pass_cold_checks(repo)

    assert client.post(DRAFT, json={"files": {"checkin.py": "#" * 300_000}}).status_code == 413


def test_the_draft_request_takes_only_files(client, repo):
    pass_cold_checks(repo)

    assert client.post(DRAFT, json={"files": {}, "exercise_id": EXERCISE}).status_code == 422


def test_the_review_note_is_checked_on_check_and_stored_with_the_attempt(client, repo):
    pass_cold_checks(repo)
    files = {"checkin.py": "# a\n# b\n# c\n", "README.md": ""}

    body = {"files": files, "ownership_note": NOTE, "run_checks": False}
    without = {r["id"]: r["met"] for r in client.post(f"{ME}/build:check", json=body).json()["requirements"]}
    with_note = {r["id"]: r["met"] for r in client.post(f"{ME}/build:check", json={**body, "review_note": REVIEW}).json()["requirements"]}

    assert without["review"] is False and with_note["review"] is True


def test_the_review_note_can_be_saved_in_the_draft(client, repo):
    pass_cold_checks(repo)
    url = f"/api/v1/learners/me/drafts/{EXERCISE}"

    assert client.put(url, json={"files": {"review-note.txt": "I fixed the command"}}).status_code == 204
    assert client.get(url).json()["files"]["review-note.txt"] == "I fixed the command"


def test_an_oversized_review_note_is_refused(client, repo):
    pass_cold_checks(repo)

    res = client.post(f"{ME}/build:check", json={"files": {}, "review_note": "x" * 300_000})

    assert res.status_code == 413


def test_the_review_note_is_stored_beside_the_ownership_note_on_a_passing_attempt(repo):
    from lms.core.models import ActivityType, AssistanceLevel, EvidenceCategory, EvidenceEntry, EvidenceStrength

    entry = EvidenceEntry(
        learner_id=LOCAL_LEARNER_ID, unit_id="PY-0.4", skill_id="CO-1",
        evidence_category=EvidenceCategory.PERFORM_SOLVE, evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE, demonstration_context="Stage build", observed_reasoning=NOTE,
        review_note=REVIEW, exercise_id=EXERCISE, seed_id=EXERCISE, activity=ActivityType.BUILD,
    )
    repo.record_evidence(entry)

    stored = repo.get_evidence_ledger(LOCAL_LEARNER_ID)[0]

    assert (stored.observed_reasoning, stored.review_note) == (NOTE, REVIEW)


# --- The course map ---


def test_stages_with_no_build_by_design_have_none(client):
    stages = client.get("/api/v1/courses/python").json()["stages"]

    technical_writing = [s for s in stages if s["label"].startswith("TW")]
    assert technical_writing, "the Python course should hold the Technical Writing stages"
    assert all(s["build"] is None for s in technical_writing)
    assert all(s["build"] is not None for s in stages if not s["label"].startswith("TW"))
