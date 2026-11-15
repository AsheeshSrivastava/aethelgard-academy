"""Review action 4: a hidden-check run must prove it finished, not just exit 0.

Governed by ADR-0036 amendment 5 and SPEC-03 section 2.4 (completion token).
Before: a learner program that called os._exit(0) at import ended the run with exit code 0
before any check ran, so every hidden-check item passed, Cold Check items included.
Now: the runner sends a random token with the checks, the harness prints it after the last
check, and a run only succeeds if the exit code is 0 and the token is in stdout. The token line
is removed from stdout, so the learner never sees it.

Not covered, by design (gap 1, SPEC-03 2.4): the token is in the same process as the learner's
functions, so a program written to attack the grader could still find it.
"""

import json
import os
from pathlib import Path

from lms.adapters.curriculum.builds import CURRICULUM_ENV
from lms.adapters.curriculum.loader import load_seeds
from lms.adapters.runner.check_harness import HARNESS, check_stdin, new_token
from lms.adapters.runner.subprocess_runner import SubprocessRunner
from lms.core.grading import Attempt, grade

RUNNER = SubprocessRunner()
GOOD = "def add(a, b):\n    return a + b\n"
CHECKS = "def test_add():\n    assert add(2, 3) == 5, 'add(2, 3) should be 5'\n"
ESCAPES = {
    "os._exit at import": "import os\nos._exit(0)\n",
    "os._exit before the function exists": "import os\nos._exit(0)\ndef add(a, b):\n    return a + b\n",
    "os._exit inside the function": "import os\ndef add(a, b):\n    os._exit(0)\n",
}


def debug_seed(cold: bool):
    seeds, _ = load_seeds(Path(os.environ[CURRICULUM_ENV]))  # the made-up fixture item, joined with its fake answers
    seed = next(s for s in seeds["PY-0.4"] if s.seed_id == "PY-0.4/debug-validate-1")
    return seed.model_copy(update={"cold_check_eligible": cold})


def attempt(seed, source):
    return Attempt(exercise_id=f"{seed.seed_id}/v1", activity=seed.activity.slug, files={"solution.py": source})


# --- The runner: every caller of execute(test_code=...) ---


def test_os_exit_at_import_no_longer_passes_the_checks():
    result = RUNNER.execute("import os\nos._exit(0)\n", test_code=CHECKS)

    assert result.exit_code == 0  # the old signal grading trusted
    assert result.success is False


def test_each_way_of_ending_the_run_early_fails_the_checks():
    for name, source in ESCAPES.items():
        result = RUNNER.execute(source, test_code=CHECKS)
        assert result.success is False, name


def test_a_correct_program_still_passes_and_the_token_is_not_shown_to_the_learner():
    result = RUNNER.execute(GOOD + "print('hello from the learner')\n", test_code=CHECKS)

    assert result.success, result.stderr
    assert "hello from the learner" in result.stdout
    assert "completion" not in result.stdout.lower()
    assert len(result.stdout.strip().splitlines()) == 1, result.stdout  # only the learner's own line remains


def test_a_wrong_program_still_fails_with_its_message():
    result = RUNNER.execute("def add(a, b):\n    return a - b\n", test_code=CHECKS)

    assert result.success is False
    assert any("add(2, 3) should be 5" in line for line in result.assertion_errors)


def test_a_learner_cannot_forge_the_token_by_printing_a_guess():
    guess = "lms-complete-" + "0" * 32
    result = RUNNER.execute(f"import os\nprint({guess!r})\nos._exit(0)\n", test_code=CHECKS)

    assert result.success is False


def test_each_run_gets_its_own_token():
    first, second = new_token(), new_token()
    line = check_stdin(CHECKS, None, first).split("\n", 1)[0]

    assert first != second and len(first) >= 32
    assert json.loads(line) == {"checks": CHECKS, "token": first}
    assert first not in HARNESS  # the harness is still fixed text


def test_a_run_without_checks_has_no_token_and_is_unchanged():
    result = RUNNER.execute("import os\nprint('hi', flush=True)\nos._exit(0)\n")

    assert result.success is True
    assert result.stdout.strip() == "hi"


# --- Grading: a normal item and a Cold Check item ---


def test_os_exit_does_not_pass_a_hidden_check_item():
    seed = debug_seed(cold=False)

    assert grade(seed, attempt(seed, "import os\nos._exit(0)\n"), RUNNER).passed is False


def test_os_exit_does_not_pass_a_cold_check_item():
    seed = debug_seed(cold=True)

    assert seed.cold_check_eligible is True
    assert grade(seed, attempt(seed, "import os\nos._exit(0)\n"), RUNNER).passed is False


def test_the_real_fix_still_passes_both_kinds_of_item():
    for cold in (False, True):
        seed = debug_seed(cold)
        assert grade(seed, attempt(seed, "def add(a, b):\n    return a + b"), RUNNER).passed is True


# --- The shared helper both runners use (so the Docker path is covered too) ---


def test_with_completion_fails_a_clean_exit_without_the_token_and_strips_it_when_present():
    from lms.adapters.runner.check_harness import with_completion
    from lms.core.interfaces import ExecutionResult

    token = new_token()

    def made(out):
        return ExecutionResult(success=True, stdout=out, stderr="", exit_code=0, duration_ms=1.0)

    missing = with_completion(made("learner line\n"), token)
    done = with_completion(made(f"learner line\n\n{token}\n"), token)

    assert missing.success is False and "ended before the checks finished" in missing.stderr
    assert done.success is True and done.stdout == "learner line\n" and token not in done.stdout
