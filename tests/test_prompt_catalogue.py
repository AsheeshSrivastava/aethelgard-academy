"""The prompt catalogue and its drift check (ADR-0039 / SPEC-31 R10, R11).

The contract these tests fix: scripts/make_prompt_catalogue.py has `render_catalogue() -> str`, and
docs/prompts/prompt-catalogue.md holds exactly that text. `axis_rules.chat_prompt_version(mode, source_state)` and
`axis_rules.prompt_version(system, user_template)` give the version printed beside a prompt (R12).
Offline: no model, no network, synthetic text only.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from lms.adapters.ai.providers import axis_rules
from lms.core.interfaces import AxisMode

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CATALOGUE = ROOT / "docs" / "prompts" / "prompt-catalogue.md"
MODES = [AxisMode.SOCRATIC, AxisMode.HYBRID, AxisMode.COACH]
NO_SOURCE_STATES = ["not_found", "no_index", "unavailable"]
VERSION = re.compile(r"(?<![0-9a-f])[0-9a-f]{12}(?![0-9a-f])")


def render() -> str:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import make_prompt_catalogue

    return make_prompt_catalogue.render_catalogue()


def committed() -> str:
    return CATALOGUE.read_text(encoding="utf-8")  # universal newlines: a CRLF checkout is not drift


def test_catalogue_matches_the_code():
    """Also catches a hand edit of the file (SPEC-31 section 6)."""
    rendered = render()

    assert committed() == rendered, "Run scripts/make_prompt_catalogue.py and commit the result."


def test_catalogue_has_every_model_prompt():
    text = render()

    # AXIS chat: three modes, grounded and each no-source state, assembled, with the passage placeholder.
    for mode in MODES:
        assert axis_rules.build_system_prompt(mode, "<passages>", "course") in text
        assert axis_rules.chat_prompt_version(mode, "course") in text
        for state in NO_SOURCE_STATES:
            assert axis_rules.build_system_prompt(mode, "", state) in text
            assert axis_rules.chat_prompt_version(mode, state) in text
    # The user message template: the optional blocks are always shown.
    for tag in ("Unit: ", "<learner_code>", "<execution_stderr>", "<learner_query>"):
        assert tag in text
    # Concept-check judge, README draft, build feedback summary and ping.
    assert axis_rules.JUDGE_SYSTEM_PROMPT in text
    for part in ("<learner_explanation>", "Ideas to look for:"):
        assert part in text
    assert "You draft a short README" in text and "Do not rewrite or improve the script." in text
    assert all(f"## {heading}" in text for heading in axis_rules.README_HEADINGS)
    assert "<brief>" in text and "<script" in text
    feedback_system, _ = axis_rules.feedback_summary_prompts([], "", "")
    assert feedback_system in text and "<points>" in text
    assert axis_rules.PING_SYSTEM_PROMPT in text and axis_rules.PING_USER_MESSAGE in text
    assert axis_rules.prompt_version(axis_rules.PING_SYSTEM_PROMPT, axis_rules.PING_USER_MESSAGE) in text
    # A version beside each: 9 distinct chat prompts (Hybrid and Coach share the no-source one, R3 and R12),
    # then the judge, README, build feedback and ping.
    assert len(set(VERSION.findall(text))) >= 13


def test_the_runtime_error_question_is_listed_only_while_its_route_exists():
    from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
    from lms.adapters.runner.subprocess_runner import SubprocessRunner
    from lms.api.app import create_app

    repo = SQLiteLearnerRepository(db_path=":memory:")
    repo.initialize()
    schema = create_app(repo=repo, runner=SubprocessRunner()).openapi()
    question = "Can you guide me Socratically to inspect my own logic"

    assert (question in render()) is ("/api/v1/explain-error" in schema["paths"])


def test_catalogue_holds_no_learner_or_answer_text(tmp_path, monkeypatch):
    """Rendering must not read the answers folder or the curriculum: a made-up sentinel placed there never shows."""
    before = render()
    sentinel = "zebra-quartz-answer-5521"
    rubric = tmp_path / "answers" / "python" / "py-0.4"
    rubric.mkdir(parents=True)
    (rubric / "rubric.json").write_text(
        json.dumps({"ideas": [{"id": "a", "text": sentinel}, {"id": "b", "text": sentinel}]}), encoding="utf-8"
    )
    monkeypatch.setenv("LMS_ANSWERS_DIR", str(tmp_path / "answers"))
    monkeypatch.setenv("LMS_CURRICULUM_DIR", str(tmp_path / "no-curriculum"))

    after = render()

    assert after == before
    assert sentinel not in after and sentinel not in committed()
    assert str(tmp_path) not in after and str(ROOT) not in after


def test_catalogue_has_no_date():
    for text in (render(), committed()):
        assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        assert not re.search(r"\b\d{1,2}:\d{2}:\d{2}\b", text)
        assert not re.search(r"\b\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|"
                             r"December) \d{4}\b", text)


def test_two_processes_render_the_same_bytes():
    """SPEC-31 section 6: nothing in the output depends on the process (hash seed, set order, clock)."""
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import make_prompt_catalogue as m; "
        "sys.stdout.buffer.write(m.render_catalogue().encode('utf-8'))"
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", code, str(SCRIPTS)], cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONHASHSEED": seed, "MOCK_AI": "true"},
        )
        for seed in ("1", "2")
    ]
    results = [(p.communicate(timeout=60), p.returncode) for p in processes]

    for (_out, err), code_ in results:
        assert code_ == 0, err.decode("utf-8", "replace")
    assert results[0][0][0] == results[1][0][0]
    assert results[0][0][0].decode("utf-8") == render()
