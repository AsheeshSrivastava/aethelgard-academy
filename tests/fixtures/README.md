# Test fixtures

- `curriculum/` and `answers/`: made-up exercise items and their fake answers. Tests never use
  the real course items or the private answers (A0, 2026-11-11). `tests/conftest.py` copies the
  real curriculum without its `exercises/` folders, adds these items, and points
  `LMS_CURRICULUM_DIR` and `LMS_ANSWERS_DIR` at the copy. Regenerate with
  `uv run python scripts/make_test_fixtures.py` after adding real seeds.
- `tests/made_up.py` gives each made-up item's right and wrong answer.
- Tests that check the real content (`real_content()` in conftest.py, and `test_stage_build.py`)
  use the real answers when the machine has them, and the made-up items otherwise.
- `concepts/`: concept notes for the concept library tests.
