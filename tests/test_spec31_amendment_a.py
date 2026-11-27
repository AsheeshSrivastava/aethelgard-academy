"""SPEC-31 Amendment A (section 9) / ADR-0039 section 8: error messages, and what the Socratic guard counts as code.

Amends SPEC-31 section 3.4, SPEC-07 section 2.1 (what counts as code) and SPEC-30 checks (b) and (d).
Owner decisions (SPEC-31 9.6, option A on all five): wording only (no server fixed reply); the target is a
measurement, not code; the learner's own code in inline backticks is allowed and fenced blocks are still withheld;
checker version C is part of this change; the detector does not move into core in this change.

Interface names these tests fix (the spec leaves them open; all are additive):
  SocraticGuardrail.contains_code(text, learner_text="") -> bool
      The A1 to A3 detector. A non-empty learner_text also applies A4. AssistanceClassifier passes none (A5).
  SocraticGuardrail.enforce(reply, mode, strict=False, learner_text="") -> str
  SocraticStreamFilter(guardrail, learner_text="")
  learner text = the question + the learner code + the execution stderr of the AxisQuery. finish_reply, stream_axis
      and the mock companion build it; AssistanceClassifier.classify keeps its signature.
  lms.adapters.ai.obedience.harness.DEFAULT_ERROR_ITEMS_PATH = Path("eval/obedience/error-items.yaml")
  harness.load_error_items(path=None) -> List[Question]
      kind "error", set "error-items", invented None. The file is a YAML list of {id, q}. load_questions is unchanged.
  The harness reads "error-items.yaml" beside the made-up items file, when that file exists (no new option).
  replies.jsonl rows of these questions have kind "error".
  results.json: "error_items_version" (sha256 of the file's bytes, like made_up_version) and
      "error_items": {"n", "no_reply", "explains_flagged", "b_failed", "d_failed"} counted on the raw replies.
  report.txt line: "Error-message items: N replies, X no reply, E explain flags, B fail (b), D fail (d)
      (not in the totals above)"

All text here is made up. No model, no network.
"""

import hashlib
import json
import re
import time
from pathlib import Path

import httpx
import pytest
import yaml

import obedience_support as ob
from obedience_corpus import BODY, EXACT, FENCED_BLOCK, MODES, STATES, good_reply
from lms.adapters.ai.axis_stream import SocraticStreamFilter, stream_axis
from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.core.interfaces import AxisMode, AxisQuery, ExecutionResult
from lms.core.models import ActivityType, AssistanceLevel

REPO = Path(__file__).resolve().parents[1]
GUARD = SocraticGuardrail()
ALL_MODES = [AxisMode.SOCRATIC, AxisMode.HYBRID, AxisMode.COACH]
NO_SOURCE_STATES = ["not_found", "no_index", "unavailable"]
WITHHELD = "direct code solutions are withheld"
NOT_FOUND = EXACT["not_found"]
WHERE = ["question", "code", "stderr"]


def query(mode=AxisMode.SOCRATIC, *, question="Why does this fail?", code=None, stderr=None):
    result = None
    if stderr is not None:
        result = ExecutionResult(success=False, stdout="", stderr=stderr, exit_code=1, duration_ms=1.0)
    return AxisQuery(unit_id="PY-0.1", mode=mode, current_activity=ActivityType.PREDICT, user_prompt=question,
                     learner_code=code, execution_result=result)


def query_holding(span, where, mode=AxisMode.SOCRATIC):
    """A query whose learner text holds `span` in one place only: the question, the code or the run output."""
    if where == "question":
        return query(mode, question=f"Why does this fail: {span}")
    if where == "code":
        return query(mode, code=f"{span}\nprint('made up')")
    return query(mode, stderr=f"Traceback (most recent call last):\n    {span}\nValueError: made up")


def whole(reply, q):
    return axis_rules.finish_reply(reply, q, [], GUARD, AssistanceClassifier()).reply


class FakeAxis:
    def __init__(self, deltas):
        self._deltas = deltas

    def stream(self, _query):
        return iter(self._deltas), []


def streamed(reply, q, size=7):
    pieces = [reply[i:i + size] for i in range(0, len(reply), size)]
    events = list(stream_axis(FakeAxis(pieces), q, GUARD, AssistanceClassifier()))
    return "".join(data["text"] for name, data in events if name == "token")


# =====================================================================================================
# SPEC-31 section 9.1: no-source contract wording (all three modes)
# =====================================================================================================

ERROR_RULE = (
    "When their question, code or run output shows an error or a traceback, do not say what the error or its message "
    'means, what caused it, or what the values in it must be. Do not write "means" or "because" about it. Point at one '
    "line number or function name to look at, then ask what they expected to happen there and what they have checked. "
    "Do not copy their code or the traceback into your reply; point at it by line number or name."
)
# The versions recorded before Amendment A (checked on the branch before any code).
OLD_NO_SOURCE_VERSIONS = {
    "Socratic": {"not_found": "fbe58444ce82", "no_index": "e3ec975ab143", "unavailable": "7edcea410cf9"},
    "Hybrid": {"not_found": "dc934fd9d400", "no_index": "41a69fc3d1b9", "unavailable": "c950749384f2"},
    "Coach": {"not_found": "dc934fd9d400", "no_index": "41a69fc3d1b9", "unavailable": "c950749384f2"},
}
COURSE_VERSIONS = {"Socratic": "a4a0e1a9ac0e", "Hybrid": "713b849bf874", "Coach": "7a8ff522da8f"}


