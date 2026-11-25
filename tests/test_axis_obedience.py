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
    "http://example.test/page",
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


@pytest.mark.parametrize("address", ["docs.pytest.org/en/stable/", "docs.python.org/3/library/os.html", "www.example.com/a"])
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
