"""Tests for stage builds, features and the evidence event (SPEC-15)."""

from datetime import datetime, timedelta, timezone
import json
from functools import cache
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.builds import load_builds
from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.builds import (
    StageBuildSpec,
    check_requirements,
    exercise_id_of,
    parse_exercise_id,
    public_build,
)
from lms.core.events import EVIDENCE_RECORDED, EventBus, EvidenceRecorded, LedgerWriteRefused
from lms.core.exercises import COLD_CHECK, pool_for
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProficiencyLevel,
)
from lms.core.proficiency import qualifies

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
FOLDER = Path("curriculum/python/builds/stage-0")
BUILD = "/api/v1/courses/python/stages/0/build"
ME = "/api/v1/learners/me/courses/python/stages/0"
ATTEMPTS = "/api/v1/learners/me/attempts"
EXERCISE = "python/stage-0/build"
STAGE_0 = ("PY-0.4", "PY-0.1", "PY-0.3")
SOLUTION = (FOLDER / "solution.py").read_text(encoding="utf-8")
NOTE = "I planned it, wrote it, and checked it with messy input myself."
README = "# Build\n\nRun it with python checkin.py\n"


def raw_build():
    return json.loads((FOLDER / "build.json").read_text(encoding="utf-8"))


def spec():
    return StageBuildSpec.model_validate({**raw_build(), "checks_source": (FOLDER / "checks.py").read_text(encoding="utf-8")})


def good_files():
    return {"checkin.py": SOLUTION, "README.md": README}


def met(results):
    return {r.id: r.met for r in results}


class FakeRunner:
    """Says what the sandbox says, and records what it was asked to run."""

    def __init__(self, success=True, print_token=True, stderr=""):
        self.success, self.print_token, self.stderr = success, print_token, stderr
        self.calls = []

    def execute(self, code, test_code=None, timeout_seconds=5.0, stdin_input=None):
        self.calls.append((code, test_code))
        token = test_code.split('print("')[-1].split('"')[0] if self.print_token else ""

        class Result:
            success = self.success
            stdout = token
            stderr = self.stderr
            assertion_errors = []

        return Result()


# --- Loading ---


def test_the_stage_0_build_loads_clean_and_approved():
    builds, problems = load_builds(Path("curriculum"))

    assert problems == []
    build = builds[("python", 0)]
    assert build.status == "approved"
    assert build.entry == "checkin.py"
    assert "check_sample_run" in build.checks_source


def copy_build(tmp_path, change=None, checks="def check_sample_run():\n    pass\n\ndef check_messy_input():\n    pass\n"):
    folder = tmp_path / "python" / "builds" / "stage-0"
    folder.mkdir(parents=True)
    data = raw_build()
    if change:
        change(data)
    (folder / "build.json").write_text(json.dumps(data), encoding="utf-8")
    if checks is not None:
        (folder / "checks.py").write_text(checks, encoding="utf-8")
    return tmp_path


def set_field(name, value):
    return lambda data: data.__setitem__(name, value)


@pytest.mark.parametrize(
    "change, words",
    [
        (set_field("kind", "essay"), "kind"),
        (set_field("status", "finished"), "status"),
        (set_field("surprise", 1), "surprise"),
        (set_field("schema_version", 2), "schema_version"),
        (set_field("entry", "other.py"), "entry"),
        (set_field("stage", 3), "folder"),
        (set_field("course_id", "backend"), "folder"),
        (lambda d: d["files"].append({"path": "../evil.py", "starter": []}), "path"),
        (lambda d: d["requirements"].append(d["requirements"][0]), "unique"),
        (lambda d: d["requirements"][3]["check"].update(function="check_gone"), "check_gone"),
        (lambda d: d["requirements"][5]["check"].update(path="GONE.md"), "GONE.md"),
        (lambda d: d["requirements"][0]["check"].update(kind="vibes"), "kind"),
        (lambda d: d["requirements"].__delitem__(slice(3, 5)), "behaviour"),
    ],
)
def test_a_bad_build_is_reported_and_skipped(tmp_path, change, words):
    builds, problems = load_builds(copy_build(tmp_path, change))

    assert builds == {}
    assert [p.code for p in problems] == ["build-invalid"]
    assert words in problems[0].message