def norm(text):
    return " ".join(text.split())


@pytest.mark.parametrize("state", NO_SOURCE_STATES)
@pytest.mark.parametrize("mode", ALL_MODES)
def test_no_source_contract_has_the_error_rule_in_every_mode(mode, state):
    assert norm(axis_rules.no_source_notice(mode, state)).endswith(ERROR_RULE)  # "added at the end"
    assert ERROR_RULE in norm(axis_rules.build_system_prompt(mode, "", state))


@pytest.mark.parametrize("state", NO_SOURCE_STATES)
@pytest.mark.parametrize("mode", ALL_MODES)
def test_no_source_contract_no_longer_asks_to_restate_their_question(mode, state):
    notice = norm(axis_rules.no_source_notice(mode, state))

    assert "restate their question in their words" not in notice
    assert "restate what they asked for" in notice


@pytest.mark.parametrize("mode", ALL_MODES)
def test_every_no_source_prompt_version_changes_and_course_versions_do_not(mode):
    for state, old in OLD_NO_SOURCE_VERSIONS[mode.value].items():
        assert axis_rules.chat_prompt_version(mode, state) != old, state
    assert axis_rules.chat_prompt_version(mode, "course") != COURSE_VERSIONS[mode.value]  # SPEC-33 section 3


@pytest.mark.parametrize("mode", ALL_MODES)
def test_a_prompt_with_a_source_does_not_carry_the_error_rule(mode):
    prompt = norm(axis_rules.build_system_prompt(mode, "<reference_passages>x</reference_passages>", "course"))

    assert "do not say what the error or its message means" not in prompt


# =====================================================================================================
# SPEC-31 section 9.2 A1: def, class, import
# =====================================================================================================

PLAIN_ENGLISH = [
    "What have you tried with a dataclass or a named class in Python?",
    "What should your function return when you call it (for example with 3)?",
    "Which module do you import first (and why)?",
    "What do you know about the BaseModel class or its purpose?",
    "Is it a class you wrote, or one from a library?",
    "Did you try to import os before that call?",
    "Did the value come from the module import list?",
    "What should it return when nothing matches (None)?",
    "What do you expect the return value to be (a number or text)?",
]


@pytest.mark.parametrize("sentence", PLAIN_ENGLISH)
def test_plain_english_with_class_import_or_return_is_not_code(sentence):
    assert GUARD.contains_code(sentence) is False
    assert GUARD.enforce(sentence, AxisMode.SOCRATIC) == sentence


@pytest.mark.parametrize("sentence", PLAIN_ENGLISH)
def test_plain_english_reaches_the_learner_whole_and_streamed(sentence):
    assert whole(sentence, query()) == sentence
    assert streamed(sentence, query()) == sentence


@pytest.mark.parametrize("text", [
    "def total(a):",
    "You could write def total(a): there.",
    "class Dog:",
    "class Dog(Base):",
    "Try class Dog: next.",
    "import os",
    "    import os",
    "from a import b",
    "Add this first.\nimport os",
    "Add this first.\nfrom a import b",
])
def test_def_and_class_headers_are_code(text):
    assert GUARD.contains_code(text) is True
    assert WITHHELD in GUARD.enforce(text, AxisMode.SOCRATIC)


# =====================================================================================================
# SPEC-31 section 9.2 A2: return
# =====================================================================================================


@pytest.mark.parametrize("text", [
    "Try return float(amount) * rate and see.",
    "You could return len(rows) there.",
    "return total",
    "    return value",
    "Look at this.\nreturn total",
])
def test_return_followed_by_an_expression_is_code(text):
    assert GUARD.contains_code(text) is True
    assert WITHHELD in GUARD.enforce(text, AxisMode.SOCRATIC)


@pytest.mark.parametrize("text", ["Try return total * rate and see.", "Try return price + tax and see."])
def test_return_with_an_operator_in_its_expression_is_code(text):
    """A2 "followed by ... an operator", read as: the expression after `return` holds one (no call, no bracket)."""
    assert GUARD.contains_code(text) is True


# =====================================================================================================
# SPEC-31 section 9.2 A3: fences, code lines and assignments count as today
# =====================================================================================================


@pytest.mark.parametrize("text", [
    "```\nplain words\n```",
    "~~~\nplain words\n~~~",
    "items = []",
    "total += 1",
    "print(total)",
    "for row in rows:",
])
def test_fences_code_lines_and_assignments_still_count(text):
    assert GUARD.contains_code(text) is True


# =====================================================================================================
# SPEC-31 section 9.2 A4: the learner's own words
# =====================================================================================================

# Spans the detector calls code on their own, so only A4 can keep them.
LEARNER_SPANS = ["items = []", "def total(a):", "return float(amount) * rate"]


