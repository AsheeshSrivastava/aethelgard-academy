"""Shared test setup.

Tests never use the real course items or the private answers (A0, 2026-11-11). At start-up
this file builds a curriculum copy whose exercise items are made up (tests/fixtures/curriculum)
and an answers folder with made-up keys (tests/fixtures/answers), then points
LMS_CURRICULUM_DIR and LMS_ANSWERS_DIR at them. Lessons, meta.json and builds are copied from
the real curriculum; quick-check questions are swapped for made-up ones so no real key is needed.

REAL_ANSWERS is the real answers folder when this machine has one (LMS_ANSWERS_DIR or the
sibling lms-answers folder), for the few tests that check the real content.
"""

import atexit
from contextlib import contextmanager
import os
import re
import shutil
import tempfile
from pathlib import Path

import pytest

from lms.adapters.curriculum.builds import ANSWERS_ENV, CURRICULUM_ENV, answers_dir_from_env

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
REAL_ANSWERS = answers_dir_from_env()
_QUICKCHECK = re.compile(r"```quickcheck\nid: (\S+)\n.*?```", re.S)
MADE_UP_QUICKCHECK = "```quickcheck\nid: {id}\nquestion: Made-up question for tests?\nA: one\nB: two\nC: three\n```"


def _build_test_tree() -> Path:
    root = Path(tempfile.mkdtemp(prefix="lms-test-tree-"))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    curriculum, answers = root / "curriculum", root / "answers"
    shutil.copytree(REPO / "curriculum", curriculum, ignore=shutil.ignore_patterns("exercises"))
    shutil.copytree(FIXTURES / "curriculum", curriculum, dirs_exist_ok=True)
    for lesson in curriculum.glob("*/*/lesson.md"):
        text = lesson.read_text(encoding="utf-8")
        lesson.write_text(_QUICKCHECK.sub(lambda m: MADE_UP_QUICKCHECK.format(id=m.group(1)), text), encoding="utf-8")
    shutil.copytree(FIXTURES / "answers", answers)
    for practice in curriculum.glob("*/builds/*/practice_checks.py"):
        target = answers / practice.parent.parent.parent.name / "builds" / practice.parent.name / "checks.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(practice, target)
    os.environ[CURRICULUM_ENV] = str(curriculum)
    os.environ[ANSWERS_ENV] = str(answers)
    return root


TEST_TREE = _build_test_tree()
collect_ignore_glob = ["fixtures/*"]  # made-up answer files, not tests


@contextmanager
def real_content():
    """The real curriculum and answers when this machine has them; otherwise the made-up ones.

    For the tests that check the real course content (keys match real output, real findings).
    In CI they run on the made-up items instead, which still exercises the checks themselves.
    """
    if REAL_ANSWERS is None:
        yield
        return
    saved = {name: os.environ.get(name) for name in (ANSWERS_ENV, CURRICULUM_ENV)}
    os.environ[ANSWERS_ENV] = str(REAL_ANSWERS)
    os.environ[CURRICULUM_ENV] = str(REPO / "curriculum")
    try:
        yield
    finally:
        for name, value in saved.items():
            os.environ[name] = value


@pytest.fixture(autouse=True)
def real_waits_unless_a_test_says_otherwise(monkeypatch):
    """Tests never take settings from a developer's local .env (ADR-0019 amendment).

    The .env loader only fills names that are not set, so setting the mode here keeps a
    local LMS_TEST_MODE=true from removing the waits the tests check. A test about test
    mode sets or removes it itself.
    """
    monkeypatch.setenv("LMS_TEST_MODE", "false")