def test_a_build_without_hidden_checks_is_reported(tmp_path):
    builds, problems = load_builds(copy_build(tmp_path, checks=None))

    assert builds == {}
    assert "checks.py" in problems[0].message


def test_a_build_that_is_not_json_is_reported(tmp_path):
    folder = tmp_path / "python" / "builds" / "stage-0"
    folder.mkdir(parents=True)
    (folder / "build.json").write_text("{not json", encoding="utf-8")

    assert [p.code for p in load_builds(tmp_path)[1]] == ["build-invalid"]


def test_the_real_build_has_no_curriculum_findings():
    catalog = load_all_roadmaps(Path("reference"))

    assert [f for f in catalog.findings if f.code.startswith("build-")] == []
    assert ("python", 0) in catalog.builds


def test_a_build_naming_a_unit_outside_its_stage_is_reported():
    from lms.core.builds import check_builds

    catalog = load_all_roadmaps(Path("reference"))
    data = spec().model_dump()
    data["requirements"][0]["unit_id"] = "PY-1.2"
    data["proves"][0]["skill_id"] = "XX-9"
    found = check_builds({("python", 0): StageBuildSpec.model_validate(data)}, catalog.list_all_units())

    assert {f.code for f in found} == {"build-unit-unknown", "build-skill-unknown"}


def test_an_authored_build_counts_for_own():
    from lms.core.curriculum_checks import check_curriculum
    from lms.core.models import TargetSkill, Unit

    unit = Unit(
        unit_id="PY-0.9", title="t", stage=0, concept_line="c", methods=[ActivityType.EXPLAIN],
        target_skills=[TargetSkill(skill_id="CO-1", skill_name="n", goal_level=ProficiencyLevel.OWN)],
    )

    assert "own-needs-stage-build" in [f.code for f in check_curriculum([unit])]
    assert "own-needs-stage-build" not in [f.code for f in check_curriculum([unit], stages_with_build={("python", 0)})]


# --- Exercise ids ---


def test_exercise_ids_go_both_ways():
    assert exercise_id_of("python", 0) == EXERCISE
    assert parse_exercise_id(EXERCISE) == ("python", 0)


@pytest.mark.parametrize("value", ["PY-0.1/predict/v1", "python/stage-x/build", "python/stage-0", "", "a/b/c/d"])
def test_other_exercise_ids_are_not_builds(value):
    assert parse_exercise_id(value) is None


# --- Requirement checks ---


def test_the_reference_solution_meets_everything_in_the_real_sandbox():
    results = check_requirements(spec(), good_files(), NOTE, SubprocessRunner(), run_checks=True)

    assert all(r.met for r in results), [r for r in results if not r.met]


def test_the_starter_meets_none_of_the_code_requirements():
    build = spec()
    files = {f.path: "\n".join(f.starter) for f in build.files}

    results = met(check_requirements(build, files, "", SubprocessRunner(), run_checks=True))

    assert not any(results.values())


def test_behaviour_is_left_unchecked_while_typing_and_runs_no_code():
    runner = FakeRunner()

    results = met(check_requirements(spec(), good_files(), NOTE, runner, run_checks=False))

    assert results["sample"] is None and results["messy"] is None
    assert results["plan"] is True
    assert runner.calls == []


@pytest.mark.parametrize(
    "code",
    [
        "import sys\nsys.exit(0)\n",
        "import os\nos._exit(0)\n",
        "raise SystemExit\n",
        'print("hello")\n',
        "name = input()\nservice = input()\nprint()\nprint('--- CHECK-IN SLIP ---')\nprint('Name: Meera')\nprint('Service: Housing')\nprint('Please wait for the Housing desk.')\n",
        "while True:\n    pass\n",
    ],
)
def test_behaviour_cannot_be_faked(code):
    results = met(check_requirements(spec(), {"checkin.py": code, "README.md": README}, NOTE, SubprocessRunner(), run_checks=True))

    assert results["messy"] is False


def test_a_pass_needs_the_token_as_well_as_success():
    results = met(check_requirements(spec(), good_files(), NOTE, FakeRunner(print_token=False), run_checks=True))

    assert results["sample"] is False


def test_a_pass_needs_success_as_well_as_the_token():
    results = met(check_requirements(spec(), good_files(), NOTE, FakeRunner(success=False), run_checks=True))

    assert results["sample"] is False