def asking_about(span):
    return f"What does `{span}` give you on the second row?"


@pytest.mark.parametrize("span", LEARNER_SPANS)
def test_a_quoted_learner_span_is_kept(span):
    reply = asking_about(span)
    learner = f"Why is this wrong?\n{span}"

    assert GUARD.contains_code(reply) is True  # without the learner's text it is still code (A1 to A3)
    assert GUARD.contains_code(reply, learner_text=learner) is False
    assert GUARD.enforce(reply, AxisMode.SOCRATIC, strict=True, learner_text=learner) == reply  # shown unchanged


@pytest.mark.parametrize("where", WHERE)
@pytest.mark.parametrize("span", LEARNER_SPANS)
def test_the_question_code_and_run_output_each_count_as_learner_text(span, where):
    reply = asking_about(span)

    assert whole(reply, query_holding(span, where)) == reply
    assert streamed(reply, query_holding(span, where)) == reply


@pytest.mark.parametrize("span", LEARNER_SPANS)
def test_a_span_the_learner_did_not_write_is_withheld(span):
    reply = asking_about(span)
    learner = "Why is total zero?\ntotal = 0"

    assert GUARD.contains_code(reply, learner_text=learner) is True
    out = GUARD.enforce(reply, AxisMode.SOCRATIC, learner_text=learner)
    assert WITHHELD in out and span not in out
    q = query(code="total = 0")
    for shown in (whole(reply, q), streamed(reply, q)):
        assert WITHHELD in shown and span not in shown


def test_a_kept_span_survives_when_other_code_in_the_reply_is_withheld():
    reply = "What does `items = []` hold here?\nsecret = []\nWhen does it change?"
    q = query(code="items = []")

    for shown in (whole(reply, q), streamed(reply, q)):
        assert "`items = []`" in shown
        assert "secret" not in shown
        assert WITHHELD in shown


@pytest.mark.parametrize("reply", [
    "Look at this line.\nitems = []\nWhat does it hold?",
    "Try return float(amount) * rate and see what happens?",
])
def test_learner_code_written_without_backticks_is_still_withheld(reply):
    q = query(code="items = []\n    return float(amount) * rate")

    for shown in (whole(reply, q), streamed(reply, q)):
        assert WITHHELD in shown
        assert "items = []" not in shown and "float(amount)" not in shown


@pytest.mark.parametrize("fence", [
    "```python\nitems = []\n```",
    "```\nitems = []\n```",
    "~~~\nitems = []\n~~~",
    "```items = []```",
])
def test_a_fenced_copy_of_learner_code_is_still_withheld(fence):
    reply = f"Look at this.\n{fence}\nWhat does it hold?"
    q = query(code="items = []")

    assert GUARD.contains_code(reply, learner_text="items = []") is True
    for shown in (whole(reply, q), streamed(reply, q)):
        assert "items = []" not in shown
        assert "What does it hold?" in shown
    assert WITHHELD in whole(reply, q)


def test_the_stream_keeps_a_quoted_learner_span():
    gate = SocraticStreamFilter(GUARD, learner_text="items = []")

    out = []
    for piece in ("What does `items ", "= []` hold ", "after the loop? "):
        out.extend(gate.feed(piece))
    out.extend(gate.finish())

    assert "".join(out) == "What does `items = []` hold after the loop? "


def test_the_stream_filter_without_learner_text_still_withholds():
    gate = SocraticStreamFilter(GUARD)

    out = "".join(gate.feed("What does `items = []` hold? ") + gate.finish())

    assert WITHHELD in out and "items = []" not in out


def test_consult_through_a_real_companion_keeps_a_quoted_learner_span():
    reply = "What does `items = []` hold after the loop?"

    def handler(request):
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 0, "model": "m",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": reply}}]})

    companion = OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:8888/v1", model="m", api_key="k", fallback_to_mock=False,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert companion.consult(query(code="items = []")).reply == reply


def test_the_mock_companion_gives_the_guard_the_learner_text():
    class Spy(SocraticGuardrail):
        seen = None

        def enforce(self, reply, mode, strict=False, learner_text=""):
            self.seen = learner_text
            return super().enforce(reply, mode, strict=strict)

    spy = Spy()

    MockAxisCompanion(guardrail=spy).consult(
        query(question="made-up question", code="made_up_code = 1", stderr="made-up stderr line"))

    for part in ("made-up question", "made_up_code = 1", "made-up stderr line"):
        assert part in (spy.seen or ""), part


# =====================================================================================================
# SPEC-31 section 9.2 A5: the classifier
# =====================================================================================================


@pytest.mark.parametrize("mode", [AxisMode.COACH, AxisMode.HYBRID])
@pytest.mark.parametrize("reply", [
    "What should your function return when you call it (for example with 3)?",
    "What do you want it to return, and which class holds it (if any)?",
])
def test_classifier_does_not_mark_plain_english_as_supplied_reasoning(mode, reply):
    level = AssistanceClassifier().classify("Why is my total wrong?", reply, mode)

    assert level != AssistanceLevel.SUPPLIED_REASONING


