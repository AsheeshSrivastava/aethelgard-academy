"""Write docs/prompts/prompt-catalogue.md from the code (ADR-0039 / SPEC-31 R10, R11).

Run from the repo root: `uv run python scripts/make_prompt_catalogue.py`

It only imports the prompt builders and prints what they build from placeholders: no model call, no learner data,
and nothing is read from the curriculum or the answers folder. No date, so the file changes only when the wording
does. tests/test_prompt_catalogue.py fails when the file and the code differ.
"""

from pathlib import Path

from lms.adapters.ai.providers import axis_rules
from lms.core.interfaces import AxisMode

CATALOGUE = Path(__file__).resolve().parents[1] / "docs" / "prompts" / "prompt-catalogue.md"
MODES = (AxisMode.SOCRATIC, AxisMode.HYBRID, AxisMode.COACH)
STATES = ("course", "not_found", "no_index", "unavailable")

INTRO = """# Prompt catalogue

Written by `scripts/make_prompt_catalogue.py` from the code. Do not edit by hand: run the script again.

Every prompt this application sends to a model. Text in `<angle brackets>` is a placeholder, except for the real
prompt tags (`<learner_query>`, `<learner_code>`, `<execution_stderr>`, `<learner_explanation>`,
`<reference_passages>`, `<brief>`, `<script>`, `<points>`, `<readme>`, `<note>`, `<output>`) which the model
really sees. In the judge system prompt, `<idea id>` and `<one or two sentences>` are also sent as written.
Long lines are one line in the real prompt.

The version beside each prompt is the `prompt_version` recorded for a call (SPEC-31 R12): it covers the system
prompt and the user message template, so learner text, passages and rubric ideas never change it.

With `MOCK_AI=true` no prompt is sent to any model."""


def _block(text: str) -> str:
    return f"~~~~text\n{text}\n~~~~"


def _pair(title: str, system: str, user: str) -> list:
    version = axis_rules.prompt_version(system, user)
    return [
        f"## {title}",
        f"Version: `{version}`",
        "### System prompt",
        _block(system),
        "### User message template",
        _block(user),
    ]


def render_catalogue() -> str:
    parts = [
        INTRO,
        "## AXIS chat",
        "The system prompt is: base rules, mode block, source block. `<passages>` stands for the "
        "`<reference_passages>` block of course passages.",
        "### User message template",
        "The same for every mode and state. `<learner_code>` and `<execution_stderr>` are left out of a real "
        "message when there is nothing to put in them.",
        _block(axis_rules.chat_user_template()),
    ]
    for mode in MODES:
        for state in STATES:
            passages = axis_rules.PASSAGES_PLACEHOLDER if state == "course" else ""
            parts += [
                f"### {mode.value}, {state}",
                f"Version: `{axis_rules.chat_prompt_version(mode, state)}`",
                _block(axis_rules.build_system_prompt(mode, passages, state)),
            ]
    parts += _pair("Concept check judge", *axis_rules.judge_templates())
    parts.append("The idea line repeats for each idea. The ideas come from private rubric files and are not copied here.")
    parts += _pair("README draft", *axis_rules.readme_draft_templates())
    parts += _pair("Build feedback summary", *axis_rules.feedback_summary_templates())
    parts.append("The line inside `<points>` repeats for each measured point.")
    parts += _pair("Settings connection ping", axis_rules.PING_SYSTEM_PROMPT, axis_rules.PING_USER_MESSAGE)
    return "\n\n".join(parts) + "\n"


def main() -> None:
    CATALOGUE.write_bytes(render_catalogue().encode("utf-8"))
    print(f"Wrote {CATALOGUE.relative_to(CATALOGUE.parents[2]).as_posix()}")


if __name__ == "__main__":
    main()
