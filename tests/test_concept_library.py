"""Tests for the Concept Library (SPEC-14)."""

from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.concepts import ConceptCatalog, load_concepts
from lms.adapters.curriculum.loader import CurriculumCatalog, load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.api.app import LOCAL_LEARNER_ID, create_app
from lms.core.concepts import check_concept_links, rank_concepts, used_in, wiki_links
from lms.core.curriculum_checks import Severity
from lms.core.models import ConceptItem, ConceptStatus, Unit

BASE = "/api/v1/concepts"
RECENT = "/api/v1/learners/me/concepts/recent"


def concept(slug, title=None, summary="s", body="b", aliases=(), units=(), related=()):
    return ConceptItem(
        concept_id=slug,
        name=title or slug.title(),
        category="c",
        summary=summary,
        status=ConceptStatus.DRAFT,
        content_markdown=body,
        aliases=list(aliases),
        units=list(units),
        related=list(related),
    )


def unit(unit_id="PY-0.1", lesson=None):
    return Unit(
        unit_id=unit_id, title=f"Title of {unit_id}", stage=0, concept_line="c", methods=[], target_skills=[], lesson_markdown=lesson,
    )


def note(
    slug="variables",
    title="Variables",
    extra="",
    body="A body.",
    status="draft",
):
    return (
        f"---\nid: {slug}\ntitle: {title}\ncategory: State\nsummary: A short line.\n"
        f"status: {status}\n{extra}---\n\n{body}\n"
    )


def write(folder, name, text):
    folder.mkdir(exist_ok=True)
    (folder / f"{name}.md").write_text(text, encoding="utf-8")


# --- Loading ---


def test_a_good_note_loads_with_all_its_fields(tmp_path):
    write(
        tmp_path,
        "variables",
        note(
            extra=(
                'units: ["PY-0.1"]\nrelated: ["expressions"]\naliases: ["names", "="]\n'
                "doc_url: https://docs.python.org/3/\n"
            ),
            body="# Not stripped\n\nBody text.",
        ),
    )

    items, problems = load_concepts(tmp_path)

    assert problems == []
    item = items[0]
    assert item.concept_id == "variables"
    assert item.name == "Variables"
    assert item.category == "State"
    assert item.summary == "A short line."
    assert item.status == ConceptStatus.DRAFT
    assert item.units == ["PY-0.1"]
    assert item.related == ["expressions"]
    assert item.aliases == ["names", "="]
    assert item.doc_url == "https://docs.python.org/3/"
    assert item.content_markdown == "# Not stripped\n\nBody text."


def test_a_missing_folder_is_an_empty_library(tmp_path):
    assert load_concepts(tmp_path / "nothing") == ([], [])


@pytest.mark.parametrize(
    "text, words",
    [
        ("No frontmatter at all.", "frontmatter"),
        ("---\nid: [unclosed\n---\n\nBody", "frontmatter"),
        ("---\n- a list\n---\n\nBody", "frontmatter"),
        ("---\ntitle: T\ncategory: C\nsummary: S\nstatus: draft\n---\n\nBody", "id"),
        ("---\nid: bad\ncategory: C\nsummary: S\nstatus: draft\n---\n\nBody", "title"),
        ("---\nid: bad\ntitle: T\ncategory: C\nstatus: draft\n---\n\nBody", "summary"),
        ("---\nid: bad\ntitle: T\ncategory: C\nsummary: S\n---\n\nBody", "status"),
        (note(slug="bad", status="finished"), "status"),
        (note(slug="bad", extra="colour: red\n"), "colour"),
        (note(slug="bad", extra="units: PY-0.1\n"), "units"),
        (note(slug="bad", extra="aliases: [1, 2]\n"), "aliases"),
        (note(slug="bad", extra="doc_url: javascript:alert(1)\n"), "doc_url"),
        (note(slug="bad", body=" "), "body"),
        (note(slug="other"), "file name"),
        ("---\nid: 12\ntitle: T\ncategory: C\nsummary: S\nstatus: draft\n---\n\nBody", "id"),
    ],
)
def test_a_bad_note_is_reported_and_the_rest_still_load(tmp_path, text, words):
    write(tmp_path, "good", note(slug="good"))
    write(tmp_path, "bad", text)

    items, problems = load_concepts(tmp_path)

    assert [i.concept_id for i in items] == ["good"]
    assert [p.code for p in problems] == ["concept-invalid"]
    assert problems[0].severity == Severity.ERROR
    assert "bad.md" in problems[0].message
    assert words in problems[0].message