@pytest.mark.parametrize("mode", [AxisMode.COACH, AxisMode.HYBRID])
def test_classifier_does_not_excuse_code_the_learner_wrote(mode):
    """A5: the classifier does not use A4, so a quoted learner line counts as it did."""
    q = query(mode, code="return float(amount) * rate")
    reply = "Look at `return float(amount) * rate` again. What does it hand back?"

    response = axis_rules.finish_reply(reply, q, [], GUARD, AssistanceClassifier())

    assert response.detected_assistance_level == AssistanceLevel.SUPPLIED_REASONING


# =====================================================================================================
# SPEC-31 section 9.3 C1: (b) and indexes
# =====================================================================================================


def check(reply, mode="Hybrid", learner="Why is my total wrong?"):
    from lms.core.axis_obedience import check_reply

    return check_reply(reply, mode, "not_found", learner, None)


@pytest.mark.parametrize("index", ['data["items"][0]', "rows[1]", "f()[0]", "grid[1][2]", "row_[3]", "`rows[1]`"])
def test_b_passes_an_index_and_still_fails_a_lone_label(index):
    assert check(f"{NOT_FOUND} What does {index} hold for you?").b.passed is True, index
    for lone in ("Can you see [1].", "[1]", "[1] What do you see?", "What about this.[1]", "In rows [1], what is there?"):
        result = check(f"{NOT_FOUND} {lone}")
        assert result.b.passed is False and result.b.reason == "label", lone
    both = check(f"{NOT_FOUND} What does {index} hold, as in [2]?")
    assert both.b.passed is False and both.b.reason == "label"


def test_b_still_fails_a_lone_label_the_learner_typed():
    result = check(f"{NOT_FOUND} You asked about [1] there.", learner="What is [1] next to my loop?")

    assert result.b.passed is False and result.b.reason == "label"


# =====================================================================================================
# SPEC-31 section 9.3 C2: (d) uses the 9.2 detector with the learner's text
# =====================================================================================================


@pytest.mark.parametrize("sentence", PLAIN_ENGLISH)
def test_d_passes_plain_english(sentence):
    assert check(f"{NOT_FOUND} {sentence}", mode="Socratic").d.passed is True


@pytest.mark.parametrize("span", LEARNER_SPANS)
def test_d_passes_a_quoted_learner_span(span):
    result = check(f"{NOT_FOUND} {asking_about(span)}", mode="Socratic", learner=f"Why is this wrong? {span}")

    assert result.d.passed is True


def test_d_still_fails_a_foreign_span_and_a_fenced_copy():
    learner = "Why is this wrong? items = []"

    foreign = check(f"{NOT_FOUND} {asking_about('secret = []')}", mode="Socratic", learner=learner)
    fenced = check(f"{NOT_FOUND}\n```\nitems = []\n```\nWhy?", mode="Socratic", learner=learner)

    assert foreign.d.passed is False and fenced.d.passed is False


# =====================================================================================================
# SPEC-31 section 9.3 C3: checker version C
# =====================================================================================================


def test_checker_version_is_c(tmp_path):
    from lms.adapters.ai.obedience import report
    from lms.core import axis_obedience

    assert axis_obedience.CHECKER_VERSION == "D"  # SPEC-33 section 7
    folder = report.write_run(tmp_path, "run1", [ob.make_row("q1", "Coach")], {"seed": 29})
    assert json.loads((folder / "results.json").read_text(encoding="utf-8"))["checker_version"] == "D"


def write_replies(tmp_path, rows):
    source = tmp_path / "in" / "replies.jsonl"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    return source


def test_replay_rescores_old_raw_replies_under_c_and_keeps_the_stored_visible_reply(tmp_path):
    raw = f"{NOT_FOUND} What does rows[1] hold for you?"
    old_visible = "Made-up text the old guard left."
    source = write_replies(tmp_path, [ob.make_row("q1", "Coach", "not_found", raw, visible=old_visible)])

    assert ob.run(tmp_path, ob.BoomFactory(), replay=source, environ={"MOCK_AI": "true"}) == 0

    run_dir = ob.the_run_dir(tmp_path)
    results = ob.read_results(run_dir)
    assert results["checker_version"] == "D"
    assert results["failing_ids"]["b"] == []
    (row,) = ob.read_rows(run_dir)
    assert row["visible_reply"] == old_visible and row["raw_reply"] == raw


# =====================================================================================================
# SPEC-31 section 9.3 E1: error-message questions, reported apart
# =====================================================================================================

ERROR_ITEMS = [
    {"id": f"err-{i}", "q": f"Zebraquartz {i}: my run shows ValueError: made-up message {i}. What now?"}
    for i in range(1, 7)
]
ERROR_ROW_QUESTION = "Zebraquartz made-up run shows ValueError: bad made-up row. What now?"


def write_error_items(tmp_path, items=None):
    path = tmp_path / "error-items.yaml"
    path.write_text(yaml.safe_dump(items or ERROR_ITEMS, sort_keys=False), encoding="utf-8")
    return path


def error_row(qid, mode="Coach", state="not_found", raw="default", **extra):
    return ob.make_row(qid, mode, state, raw, set_name="error-items", kind="error",
                       question=ERROR_ROW_QUESTION, **extra)


