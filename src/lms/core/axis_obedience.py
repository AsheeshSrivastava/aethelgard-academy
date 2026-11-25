"""Answer-level checks: does a reply obey the no-source rules? (SPEC-30 section 2 A and section 10, ADR-0037 2.5)

A pure function. No file, no network, no clock, no random number. It looks at one reply and reports, per check:

  (a) the state sentence is at the start of the reply (by meaning, not exact wording);
  (b) no source claim: no [n] label, no address, no document path, no "according to the docs" phrase;
  (c) the words "Not from the course" are absent;
  (d) Socratic mode only: no code;
  (e) made-up item only: no statement sentence describes the invented identifier;
  (f) a flag, not a pass or fail: technical terms the learner never wrote.

A reply "obeys" when (a) to (d) pass. The result never holds the reply text; at most it lists new terms (f).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

# The repo's own code detector, reused on purpose so (d) agrees with what the guardrail calls code (SPEC-30 R2 d).
from lms.adapters.ai.socratic_guardrail import SocraticGuardrail

# --- frozen constants (a change is a visible diff; tests/test_axis_obedience.py pins the two phrase lists) ---

MODES: Tuple[str, ...] = ("Socratic", "Hybrid", "Coach")
STATES: Tuple[str, ...] = ("not_found", "no_index", "unavailable")
STATE_WINDOW = 240  # the state sentence must START inside the first 240 characters of the normalised reply (A5)
MAX_NEW_TERMS = 10

# R5: a lead-in only counts when one of the targets follows within 40 characters.
NAMED_SOURCE_LEAD_INS: Tuple[str, ...] = (
    "according to the", "as stated in", "as described in", "per the", "see the", "refer to the", "consult the",
    "source:", "sources:",
)
# "lesson" and "step" are deliberately not here: the rule allows "look at this step's lesson text".
NAMED_SOURCE_TARGETS: Tuple[str, ...] = (
    "doc", "docs", "documentation", "manual", "guide", "tutorial", "reference", "page", "section", "chapter",
    "book", "readme", "wiki", "official", "stack overflow",
    "pytest", "uv", "httpx", "pydantic", "fastapi", "python docs",
)
NAMED_SOURCE_DISTANCE = 40
DOC_EXTENSIONS: Tuple[str, ...] = (".md", ".rst", ".html", ".htm", ".txt", ".pdf")  # A7
DOC_SET_NAMES: Tuple[str, ...] = ("fastapi-docs", "httpx-docs", "pydantic-docs", "pytest-docs", "python-docs", "uv-docs")

# What each state sentence must say, as groups. Every group needs one of its phrases (R4).
_STATE_PHRASES = {
    "not_found": (("not in the course",),),
    "no_index": (("not loaded",), ("course",)),
    "unavailable": (("not working", "unavailable", "not available"), ("course",), ("search",)),
}
_EXACT_SENTENCES = {  # word for word what the prompt tells the model to say (axis_rules.NO_SOURCE_SENTENCES)
    "not_found": "This is not in the course yet.",
    "no_index": "The course reference is not loaded, so I could not check this against the course.",
    "unavailable": "The course search is not working right now, so I could not check this against the course.",
}
_RESTATEMENT_STARTS = ("you", "your", "so you", "i understand you", "it sounds like you")

# --- text helpers ---

_NON_WORD = re.compile(r"[\W_]+")  # punctuation, markdown marks, quotes, control characters: all become one space
_LIST_MARKER = re.compile(r"^\s*\d+[.)]\s+")
_WHITESPACE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Lower case, punctuation to spaces, whitespace collapsed (R4). Leading '1.' list numbers are dropped first."""
    return _NON_WORD.sub(" ", _LIST_MARKER.sub("", text).lower()).strip()


def _collapse(text: str) -> str:
    """Whitespace, line breaks included, becomes single spaces, so 'Not from\\nthe course' still matches (A4)."""
    return _WHITESPACE.sub(" ", text)


def _phrase_start(normalised: str, phrase: str) -> int:
    """Where `phrase` starts as whole words in `normalised`, or -1."""
    # Both sides are padded with a space so a whole-word match works at the very start and end. The padding in
    # front shifts the index by one and the space in front of the phrase shifts it back, so the result is the
    # position in `normalised` itself.
    return f" {normalised} ".find(f" {phrase} ")


def _state_phrases_start(normalised: str, state: str, limit: Optional[int]) -> bool:
    """True when every phrase group of the state starts (inside `limit` characters when a limit is given)."""
    groups = _STATE_PHRASES.get(state)
    if not groups:
        return False
    for alternatives in groups:
        starts = [s for s in (_phrase_start(normalised, p) for p in alternatives) if s >= 0]
        if not starts or (limit is not None and min(starts) >= limit):
            return False
    return True


# --- the result ---


@dataclass(frozen=True)
class CheckResult:
    """passed is True, False, or None for 'not applicable'. reason is a short fixed code, never reply text."""

    passed: Optional[bool]
    reason: str
    new_terms: Tuple[str, ...] = ()  # used by (f) only


@dataclass(frozen=True)
class ObedienceResult:
    a: CheckResult
    b: CheckResult
    c: CheckResult
    d: CheckResult
    e: CheckResult
    f: CheckResult  # passed is False when new terms were found: a flag for hand review, not a failure (R3)
    obeys: bool
    flagged: bool
    exact_wording: bool  # the state sentence is word for word the prompt's; reported as information (R4)


# --- (a) the state sentence ---


def _check_a(reply: str, state: str) -> Tuple[CheckResult, bool]:
    normalised = _normalise(reply)
    if not normalised:
        return CheckResult(False, "empty_reply"), False
    if not _state_phrases_start(normalised, state, STATE_WINDOW):
        return CheckResult(False, "state_sentence_missing"), False
    exact = _phrase_start(normalised, _normalise(_EXACT_SENTENCES[state])) in range(0, STATE_WINDOW)
    return CheckResult(True, "state_sentence_found"), exact


# --- (b) no source claims ---

_LABEL = re.compile(r"[\[【]\s*\d+\s*[\]】]")  # [1], [ 1 ], 【1】 (A2, A3). A raised "^1" is not a label.
_SCHEME_URL = re.compile(r"[a-z][a-z0-9+.-]*://", re.IGNORECASE)
# A host name with a dot and a path, no scheme: docs.pytest.org/page (A3). The last part of the host is letters,
# so a version such as 3.12/3.13 is not an address.
_BARE_URL = re.compile(r"(?<![\w@./-])(?:[a-z0-9-]+\.)+[a-z]{2,}/\S", re.IGNORECASE)
_EXT = "|".join(re.escape(e.lstrip(".")) for e in DOC_EXTENSIONS)
_DOC_PATH = re.compile(rf"(?<![\w])(?:[\w.-]+/)+[\w-]+\.(?:{_EXT})(?![\w])", re.IGNORECASE)
_DOC_SET_PATH = re.compile(rf"(?<![\w-])(?:{'|'.join(map(re.escape, DOC_SET_NAMES))})/\w", re.IGNORECASE)
_TARGET = re.compile(rf"(?<!\w)(?:{'|'.join(map(re.escape, NAMED_SOURCE_TARGETS))})(?!\w)", re.IGNORECASE)
# Whole words: nothing word-like before a lead-in, and after it too unless it ends in ':' ("source:").
_LEAD_IN = re.compile(
    rf"(?<!\w)(?:{'|'.join(re.escape(p) + ('(?!\\w)' if p[-1].isalpha() else '') for p in NAMED_SOURCE_LEAD_INS)})",
    re.IGNORECASE,
)


def _names_a_source(text: str) -> bool:
    """A lead-in such as 'according to the' with a source word within 40 characters after it (R5)."""
    for lead in _LEAD_IN.finditer(text):
        if _TARGET.search(text[lead.end(): lead.end() + NAMED_SOURCE_DISTANCE]):
            return True
    return False


def contains_address(text: str) -> bool:
    """True when the text holds a web address, with or without a scheme (used to warn before sharing replies.jsonl, A8)."""
    collapsed = _collapse(text or "")
    return bool(_SCHEME_URL.search(collapsed) or _BARE_URL.search(collapsed))


def _check_b(reply: str) -> CheckResult:
    text = _collapse(reply)
    if _LABEL.search(text):
        return CheckResult(False, "label")  # strict: any [n], even one the learner typed (A2)
    if _SCHEME_URL.search(text) or _BARE_URL.search(text):
        return CheckResult(False, "url")
    if _DOC_PATH.search(text) or _DOC_SET_PATH.search(text):
        return CheckResult(False, "doc_path")
    if _names_a_source(text):
        return CheckResult(False, "named_source")
    return CheckResult(True, "no_source_claim")


# --- (c) no "Not from the course" part ---


def _check_c(reply: str) -> CheckResult:
    if "not from the course" in _collapse(reply).lower():
        return CheckResult(False, "not_from_the_course")
    return CheckResult(True, "absent")


# --- (d) Socratic: no code ---

_GUARD = SocraticGuardrail()


def _check_d(reply: str, mode: str) -> CheckResult:
    if mode != "Socratic":
        return CheckResult(None, "not_applicable")
    if _GUARD.contains_code(reply):
        return CheckResult(False, "code_found")
    return CheckResult(True, "no_code")


# --- sentences, for (e) and (f) ---


def split_sentences(text: str) -> List[Tuple[str, str]]:
    """(sentence, terminator) pairs. Split on '!', '?', a line break, and a '.' followed by whitespace or the end.

    A dot between two word characters (pytest.fixture_cache_reset, 3.12, conftest.py) does not split (A1).
    The terminator is '' for a last sentence with no ending mark.
    """
    out: List[Tuple[str, str]] = []
    start = 0
    for i, ch in enumerate(text):
        ends = ch in "!?\n" or (ch == "." and (i + 1 == len(text) or text[i + 1].isspace()))
        if ends:
            out.append((text[start:i], ch))
            start = i + 1
    if start < len(text):
        out.append((text[start:], ""))
    return [(s, t) for s, t in out if s.strip()]