@pytest.mark.parametrize("name", ["Has-Capitals", "two_words", "trailing-", "-leading", "a--b"])
def test_a_slug_must_be_lowercase_words_joined_by_hyphens(tmp_path, name):
    write(tmp_path, name, note(slug=name))

    items, problems = load_concepts(tmp_path)

    assert items == []
    assert "id" in problems[0].message


def test_a_file_that_is_not_utf8_is_reported(tmp_path):
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe\x00bad")

    items, problems = load_concepts(tmp_path)

    assert items == []
    assert [p.code for p in problems] == ["concept-invalid"]


def test_the_catalog_lists_a_to_z_whatever_the_case(tmp_path):
    write(tmp_path, "b", note(slug="b", title="banana"))
    write(tmp_path, "a", note(slug="a", title="Zebra"))
    write(tmp_path, "c", note(slug="c", title="Apple"))

    assert [c.name for c in ConceptCatalog(tmp_path).list_all()] == ["Apple", "banana", "Zebra"]


# --- Search ---


def ranked(concepts, query):
    return [c.concept_id for c in rank_concepts(concepts, query)]


def test_ranking_runs_title_then_alias_then_summary_then_body():
    library = [
        concept("in-body", title="Zulu", body="the word print is here"),
        concept("in-summary", title="Yankee", summary="about print"),
        concept("in-alias", title="Xray", aliases=["print"]),
        concept("title-contains", title="The print rule"),
        concept("title-starts", title="Printing"),
        concept("title-exact", title="Print"),
    ]

    assert ranked(library, "print") == [
        "title-exact",
        "title-starts",
        "title-contains",
        "in-alias",
        "in-summary",
        "in-body",
    ]


def test_ties_go_by_title():
    library = [concept("b", title="Print two"), concept("a", title="Print one")]

    assert ranked(library, "print") == ["a", "b"]


def test_search_ignores_case_and_needs_every_word():
    library = [concept("a", title="Comments in Python"), concept("b", title="Python basics")]

    assert ranked(library, "PYTHON comments") == ["a"]


def test_punctuation_in_a_query_does_not_stop_a_match():
    library = [concept("a", title="The print() function"), concept("b", title="Other")]

    assert ranked(library, "print()") == ["a"]
    assert ranked(library, "print(") == ["a"]


def test_a_query_with_no_letters_is_matched_as_written():
    library = [concept("a", aliases=["#"]), concept("b", title="Other")]

    assert ranked(library, "#") == ["a"]


@pytest.mark.parametrize("query", ["", "   ", "zzzz", "'; DROP TABLE", "\x00", "(((", "[[", "%"])
def test_odd_queries_find_nothing_and_never_fail(query):
    assert ranked([concept("a", title="Print")], query) == []


# --- Wiki links ---


def test_wiki_links_finds_plain_and_labelled_links():
    assert wiki_links("See [[variables]] and [[print-function|print]].") == ["variables", "print-function"]


def test_wiki_links_finds_a_link_escaped_for_a_table():
    assert wiki_links(r"| [[variables\|a name]] |") == ["variables"]


def test_wiki_links_skips_code():
    text = "`[[inline]]`\n\n```python\nx = [[fenced]]\n```\n\n~~~\n[[tilde]]\n~~~\n\n[[real]]"

    assert wiki_links(text) == ["real"]


def test_wiki_links_skips_an_unclosed_fence():
    assert wiki_links("[[real]]\n\n```python\nx = [[open]]\n") == ["real"]


def test_wiki_links_reports_a_badly_written_slug_so_a_check_can_catch_it():
    assert wiki_links("[[Not A Slug]]") == ["Not A Slug"]


def codes(findings):
    return [f.code for f in findings]


