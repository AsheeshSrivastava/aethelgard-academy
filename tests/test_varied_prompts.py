"""Several concept-check prompts per unit (ADR-0032, SPEC-18 section 1).

Made-up prompts and rubrics only: the unit's config is changed in memory and the rubric file
is written to a temporary answers folder.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.curriculum.loader import load_all_roadmaps
from lms.adapters.curriculum.rubric import check_concept_checks, load_rubric
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.ai_judgement import AiJudgement, IdeaResult
from lms.core.curriculum_checks import Severity
from lms.core.exercises import concept_prompts, explain_exercise

T0 = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)
UNIT = "PY-0.4"
BASE = "/api/v1/learners/me"
PROMPTS = {"prompt": "Made-up prompt one.", "more_prompts": ["Made-up prompt two.", "Made-up prompt three."]}


def ideas(prefix):
    return [{"id": f"{prefix}-a", "text": f"Idea {prefix} A."}, {"id": f"{prefix}-b", "text": f"Idea {prefix} B."}]


def write_answers(answers: Path, variants=("v2", "v3")):
    folder = answers / "python" / "py-0.4"
    folder.mkdir(parents=True, exist_ok=True)
    data = {"unit_id": UNIT, "ideas": ideas("one"), "variants": {v: {"ideas": ideas(v)} for v in variants}}
    (folder / "concept_check.json").write_text(json.dumps(data), encoding="utf-8")


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now

    def advance(self, delta=HOUR):
        self.now += delta


class Judge:
    """Records the prompt and rubric it was given, and judges every idea met."""

    def __init__(self):
        self.calls = []

    def judge_explanation(self, unit_id, prompt, explanation, rubric):
        self.calls.append((prompt, rubric))
        return AiJudgement(
            status="judged", verdict="Solid", model="fake", feedback="Clear.",
            ideas=[IdeaResult(id=i.id, text=i.text, met=True) for i in rubric.ideas],
        )

    def consult(self, query):  # pragma: no cover - not used
        raise AssertionError


@pytest.fixture(scope="module")
def catalog():
    return load_all_roadmaps(Path("reference"))


@pytest.fixture
def three_prompts(catalog):
    unit = catalog.get_unit(UNIT)
    original = unit.concept_check_config
    unit.concept_check_config = dict(PROMPTS)
    yield unit
    unit.concept_check_config = original


@pytest.fixture
def answers(tmp_path, monkeypatch):
    write_answers(tmp_path / "answers")
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    return tmp_path / "answers"


@pytest.fixture
def repo():
    r = SQLiteLearnerRepository(db_path=":memory:")
    r.initialize()
    return r


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def judge():
    return Judge()


@pytest.fixture
def client(repo, catalog, clock, judge, three_prompts, answers):
    return TestClient(create_app(repo=repo, runner=SubprocessRunner(), axis=judge, catalog=catalog, clock=clock))


def served(client):
    res = client.get(f"{BASE}/units/{UNIT}/activities/explain/exercise")
    assert res.status_code == 200, res.text
    return res.json()


def explain(client, exercise_id=None, unit=UNIT):
    body = {"unit_id": unit, "explanation": "Because made-up reasons."}
    if exercise_id is not None:
        body["exercise_id"] = exercise_id
    return client.post("/api/v1/explain", json=body)


def answer_served(client, clock):
    exercise = served(client)
    assert explain(client, exercise["exercise_id"]).status_code == 200
    clock.advance()
    return exercise["exercise_id"]


# --- Serving ---


def test_a_new_learner_is_served_v1(client):
    body = served(client)

    assert body["exercise_id"] == f"{UNIT}/explain/v1" and body["prompt_markdown"] == "Made-up prompt one."


def test_the_next_prompt_follows_each_answer(client, clock):
    assert [answer_served(client, clock) for _ in range(3)] == [f"{UNIT}/explain/v{n}" for n in (1, 2, 3)]


def test_when_all_are_answered_the_oldest_answer_comes_first(client, clock):
    for _ in range(3):
        answer_served(client, clock)

    assert served(client)["exercise_id"] == f"{UNIT}/explain/v1"
    answer_served(client, clock)
    assert served(client)["exercise_id"] == f"{UNIT}/explain/v2"


def test_a_reset_makes_v1_fresh_again(client, repo, clock):
    answer_served(client, clock)
    answer_served(client, clock)
    assert served(client)["exercise_id"].endswith("/v3")

    repo.reset_unit(LOCAL_LEARNER_ID, UNIT, clock())
    clock.advance()

    assert served(client)["exercise_id"].endswith("/v1")


def test_a_prompt_that_was_not_judged_is_not_answered(client, answers):
    """No evidence entry, so the prompt is served again."""
    (answers / "python" / "py-0.4" / "concept_check.json").unlink()
    explain(client, f"{UNIT}/explain/v1")

    assert served(client)["exercise_id"].endswith("/v1")


def test_old_rows_without_an_id_count_as_v1(three_prompts):
    from test_concept_check_counts_once import check

    old = check(exercise_id=None, unit_id=UNIT)

    assert explain_exercise(three_prompts, [old]).exercise_id == f"{UNIT}/explain/v2"


def test_without_history_the_exercise_is_v1(three_prompts):
    assert explain_exercise(three_prompts).exercise_id == f"{UNIT}/explain/v1"


def test_no_prompt_means_no_exercise(three_prompts):
    three_prompts.concept_check_config = {"more_prompts": ["Orphan."]}

    assert explain_exercise(three_prompts) is None


def test_prompts_are_capped_at_three_and_cleaned():
    assert concept_prompts({"prompt": "a", "more_prompts": ["b", "", 5, "c", "d"]}) == ["a", "b", "c"]
    assert concept_prompts({"prompt": "a", "more_prompts": "nope"}) == ["a"]
    assert concept_prompts(None) == []


def test_the_public_unit_never_carries_the_other_prompts(client):
    config = client.get(f"/api/v1/units/{UNIT}").json()["concept_check_config"]

    assert config == {"prompt": "Made-up prompt one."}


# --- Answering ---


def test_an_answer_to_v2_is_judged_with_the_v2_prompt_and_rubric(client, repo, judge):
    res = explain(client, f"{UNIT}/explain/v2")

    assert res.status_code == 200 and res.json()["evidence_logged"] is True
    prompt, rubric = judge.calls[0]
    assert prompt == "Made-up prompt two." and [i.id for i in rubric.ideas] == ["v2-a", "v2-b"]
    [entry] = repo.get_evidence_ledger(LOCAL_LEARNER_ID)
    assert entry.exercise_id == f"{UNIT}/explain/v2"


def test_a_missing_id_means_v1(client, repo, judge):
    explain(client)

    prompt, rubric = judge.calls[0]
    assert prompt == "Made-up prompt one." and [i.id for i in rubric.ideas] == ["one-a", "one-b"]
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID)[0].exercise_id == f"{UNIT}/explain/v1"


@pytest.mark.parametrize(
    "bad", [f"{UNIT}/explain/v4", f"{UNIT}/explain/v0", "PY-0.1/explain/v1", f"{UNIT}/predict-1/v1", "nonsense"]
)
def test_an_id_that_is_not_a_prompt_of_the_unit_is_422(client, repo, judge, bad):
    res = explain(client, bad)

    assert res.status_code == 422
    assert res.headers["content-type"].startswith("application/problem+json")
    assert judge.calls == [] and repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_a_unit_with_one_prompt_refuses_v2(client, three_prompts):
    three_prompts.concept_check_config = {"prompt": "Only one."}

    assert explain(client, f"{UNIT}/explain/v2").status_code == 422
    assert explain(client, f"{UNIT}/explain/v1").status_code == 200


def test_a_prompt_without_a_rubric_is_not_judged_and_writes_nothing(client, repo, judge, answers):
    write_answers(answers, variants=("v3",))

    body = explain(client, f"{UNIT}/explain/v2").json()

    assert body["status"] == "not_judged" and body["reason"] == "no_rubric"
    assert judge.calls == [] and repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_two_prompts_count_as_two_pieces_of_evidence_but_a_repeat_counts_once(client, repo):
    from lms.core.proficiency import estimate_skill

    for exercise_id in (f"{UNIT}/explain/v1", f"{UNIT}/explain/v2", f"{UNIT}/explain/v2"):
        explain(client, exercise_id)

    assert len(estimate_skill(repo.get_evidence_ledger(LOCAL_LEARNER_ID), "CO-6").qualifying_entry_ids) == 2


def test_the_event_log_names_the_prompt(client, repo):
    explain(client, f"{UNIT}/explain/v3")

    [event] = [e for e in repo.get_interactions(LOCAL_LEARNER_ID) if e.event_type == "concept_check"]
    assert event.payload["exercise_id"] == f"{UNIT}/explain/v3"


# --- Rubric files and findings ---


def test_the_rubric_of_each_prompt_is_loaded(tmp_path):
    write_answers(tmp_path)

    assert [i.id for i in load_rubric(tmp_path, UNIT).ideas] == ["one-a", "one-b"]
    assert [i.id for i in load_rubric(tmp_path, UNIT, 2).ideas] == ["v2-a", "v2-b"]
    assert load_rubric(tmp_path, UNIT, 4) is None


def test_a_bad_variant_leaves_the_others_usable(tmp_path):
    write_answers(tmp_path)
    path = tmp_path / "python" / "py-0.4" / "concept_check.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["variants"]["v2"] = {"ideas": [{"id": "only", "text": "one idea"}]}
    path.write_text(json.dumps(data), encoding="utf-8")

    assert load_rubric(tmp_path, UNIT, 2) is None
    assert load_rubric(tmp_path, UNIT, 3) is not None and load_rubric(tmp_path, UNIT, 1) is not None


def write_meta(curriculum: Path, concept_check):
    folder = curriculum / "python" / "py-0.4"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meta.json").write_text(json.dumps({"unit_id": UNIT, "concept_check": concept_check}), encoding="utf-8")


def test_each_prompt_without_a_rubric_is_its_own_warning(tmp_path):
    write_meta(tmp_path / "c", PROMPTS)
    write_answers(tmp_path / "a", variants=("v3",))

    found = check_concept_checks(tmp_path / "c", tmp_path / "a")

    assert [f.code for f in found] == ["concept-check-rubric-missing"]
    assert found[0].severity == Severity.WARNING and f"{UNIT}/explain/v2" in found[0].message


def test_no_rubric_file_warns_for_every_prompt(tmp_path):
    write_meta(tmp_path / "c", PROMPTS)
    (tmp_path / "a").mkdir()

    found = check_concept_checks(tmp_path / "c", tmp_path / "a")

    assert [f.message.split(" ")[0] for f in found] == [f"{UNIT}/explain/v{n}" for n in (1, 2, 3)]


def test_all_prompts_with_rubrics_have_no_findings(tmp_path):
    write_meta(tmp_path / "c", PROMPTS)
    write_answers(tmp_path / "a")

    assert check_concept_checks(tmp_path / "c", tmp_path / "a") == []


def test_more_than_three_prompts_is_an_error(tmp_path):
    write_meta(tmp_path / "c", {"prompt": "One.", "more_prompts": ["Two.", "Three.", "Four."]})
    write_answers(tmp_path / "a")

    [found] = [f for f in check_concept_checks(tmp_path / "c", tmp_path / "a") if f.code == "concept-check-too-many-prompts"]

    assert found.severity == Severity.ERROR and found.unit_id == UNIT


@pytest.mark.parametrize("bad", ["Two.", [""], [5]])
def test_more_prompts_must_be_a_list_of_texts(tmp_path, bad):
    write_meta(tmp_path / "c", {"prompt": "One.", "more_prompts": bad})
    write_answers(tmp_path / "a")

    codes = [f.code for f in check_concept_checks(tmp_path / "c", tmp_path / "a")]

    assert "concept-check-bad-prompts" in codes


@pytest.mark.parametrize("field", ["rubric", "solid_keywords", "ideas", "variants"])
def test_a_public_rubric_or_variants_is_still_an_error(tmp_path, field):
    write_meta(tmp_path / "c", {**PROMPTS, field: ["x"]})
    write_answers(tmp_path / "a")

    [found] = [f for f in check_concept_checks(tmp_path / "c", tmp_path / "a") if f.code == "concept-check-answers-public"]

    assert found.severity == Severity.ERROR