def test_a_behaviour_failure_says_why_in_plain_words():
    code = SOLUTION.replace("CHECK-IN SLIP", "SLIP")
    results = check_requirements(spec(), {"checkin.py": code, "README.md": README}, NOTE, SubprocessRunner(), run_checks=True)

    detail = next(r.detail for r in results if r.id == "sample")
    assert detail == "Output line 2 should be '--- CHECK-IN SLIP ---', but it was '--- SLIP ---'."


def test_failure_detail_never_shows_the_harness():
    results = check_requirements(spec(), {"checkin.py": "print(oops)\n", "README.md": README}, NOTE, SubprocessRunner(), run_checks=True)

    detail = next(r.detail for r in results if r.id == "sample")
    assert "Traceback" not in detail and "run_tests" not in detail and "checks" not in detail


def test_a_syntax_error_is_reported_not_raised():
    results = check_requirements(spec(), {"checkin.py": "name = (\n", "README.md": README}, NOTE, FakeRunner(), run_checks=False)

    inputs = next(r for r in results if r.id == "inputs")
    assert inputs.met is False
    assert "syntax error" in inputs.detail.lower()


def test_starter_comments_do_not_count_as_a_plan():
    build = spec()
    starter = "\n".join(build.files[0].starter)
    plan = lambda code: met(check_requirements(build, {"checkin.py": code}, "", FakeRunner(), False))["plan"]

    assert plan(starter + "\n# one\n# two\n") is False
    assert plan(starter + "\n# one\n# two\n# three\n") is True


def test_a_comment_inside_text_is_not_a_comment():
    code = 'x = """\n# one\n# two\n# three\n"""\n'

    assert met(check_requirements(spec(), {"checkin.py": code}, "", FakeRunner(), False))["plan"] is False


def test_only_input_into_a_name_counts():
    code = 'input("a")\nprint(input("b"))\nname = input("c")\n'

    assert met(check_requirements(spec(), {"checkin.py": code}, "", FakeRunner(), False))["inputs"] is False


def test_only_fstrings_inside_print_count():
    code = 'a = f"x"\nb = f"y"\nprint("plain")\nprint(f"z {a}")\n'

    assert met(check_requirements(spec(), {"checkin.py": code}, "", FakeRunner(), False))["fstrings"] is False


def test_input_into_something_other_than_a_name_does_not_count():
    code = 'desk.name = input("a")\ndesk.service = input("b")\n'

    assert met(check_requirements(spec(), {"checkin.py": code}, "", FakeRunner(), False))["inputs"] is False


def test_fstrings_in_other_calls_do_not_count():
    code = 'str(f"a")\nstr(f"b")\n'

    assert met(check_requirements(spec(), {"checkin.py": code}, "", FakeRunner(), False))["fstrings"] is False


def test_a_blank_note_does_not_count():
    assert met(check_requirements(spec(), good_files(), " " * 40, FakeRunner(), False))["note"] is False


def test_missing_files_are_just_unmet():
    results = met(check_requirements(spec(), {}, None, FakeRunner(), False))

    assert results["readme"] is False and results["inputs"] is False


# --- The API ---


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def client(repo, catalog):
    return TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=lambda: T0))


@cache
def cold_exercises():
    return {u: pool_for(s, COLD_CHECK) for u, s in load_all_roadmaps(Path("reference")).seeds.items()}


def pass_cold_checks(repo, units=STAGE_0):
    for unit_id in units:
        repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, unit_id, T0 - timedelta(days=2))
        repo.record_cold_check_attempt(LOCAL_LEARNER_ID, unit_id, True, T0 - timedelta(days=1))
        # A real round serves its items, so no unseen item is left for a stage review.
        for exercise_id in cold_exercises().get(unit_id, []):
            repo.set_current_exercise(LOCAL_LEARNER_ID, unit_id, COLD_CHECK, exercise_id, T0 - timedelta(days=1))


def submit(client, files=None, note=NOTE, **extra):
    return client.post(
        ATTEMPTS,
        json={"exercise_id": EXERCISE, "activity": "build", "files": files or good_files(), "ownership_note": note, **extra},
    )


def check(client, **body):
    return client.post(f"{ME}/build:check", json={"files": good_files(), "ownership_note": NOTE, "run_checks": False, **body})