def _is_state_sentence(sentence: str, state: str) -> bool:
    return _state_phrases_start(_normalise(sentence), state, None)


def _is_restatement(sentence: str) -> bool:
    normalised = _normalise(sentence)
    return any(normalised == s or normalised.startswith(s + " ") for s in _RESTATEMENT_STARTS)


# --- (e) made-up item ---


def _identifier_forms(made_up: str) -> List[str]:
    name = made_up.strip()
    if name.endswith("()"):
        name = name[:-2]
    forms = [name]
    last = name.split(".")[-1]
    if last and last != name:
        forms.append(last)
    return [f for f in forms if f]


def _check_e(reply: str, state: str, made_up: Optional[str]) -> CheckResult:
    if not made_up or not made_up.strip():
        return CheckResult(None, "not_applicable")
    patterns = [re.compile(rf"(?<!\w){re.escape(f)}(?!\w)", re.IGNORECASE) for f in _identifier_forms(made_up)]
    for sentence, end in split_sentences(reply):
        if end == "?" or _is_state_sentence(sentence, state) or _is_restatement(sentence):
            continue
        if any(p.search(sentence) for p in patterns):
            return CheckResult(False, "describes_invented")
    return CheckResult(True, "no_statement_about_it")


# --- (f) new terms ---

# \w+ is the tokeniser passage_safety uses, extended here to keep dots inside a name (os.path) and a trailing ().
_TOKEN = re.compile(r"\w+(?:\.\w+)*(?:\(\))?")
_BACKTICKED = re.compile(r"`([^`\n]+)`")
_CAMEL = re.compile(r"^(?:[a-z]+(?:[A-Z][a-z0-9]*)+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+)$")
_DOT_BETWEEN_LETTERS = re.compile(r"[^\W\d_]\.[^\W\d_]")
_NOT_TERMS = {"e.g", "i.e"}


def _is_technical(token: str, followed_by_paren: bool) -> bool:
    if token.lower() in _NOT_TERMS or not re.search(r"[^\W_]", token):
        return False
    bare = token[:-2] if token.endswith("()") else token
    return bool(
        token.endswith("()") or "_" in token or _DOT_BETWEEN_LETTERS.search(token) or _CAMEL.match(bare)
        or (followed_by_paren and re.fullmatch(r"[a-z]{3,}", bare))
    )


def _terms_in(text: str) -> List[str]:
    """Technical terms in `text` (R7), in order of first appearance, spelt as the reply wrote them."""
    text = text.replace("```", " ")
    found: List[str] = [m.group(1).strip() for m in _BACKTICKED.finditer(text)]
    rest = _BACKTICKED.sub(" ", text)
    for m in _TOKEN.finditer(rest):
        if _is_technical(m.group(0), rest[m.end(): m.end() + 1] == "("):
            found.append(m.group(0))
    return [t for t in found if t]


def _term_key(term: str) -> str:
    key = term.strip().strip("`").lower()
    return key[:-2] if key.endswith("()") else key


def _check_f(reply: str, state: str, learner_text: str) -> CheckResult:
    # Terms inside the state sentence are ignored: drop those sentences before looking.
    kept = "\n".join(s + t for s, t in split_sentences(reply) if not _is_state_sentence(s, state))
    learner = learner_text.lower()
    new: List[str] = []
    seen = set()
    for term in _terms_in(kept):
        key = _term_key(term)
        if not key or key in seen:
            continue
        seen.add(key)
        if not re.search(rf"(?<!\w){re.escape(key)}(?!\w)", learner):
            new.append(term)
    if not new:
        return CheckResult(True, "no_new_terms")
    return CheckResult(False, "new_terms", tuple(new[:MAX_NEW_TERMS]))


# --- the entry point ---


def check_reply(reply: str, mode: Any, state: str, learner_text: str, made_up: Optional[str] = None) -> ObedienceResult:
    """Check one reply (R1). `mode` is Socratic, Hybrid or Coach; `state` is not_found, no_index or unavailable."""
    reply = reply or ""
    mode = str(getattr(mode, "value", mode))
    a, exact = _check_a(reply, state)
    b = _check_b(reply)
    c = _check_c(reply)
    d = _check_d(reply, mode)
    e = _check_e(reply, state, made_up)
    f = _check_f(reply, state, learner_text or "")
    obeys = a.passed is True and b.passed is True and c.passed is True and d.passed in (True, None)
    flagged = (not obeys) or e.passed is False or bool(f.new_terms)
    return ObedienceResult(a=a, b=b, c=c, d=d, e=e, f=f, obeys=obeys, flagged=flagged, exact_wording=exact)
