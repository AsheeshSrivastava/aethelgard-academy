"""Tests for private seed answers (ADR-0021 amendment 2026-11-04, SPEC-13)."""

import json
from pathlib import Path


from lms.adapters.curriculum.builds import answers_dir_from_env
from lms.adapters.curriculum.loader import load_seeds
from lms.core.exercises import HIDDEN_REQUIRED, PRIVATE_FIELDS, public_and_private

REPO = Path(__file__).resolve().parents[1]


def full_seed(stem="cold-predict-1", unit="PY-0.1"):
    return {
        "schema_version": 2,
        "seed_id": f"{unit}/{stem}",
        "unit_id": unit,
        "activity": "Predict",
        "skill_id": "CO-1",
        "level": "Understand",
        "prompt_markdown": ["What prints?"],
        "cold_check_eligible": True,
        "curator_approved": True,
        "predict": {
            "code": ["print(1)"],
            "stdin": "",
            "options": [{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
            "answer_key": "A",
            "why": ["It prints 1."],
        },
    }


def write(folder: Path, unit: str, stem: str, data: dict) -> None:
    path = folder / "python" / unit.lower() / "exercises" / f"{stem}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


# --- Splitting ---


def test_a_seed_splits_into_a_public_and_a_private_half():
    public, private = public_and_private(full_seed())

    assert "answer_key" not in public["predict"] and "why" not in public["predict"]
    assert public["predict"]["options"]
    assert private == {"seed_id": "PY-0.1/cold-predict-1", "predict": {"answer_key": "A", "why": ["It prints 1."]}}


def test_every_hidden_field_is_private():
    hidden = {field for fields in HIDDEN_REQUIRED.values() for field in fields} | {"line_states"}

    assert hidden <= PRIVATE_FIELDS


# --- Loading ---


def test_the_loader_joins_the_two_halves(tmp_path):
    public, private = public_and_private(full_seed())
    write(tmp_path / "curriculum", "PY-0.1", "cold-predict-1", public)
    write(tmp_path / "answers", "PY-0.1", "cold-predict-1", private)

    seeds, problems = load_seeds(tmp_path / "curriculum", tmp_path / "answers")

    assert problems == []
    assert seeds["PY-0.1"][0].body["answer_key"] == "A"


def test_a_seed_without_its_private_half_is_skipped_loudly(tmp_path):
    public, _ = public_and_private(full_seed())
    write(tmp_path / "curriculum", "PY-0.1", "cold-predict-1", public)
    (tmp_path / "answers").mkdir()

    seeds, problems = load_seeds(tmp_path / "curriculum", tmp_path / "answers")

    assert seeds == {}
    assert [p.code for p in problems] == ["seed-answers-missing"]
    assert "PY-0.1/cold-predict-1" in problems[0].message


def test_with_no_answers_folder_every_seed_with_answers_is_skipped_loudly(tmp_path):
    public, _ = public_and_private(full_seed())
    write(tmp_path / "curriculum", "PY-0.1", "cold-predict-1", public)

    seeds, problems = load_seeds(tmp_path / "curriculum", None)

    assert seeds == {}
    assert [p.code for p in problems] == ["seed-answers-missing"]


def test_a_public_file_holding_an_answer_is_refused(tmp_path):
    write(tmp_path / "curriculum", "PY-0.1", "cold-predict-1", full_seed())
    _, private = public_and_private(full_seed())
    write(tmp_path / "answers", "PY-0.1", "cold-predict-1", private)

    seeds, problems = load_seeds(tmp_path / "curriculum", tmp_path / "answers")

    assert seeds == {}
    assert [p.code for p in problems] == ["seed-answers-public"]


def test_a_private_half_for_another_seed_is_refused(tmp_path):
    public, private = public_and_private(full_seed())
    write(tmp_path / "curriculum", "PY-0.1", "cold-predict-1", public)
    write(tmp_path / "answers", "PY-0.1", "cold-predict-1", {**private, "seed_id": "PY-0.1/other"})

    seeds, problems = load_seeds(tmp_path / "curriculum", tmp_path / "answers")

    assert seeds == {}
    assert [p.code for p in problems] == ["seed-answers-missing"]


# --- Where the answers are ---


def test_the_variable_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path))

    assert answers_dir_from_env() == tmp_path