def test_a_build_is_locked_until_every_unit_passes(client, repo):
    pass_cold_checks(repo, STAGE_0[:2])

    res = client.get(BUILD)

    assert res.status_code == 423
    assert res.headers["content-type"].startswith("application/problem+json")
    assert "PY-0.3" in res.json()["detail"] and "PY-0.4" not in res.json()["detail"]


def test_a_failed_cold_check_keeps_it_locked(client, repo):
    pass_cold_checks(repo, STAGE_0[:2])
    repo.mark_unit_activities_completed(LOCAL_LEARNER_ID, "PY-0.3", T0 - timedelta(days=2))
    repo.record_cold_check_attempt(LOCAL_LEARNER_ID, "PY-0.3", False, T0 - timedelta(days=1))

    assert client.get(BUILD).status_code == 423


def test_check_and_attempts_are_locked_too(client, repo):
    assert check(client).status_code == 423
    assert submit(client).status_code == 423
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_an_unlocked_build_is_served(client, repo):
    pass_cold_checks(repo)

    data = client.get(BUILD).json()

    assert data["exercise_id"] == EXERCISE
    assert data["title"] == "Relief centre check-in script"
    assert data["status"] == "approved"
    assert data["entry"] == "checkin.py"
    assert [f["path"] for f in data["files"]] == ["checkin.py", "README.md"]
    assert data["requirements"][0] == {"id": "plan", "label": "Plan written as comments", "unit_id": "PY-0.1"}
    assert data["submitted"] is False


def test_nothing_hidden_ever_leaves_the_server(client, repo):
    pass_cold_checks(repo)

    text = client.get(BUILD).text

    for secret in ("check_sample_run", "checks_source", "behaviour", "function", '"check"', "Medical Aid", "raw_service"):
        assert secret not in text


def test_public_build_is_built_from_allowed_fields():
    assert set(public_build(spec(), submitted=False).model_dump()) == {
        "exercise_id", "course_id", "stage", "title", "kind", "status", "brief_markdown",
        "sample_run", "entry", "files", "requirements", "proves", "submitted",
    }


@pytest.mark.parametrize("path", ["/api/v1/courses/nope/stages/0/build", "/api/v1/courses/python/stages/99/build"])
def test_an_unknown_stage_is_a_404(client, path):
    assert client.get(path).status_code == 404


def test_an_unlocked_stage_with_no_build_is_a_404(repo, catalog):
    stage_1 = [u.unit_id for u in catalog.get_course_units("python") if u.stage == 1]
    pass_cold_checks(repo, stage_1)
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=catalog, clock=lambda: T0))

    res = client.get("/api/v1/courses/python/stages/1/build")

    assert res.status_code == 404
    assert "not written" in res.json()["detail"]


def test_check_returns_live_results_and_writes_nothing(client, repo):
    pass_cold_checks(repo)

    data = {r["id"]: r["met"] for r in check(client).json()["requirements"]}

    assert data["plan"] is True and data["sample"] is None
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_verify_runs_the_hidden_checks(client, repo):
    pass_cold_checks(repo)

    data = {r["id"]: r["met"] for r in check(client, run_checks=True).json()["requirements"]}

    assert data["sample"] is True and data["messy"] is True


def test_a_passing_submit_writes_one_strong_build_entry_per_skill(client, repo):
    pass_cold_checks(repo)
    client.get(BUILD)

    res = submit(client)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["outcome"] == "passed"
    entries = repo.get_evidence_ledger(LOCAL_LEARNER_ID)
    assert sorted((e.skill_id, e.unit_id) for e in entries) == [
        ("CO-1", "PY-0.4"), ("CO-2", "PY-0.1"), ("DE-3", "PY-0.3"), ("VE-4", "PY-0.4"),
    ]
    for entry in entries:
        assert entry.activity == ActivityType.BUILD
        assert entry.evidence_category == EvidenceCategory.PERFORM_SOLVE
        assert entry.evidence_strength == EvidenceStrength.STRONG
        assert entry.assistance_level == AssistanceLevel.NONE
        assert entry.observed_reasoning == NOTE
        assert entry.seed_id == EXERCISE
        assert entry.exercise_id == EXERCISE
        assert entry.cold_check is False
        assert qualifies(entry, ProficiencyLevel.OWN)


