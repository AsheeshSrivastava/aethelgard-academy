"""Quick checks and step diagrams in Explain parts (SPEC-19, ADR-0029)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lms.adapters.curriculum.quick_checks import (
    QUICK_CHECKS_FILE,
    check_explain_blocks,
    load_quick_check_key,
    parse_quick_checks,
    steps_block_problems,
)
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.curriculum_checks import Severity

GOOD = """# Unit

## Cleaning recipes

```quickcheck
id: py-0.4-strip-upper
question: Someone types `  north-01 `. Which line gives `NORTH-01`?
A: `code.upper()`
B: `code.strip().upper()`
C: `code.title()`
```
"""

PILOT_ID = "py-0.4-strip-upper"
# A fixture key, not the real one: the real key lives only in the private answers repo (ADR-0021).
FIXTURE_KEY = {"answer": "C", "why": "Fixture reason."}


def lesson_with(block: str, lang: str = "quickcheck") -> str:
    return f"# Unit\n\n## Part\n\n```{lang}\n{block}\n```\n"


# --- Parsing (SPEC-19 section 3) ---


def test_parses_a_quick_check():
    checks, problems = parse_quick_checks(GOOD)
    assert problems == []
    assert len(checks) == 1
    check = checks[0]
    assert check.id == PILOT_ID
    assert check.question.startswith("Someone types")
    assert check.options == {"A": "`code.upper()`", "B": "`code.strip().upper()`", "C": "`code.title()`"}
    assert check.leaked == []


@pytest.mark.parametrize(
    "block, why",
    [
        ("id: q1\nquestion: Q?\nA: only one", "options"),
        ("id: q1\nquestion: Q?\nA: a\nC: c", "options"),
        ("id: Bad Id\nquestion: Q?\nA: a\nB: b", "id"),
        ("question: Q?\nA: a\nB: b", "id"),
        ("id: q1\nA: a\nB: b", "question"),
        ("id: q1\nquestion: Q?\nA: a\nB: b\nE: e", "key"),
    ],
)
def test_reports_an_invalid_quick_check(block, why):
    checks, problems = parse_quick_checks(lesson_with(block))
    assert checks == []
    assert len(problems) == 1 and why in problems[0]


def test_flags_an_answer_left_in_the_public_block():
    checks, _ = parse_quick_checks(lesson_with("id: q1\nquestion: Q?\nA: a\nB: b\nanswer: B\nwhy: Because."))
    assert checks[0].leaked == ["answer", "why"]


def test_repeated_ids_in_one_unit_are_invalid():
    text = lesson_with("id: q1\nquestion: Q?\nA: a\nB: b") + lesson_with("id: q1\nquestion: R?\nA: a\nB: b")
    checks, problems = parse_quick_checks(text)
    assert [c.id for c in checks] == ["q1"]
    assert any("repeated" in p for p in problems)


# --- Steps blocks (SPEC-19 section 2) ---


def test_a_valid_steps_block_has_no_problems():
    block = 'caption: A desk.\n\ntitle: Take in\ncode: input("Name: ")\nresult: "  meera "\nnote: Text.\n\ntitle: Send out\ncode: print(name)'
    assert steps_block_problems(block) == []


@pytest.mark.parametrize(
    "block, why",
    [
        ("title: Only one", "2 to 5"),
        ("\n".join(f"title: Step {n}" for n in range(6)), "2 to 5"),
        ("code: x\ntitle: A\ntitle: B", "title"),
        ("title: A\ntitle: B\ncolour: red", "key"),
        ("caption: one\ncaption: two\ntitle: A\ntitle: B", "caption"),
    ],
)
def test_reports_an_invalid_steps_block(block, why):
    problems = steps_block_problems(block)
    assert problems and why in problems[0]


# --- Private keys and curriculum findings ---


def write_key(answers: Path, keys: dict, unit: str = "py-0.4", course: str = "python") -> None:
    folder = answers / course / unit
    folder.mkdir(parents=True, exist_ok=True)
    (folder / QUICK_CHECKS_FILE).write_text(json.dumps(keys), encoding="utf-8")


def write_lesson(curriculum: Path, text: str, unit: str = "py-0.4") -> None:
    folder = curriculum / "python" / unit
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "lesson.md").write_text(text, encoding="utf-8")


def test_loads_a_key_from_the_answers_folder(tmp_path):
    write_key(tmp_path, {PILOT_ID: FIXTURE_KEY})
    key = load_quick_check_key(tmp_path, "PY-0.4", PILOT_ID)
    assert key is not None and key.answer == "C" and key.why == "Fixture reason."
    assert load_quick_check_key(tmp_path, "PY-0.4", "other") is None
    assert load_quick_check_key(None, "PY-0.4", PILOT_ID) is None


def codes(findings):
    return sorted((f.code, f.severity) for f in findings)


def test_findings_for_public_answers_missing_keys_and_bad_blocks(tmp_path):
    curriculum, answers = tmp_path / "curriculum", tmp_path / "answers"
    write_lesson(curriculum, GOOD + lesson_with("id: q2\nquestion: Q?\nA: a\nB: b\nanswer: A") + lesson_with("title: one", "steps"))
    answers.mkdir()

    found = codes(check_explain_blocks(curriculum, answers))
    assert ("quickcheck-answers-public", Severity.ERROR) in found
    assert ("quickcheck-answers-missing", Severity.ERROR) in found
    assert ("explain-steps-invalid", Severity.WARNING) in found


def test_a_missing_key_is_only_a_warning_without_an_answers_folder(tmp_path):
    write_lesson(tmp_path, GOOD)
    assert codes(check_explain_blocks(tmp_path, None)) == [("quickcheck-answers-missing", Severity.WARNING)]


def test_a_key_whose_answer_is_not_an_option_counts_as_missing(tmp_path):
    curriculum, answers = tmp_path / "curriculum", tmp_path / "answers"
    write_lesson(curriculum, GOOD)
    write_key(answers, {PILOT_ID: {"answer": "D", "why": "No such option."}})
    assert codes(check_explain_blocks(curriculum, answers)) == [("quickcheck-answers-missing", Severity.ERROR)]


def test_a_complete_lesson_has_no_findings(tmp_path):
    curriculum, answers = tmp_path / "curriculum", tmp_path / "answers"
    write_lesson(curriculum, GOOD)
    write_key(answers, {PILOT_ID: FIXTURE_KEY})
    assert check_explain_blocks(curriculum, answers) == []


# --- API (SPEC-19 section 4), on the real PY-0.4 pilot ---


@pytest.fixture
def repo():
    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    return repo


@pytest.fixture
def client(repo, tmp_path, monkeypatch):
    write_key(tmp_path / "answers", {PILOT_ID: FIXTURE_KEY})
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    return TestClient(create_app(repo=repo, runner=SubprocessRunner()))


def check(client, choice, unit="PY-0.4", check_id=PILOT_ID):
    return client.post(f"/api/v1/units/{unit}/quick-checks/{check_id}", json={"choice": choice})


def test_a_right_choice_gets_the_why(client):
    response = check(client, "C")
    assert response.status_code == 200
    assert response.json() == {"correct": True, "why": "Fixture reason."}


def test_a_wrong_choice_does_not_reveal_the_answer(client):
    response = check(client, "A")
    assert response.status_code == 200
    assert response.json() == {"correct": False, "why": None}


def test_a_choice_that_is_not_an_option_is_rejected(client):
    assert check(client, "D").status_code == 422
    assert check(client, "b").status_code == 422


def test_unknown_unit_or_check_is_not_found(client):
    assert check(client, "B", unit="PY-99.9").status_code == 404
    assert check(client, "B", check_id="no-such-check").status_code == 404


def test_no_key_means_not_available(repo, tmp_path, monkeypatch):
    (tmp_path / "empty").mkdir()
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "empty"))
    client = TestClient(create_app(repo=repo, runner=SubprocessRunner()))
    response = check(client, "B")
    assert response.status_code == 503
    assert response.json()["title"] == "Quick check not available"


def test_quick_checks_write_no_evidence(client, repo):
    check(client, "A")
    check(client, "C")
    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []
