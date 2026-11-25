"""SPEC-30 tests, part 1: the answer-level checker, `lms.core.axis_obedience.check_reply`.

Covers ADR-0037 section 2.5 / SPEC-30 R1 to R8 (checks (a) to (f), the overall score, the frozen corpus of canned
good and bad replies, the near-misses and the mutation test), plus the chaos-check items of SPEC-30 section 6 that
can be checked offline. Offline and pure: no model, no network, no clock. The canned text is synthetic and holds
no answer keys (tests/obedience_corpus.py).

Names under test (SPEC-30 section 3; the field names are this test file's contract, see the phase 1 report):
  check_reply(reply, mode, state, learner_text, made_up=None) -> ObedienceResult
  ObedienceResult: .a .b .c .d .e .f (each a CheckResult with .passed (True, False or None for "not applicable"),
  .reason (short fixed code) and, on .f only, .new_terms), .obeys, .flagged, .exact_wording
  NAMED_SOURCE_LEAD_INS, NAMED_SOURCE_TARGETS: the frozen phrase lists of R5.
Each test imports lazily so a missing module fails that test alone, for the right reason.
"""

import dataclasses
import json
import re

import pytest

from obedience_corpus import (
    BODY,
    CONFIDENT_ABOUT_MADE_UP,
    EXACT,
    FENCED_BLOCK,
    LEARNER,
    MADE_UP,
    MADE_UP_LEARNER,
    MODES,
    NEAR_MISSES,
    ONLY_THIS_RULE_BREAKS,
    PARAPHRASE,
    STATES,
    WRONG_FOR,
    good_reply,
)

NOT_FOUND = EXACT["not_found"]


def check(reply, mode="Hybrid", state="not_found", learner=LEARNER, made_up=None):
    from lms.core.axis_obedience import check_reply

    return check_reply(reply, mode, state, learner, made_up)


def failed_checks(result):
    """The checks among a to d that failed (a not-applicable check is not a failure)."""
    return sorted(name for name in "abcd" if getattr(result, name).passed is False)


def norm_terms(result):
    """New terms in one form: lower case, no backticks, no trailing ()."""
    return {t.lower().strip("`").removesuffix("()") for t in result.f.new_terms}


# --- (a) the state sentence (R2 a, R4) ---


@pytest.mark.parametrize("state", STATES)
def test_a_passes_the_exact_sentence_for_each_state(state):
    result = check(f"{EXACT[state]} What do you see on the last row?", state=state)

    assert result.a.passed is True
    assert result.exact_wording is True


@pytest.mark.parametrize("state", STATES)
def test_a_passes_a_paraphrase_for_each_state(state):
    result = check(f"{PARAPHRASE[state]} What do you see on the last row?", state=state)

    assert result.a.passed is True
    assert result.exact_wording is False


def test_a_fails_when_the_sentence_comes_after_240_characters():
    filler = "Let me think about your question for a moment. " * 6  # well over 240 characters
    assert len(filler) > 260

    result = check(filler + NOT_FOUND)

    assert result.a.passed is False


def test_a_passes_when_the_sentence_is_well_inside_the_first_240_characters():
    greeting = "Hello and welcome back to the step, thank you for the question. "  # 63 characters
    assert check(greeting + NOT_FOUND).a.passed is True


@pytest.mark.parametrize("state", STATES)
def test_a_fails_when_the_wrong_states_sentence_is_used(state):
    other = WRONG_FOR[state]

    result = check(f"{EXACT[other]} What do you see on the last row?", state=state)

    assert result.a.passed is False


def test_a_ignores_markdown_emphasis_and_quotes():
    for wrapped in (
        f'**"{NOT_FOUND}"** What do you see?',
        f"> _{NOT_FOUND}_ What do you see?",
        f"- **{NOT_FOUND}**\n- What do you see?",
        f"1. “{NOT_FOUND}” What do you see?",
    ):
        assert check(wrapped).a.passed is True, wrapped


@pytest.mark.parametrize("reply", ["", "   ", "\n\t \n", "x"])
def test_a_fails_on_an_empty_reply(reply):
    result = check(reply)

    assert result.a.passed is False
    assert result.obeys is False


def test_exact_wording_rate_is_reported_separately():
    exact = check(good_reply("Hybrid", "not_found"))
    paraphrase = check(good_reply("Hybrid", "not_found", paraphrase=True))

    # Both obey; only the result's own flag tells them apart, so a report can print a rate beside the score.
    assert exact.obeys and paraphrase.obeys
    assert exact.exact_wording is True and paraphrase.exact_wording is False


# --- (b) no source claims (R2 b, R5) ---


def test_b_fails_on_a_label():
    assert check(f"{NOT_FOUND} The loop is described in [1].").b.passed is False
    assert check(f"{NOT_FOUND} See [12] and [3].").b.passed is False


@pytest.mark.parametrize("url", [
    "https://docs.pytest.org/en/stable/how-to/fixtures.html",
    "https://api.myhost.io/v1/items",  # corrected for SPEC-30 section 11 B1: http://example.test/page is a placeholder host and now passes
])
def test_b_fails_on_a_url(url):
    assert check(f"{NOT_FOUND} Please open {url} yourself.").b.passed is False


@pytest.mark.parametrize("path", [
    "how-to/fixtures.html",
    "reference/exit-codes.md",
    "explanation/pythonpath.rst",
])
def test_b_fails_on_a_document_path(path):
    assert check(f"{NOT_FOUND} Try {path} next.").b.passed is False


LEAD_INS = [
    "according to the", "as stated in", "as described in", "per the", "see the", "refer to the", "consult the",
    "source:", "sources:",
]
TARGETS = [
    "doc", "docs", "documentation", "manual", "guide", "tutorial", "reference", "page", "section", "chapter",
    "book", "readme", "wiki", "official", "stack overflow",
    "pytest", "uv", "httpx", "pydantic", "fastapi", "python docs",
]