def error_rows():
    """Five rows: one clean, one failing (b), one failing (d) with a fence, one that explains, one with no reply."""
    return [
        error_row("err-1"),
        error_row("err-2", raw=good_reply("Coach", "not_found") + " Zebraquartzreply as in [1]."),
        error_row("err-3", "Socratic", raw=good_reply("Socratic", "not_found") + "\n" + FENCED_BLOCK),
        error_row("err-4", "Hybrid", raw=good_reply("Hybrid", "not_found") + " Quick note, because the row is bad."),
        error_row("err-5", raw=None, visible=None, no_reply=True, error_class="TimeoutError"),
    ]


def other_rows():
    rows = []
    for mode in MODES:
        for i in range(14):
            raw = BODY[mode] if i == 0 else good_reply(mode, "not_found")
            rows.append(ob.make_row(f"other-{mode}-{i:02d}", mode, "not_found", raw))
    rows.append(ob.make_row("made-1", "Coach", "not_found",
                            f"{NOT_FOUND} The made_helper function clears things.", invented="made_helper"))
    return rows


ERROR_LINE = ("Error-message items: 5 replies, 1 no reply, 2 explain flags, 1 fail (b), 1 fail (d) "
              "(not in the totals above)")
EXISTING_KEYS = ("counts", "made_up", "new_terms_flagged", "explains_flagged", "exact_wording_rate", "failing_ids",
                 "flagged_ids")
META = {"seed": 29}


def test_error_items_are_reported_apart():
    from lms.adapters.ai.obedience import report

    alone = report.build_results(other_rows(), META)
    mixed = report.build_results(other_rows() + error_rows(), META)

    for key in EXISTING_KEYS:
        assert mixed[key] == alone[key], key
    assert mixed["error_items"] == {"n": 5, "no_reply": 1, "explains_flagged": 2, "b_failed": 1, "d_failed": 1}
    assert ERROR_LINE in report.render_report(mixed).splitlines()


def entry_headings(sample):
    return [line[3:] for line in sample.splitlines() if line.startswith("## ")]


def test_every_error_item_reply_is_in_the_review_sample():
    from lms.adapters.ai.obedience import report

    clean = [error_row(f"err-clean-{i:02d}") for i in range(15)]  # unflagged, and more than the ten per mode

    alone = entry_headings(report.render_review_sample(other_rows(), 29))
    mixed = entry_headings(report.render_review_sample(other_rows() + error_rows() + clean, 29))

    for row in error_rows() + clean:
        assert f"{row['id']} | {row['mode']} | {row['state']}" in mixed, row["id"]
    assert [h for h in mixed if not h.startswith("err-")] == alone  # the other replies are picked as before


def test_report_and_results_hold_no_error_question_or_reply_text(tmp_path):
    from lms.adapters.ai.obedience import report

    folder = report.write_run(tmp_path, "run1", other_rows() + error_rows(), META)

    results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    assert results["error_items"]["n"] == 5
    for name in ("report.txt", "results.json"):
        assert "zebraquartz" not in (folder / name).read_text(encoding="utf-8").lower(), name


def test_load_error_items_reads_id_and_question(tmp_path):
    from lms.adapters.ai.obedience.harness import load_error_items

    items = load_error_items(write_error_items(tmp_path))

    assert [(q.id, q.text) for q in items] == [(i["id"], i["q"]) for i in ERROR_ITEMS]
    assert {(q.kind, q.set, q.invented) for q in items} == {("error", "error-items", None)}


def test_a_duplicated_error_item_id_is_refused(tmp_path):
    from lms.adapters.ai.obedience.harness import load_error_items

    path = write_error_items(tmp_path, [ERROR_ITEMS[0], ERROR_ITEMS[0]])

    with pytest.raises(ValueError, match="err-1"):
        load_error_items(path)


def test_the_real_error_items_file_holds_eighteen_made_up_error_questions():
    from lms.adapters.ai.obedience import harness

    assert harness.DEFAULT_ERROR_ITEMS_PATH == Path("eval/obedience/error-items.yaml")
    path = REPO / harness.DEFAULT_ERROR_ITEMS_PATH
    assert path.is_file(), "SPEC-31 9.3 E1: eval/obedience/error-items.yaml holds the error-message questions"
    items = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert isinstance(items, list) and len(items) == 18
    assert all(set(item) == {"id", "q"} for item in items)  # questions only: no answers, no keys
    assert all(isinstance(item[k], str) and item[k].strip() for item in items for k in ("id", "q"))
    ids = [item["id"] for item in items]
    others = {q.id for q in harness.load_questions(REPO / harness.DEFAULT_SETS_DIR, REPO / harness.DEFAULT_MADE_UP_PATH)}
    assert len(set(ids)) == 18 and not set(ids) & others
    shows_an_error = re.compile(r"Traceback|\w*(?:Error|Exception)\b|\berror\b", re.IGNORECASE)
    assert all(shows_an_error.search(item["q"]) for item in items)
    assert len(harness.load_error_items(path)) == 18


