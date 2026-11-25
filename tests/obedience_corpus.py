"""Canned replies for the SPEC-30 checker tests (ADR-0037 section 2.5 / SPEC-30 R8).

Synthetic text only: questions and replies are made up for the tests and hold no answer keys.
No model is called. The state sentences come from the real prompt module, so a change there shows up here.
"""

from lms.adapters.ai.providers.axis_rules import NO_SOURCE_SENTENCES

MODES = ("Socratic", "Hybrid", "Coach")
STATES = ("not_found", "no_index", "unavailable")

EXACT = dict(NO_SOURCE_SENTENCES)

# Different words, same meaning (R4). Each is a good opening for its state.
PARAPHRASE = {
    "not_found": "That is not in the course at the moment.",
    "no_index": "I could not check this because the course reference is not loaded.",
    "unavailable": "Course search is unavailable right now, so I cannot check this.",
}

# The sentence of another state: a reply that opens with it is wrong for this state.
WRONG_FOR = {"not_found": "no_index", "no_index": "unavailable", "unavailable": "not_found"}

LEARNER = "Why does my loop skip the last row of the file?"

# What a good reply says after the state sentence, per mode: restates, asks, no facts, no code.
BODY = {
    "Socratic": (
        "You are asking why your loop skips the last row of the file. "
        "What do you expect the loop to do on the final row, and what do you see instead?"
    ),
    "Hybrid": (
        "It sounds like your loop leaves out the last row. "
        "Which row does it stop at, and how did you decide that? You could also reread this step's lesson text."
    ),
    "Coach": (
        "You want to know why the last row of the file is skipped. "
        "Try saying in your own words what the loop should do on the final row, then tell me what you see."
    ),
}


def good_reply(mode: str, state: str, paraphrase: bool = False) -> str:
    opening = (PARAPHRASE if paraphrase else EXACT)[state]
    return f"{opening} {BODY[mode]}"


# A made-up-item question: the invented identifier is not a real pytest helper.
MADE_UP = "pytest.fixture_cache_reset"
MADE_UP_LEARNER = "How do I use pytest.fixture_cache_reset to clear my fixtures between tests?"

CONFIDENT_ABOUT_MADE_UP = (
    f"{EXACT['not_found']} The fixture_cache_reset helper clears every cached fixture between tests."
)

FENCED_BLOCK = "```python\nfor row in rows:\n    print(row)\n```"

# Replies that must still obey (a to d all pass) although they look odd. (name, mode, state, reply)
NEAR_MISSES = [
    ("a greeting before the sentence", "Coach", "not_found",
     f"Hello, thanks for asking! {EXACT['not_found']} {BODY['Coach']}"),
    ("markdown emphasis and quotes", "Hybrid", "no_index",
     f'**"{EXACT["no_index"]}"** {BODY["Hybrid"]}'),
    ("a list marker before the sentence", "Socratic", "unavailable",
     f"- {EXACT['unavailable']}\n- {BODY['Socratic']}"),
    ("the step's lesson text", "Hybrid", "not_found",
     f"{EXACT['not_found']} Look at this step's lesson text and tell me which part matches your loop."),
    ("a heading, a table and a nested list around the sentence", "Hybrid", "not_found",
     f"# Note\n\n| a | b |\n|---|---|\n\n- - {EXACT['not_found']}\n\n{BODY['Hybrid']}"),
    ("a fenced block in Coach mode", "Coach", "not_found", f"{EXACT['not_found']} {BODY['Coach']}\n{FENCED_BLOCK}"),
    ("a fenced block in Hybrid mode", "Hybrid", "not_found", f"{EXACT['not_found']} {BODY['Hybrid']}\n{FENCED_BLOCK}"),
    ("inline backticks around the learner's own word", "Socratic", "not_found",
     f"{EXACT['not_found']} What does `loop` hold when it reaches the last row of the file?"),
    ("a path that is not a document", "Hybrid", "not_found",
     f"{EXACT['not_found']} Open tests/conftest.py yourself and tell me what you find. {BODY['Hybrid']}"),
    ("input/output is not a document path", "Hybrid", "not_found",
     f"{EXACT['not_found']} Think about input/output for one row. {BODY['Hybrid']}"),
    ("as stated in your message, with no source word near", "Coach", "not_found",
     f"{EXACT['not_found']} As stated in your message, the loop stops early. What do you see on the last row?"),
    ("the learner's whole question quoted back", "Coach", "not_found",
     f"{EXACT['not_found']} You wrote: {LEARNER} What did you try first?"),
    ("the sentence repeated fifty times", "Hybrid", "not_found", (EXACT["not_found"] + " ") * 50),
    ("a very long reply", "Hybrid", "no_index",
     f"{EXACT['no_index']} " + "What do you see on this row? " * 4000),
]

# One reply that breaks ONLY the named rule. (rule, mode, state, reply, made_up)
ONLY_THIS_RULE_BREAKS = [
    ("a", "Hybrid", "not_found", BODY["Hybrid"], None),
    ("b", "Hybrid", "not_found", f"{good_reply('Hybrid', 'not_found')} This is described in [1].", None),
    ("c", "Hybrid", "not_found",
     f"{good_reply('Hybrid', 'not_found')} Not from the course: loops count from zero.", None),
    ("d", "Socratic", "not_found", f"{good_reply('Socratic', 'not_found')}\n{FENCED_BLOCK}", None),
]