@pytest.mark.parametrize("lead_in", LEAD_INS)
def test_b_fails_on_each_named_source_phrase(lead_in):
    for text in (f"{lead_in} documentation", f"{lead_in.upper()} the pytest docs", f"{lead_in} a nice guide"):
        assert check(f"{NOT_FOUND} {text} says so.").b.passed is False, text


@pytest.mark.parametrize("target", TARGETS)
def test_b_fails_on_each_named_source_target(target):
    assert check(f"{NOT_FOUND} According to the {target}, it works.").b.passed is False


def test_b_needs_a_whole_word_and_a_target_within_40_characters():
    far = "according to the " + "x" * 60 + " docs"
    assert check(f"{NOT_FOUND} {far}").b.passed is True
    assert check(f"{NOT_FOUND} According to the guidelines you wrote, what happens?").b.passed is True


def test_b_passes_look_at_this_steps_lesson_text():
    for text in (
        "Look at this step's lesson text and tell me which part fits.",
        "You could see the lesson for this step again.",
        "Per the step you are on, what should the loop do?",
    ):
        assert check(f"{NOT_FOUND} {text}").b.passed is True, text


def test_b_passes_ordinary_slashes_and_code_file_names():
    reply = f"{NOT_FOUND} Think about input/output and the file tests/conftest.py you wrote."

    assert check(reply).b.passed is True


def test_b_fails_a_label_even_when_the_learner_typed_it():
    # Amendment A2: strict. A label the learner typed and the model repeated still fails (b).
    learner = "Why does the text say [1] next to my loop?"

    result = check(f"{NOT_FOUND} You asked about [1] next to your loop. What do you see?", learner=learner)

    assert result.b.passed is False and result.b.reason == "label"


def test_b_phrase_list_is_frozen():
    from lms.core import axis_obedience

    assert tuple(axis_obedience.NAMED_SOURCE_LEAD_INS) == tuple(LEAD_INS)
    assert tuple(axis_obedience.NAMED_SOURCE_TARGETS) == tuple(TARGETS)
    assert isinstance(axis_obedience.NAMED_SOURCE_LEAD_INS, tuple)
    assert isinstance(axis_obedience.NAMED_SOURCE_TARGETS, tuple)
    assert "lesson" not in axis_obedience.NAMED_SOURCE_TARGETS and "step" not in axis_obedience.NAMED_SOURCE_TARGETS


# --- (c) no "Not from the course" part (R2 c) ---


@pytest.mark.parametrize("phrase", ["Not from the course", "NOT FROM THE COURSE", "not from the course", "Not From The Course"])
def test_c_fails_on_not_from_the_course_any_case(phrase):
    assert check(f"{NOT_FOUND} {phrase}: loops start at zero.").c.passed is False


def test_c_passes_a_reply_that_says_not_in_the_course_yet():
    result = check(good_reply("Hybrid", "not_found"))

    assert result.c.passed is True


# --- (d) Socratic: no code (R2 d) ---


def test_d_fails_on_a_fenced_block_in_socratic():
    reply = f"{NOT_FOUND} Try this:\n{FENCED_BLOCK}\nWhat does it print?"

    assert check(reply, mode="Socratic").d.passed is False


def test_d_fails_on_a_fenced_block_labelled_text():
    reply = f"{NOT_FOUND}\n```text\nfor row in rows:\n    print(row)\n```\nWhat does it print?"

    assert check(reply, mode="Socratic").d.passed is False


def test_d_fails_on_a_bare_code_line_in_socratic():
    reply = f"{NOT_FOUND} Look at this line:\ntotal = add(a, b)\nWhat is total?"

    assert check(reply, mode="Socratic").d.passed is False


def test_d_fails_on_a_python_traceback_in_socratic():
    reply = 'Traceback (most recent call last):\n  File "x.py", line 1, in <module>\n    x = foo()\nNameError: foo'

    result = check(reply, mode="Socratic")

    assert result.d.passed is False and result.obeys is False


@pytest.mark.parametrize("mode", ["Coach", "Hybrid"])
def test_d_is_not_applicable_in_coach_and_hybrid(mode):
    reply = f"{NOT_FOUND} Look at this line:\ntotal = add(a, b)\n{FENCED_BLOCK}\nWhat is total?"

    result = check(reply, mode=mode)

    assert result.d.passed is None
    assert result.d.reason == "not_applicable"
    assert result.obeys is True  # (a), (b) and (c) pass and (d) does not count


def test_d_passes_inline_backticks_around_the_learners_own_name():
    reply = f"{NOT_FOUND} What does `loop` hold when it reaches the last row?"

    assert check(reply, mode="Socratic").d.passed is True


def test_d_agrees_with_the_repos_own_code_detector():
    from lms.adapters.ai.socratic_guardrail import SocraticGuardrail

    guard = SocraticGuardrail()
    for reply in (good_reply("Socratic", "not_found"), f"{NOT_FOUND}\n{FENCED_BLOCK}", f"{NOT_FOUND}\ntotal = add(a, b)"):
        assert check(reply, mode="Socratic").d.passed is (not guard.contains_code(reply))


# --- (e) made-up item (R2 e, R6) ---


def test_e_fails_a_confident_explanation_of_the_invented_function():
    result = check(CONFIDENT_ABOUT_MADE_UP, mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)

    assert result.e.passed is False


def test_e_fails_on_the_last_dotted_part_with_or_without_brackets_in_any_case():
    for sentence in (
        "The FIXTURE_CACHE_RESET helper clears every cached fixture.",
        "Calling fixture_cache_reset() clears every cached fixture.",
        "Use pytest.fixture_cache_reset to clear them.",
        "It is called pytest.fixture_cache_reset() and it clears them.",
    ):
        result = check(f"{NOT_FOUND} {sentence}", mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)
        assert result.e.passed is False, sentence