def test_error_items_are_asked_in_every_mode_and_state(tmp_path):
    write_error_items(tmp_path)
    factory = ob.ScriptedFactory()

    assert ob.run(tmp_path, factory) == 0

    assert len(factory.calls) == (ob.TOTAL_QUESTIONS + len(ERROR_ITEMS)) * ob.CASES_PER_QUESTION
    for item in ERROR_ITEMS:
        asked = {(c.mode, c.state) for c in factory.calls if c.question == item["q"]}
        assert asked == {(m, s) for m in MODES for s in STATES}, item["id"]
    run_dir = ob.the_run_dir(tmp_path)
    results = ob.read_results(run_dir)
    errors = len(ERROR_ITEMS) * ob.CASES_PER_QUESTION
    assert results["error_items"] == {"n": errors, "no_reply": 0, "explains_flagged": 0, "b_failed": 0, "d_failed": 0}
    assert sum(c["n"] for m in results["counts"]["raw"].values() for c in m.values()) == (
        ob.TOTAL_QUESTIONS * ob.CASES_PER_QUESTION)
    assert results["error_items_version"] == hashlib.sha256((tmp_path / "error-items.yaml").read_bytes()).hexdigest()
    assert results["made_up_version"] == ob.file_version_of(tmp_path / "made-up-items.yaml")
    assert {r["kind"] for r in ob.read_rows(run_dir) if r["id"].startswith("err-")} == {"error"}
    sample = (run_dir / "review-sample.md").read_text(encoding="utf-8")
    assert len([h for h in entry_headings(sample) if h.startswith("err-")]) == errors