def test_a_clean_library_has_no_findings():
    library = [concept("a", related=["b"], units=["PY-0.1"]), concept("b", body="[[a]]")]

    assert check_concept_links(library, [unit(lesson="[[a]] and [[b|B]]")]) == []


def test_a_broken_link_in_a_lesson_is_an_error_naming_the_unit():
    found = check_concept_links([concept("a")], [unit(lesson="[[missing]]")])

    assert codes(found) == ["concept-link-broken"]
    assert found[0].severity == Severity.ERROR
    assert found[0].unit_id == "PY-0.1"
    assert "missing" in found[0].message


def test_a_broken_link_in_a_note_is_an_error_naming_the_note():
    found = check_concept_links([concept("a", body="[[missing]]")], [])

    assert codes(found) == ["concept-link-broken"]
    assert "a.md" in found[0].message


def test_an_unknown_related_note_or_unit_is_an_error():
    found = check_concept_links([concept("a", related=["gone"], units=["PY-9.9"])], [unit()])

    assert sorted(codes(found)) == ["concept-related-unknown", "concept-unit-unknown"]


def test_used_in_joins_declared_and_linked_units_in_teaching_order():
    units = [unit("PY-0.1", "[[a]]"), unit("PY-0.3"), unit("PY-0.4", "[[a|A]]"), unit("PY-0.5", "`[[a]]`")]
    item = concept("a", units=["PY-0.4", "PY-0.3", "PY-9.9"])

    assert [(u.unit_id, u.title) for u in used_in(item, units)] == [
        ("PY-0.1", "Title of PY-0.1"),
        ("PY-0.3", "Title of PY-0.3"),
        ("PY-0.4", "Title of PY-0.4"),
    ]


# --- The real curriculum ---


NOTES = Path("curriculum/concepts")


def test_the_four_draft_notes_load_clean():
    items, problems = load_concepts(NOTES)

    assert problems == []
    assert {"comments-in-python", "print-function", "variables", "expressions"} <= {
        i.concept_id for i in items
    }
    assert all(i.status == ConceptStatus.DRAFT for i in items)


def test_every_python_block_in_the_notes_compiles():
    items, _ = load_concepts(NOTES)
    blocks = [
        block
        for item in items
        for block in re.findall(r"```python\n(.*?)```", item.content_markdown, re.S)
    ]

    assert blocks
    for block in blocks:
        compile(block, "note", "exec")


def test_stage_0_lessons_link_to_the_notes_with_nothing_broken():
    catalog = load_all_roadmaps(Path("reference"))

    assert [f for f in catalog.findings if f.code.startswith("concept-")] == []
    linked = {slug for u in catalog.list_all_units() for slug in wiki_links(u.lesson_markdown or "")}
    assert {"comments-in-python", "print-function", "variables", "expressions"} <= linked


def test_a_bad_note_reaches_the_catalog_findings(tmp_path):
    (tmp_path / "curriculum" / "concepts").mkdir(parents=True)
    write(tmp_path / "curriculum" / "concepts", "bad", "No frontmatter.")
    (tmp_path / "reference").mkdir()

    catalog = load_all_roadmaps(tmp_path / "reference")

    assert "concept-invalid" in codes(catalog.findings)


# --- The API ---


@pytest.fixture
def repo():
    repository = SQLiteLearnerRepository(db_path=":memory:")
    repository.initialize()
    return repository


@pytest.fixture
def library(tmp_path):
    folder = tmp_path / "notes"
    for slug in ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf"):
        write(folder, slug, note(slug=slug, title=slug.title()))
    write(
        folder,
        "variables",
        note(extra='related: ["alpha", "gone"]\nunits: ["PY-0.1"]\naliases: ["names"]\n', body="Body [[alpha]]."),
    )
    return ConceptCatalog(folder)


@pytest.fixture
def units():
    catalog = CurriculumCatalog()
    catalog.add_unit(unit("PY-0.1"))
    catalog.add_unit(unit("PY-0.3", "See [[variables]]."))
    return catalog


@pytest.fixture
def client(repo, library, units):
    app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=units, concepts=library)
    return TestClient(app)


def test_the_list_is_a_to_z_and_holds_no_bodies(client):
    data = client.get(BASE).json()

    assert [c["concept_id"] for c in data][:2] == ["alpha", "bravo"]
    assert "content_markdown" not in data[0]
    assert data[0]["status"] == "draft"