def test_without_the_variable_the_sibling_folder_is_used(monkeypatch):
    monkeypatch.delenv("LMS_ANSWERS_DIR", raising=False)
    sibling = REPO.parent / "lms-answers"

    assert answers_dir_from_env() == (sibling if sibling.is_dir() else None)


# --- Playground practice checks (decision 3.2, 2026-11-04) ---


def test_practice_checks_are_read_from_the_answers_folder(tmp_path):
    from lms.adapters.curriculum.loader import CurriculumCatalog, overlay_curriculum_packages
    from lms.core.models import ActivityType, Unit

    catalog = CurriculumCatalog()
    catalog.add_unit(Unit(unit_id="PY-0.1", title="t", stage=0, concept_line="c", target_skills=[], methods=[ActivityType.EXPLAIN]))
    (tmp_path / "curriculum" / "python" / "py-0.1").mkdir(parents=True)
    private = tmp_path / "answers" / "python" / "py-0.1"
    private.mkdir(parents=True)
    (private / "test_solution.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    overlay_curriculum_packages(catalog, tmp_path / "curriculum", tmp_path / "answers")

    assert catalog.get_unit("PY-0.1").test_code == "def test_x():\n    pass\n"


def test_without_the_answers_folder_a_unit_has_no_practice_checks(tmp_path):
    from lms.adapters.curriculum.loader import CurriculumCatalog, overlay_curriculum_packages
    from lms.core.models import ActivityType, Unit

    catalog = CurriculumCatalog()
    catalog.add_unit(Unit(unit_id="PY-0.1", title="t", stage=0, concept_line="c", target_skills=[], methods=[ActivityType.EXPLAIN]))
    (tmp_path / "curriculum" / "python" / "py-0.1").mkdir(parents=True)

    overlay_curriculum_packages(catalog, tmp_path / "curriculum", None)

    assert catalog.get_unit("PY-0.1").test_code is None


def test_no_public_unit_holds_practice_checks():
    assert sorted(str(p.relative_to(REPO)) for p in (REPO / "curriculum").glob("*/*/test_solution.py")) == []


# --- The guard on the public tree ---


def test_no_public_seed_file_holds_an_answer():
    leaks = []
    for path in sorted((REPO / "curriculum").glob("*/*/exercises/*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for block in (v for v in raw.values() if isinstance(v, dict)):
            leaks += [f"{path.relative_to(REPO)}: {field}" for field in PRIVATE_FIELDS & set(block)]

    assert leaks == []


def test_no_public_lesson_holds_a_quick_check_answer():
    """SPEC-19 section 3: a quickcheck block in lesson.md never holds `answer` or `why`."""
    from lms.adapters.curriculum.quick_checks import parse_quick_checks

    leaks = []
    for path in sorted((REPO / "curriculum").glob("*/*/lesson.md")):
        checks, _ = parse_quick_checks(path.read_text(encoding="utf-8"))
        leaks += [f"{path.relative_to(REPO)}: {check.id} {field}" for check in checks for field in check.leaked]

    assert leaks == []


# --- The made-up test items (A0, 2026-11-11) ---


def test_the_test_fixtures_hold_only_made_up_items():
    """Answer-shaped files under tests/fixtures are allowed only for made-up items, never real ones."""
    fixtures = REPO / "tests" / "fixtures"
    public = sorted((fixtures / "curriculum").glob("*/*/exercises/*.json"))
    assert public
    for seed_file in public:
        seed = json.loads(seed_file.read_text(encoding="utf-8"))
        assert seed["prompt_markdown"][0].startswith("Made-up test item"), seed_file
    private = {p.relative_to(fixtures / "answers") for p in (fixtures / "answers").glob("*/*/exercises/*.json")}
    assert private == {p.relative_to(fixtures / "curriculum") for p in public}