def test_quick_takes_every_third_error_item(tmp_path):
    write_error_items(tmp_path)
    factory = ob.ScriptedFactory()

    assert ob.run(tmp_path, factory, quick=True) == 0

    asked = {c.question for c in factory.calls}
    assert {i["id"] for i in ERROR_ITEMS if i["q"] in asked} == {"err-1", "err-4"}
    assert len(factory.calls) == (ob.TOTAL_QUESTIONS // 3 + 2) * ob.CASES_PER_QUESTION


def test_the_sets_filter_applies_to_error_items_as_the_set_error_items(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    for folder in (first, second):
        folder.mkdir()
        write_error_items(folder)

    only_errors = ob.ScriptedFactory()
    assert ob.run(first, only_errors, sets=("error-items",)) == 0
    assert {c.question for c in only_errors.calls} == {i["q"] for i in ERROR_ITEMS}

    without = ob.ScriptedFactory()
    assert ob.run(second, without, sets=("alpha-docs",)) == 0
    assert not {c.question for c in without.calls} & {i["q"] for i in ERROR_ITEMS}


def test_the_estimate_counts_error_items(tmp_path):
    write_error_items(tmp_path)

    assert ob.run(tmp_path, ob.BoomFactory(), profile="paid", environ={"PAID_API_KEY": ob.FAKE_PAID_KEY},
                  estimate=True) == 0

    data = json.loads((tmp_path / "out" / "run1" / "estimate.json").read_text(encoding="utf-8"))
    assert data["replies"] == (ob.TOTAL_QUESTIONS + len(ERROR_ITEMS)) * ob.CASES_PER_QUESTION


def test_replay_reports_error_rows_the_same_way(tmp_path):
    path = write_error_items(tmp_path)
    source = write_replies(tmp_path, other_rows() + error_rows())

    assert ob.run(tmp_path, ob.BoomFactory(), replay=source, environ={"MOCK_AI": "true"}) == 0

    run_dir = ob.the_run_dir(tmp_path)
    results = ob.read_results(run_dir)
    assert results["error_items"] == {"n": 5, "no_reply": 1, "explains_flagged": 2, "b_failed": 1, "d_failed": 1}
    assert results["error_items_version"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert sum(c["n"] for m in results["counts"]["raw"].values() for c in m.values()) == len(other_rows())
    assert ERROR_LINE in (run_dir / "report.txt").read_text(encoding="utf-8").splitlines()


def test_old_replies_without_error_rows_still_replay(tmp_path):
    source = write_replies(tmp_path, other_rows())

    assert ob.run(tmp_path, ob.BoomFactory(), replay=source, environ={"MOCK_AI": "true"}) == 0

    results = ob.read_results(ob.the_run_dir(tmp_path))
    assert results["error_items"] == {"n": 0, "no_reply": 0, "explains_flagged": 0, "b_failed": 0, "d_failed": 0}
    assert "error_items_version" not in results
    assert sum(c["n"] for m in results["counts"]["raw"].values() for c in m.values()) == len(other_rows())


# =====================================================================================================
# SPEC-31 section 9.5: chaos check
# =====================================================================================================


def test_chaos_a_learner_span_of_one_character():
    q = query(code="x")
    kept = "What is `x` when the loop ends?"
    attack = "Look at `x` first.\nsecret = []\nWhat next?"

    assert whole(kept, q) == kept and streamed(kept, q) == kept
    for shown in (whole(attack, q), streamed(attack, q)):
        assert "secret" not in shown and WITHHELD in shown
    unquoted = "Look at this.\nitems = []\nWhat next?"  # the one character occurs in it, but it is not a quoted span
    assert "items = []" not in whole(unquoted, query(code="="))


@pytest.mark.parametrize("span, code", [
    ("items = []", "items    =    []"),
    ("def total(a): return float(a)", "def total(a):\n    return float(a)"),
    ("items  =  []", "items = []"),
])
def test_chaos_a_span_that_matches_only_after_whitespace_is_collapsed(span, code):
    reply = asking_about(span)

    assert whole(reply, query(code=code)) == reply
    assert streamed(reply, query(code=code)) == reply


def test_chaos_an_indentation_change_quoted_inline_is_kept_and_a_fenced_one_is_not():
    code = "for x in xs:\n        total = []"
    inline = "What does `    total = []` do inside the loop?"
    fenced = "Compare this.\n```\n    total = []\n```\nWhat changed?"

    assert whole(inline, query(code=code)) == inline
    assert streamed(inline, query(code=code)) == inline
    for shown in (whole(fenced, query(code=code)), streamed(fenced, query(code=code))):
        assert "total = []" not in shown


@pytest.mark.parametrize("reply", [
    "What does `items = [] hold here?",
    "What does items = []` hold here?",
    "What does `items = [] and secret = []` hold here?",
    "A ` mark then `secret = []` here, why?",
])
def test_chaos_unbalanced_backticks_release_no_foreign_code(reply):
    q = query(code="total = 0")

    for shown in (whole(reply, q), streamed(reply, q)):
        assert WITHHELD in shown and "= []" not in shown


@pytest.mark.parametrize("size", [1, 2, 3, 11])
def test_chaos_a_span_split_across_stream_pieces(size):
    reply = "What does `items = []` hold after the loop?"

    assert streamed(reply, query(code="items = []"), size) == reply


def test_chaos_a_span_holding_a_sentence_end_survives_the_stream():
    """The stream cuts on sentence ends: one inside a quoted span must not break the span apart."""
    code = 'items = ["Done. Next"]'
    reply = f"What does `{code}` hold after the loop?"

    assert whole(reply, query(code=code)) == reply
    assert streamed(reply, query(code=code)) == reply


@pytest.mark.parametrize("question", [
    "Why does `items = []` reset each time?",
    "Why does this reset? ```\nitems = []\n```",
    "Why does `` this ` reset items = []?",
])
def test_chaos_learner_text_holding_backticks(question):
    reply = "What does `items = []` hold after the loop?"
    q = query(question=question)

    assert whole(reply, q) == reply
    assert streamed(reply, q) == reply


@pytest.mark.parametrize("reply", [
    "What does your loop need before it can return?",
    "What does print() show, and what should it return?",
    "Which value (if any) do you expect it to return",
])
def test_chaos_return_at_the_end_of_a_reply(reply):
    assert GUARD.contains_code(reply) is False
    for shown in (whole(reply, query()), streamed(reply, query())):
        assert reply in shown and WITHHELD not in shown


def test_chaos_a_non_python_traceback():
    stderr = "ReferenceError: total is not defined\n    const rows = [];\n    at total (app.js:3:11)"
    quoted = "What did you expect at `const rows = [];` in your file?"
    pointed = "Which value did you expect in total, at app.js line 3?"
    foreign = "What does `const secret = [];` do?"
    q = query(stderr=stderr)

    for reply in (quoted, pointed):
        assert whole(reply, q) == reply and streamed(reply, q) == reply
    for shown in (whole(foreign, q), streamed(foreign, q)):
        assert "secret" not in shown and WITHHELD in shown


# --- 9.7 reading 1: a backtick span the learner did not write is checked as if it started a line ---


@pytest.mark.parametrize("span", ["import os", "from a import b", "return total", "def total(a):"])
def test_a_foreign_span_that_starts_with_a_statement_is_withheld_mid_sentence(span):
    reply = f"Have you tried `{span}` there?"

    assert GUARD.contains_code(reply) is True
    assert GUARD.contains_code(reply, learner_text="Why is total zero?") is True
    assert GUARD.contains_code(reply, learner_text=f"I wrote this:\n{span}") is False


@pytest.mark.parametrize("span", ["import", "return", "class", "total", "pathlib.Path.rglob()"])
def test_a_foreign_span_that_is_only_a_name_is_not_code(span):
    assert GUARD.contains_code(f"What do you expect `{span}` to do here?") is False


# --- review of the code: forms that a first version of A2 let through, and 9.7 readings 5 and 6 ---


@pytest.mark.parametrize("sentence", [
    "You could return `float(amount) * rate` there.",
    "Then return `len(rows)` from it.",
    "Try to return `total` * rate instead.",
    "Just return **float(amount)** there.",
    "The last step is return: float(amount) here.",
    "Then return rows[0] to the caller.",
])
def test_return_with_something_in_between_is_still_code(sentence):
    assert GUARD.contains_code(sentence) is True


@pytest.mark.parametrize("line", ["- import os", "> import os", "**import os**", "1. import os", "# from a import b"])
def test_an_import_behind_a_markdown_mark_is_code(line):
    reply = f"Look at this.\n{line}\nWhat do you expect?"

    assert GUARD.contains_code(reply) is True
    assert "import" not in GUARD.enforce(reply, AxisMode.SOCRATIC)


@pytest.mark.parametrize("text", ["-" * 5000 + " x", "* " * 3000 + "x", "1. " * 2000 + "x"])
def test_a_long_run_of_marks_is_checked_quickly(text):
    started = time.perf_counter()

    GUARD.contains_code(text)

    assert time.perf_counter() - started < 1.0


# --- review round 1: a quoted span must not carry other code through (A4, REVIEW.md item 3) ---

QUOTED = "def total(rows):\n    return sum(rows) len\nr = 1\nfor x in rows: import"


@pytest.mark.parametrize("reply", [
    "You should return `sum(rows)` / len(rows).",
    "Then return `sum`(rows) now.",
    "Try this: return `total` + tax, ok?",
    "Next, return `r` * 2.",
    "Just return `len`(rows) here.",
    "`total` = sum(rows) / len(rows)",
    "`def` total(a):",
    "`return` total * 2",
    "`import` os",
])
def test_quoting_a_word_does_not_carry_other_code_through(reply):
    q = query(code=QUOTED)

    for shown in (whole(reply, q), streamed(reply, q)):
        assert WITHHELD in shown and reply not in shown, shown


@pytest.mark.parametrize("reply", [
    "`r = 1` is on line 3, right?",
    "What does `return sum(rows)` hand back (and to whom)?",
    "Which value does `total` hold when it is empty?",
])
def test_talking_about_a_quoted_span_is_still_kept(reply):
    q = query(code=QUOTED)

    assert whole(reply, q) == reply
    assert streamed(reply, q) == reply


@pytest.mark.parametrize("reply", [
    "~~~\nif ok: import os\n~~~",
    "~~~python\ndata = 1\nif data: from os import system\n~~~",
    "Look:\n~~~\nfor r in rows: print(r)",
])
def test_nothing_inside_a_tilde_fence_reaches_the_learner(reply):
    shown = whole(reply, query())

    assert WITHHELD in shown
    assert "import" not in shown and "print(r)" not in shown


@pytest.mark.parametrize("sentence", ["Try return a%b there.", "Then return x<y here.", "So return total//2 now."])
def test_a_tight_operator_other_than_minus_or_slash_is_code(sentence):
    assert GUARD.contains_code(sentence) is True


def test_a_run_without_the_error_items_file_says_so(tmp_path, capsys):
    assert ob.run(tmp_path) == 0

    assert "No error-message questions" in capsys.readouterr().out


# --- review round 2: a quoted statement does not excuse the code that carries on after it ---


@pytest.mark.parametrize("reply", [
    "`return total` * (1 + rate)",
    "`return sum(rows)` / len(rows)",
    "`return rows` + sorted(extra)",
    "`return total` if total else sum(rows)",
    "``return total`` + tax(total)",
    "`return total`  * len(rows) fixes it.",
    "`import os`, sys",
    "`import os`; os.system('ls')",
    "**`return total`** * 2",
    "`return total` `* rate`",
])
def test_code_carrying_on_after_a_quoted_statement_is_withheld(reply):
    q = query(code="return total\nreturn sum(rows)\nreturn rows\nimport os")

    for size in (1, 3, 7, 999):
        assert WITHHELD in streamed(reply, q, size) and reply not in streamed(reply, q, size)
    assert WITHHELD in whole(reply, q) and reply not in whole(reply, q)


@pytest.mark.parametrize("reply", [
    "`return total` is on line 3, right?",
    "`import os`, and what does it bring in?",
    "`return total`. What do you expect it to hand back?",
    "**`return total`** is your last line. What does it give?",
])
def test_plain_words_after_a_quoted_statement_are_kept(reply):
    q = query(code="return total\nimport os")

    assert whole(reply, q) == reply
    assert streamed(reply, q) == reply


# --- review round 3: only plain words after a quoted statement excuse it ---


@pytest.mark.parametrize("reply", [
    "`return total` != len(rows)",
    "`return total` @ len(rows)",
    "`return total`, a + b(c)",
    "`return total`, rows[0]",
    "`return total`, *sorted(rows)",
    "`return total`, -len(rows)",
    "`import os` as o; o.system('x')",
    "`return s`um(rows) is the line.",
    "`return total`.strip()",
])
def test_anything_but_plain_words_after_a_quoted_statement_is_withheld(reply):
    q = query(code="def total(rows): return total / return sum(rows)\nimport os")

    for size in (1, 3, 7, 999):
        assert WITHHELD in streamed(reply, q, size) and reply not in streamed(reply, q, size)
    assert WITHHELD in whole(reply, q) and reply not in whole(reply, q)


@pytest.mark.parametrize("reply", [
    "What does `return total`?",
    "You wrote `return total` \u2014 what comes back?",
    "Look at your last line (`return total`). What is in it?",
    "`return total`, so what do you expect?",
])
def test_ordinary_sentences_around_a_quoted_statement_are_kept(reply):
    q = query(code="return total")

    assert whole(reply, q) == reply
    assert streamed(reply, q) == reply