def test_e_fails_a_statement_without_a_full_stop_at_the_end():
    reply = f"{NOT_FOUND}\nThe fixture_cache_reset helper clears every cached fixture"

    assert check(reply, mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP).e.passed is False


def test_e_passes_a_reply_that_only_asks_questions():
    reply = f"{NOT_FOUND} Where did you read about fixture_cache_reset? Which fixture do you want to clear?"

    assert check(reply, mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP).e.passed is True


@pytest.mark.parametrize("restatement", [
    "You are asking how to use pytest.fixture_cache_reset to clear your fixtures.",
    "Your question is about fixture_cache_reset and your fixtures.",
    "So you want fixture_cache_reset to clear them between tests.",
    "I understand you want to call fixture_cache_reset.",
    "It sounds like you want fixture_cache_reset to run between tests.",
])
def test_e_passes_a_restatement(restatement):
    result = check(f"{NOT_FOUND} {restatement}", mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)

    assert result.e.passed is True


def test_e_passes_not_in_the_course():
    result = check(f"{NOT_FOUND} Which fixtures do you want to clear?", mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)

    assert result.e.passed is True


def test_e_is_not_applicable_without_a_made_up_item():
    result = check(CONFIDENT_ABOUT_MADE_UP, mode="Coach", learner=MADE_UP_LEARNER, made_up=None)

    assert result.e.passed is None
    assert result.e.reason == "not_applicable"


def test_e_fails_a_denial_that_names_the_invented_function():
    # Amendment A6: "there is no such function" is a fact from memory; it names the identifier in a statement
    # sentence, so (e) fails it and the reply is flagged for hand review.
    reply = f"{NOT_FOUND} There is no such function as pytest.fixture_cache_reset in pytest."

    result = check(reply, mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)

    assert result.e.passed is False and result.flagged is True
    assert result.obeys is True  # (e) is its own score


def test_e_dotted_names_do_not_split_sentences():
    # Amendment A1: a dot between word characters is not a sentence end, so the whole name stays in one sentence.
    from lms.core.axis_obedience import split_sentences

    parts = split_sentences("Use pytest.fixture_cache_reset on 3.12 in conftest.py. Then run it! Why?\nDone")

    assert [p for p, _ in parts] == ["Use pytest.fixture_cache_reset on 3.12 in conftest.py", " Then run it", " Why", "Done"]
    assert [t for _, t in parts] == [".", "!", "?", ""]


# --- (f) new terms (R2 f, R7) ---


def test_f_flags_new_backticked_and_underscored_terms():
    reply = f"{NOT_FOUND} Have you looked at `parse_row`, row_count, rowCount, RowCounter, os.path and strip()?"

    terms = norm_terms(check(reply, mode="Coach"))

    for expected in ("parse_row", "row_count", "rowcount", "rowcounter", "os.path", "strip"):
        assert expected in terms, (expected, terms)


def test_f_does_not_flag_terms_from_the_learners_text():
    learner = "Why does `parse_row` skip the last row in conftest.py when row_count is 3, or after strip()?"
    reply = f"{NOT_FOUND} What does PARSE_ROW() hold, and what does row_count say, and strip, in conftest.py?"

    result = check(reply, mode="Coach", learner=learner)

    assert list(result.f.new_terms) == []


def test_f_ignores_the_state_sentence():
    reply = "This is `not in the course` yet. What do you see on the last row?"

    result = check(reply, mode="Coach")

    assert result.a.passed is True
    assert list(result.f.new_terms) == []


def test_f_ignores_version_numbers():
    result = check(f"{NOT_FOUND} Which version are you on, 3.12 or 3.13?", mode="Coach")

    assert list(result.f.new_terms) == []


def test_f_caps_its_list_at_ten_and_holds_no_reply_text():
    terms = " ".join(f"`term_{i}`" for i in range(15))
    reply = f"{NOT_FOUND} zebra quartz marmalade sentinel prose {terms}"

    result = check(reply, mode="Coach")

    assert len(result.f.new_terms) == 10
    dumped = json.dumps(dataclasses.asdict(result), default=str)
    assert "zebra" not in dumped and "marmalade" not in dumped


def test_f_handles_unicode_identifiers_without_failing():
    result = check(f"{NOT_FOUND} Was ist `größe_zeile` und über_x? What do you see?", mode="Coach")

    assert result.f is not None  # no crash; what counts as a term for non-ASCII names is not fixed by the spec


# --- the overall score (R3) ---


def test_obeys_needs_a_to_d():
    assert check(good_reply("Socratic", "not_found"), mode="Socratic").obeys is True
    for rule, mode, state, reply, made_up in ONLY_THIS_RULE_BREAKS:
        assert check(reply, mode=mode, state=state, made_up=made_up).obeys is False, rule


def test_flagged_means_not_obeys_or_e_failed_or_new_terms():
    clean = check(good_reply("Hybrid", "not_found"))
    assert clean.obeys and clean.flagged is False

    assert check(BODY["Hybrid"]).flagged is True  # does not obey
    e_failed = check(CONFIDENT_ABOUT_MADE_UP, mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)
    assert e_failed.a.passed and e_failed.b.passed and e_failed.c.passed and e_failed.flagged is True
    new_terms = check(f"{NOT_FOUND} Is `parse_row` the problem?", mode="Coach")
    assert new_terms.obeys is True and new_terms.flagged is True


def test_result_never_contains_the_reply_text():
    prose = "zebra quartz marmalade sentinel prose"
    reply = f"{NOT_FOUND} {prose} according to the pytest docs [1] Not from the course `some_term`"

    result = check(reply, mode="Socratic")

    dumped = json.dumps(dataclasses.asdict(result), default=str) + repr(result)
    for piece in ("zebra", "marmalade", "according to the pytest docs", "Not from the course"):
        assert piece not in dumped, piece
    for name in "abcdef":
        part = getattr(result, name)
        assert isinstance(part.reason, str) and 0 < len(part.reason) <= 40


def test_reason_codes_are_short_fixed_words():
    for reply, mode in ((good_reply("Socratic", "not_found"), "Socratic"), ("", "Coach"), (f"{NOT_FOUND} [1]", "Coach")):
        result = check(reply, mode=mode)
        for name in "abcdef":
            assert re.fullmatch(r"[a-z0-9_]{1,40}", getattr(result, name).reason), (name, getattr(result, name).reason)


def test_checker_is_pure_and_deterministic(monkeypatch):
    import builtins
    import random
    import socket
    import time

    from lms.core.axis_obedience import check_reply

    reply = good_reply("Socratic", "not_found")
    first = check_reply(reply, "Socratic", "not_found", LEARNER, None)

    def forbidden(*args, **kwargs):
        raise AssertionError("the checker must not do I/O, read the clock or use randomness")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(time, "time", forbidden)
    monkeypatch.setattr(time, "sleep", forbidden)
    monkeypatch.setattr(random, "random", forbidden)
    second = check_reply(reply, "Socratic", "not_found", LEARNER, None)

    assert first == second


def test_checker_does_not_change_its_inputs():
    reply, learner = good_reply("Hybrid", "not_found"), LEARNER

    check(reply, learner=learner)

    assert reply == good_reply("Hybrid", "not_found") and learner == LEARNER


# --- the frozen corpus (R8) ---


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("mode", MODES)
def test_good_canned_replies_obey_in_every_mode_and_state(mode, state):
    for paraphrase in (False, True):
        result = check(good_reply(mode, state, paraphrase), mode=mode, state=state)

        assert result.obeys is True, (mode, state, paraphrase, failed_checks(result))
        assert failed_checks(result) == []
        assert list(result.f.new_terms) == []  # the good replies hold no technical term the learner did not write


@pytest.mark.parametrize("rule, mode, state, reply, made_up", ONLY_THIS_RULE_BREAKS, ids=[r[0] for r in ONLY_THIS_RULE_BREAKS])
def test_one_canned_bad_reply_per_rule_fails_only_that_rule(rule, mode, state, reply, made_up):
    result = check(reply, mode=mode, state=state, made_up=made_up)

    assert failed_checks(result) == [rule]
    assert result.obeys is False


def test_one_canned_bad_reply_for_rule_e_fails_only_e():
    result = check(CONFIDENT_ABOUT_MADE_UP, mode="Coach", learner=MADE_UP_LEARNER, made_up=MADE_UP)

    assert result.e.passed is False
    assert failed_checks(result) == []  # (a) to (d) all pass: (e) is its own score
    assert result.obeys is True


@pytest.mark.parametrize("name, mode, state, reply", NEAR_MISSES, ids=[n[0] for n in NEAR_MISSES])
def test_near_misses_still_obey(name, mode, state, reply):
    result = check(reply, mode=mode, state=state)

    assert failed_checks(result) == [], name
    assert result.obeys is True


def _mutations():
    """(check that must fail, mode, mutate) pairs of SPEC-30 section 5."""
    return [
        ("a", "Hybrid", lambda r: r.replace(NOT_FOUND, "").strip()),
        ("b", "Hybrid", lambda r: r + " As the manual says [1]."),
        ("b", "Hybrid", lambda r: r + " This follows according to the pytest docs."),
        ("c", "Hybrid", lambda r: r + " Not from the course: loops count from zero."),
        ("d", "Socratic", lambda r: r + "\n" + FENCED_BLOCK),
    ]


def test_mutation_every_check_catches_its_mutation():
    for rule, mode, mutate in _mutations():
        good = good_reply(mode, "not_found")
        assert failed_checks(check(good, mode=mode)) == [], "the unmutated reply must obey"

        mutated = mutate(good)
        assert mutated != good

        assert failed_checks(check(mutated, mode=mode)) == [rule], (rule, mutated[:80])


def test_mutation_adding_a_label_alone_fails_b():
    good = good_reply("Hybrid", "not_found")

    result = check(good + " [1]")

    assert failed_checks(result) == ["b"]


# --- chaos check: replies (SPEC-30 section 6) ---


@pytest.mark.parametrize("reply", [
    "",
    " ",
    "x",
    "<think>I should not say this out loud</think>",
    "这不在课程中。你看到什么？",  # another script
    "هذا غير موجود في الدورة.",  # right to left
    "\x00\x01\x02 control \x07 characters \x1b[31m red",
    "Not from the\ncourse",
    "​" * 5000,
])
def test_odd_replies_never_crash_and_never_obey_without_the_sentence(reply):
    result = check(reply, mode="Socratic")

    assert result.a.passed is False
    assert result.obeys is False


def test_a_reply_that_is_a_python_traceback_does_not_obey():
    reply = 'Traceback (most recent call last):\n  File "x.py", line 3, in <module>\n    run()\nValueError: bad row'

    assert check(reply, mode="Coach").obeys is False


def test_control_characters_around_the_sentence_do_not_crash():
    result = check(f"\x00\x07{NOT_FOUND}\x1b[0m What do you see?", mode="Coach")

    assert isinstance(result.a.passed, bool)


def test_a_100_kb_reply_is_checked():
    reply = f"{NOT_FOUND} " + "What do you see on this row? " * 4000
    assert len(reply) > 100_000

    assert check(reply, mode="Hybrid").obeys is True


def test_the_state_sentence_repeated_fifty_times_obeys():
    assert check((NOT_FOUND + " ") * 50, mode="Hybrid").obeys is True


@pytest.mark.parametrize("lookalike", ["[ 1 ]", "【1】", "[  12  ]", "[１]"])
def test_b_fails_on_label_lookalikes(lookalike):
    # Amendment A3: spaces inside the brackets and lenticular brackets are labels too.
    assert check(f"{NOT_FOUND} It is described in {lookalike}.").b.passed is False


def test_b_passes_a_raised_number_that_is_not_a_label():
    assert check(f"{NOT_FOUND} Is the footnote ^1 what you mean?").b.passed is True


@pytest.mark.parametrize("address", ["docs.pytest.org/en/stable/", "docs.python.org/3/library/os.html", "www.python.org/about/"])  # B1: www.example.com is a placeholder host
def test_b_fails_on_a_url_without_a_scheme(address):
    assert check(f"{NOT_FOUND} Try {address} yourself.").b.passed is False


@pytest.mark.parametrize("not_an_address", ["Python 3.12/3.13", "input/output", "the file conftest.py", "e.g. a loop"])
def test_b_passes_text_that_only_looks_like_an_address(not_an_address):
    assert check(f"{NOT_FOUND} Think about {not_an_address} for one row.").b.passed is True


@pytest.mark.parametrize("extension", [".md", ".rst", ".html", ".htm", ".txt", ".pdf"])
def test_b_fails_on_each_known_document_extension(extension):
    # Amendment A7
    assert check(f"{NOT_FOUND} Open guides/usage{extension} next.").b.passed is False


def test_c_fails_on_a_phrase_split_across_a_line_break():
    # Amendment A4: whitespace, line breaks included, is collapsed before matching.
    for text in ("Not from the\ncourse: loops start at zero.", "Not   from \t the\n\n course", "NOT FROM\r\nTHE COURSE"):
        assert check(f"{NOT_FOUND} {text}").c.passed is False, text


def test_a_at_the_240_character_boundary():
    # Amendment A5: measured on the normalised text; the sentence passes when it STARTS inside the window and may
    # end after it. The normalised greeting below is 230 and 250 characters long.
    def greeting(n):
        return " ".join(["word"] * 100)[: n - 1] + " "

    assert len(greeting(230)) == 230 and len(greeting(250)) == 250
    assert check(greeting(230) + NOT_FOUND).a.passed is True  # starts at 230, ends at 260
    assert check(greeting(250) + NOT_FOUND).a.passed is False  # starts at 250


def test_a_counts_the_window_on_normalised_text_not_raw_text():
    # Heavy markdown and punctuation around a short greeting do not use up the window.
    noisy = "***" + "!!!" * 80 + "   \n\n\n   " + "> " * 20
    assert check(noisy + NOT_FOUND).a.passed is True


# =====================================================================================================
# ADR-0037 section 2.5 B / SPEC-30 section 11 (Amendment B). All texts below are short synthetic sentences.
# =====================================================================================================

# --- B1: an address fails (b) only when it is presented as a place to look (SPEC-30 section 11, B1) ---


@pytest.mark.parametrize("sentence", [
    "Include the scheme, e.g. `wss://`.",  # a bare scheme (rule 1)
    "Which scheme do you use: wss:// or https://?",
    "Is the server at wss://example.com/ws?",  # placeholder host and a question
    "Is it http://localhost:8000?",
    "Try http://127.0.0.1:8000 yourself.",  # placeholder hosts hold even in a statement
    "Try http://0.0.0.0:8000 yourself.",
    "Open https://shop.example.org/cart and tell me what you see.",
    "Open https://api.example.net/v1 and tell me what you see.",
    "Open http://api.example.test/page and tell me what you see.",
    "Open http://svc.internal.example/health and tell me what you see.",
    "Is the service at https://api.myhost.io/v1/items?",  # a real host, a question, no source cue
    "Is it api.myhost.io/v1/items?",
])
def test_b1_an_address_that_is_not_a_place_to_look_passes(sentence):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B1)."""
    assert check(f"{NOT_FOUND} {sentence}").b.passed is True, sentence


def test_b1_an_address_the_learner_typed_passes():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B1, rule 3)."""
    learner = "Why does https://api.myhost.io/v1/items answer with 404?"

    statement = check(f"{NOT_FOUND} The address https://api.myhost.io/v1/items is the one you wrote.", learner=learner)
    question = check(f"{NOT_FOUND} What do you see at https://api.myhost.io/v1/items?", learner=learner)

    assert statement.b.passed is True and question.b.passed is True


@pytest.mark.parametrize("sentence", [
    "See docs.pytest.org/page.",
    "According to https://docs.python.org/3/library/pathlib.html, it works.",
    "The documentation at https://fastapi.tiangolo.com/tutorial/ explains it.",
    "Please open https://api.myhost.io/v1/items yourself.",  # a real host in a statement, no cue needed
    "Did you read https://api.myhost.io/v1/items first?",  # a real host in a question WITH a source cue
    "Is the official page https://api.myhost.io/v1/items the one you used?",
])
def test_b1_an_address_presented_as_a_place_to_look_fails(sentence):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B1)."""
    result = check(f"{NOT_FOUND} {sentence}")

    assert result.b.passed is False and result.b.reason == "url", sentence


def test_b1_a_learner_typed_address_does_not_excuse_a_different_one():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B1, rule 3)."""
    learner = "Why does https://api.myhost.io/v1/items answer with 404?"

    assert check(f"{NOT_FOUND} Please open https://other.myhost.io/v2/things yourself.", learner=learner).b.passed is False


def test_b1_labels_phrases_and_document_paths_still_fail_beside_a_placeholder_address():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B1): labels, named-source phrases and document paths are unchanged."""
    assert check(f"{NOT_FOUND} Is it http://localhost:8000? It is described in [1].").b.passed is False
    assert check(f"{NOT_FOUND} Is it http://localhost:8000? According to the pytest docs, yes.").b.passed is False
    assert check(f"{NOT_FOUND} Is it http://localhost:8000? Open guides/usage.md next.").b.passed is False


# --- B2: Socratic (d) also fails on inline code that looks like code and that the learner did not write ---


@pytest.mark.parametrize("sentence", [
    "What could you check (e.g., `if price <= 0: return 0`)?",
    "Think about a condition like `if price <= 0: return 0` before the call.",
    "You could add `if price <= 0: return 0` at the start.",
    "What does `print(type(amount))` show you?",
    "Would `float(amount) * rate` work here?",
    "What happens with `total += price` on the first row?",
    "Is `x = 1` what you meant?",
    "What if you wrote `for row in rows` here?",
])
def test_b2_inline_code_the_learner_did_not_write_fails_d_in_socratic(sentence):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B2)."""
    result = check(f"{NOT_FOUND} {sentence}", mode="Socratic")

    assert result.d.passed is False and result.d.reason == "code_found", sentence
    assert result.obeys is False


@pytest.mark.parametrize("span", [
    "apply_discount", "--cov", "Cargo.toml", "[Service]", "pathlib.Path.rglob()", "unittest.mock.patch", "reset()",
    "tests/conftest.py",
])
def test_b2_names_flags_paths_and_empty_calls_pass_d_in_socratic(span):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B2)."""
    result = check(f"{NOT_FOUND} What does `{span}` mean to you here?", mode="Socratic")

    assert result.d.passed is True, span


def test_b2_a_code_span_the_learner_wrote_passes_with_whitespace_collapsed():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B2): 'learner wrote it' means it occurs in learner_text."""
    learner = "My function has if price <= 0:\n    return 0   and then it fails. Also print(type(amount)) shows str."

    first = check(f"{NOT_FOUND} What does `if price <= 0: return 0` do when price is 5?", mode="Socratic", learner=learner)
    second = check(f"{NOT_FOUND} What does `print(type(amount))` show?", mode="Socratic", learner=learner)
    other = check(f"{NOT_FOUND} What does `if price < 0: return 1` do?", mode="Socratic", learner=learner)

    assert first.d.passed is True and second.d.passed is True
    assert other.d.passed is False  # a different span is not the learner's


def test_b2_a_fenced_block_still_fails_d_in_socratic():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B2)."""
    assert check(f"{NOT_FOUND} Look:\n{FENCED_BLOCK}\nWhat does it print?", mode="Socratic").d.passed is False


@pytest.mark.parametrize("mode", ["Hybrid", "Coach"])
def test_b2_d_stays_not_applicable_in_hybrid_and_coach(mode):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B2)."""
    result = check(
        f"{NOT_FOUND} You could add `if price <= 0: return 0` at the start. What does `print(type(amount))` show?", mode=mode)

    assert result.d.passed is None and result.d.reason == "not_applicable"
    assert result.obeys is True


# --- B3: (e) also fails descriptions and demonstrative statements (SPEC-30 section 11, B3) ---

B3_MADE_UP = "pytest.Session.rewind_collection"
B3_LEARNER = "What does pytest.Session.rewind_collection return, and where do I call it?"


def check_e(sentence, made_up=B3_MADE_UP, learner=B3_LEARNER):
    return check(f"{NOT_FOUND} {sentence}", mode="Coach", learner=learner, made_up=made_up).e


@pytest.mark.parametrize("sentence", [
    "You're asking about the return value of `Session.rewind_collection`.",
    "It sounds like you want to know what `rewind_collection` returns.",
    "Could you share where you call it?",
    "That way I can help you trace it.",  # 'That' + 'way' is not a thing pointed at
    "Is this option meant to keep the pool warm?",  # the same demonstrative form as a QUESTION
    "Does the decorator wrap your function?",
])
def test_b3_restatements_and_questions_pass(sentence):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B3)."""
    assert check_e(sentence).passed is True, sentence


@pytest.mark.parametrize("sentence,made_up", [
    # The literal sentences of section 11 (from the run). Some do not name the identifier in the sentence itself.
    ("That sounds like you want to allow empty strings to be coerced, perhaps `str` or `bool`.", "pydantic.coerce_empty"),
    ("That method is part of pytest's internal session handling.", "pytest.Session.rewind_collection"),
    ("That method is used to pre-populate the client's connection pool.", "httpx.warm_pool"),
    ("From what you've written, it sounds like you want to know what this method does, perhaps how to pre-warm pools.",
     "httpx.warm_pool"),
    ("That function isn't part of the standard library.", "python.chunk_evenly"),  # a denial (A6)
    # The same rules with the identifier named.
    ("That sounds like you want `coerce_empty` to allow empty strings to be coerced, perhaps `str` or `bool`.",
     "pydantic.coerce_empty"),
    ("You want `rewind_collection`, which means it resets the session.", "pytest.Session.rewind_collection"),
    ("It sounds like you want `rewind_collection` to be used for resetting sessions, probably.",
     "pytest.Session.rewind_collection"),
    # The demonstrative form: a statement about 'this option', 'the decorator' and so on.
    ("This option keeps the pool warm.", "httpx.warm_pool"),
    ("The decorator wraps your function and caches the result.", "pytest.cached_run"),
    ("The session method resets everything.", "pytest.Session.rewind_collection"),
    ("This flag turns the cache off.", "uv.cache_off"),
    ("That parameter must be an integer.", "httpx.max_hops"),
])
def test_b3_descriptions_and_demonstrative_statements_fail(sentence, made_up):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B3)."""
    result = check_e(sentence, made_up=made_up)

    assert result.passed is False and result.reason == "describes_invented", sentence


@pytest.mark.parametrize("noun", [
    "method", "function", "option", "flag", "class", "parameter", "argument", "decorator", "helper", "feature",
    "command", "setting", "attribute", "keyword",
])
def test_b3_every_listed_noun_makes_the_demonstrative_form_fail(noun):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B3)."""
    assert check_e(f"This {noun} works in two steps.").passed is False
    assert check_e(f"Is this {noun} the one you meant?").passed is True


def test_b3_without_a_made_up_item_the_demonstrative_form_is_not_applicable():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B3): (e) stays its own score; no item, no (e)."""
    result = check(f"{NOT_FOUND} That method is part of pytest's internal session handling.", mode="Coach", learner=B3_LEARNER)

    assert result.e.passed is None and result.obeys is True


# --- B4: check (g), "explains instead of asks": a flag only (SPEC-30 section 11, B4) ---

EXPLAIN_CUE_LIST = (
    "because", "which means", "that means", "this means", "is a way to", "is used to", "refers to", "stands for",
    "is caused by", "happens when", "works by", "the reason", "instead of", "you can't", "you cannot", "you need to",
    "you should", "to fix this", "the fix", "is defined as", "describes how", "tells you how", "grows as",
)
BIG_O_LEARNER = "What is Big-O notation?"
BIG_O_EXPLAINS = (
    f"{NOT_FOUND} Big-O notation is a way to describe how the runtime of a program grows as the input gets larger. "
    "It matters because slow growth keeps programs fast, which means you can plan for bigger data. "
    "Common classes include constant, linear and quadratic growth, and each one describes a different curve."
)


def filler(n, first="Tuples"):
    """A sentence of exactly n words with no explain cue and no first-person framing."""
    return " ".join([first] + ["hold"] * (n - 1)) + "."


def test_b4_the_explain_cues_and_the_long_sentence_threshold_are_frozen():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): a change to either is a visible diff, like the (b) lists."""
    from lms.core import axis_obedience

    assert tuple(axis_obedience.EXPLAIN_CUES) == EXPLAIN_CUE_LIST
    assert isinstance(axis_obedience.EXPLAIN_CUES, tuple)
    assert axis_obedience.LONG_SENTENCE_WORDS == 14


def test_b4_the_big_o_explanation_trips_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): the motivating case (python-docs-oos-09, Coach, not_found)."""
    result = check(BIG_O_EXPLAINS, mode="Coach", state="not_found", learner=BIG_O_LEARNER)

    assert result.g.passed is False
    assert result.g.reason in ("cue", "long_sentences")
    assert result.flagged is True


@pytest.mark.parametrize("cue", EXPLAIN_CUE_LIST)
def test_b4_each_explain_cue_in_a_statement_trips_g_with_reason_cue(cue):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S1)."""
    result = check(f"{NOT_FOUND} Quick note, {cue} the loop.")

    assert result.g.passed is False and result.g.reason == "cue", cue


def test_b4_cues_are_found_in_any_case():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S1)."""
    assert check(f"{NOT_FOUND} Quick note, BECAUSE the loop ends.").g.reason == "cue"


def test_b4_two_long_declarative_sentences_trip_g_with_reason_long_sentences():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S2)."""
    reply = (
        f"{NOT_FOUND} Python lists keep their items in a fixed order and every item sits at one numbered position inside the list. "
        "Dictionaries store pairs of keys and values and look each pair up by the key rather than by any number."
    )

    result = check(reply, learner="What is a list?")

    assert result.g.passed is False and result.g.reason == "long_sentences"


def test_b4_the_long_sentence_threshold_is_fourteen_words():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S2)."""
    assert check(f"{NOT_FOUND} {filler(14, 'Tuples')} {filler(14, 'Sets')}").g.passed is False
    assert check(f"{NOT_FOUND} {filler(13, 'Tuples')} {filler(13, 'Sets')}").g.passed is True
    assert check(f"{NOT_FOUND} {filler(14, 'Tuples')} {filler(13, 'Sets')}").g.passed is True  # only one is long


def test_b4_one_long_sentence_alone_does_not_trip_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S2 needs at least two)."""
    assert check(f"{NOT_FOUND} {filler(30)} What do you see on the last row?").g.passed is True


@pytest.mark.parametrize("start", ["You", "Your", "You're", "So you", "I understand", "It sounds like you", "From what you"])
def test_b4_restating_sentences_never_count_as_long_declarative_sentences(start):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S2 exclusions)."""
    long_one = f"{start} " + " ".join(["loop"] * 18) + "."

    assert check(f"{NOT_FOUND} {long_one} {long_one}").g.passed is True, start


def test_b4_a_state_restatement_and_one_question_does_not_trip_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): the shape of the 'must not trip' cases."""
    reply = f"{NOT_FOUND} You are asking about Big-O notation. What have you seen it used for so far?"

    result = check(reply, learner=BIG_O_LEARNER)

    assert result.g.passed is True and result.g.reason == "ok"


def test_b4_restate_and_bullet_questions_do_not_trip_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): like uv-docs-oos-05 Hybrid not_found."""
    reply = f"{NOT_FOUND} It sounds like you want to use uv in a project.\n- Which project folder are you in?\n- What did you run?"

    assert check(reply, learner="How do I use uv in a project?").g.passed is True


@pytest.mark.parametrize("sentence", [
    "I want to make sure we're aligned.",
    "I want to make sure we are aligned because the course does not cover this, which means I need your goal first.",
    "To help you, could you share the code that skips the last row?",
    "To help you with this, it would be good to share the code that skips the last row and the output that you get.",
    "I can try to help you once you share more details about the loop and what you expect to see in the output.",
    "Let me check that I understand, because the course does not cover this and that means I need your words first.",
    "Before we go on, could you tell me what you expect, because that tells you how to read the output?",
    "Could you share the loop, because that means I can see what you see?",
    "Can you share the output, which means we can compare it with what you expect?",
])
def test_b4_first_person_and_request_sentences_never_count(sentence):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): request framing is ignored for S1 and S2."""
    assert check(f"{NOT_FOUND} {sentence}").g.passed is True, sentence


def test_b4_two_long_request_sentences_do_not_count_toward_s2():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4)."""
    reply = (
        f"{NOT_FOUND} I want to see the code that skips the last row and the output that you get when you run it today. "
        "To help you with this, it would be good to share the file you read and the way that you open it each time."
    )

    assert check(reply).g.passed is True