def test_q_searches_with_ranking(client):
    assert [c["concept_id"] for c in client.get(BASE, params={"q": "names"}).json()] == ["variables"]


def test_search_is_another_name_for_q(client):
    assert client.get(BASE, params={"search": "names"}).json() == client.get(BASE, params={"q": "names"}).json()


def test_a_blank_query_lists_everything(client):
    assert len(client.get(BASE, params={"q": "  "}).json()) == 8


def test_a_very_long_query_is_refused(client):
    assert client.get(BASE, params={"q": "x" * 201}).status_code == 422
    assert client.get(BASE, params={"q": "x" * 200}).json() == []


def test_a_note_has_its_body_related_notes_and_units(client):
    data = client.get(f"{BASE}/variables").json()

    assert data["name"] == "Variables"
    assert data["content_markdown"] == "Body [[alpha]]."
    assert data["aliases"] == ["names"]
    assert data["related"] == [{"concept_id": "alpha", "name": "Alpha"}]
    assert data["used_in"] == [
        {"unit_id": "PY-0.1", "title": "Title of PY-0.1"},
        {"unit_id": "PY-0.3", "title": "Title of PY-0.3"},
    ]


@pytest.mark.parametrize("slug", ["nothing", "..%2F..%2Fsecret", "VARIABLES"])
def test_an_unknown_note_is_a_404_problem(client, slug):
    res = client.get(f"{BASE}/{slug}")

    assert res.status_code == 404
    assert res.headers["content-type"].startswith("application/problem+json")


def recent(client):
    return [c["concept_id"] for c in client.get(RECENT).json()]


def open_note(client, slug):
    res = client.put(f"{RECENT}/{slug}")
    assert res.status_code == 204


def test_recent_starts_empty(client):
    assert recent(client) == []


def test_recent_is_newest_first(client):
    open_note(client, "alpha")
    open_note(client, "bravo")

    assert recent(client) == ["bravo", "alpha"]


def test_opening_a_note_again_moves_it_to_the_top_without_a_repeat(client):
    for slug in ("alpha", "bravo", "alpha"):
        open_note(client, slug)

    assert recent(client) == ["alpha", "bravo"]


def test_recent_keeps_only_the_newest_five(client):
    for slug in ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf"):
        open_note(client, slug)

    assert recent(client) == ["golf", "foxtrot", "echo", "delta", "charlie"]


def test_recent_refuses_an_unknown_note(client):
    res = client.put(f"{RECENT}/nothing")

    assert res.status_code == 404
    assert recent(client) == []


def test_recent_leaves_out_a_note_that_no_longer_exists(client, repo):
    open_note(client, "alpha")
    repo.record_concept_opened(LOCAL_LEARNER_ID, "deleted-note")

    assert recent(client) == ["alpha"]


def test_recent_belongs_to_one_learner(repo):
    repo.record_concept_opened("one", "alpha")
    repo.record_concept_opened("two", "bravo")

    assert repo.get_recent_concepts("one") == ["alpha"]
    assert repo.get_recent_concepts("two") == ["bravo"]


def test_reading_a_note_does_not_count_as_a_search(client):
    client.get(f"{BASE}/alpha")

    assert recent(client) == []


def test_nothing_here_touches_the_ledger(client, repo):
    open_note(client, "alpha")
    client.get(f"{BASE}/alpha")
    client.get(BASE, params={"q": "alpha"})

    assert repo.get_evidence_ledger(LOCAL_LEARNER_ID) == []


def test_resetting_a_unit_keeps_recent(client):
    open_note(client, "alpha")

    assert client.post("/api/v1/learners/me/units/PY-0.1/reset").status_code == 204
    assert recent(client) == ["alpha"]


def test_recent_survives_a_new_connection(tmp_path):
    db = str(tmp_path / "state.db")
    first = SQLiteLearnerRepository(db_path=db)
    first.initialize()
    first.record_concept_opened("one", "alpha")

    second = SQLiteLearnerRepository(db_path=db)
    second.initialize()

    assert second.get_recent_concepts("one") == ["alpha"]