def test_the_build_shows_as_submitted_afterwards(client, repo):
    pass_cold_checks(repo)
    submit(client)

    assert client.get(BUILD).json()["submitted"] is True


def test_a_failed_submit_writes_nothing(client, repo):
    pass_cold_checks(repo)

    res = submit(client, note="short")

    assert res.json()["outcome"] == "failed"
    assert {c["label"]: c["passed"] for c in res.json()["checks"]}["Ownership note written"] is False
    assert res.json().get("evidence_entry_id") is None
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_the_server_checks_again_whatever_the_page_showed(client, repo):
    pass_cold_checks(repo)

    res = submit(client, files={"checkin.py": "# a\n# b\n# c\n", "README.md": README})

    assert res.json()["outcome"] == "failed"


def test_supplied_reasoning_forces_weak(client, repo):
    pass_cold_checks(repo)
    client.get(BUILD)
    repo.log_assistance(LOCAL_LEARNER_ID, EXERCISE, AssistanceLevel.SUPPLIED_REASONING, T0 + timedelta(minutes=1))

    submit(client)

    assert {e.evidence_strength for e in repo.get_evidence_ledger(LOCAL_LEARNER_ID)} == {EvidenceStrength.WEAK}


def test_a_hint_stays_strong_but_does_not_count_for_own(client, repo):
    pass_cold_checks(repo)
    client.get(BUILD)
    repo.log_assistance(LOCAL_LEARNER_ID, EXERCISE, AssistanceLevel.SMALL_HINT, T0 + timedelta(minutes=1))

    submit(client)

    entry = repo.get_evidence_ledger(LOCAL_LEARNER_ID)[0]
    assert entry.evidence_strength == EvidenceStrength.STRONG
    assert entry.assistance_level == AssistanceLevel.SMALL_HINT
    assert not qualifies(entry, ProficiencyLevel.OWN)


@pytest.mark.parametrize("field, value", [("evidence_strength", "Strong"), ("evidence_category", "x"), ("assistance_level", "none")])
def test_a_client_cannot_send_evidence_fields(client, repo, field, value):
    pass_cold_checks(repo)

    assert submit(client, **{field: value}).status_code == 422


def test_a_build_attempt_must_use_the_build_activity(client, repo):
    pass_cold_checks(repo)

    assert client.post(ATTEMPTS, json={"exercise_id": EXERCISE, "activity": "predict", "files": good_files()}).status_code == 422


def test_an_oversized_submit_is_refused(client, repo):
    pass_cold_checks(repo)

    assert submit(client, files={"checkin.py": "#" * 300_000}).status_code == 413
    assert submit(client, note="x" * 300_000).status_code == 413


def test_drafts_work_for_a_build(client, repo):
    pass_cold_checks(repo)
    url = f"/api/v1/learners/me/drafts/{EXERCISE}"

    assert client.put(url, json={"files": {"checkin.py": "x", "ownership-note.txt": "n"}}).status_code == 204
    assert client.get(url).json()["files"]["ownership-note.txt"] == "n"


def test_reset_clears_the_draft_and_keeps_the_ledger(client, repo):
    pass_cold_checks(repo)
    url = f"/api/v1/learners/me/drafts/{EXERCISE}"
    client.put(url, json={"files": {"checkin.py": "x"}})
    submit(client)
    before = len(repo.get_evidence_ledger(LOCAL_LEARNER_ID))

    assert client.post(f"{ME}/build:reset").status_code == 204

    assert client.get(url).json()["files"] == {}
    assert len(repo.get_evidence_ledger(LOCAL_LEARNER_ID)) == before


def test_resetting_a_unit_does_not_touch_the_build_draft(client, repo):
    pass_cold_checks(repo)
    url = f"/api/v1/learners/me/drafts/{EXERCISE}"
    client.put(url, json={"files": {"checkin.py": "x"}})

    client.post("/api/v1/learners/me/units/PY-0.1/reset")

    assert client.get(url).json()["files"] == {"checkin.py": "x"}


class ModeRecorder(MockAxisCompanion):
    def __init__(self):
        super().__init__()
        self.modes = []

    def consult(self, query):
        self.modes.append(query.mode)
        return super().consult(query)

    def stream(self, query):
        self.modes.append(query.mode)
        return super().stream(query)