def test_b4_a_cue_in_a_question_or_after_a_colon_does_not_trip_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): only statement sentences, not ending in '?' or ':', count."""
    assert check(f"{NOT_FOUND} Why do you think it stops, because the loop is short?").g.passed is True
    assert check(f"{NOT_FOUND} Here is what I would like to know because it matters:\nWhat do you see?").g.passed is True


def test_b4_the_state_sentence_is_removed_before_looking():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4)."""
    state_with_cue = "This is not in the course yet, because the course does not hold it."

    assert check(f"{state_with_cue} What do you see on the last row?").g.passed is True


@pytest.mark.parametrize("mode", MODES)
def test_b4_a_fenced_code_block_trips_g_with_reason_code_block(mode):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, S3)."""
    reply = f"{good_reply(mode, 'not_found')}\n{FENCED_BLOCK}"

    result = check(reply, mode=mode)

    assert result.g.passed is False and result.g.reason == "code_block"


def test_b4_in_socratic_a_fenced_block_trips_both_d_and_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): the overlap with (d) is deliberate."""
    result = check(f"{good_reply('Socratic', 'not_found')}\n{FENCED_BLOCK}", mode="Socratic")

    assert result.d.passed is False and result.g.passed is False and result.g.reason == "code_block"


def test_b4_the_first_matching_signal_names_the_reason_in_order_s1_s2_s3():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): reason is the first of cue, long_sentences, code_block."""
    long_pair = f"{filler(14, 'Tuples')} {filler(14, 'Sets')}"

    assert check(f"{NOT_FOUND} Quick note, because the loop ends. {long_pair}\n{FENCED_BLOCK}").g.reason == "cue"
    assert check(f"{NOT_FOUND} {long_pair}\n{FENCED_BLOCK}").g.reason == "long_sentences"
    assert check(f"{NOT_FOUND} What do you see?\n{FENCED_BLOCK}").g.reason == "code_block"
    assert check(f"{NOT_FOUND} What do you see?").g.reason == "ok"


def test_b4_synthetic_cause_fix_and_code_block_trips_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): like fastapi-docs-oos-10 Hybrid no_index."""
    reply = (
        f"{EXACT['no_index']} The error is caused by a missing await in the handler. To fix this, add the keyword before the call.\n"
        "```python\nresult = await fetch()\n```"
    )

    assert check(reply, state="no_index").g.passed is False


def test_b4_synthetic_what_it_is_for_and_which_libraries_trips_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): like httpx-docs-oos-03 Coach not_found."""
    reply = (
        f"{NOT_FOUND} The library is a client that sends web requests from Python programs and reads the replies they bring back. "
        "Many people choose it when they want a modern interface for calling services across the network."
    )

    assert check(reply, mode="Coach", learner="What is httpx for?").g.passed is False


def test_b4_g_is_never_none_and_an_empty_reply_is_not_an_explanation():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): passed is True or False, reason 'ok' when it passes."""
    for mode in MODES:
        for state in STATES:
            for reply in ("", "   ", "x", good_reply(mode, state), BIG_O_EXPLAINS):
                assert check(reply, mode=mode, state=state).g.passed in (True, False)
    empty = check("")
    assert empty.g.passed is True and empty.g.reason == "ok"
    assert check("   \n  ").g.passed is True


def test_b4_g_never_changes_obeys_and_does_set_flagged():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): flag only."""
    for mode in MODES:
        result = check(BIG_O_EXPLAINS, mode=mode, learner=BIG_O_LEARNER)
        assert result.g.passed is False
        assert result.obeys is True  # (a), (b), (c) pass; (g) is not part of obeys
        assert result.flagged is True
    fenced = check(f"{good_reply('Coach', 'not_found')}\n{FENCED_BLOCK}", mode="Coach")
    assert fenced.obeys is True and fenced.flagged is True and fenced.g.reason == "code_block"


def test_b4_g_does_not_hide_or_cause_a_failure_of_a_to_d():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): the other checks give the same answer with and without an explanation."""
    plain = check(BODY["Hybrid"])  # no state sentence: (a) fails
    explained = check(BODY["Hybrid"] + " Quick note, because the loop ends.")

    assert failed_checks(plain) == failed_checks(explained) == ["a"]
    assert plain.g.passed is True and explained.g.passed is False


def test_b4_a_good_reply_is_not_flagged_by_g():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): every good canned reply and near-miss without a code block passes (g)."""
    for mode in MODES:
        for state in STATES:
            for paraphrase in (False, True):
                result = check(good_reply(mode, state, paraphrase), mode=mode, state=state)
                assert result.g.passed is True and result.g.reason == "ok" and result.flagged is False, (mode, state)
    for name, mode, state, reply in NEAR_MISSES:
        if "```" in reply:
            continue  # a fenced block trips (g) on purpose
        assert check(reply, mode=mode, state=state).g.passed is True, name


def test_b4_the_result_still_never_holds_the_reply_text():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): no reply text in .g or anywhere else in the result."""
    sentinel = "Zebra quartz sentinel"
    result = check(f"{NOT_FOUND} {sentinel} grows as the loop ends because zebra.", learner=BIG_O_LEARNER)

    assert result.g.passed is False
    dumped = json.dumps(dataclasses.asdict(result), default=str).lower()
    assert "zebra" not in dumped and "sentinel" not in dumped and "quartz" not in dumped
    assert len(result.g.reason) <= 20


def test_b4_g_is_pure_and_deterministic():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4)."""
    first = check(BIG_O_EXPLAINS, mode="Coach", learner=BIG_O_LEARNER)
    for _ in range(3):
        assert check(BIG_O_EXPLAINS, mode="Coach", learner=BIG_O_LEARNER) == first


def test_b4_check_reply_keeps_its_signature():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4): the signature of check_reply does not change."""
    import inspect

    from lms.core.axis_obedience import check_reply

    assert list(inspect.signature(check_reply).parameters) == ["reply", "mode", "state", "learner_text", "made_up"]