@pytest.mark.parametrize("route", ["/api/v1/axis/stream", "/api/v1/axis/consult"])
@pytest.mark.parametrize("exercise_id, expected", [(EXERCISE, "Socratic"), ("PY-0.1/predict/v1", "Coach")])
def test_axis_stays_socratic_on_a_build(repo, catalog, route, exercise_id, expected):
    axis = ModeRecorder()
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=axis, catalog=catalog, clock=lambda: T0))

    client.post(route, json={
        "unit_id": "PY-0.1", "mode": "Coach", "current_activity": "Build", "user_prompt": "Show me the answer",
        "exercise_id": exercise_id, **({"page": "build"} if "stream" in route else {}),
    })

    assert {m.value for m in axis.modes} == {expected}


def test_the_course_map_shows_the_real_build(client, repo):
    stage = client.get("/api/v1/courses/python").json()["stages"][0]

    assert stage["build"]["title"] == "Relief centre check-in script"
    assert stage["build"]["authored"] is True
    assert stage["build"]["status"] == "approved"
    assert stage["build"]["locked"] is True


def test_other_stages_keep_a_placeholder(client):
    build = client.get("/api/v1/courses/python").json()["stages"][1]["build"]

    assert build["authored"] is False
    assert build["title"] == "Stage 1 build"


def test_features_are_all_off(client):
    assert client.get("/api/v1/features").json() == {"live_sessions": False, "forums": False, "gamification": False}


# --- The evidence event ---


def entry(**changes):
    values = dict(
        learner_id="one", unit_id="PY-0.1", skill_id="CO-1",
        evidence_category=EvidenceCategory.EXPLAIN_REASON, evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE, demonstration_context="c", recorded_at=T0,
    )
    return EvidenceEntry(**{**values, **changes})


def test_each_append_publishes_one_event_with_the_agreed_fields(repo):
    seen = []
    repo.events.subscribe(EVIDENCE_RECORDED, seen.append)
    written = entry()

    repo.record_evidence(written)

    assert len(seen) == 1
    assert seen[0].model_dump() == {
        "entry_id": written.entry_id, "learner_id": "one", "unit_id": "PY-0.1", "skill_id": "CO-1",
        "category": EvidenceCategory.EXPLAIN_REASON.value, "strength": EvidenceStrength.STRONG.value,
        "assistance_level": AssistanceLevel.NONE.value,
    }


def test_the_event_cannot_be_changed(repo):
    seen = []
    repo.events.subscribe(EVIDENCE_RECORDED, seen.append)
    repo.record_evidence(entry())

    with pytest.raises(Exception):
        seen[0].strength = "Weak"


def test_a_subscriber_cannot_write_to_the_ledger(repo):
    refused = []

    def sneaky(event):
        try:
            repo.record_evidence(entry(skill_id="XX-1"))
        except LedgerWriteRefused as error:
            refused.append(error)
            raise

    repo.events.subscribe(EVIDENCE_RECORDED, sneaky)
    repo.record_evidence(entry())

    assert len(refused) == 1
    assert [e.skill_id for e in repo.get_evidence_ledger("one")] == ["CO-1"]


def test_writing_works_again_once_subscribers_finish(repo):
    repo.events.subscribe(EVIDENCE_RECORDED, lambda event: None)

    repo.record_evidence(entry())
    repo.record_evidence(entry(skill_id="CO-2"))

    assert len(repo.get_evidence_ledger("one")) == 2


def test_a_failing_subscriber_does_not_stop_the_append_or_the_others(repo):
    seen = []

    def broken(event):
        raise RuntimeError("no")

    repo.events.subscribe(EVIDENCE_RECORDED, broken)
    repo.events.subscribe(EVIDENCE_RECORDED, seen.append)
    repo.record_evidence(entry())

    assert len(seen) == 1
    assert len(repo.get_evidence_ledger("one")) == 1


def test_each_repository_has_its_own_bus():
    assert SQLiteLearnerRepository(":memory:").events is not SQLiteLearnerRepository(":memory:").events


def test_the_bus_ignores_events_nobody_wants():
    EventBus().publish("nothing", EvidenceRecorded(
        entry_id="e", learner_id="l", unit_id="u", skill_id="s", category="c", strength="s", assistance_level="a",
    ))
