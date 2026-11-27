"""Answer-level checks: does a reply obey the no-source rules? (SPEC-30 section 2 A and section 10, ADR-0037 2.5)

A pure function. No file, no network, no clock, no random number. It looks at one reply and reports, per check:

  (a) the state sentence is at the start of the reply (by meaning, not exact wording);
  (b) no source claim: no [n] label (an index such as rows[1] is not one), no address, no document path, no
      "according to the docs" phrase;
  (c) the words "Not from the course" are absent;
  (d) Socratic mode only: no code;
  (e) made-up item only: no statement sentence describes the invented identifier;
  (f) a flag, not a pass or fail: technical terms the learner never wrote;
  (g) a flag too (amendment B4): the reply explains instead of asking. It never changes "obeys".

A reply "obeys" when (a) to (d) pass. The result never holds the reply text; at most it lists new terms (f).

Apart from `check_reply`, three turn-quality checks (SPEC-33 section 7), flags only: `check_anchored`,
`check_one_question` and `check_one_action`.
"""

from __future__ import annotations

import builtins
import keyword
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

# The repo's own code detector, reused on purpose so (d) agrees with what the guardrail calls code (SPEC-30 R2 d).
from lms.adapters.ai.socratic_guardrail import SocraticGuardrail

# Which set of rules scored a run (SPEC-30 section 11, B5): "A" = the first run's rules, "B" = amendment B,
# "C" = SPEC-31 section 9.3 (an index is not a label; (d) uses the 9.2 detector with the learner's text),
# "D" = SPEC-33 section 7 (the turn-quality checks are counted beside them; (a) to (g) are unchanged).
CHECKER_VERSION = "D"

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
# B3: a speculative restatement guesses at what the learner means; it is exempt only when it holds no description cue.
_SPECULATIVE_STARTS = ("that sounds like", "it sounds like", "from what you")

# B4 (g): words that mark an explanation. Frozen like the (b) lists: a change is a visible diff.
EXPLAIN_CUES: Tuple[str, ...] = (
    "because", "which means", "that means", "this means", "is a way to", "is used to", "refers to", "stands for",
    "is caused by", "happens when", "works by", "the reason", "instead of", "you can't", "you cannot", "you need to",
    "you should", "to fix this", "the fix", "is defined as", "describes how", "tells you how", "grows as",
)
LONG_SENTENCE_WORDS = 14  # S2: a "long" sentence has this many words or more (counted by whitespace)

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
    g: CheckResult  # passed is False when the reply explains instead of asking: flag only, never in obeys (B4)
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
_INDEX_FORM = re.compile(r"\[\d+\]")


def _has_source_label(text: str) -> bool:
    """True when some label stands alone (SPEC-31 C1).

    `[n]` written directly after a name, `]` or `)` is an index, by the rule that keeps it in the shown reply
    (passage_safety.strip_unknown_labels). Spaced and lenticular forms are never an index.
    """
    for found in _LABEL.finditer(text):
        before = text[found.start() - 1: found.start()]
        if not (_INDEX_FORM.fullmatch(found.group(0)) and (before.isalnum() or before in ("_", ")", "]"))):
            return True
    return False


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


# B1: an address fails (b) only when it is presented as a place to look.
_ADDRESS = re.compile(
    r"[a-z][a-z0-9+.-]*://[^\s`'\"<>)]*|(?<![\w@./-])(?:[a-z0-9-]+\.)+[a-z]{2,}/[^\s`'\"<>)]*", re.IGNORECASE)
_PLACEHOLDER_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0")
_PLACEHOLDER_DOMAINS = ("example.com", "example.org", "example.net")  # and every subdomain of them
_PLACEHOLDER_SUFFIXES = (".example", ".test")
_SOURCE_CUE = re.compile(
    r"(?<!\w)(?:see|read|refer to|consult|according to|per|source|docs|documentation|official|guide|tutorial|reference"
    r"|manual)(?!\w)",
    re.IGNORECASE,
)


def _host_of(address: str) -> str:
    """The host of an address, lower case, without port or path. Empty for a bare scheme such as 'wss://'."""
    rest = address.split("://", 1)[1] if "://" in address else address
    return re.match(r"[^/:?#\s]*", rest).group(0).lower()


def _is_placeholder_host(host: str) -> bool:
    return (host in _PLACEHOLDER_HOSTS or host.endswith(_PLACEHOLDER_SUFFIXES)
            or any(host == d or host.endswith("." + d) for d in _PLACEHOLDER_DOMAINS))


def _presents_an_address(reply: str, learner_text: str) -> bool:
    """B1: True when some address in the reply is a place to look: all four conditions of the rule hold."""
    learner = _collapse(learner_text).lower()
    for start, end, terminator in _sentence_spans(reply):
        sentence = reply[start:end]
        for found in _ADDRESS.finditer(sentence):
            address = found.group(0).rstrip(".,;:!?]}")
            host = _host_of(address)
            if not host or _is_placeholder_host(host) or address.lower() in learner:
                continue  # a bare scheme, a placeholder, or an address the learner wrote
            around = sentence[:found.start()] + " " + sentence[found.end():]  # the address itself is not a cue
            if terminator != "?" or _SOURCE_CUE.search(around):
                return True
    return False


def _check_b(reply: str, learner_text: str = "") -> CheckResult:
    text = _collapse(reply)
    if _has_source_label(text):
        return CheckResult(False, "label")  # strict: any lone [n], even one the learner typed (A2)
    if _presents_an_address(reply, learner_text):
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


# B2: inline code that looks like code: a statement word with something after it, an operator, or a call with an argument.
_FENCED = re.compile(r"```.*?(?:```|$)", re.DOTALL)
_INLINE_SPAN = re.compile(r"`([^`\n]+)`")
_CODE_STATEMENT = re.compile(
    r"^\s*(?:if|elif|else|for|while|def|return|import|from|class|lambda|try|except|with|assert|raise|print)\s+\S")
_CODE_OPERATOR = re.compile(r"==|!=|<=|>=|\+=|->|(?<![=!<>])=(?!=)|(?<=\S)\s[+\-*/%]\s(?=\S)")
_CALL_WITH_ARGUMENT = re.compile(r"\w\s*\(\s*[^\s)]")  # reset() has no argument and passes


def _looks_like_code(span: str) -> bool:
    return bool(_CODE_STATEMENT.search(span) or _CODE_OPERATOR.search(span) or _CALL_WITH_ARGUMENT.search(span))


def _has_foreign_inline_code(reply: str, learner_text: str) -> bool:
    """B2: a backtick span that looks like code and that the learner did not write (whitespace collapsed)."""
    learner = _collapse(learner_text)
    for found in _INLINE_SPAN.finditer(_FENCED.sub(" ", reply)):
        span = _collapse(found.group(1)).strip()
        if _looks_like_code(span) and span not in learner:
            return True
    return False


def _check_d(reply: str, mode: str, learner_text: str = "") -> CheckResult:
    if mode != "Socratic":
        return CheckResult(None, "not_applicable")
    if _GUARD.contains_code(reply, learner_text=learner_text) or _has_foreign_inline_code(reply, learner_text):
        return CheckResult(False, "code_found")
    return CheckResult(True, "no_code")


# --- sentences, for (e) and (f) ---


def _sentence_spans(text: str) -> List[Tuple[int, int, str]]:
    """(start, end, terminator) of each non-blank sentence; text[start:end] leaves the terminator out."""
    spans: List[Tuple[int, int, str]] = []
    start = 0
    for i, ch in enumerate(text):
        # "." ends a sentence only before whitespace or the end (A1). "?" and "!" likewise, so the "?" in an address
        # such as https://host/path?key=1 does not cut a statement short; a closing quote or bracket may also follow.
        before_a_break = i + 1 == len(text) or text[i + 1].isspace()
        ends = ch == "\n" or (ch == "." and before_a_break) or (ch in "!?" and (before_a_break or text[i + 1] in "!?)]}\"'`*_"))
        if ends:
            spans.append((start, i, ch))
            start = i + 1
    if start < len(text):
        spans.append((start, len(text), ""))
    return [(a, b, t) for a, b, t in spans if text[a:b].strip()]


def split_sentences(text: str) -> List[Tuple[str, str]]:
    """(sentence, terminator) pairs. Split on '!', '?', a line break, and a '.' followed by whitespace or the end.

    A dot between two word characters (pytest.fixture_cache_reset, 3.12, conftest.py) does not split (A1).
    The terminator is '' for a last sentence with no ending mark.
    """
    return [(text[a:b], t) for a, b, t in _sentence_spans(text)]


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


# B3: the words that turn a sentence from a restatement into a description of the invented thing.
_DESCRIPTION_CUE = re.compile(
    r"(?<!\w)(?:perhaps|probably|likely|presumably|typically|usually|is used to|used for|is part of|lets you|allows you"
    r"|which means|that means|so that)(?!\w)",
    re.IGNORECASE,
)
# "That method ...", "This flag ...", "The session method ...": the subject points at the invented thing.
_DEMONSTRATIVE_SUBJECT = re.compile(
    r"^\W*(?:that|this|it|the)\s+(?:\w+\s+)?(?:method|function|option|flag|class|parameter|argument|decorator|helper"
    r"|feature|command|setting|attribute|keyword)(?!\w)",
    re.IGNORECASE,
)


def _describes(sentence: str, patterns: List["re.Pattern[str]"]) -> bool:
    """True when this statement sentence describes the invented thing (B3). The caller has dropped questions."""
    has_cue = bool(_DESCRIPTION_CUE.search(sentence))
    if _normalise(sentence).startswith(_SPECULATIVE_STARTS):
        return has_cue  # a guess that holds a cue describes it, even unnamed; without a cue it only restates
    names_it = any(p.search(sentence) for p in patterns)
    if _is_restatement(sentence):
        return has_cue and names_it  # a plain restatement is exempt unless it describes while naming the thing
    return bool(_DEMONSTRATIVE_SUBJECT.search(sentence)) or names_it


def _check_e(reply: str, state: str, made_up: Optional[str]) -> CheckResult:
    if not made_up or not made_up.strip():
        return CheckResult(None, "not_applicable")
    patterns = [re.compile(rf"(?<!\w){re.escape(f)}(?!\w)", re.IGNORECASE) for f in _identifier_forms(made_up)]
    for sentence, end in split_sentences(reply):
        if end == "?" or _is_state_sentence(sentence, state):
            continue
        if _describes(sentence, patterns):
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


# --- (g) explains instead of asking (B4): a flag only ---

_FRAMING = re.compile(  # first-person and request framing: the model is asking for something, not explaining
    r"(?<!\w)(?:i want|i can|let me|to help you|could you|can you|share|before we)(?!\w)", re.IGNORECASE)
_EXPLAIN_CUE = re.compile(
    "(?<!\\w)(?:" + "|".join(re.escape(c) for c in EXPLAIN_CUES) + ")(?!\\w)", re.IGNORECASE)
_NOT_DECLARATIVE_STARTS = ("you", "your", "so you", "i understand", "it sounds like you", "from what you")
_PLEASANTRY = re.compile(r"great question|good question|that's a great|that is a great|happy to help", re.IGNORECASE)
_LIST_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def _statements_for_g(reply: str, state: str) -> List[str]:
    """Statement sentences left after the state sentence, questions, lead-ins ending in ':' and request framing go."""
    kept: List[str] = []
    for sentence, end in split_sentences(_FENCED.sub("\n", reply)):
        text = _LIST_BULLET.sub("", sentence).strip()
        if not text or end == "?" or text.endswith(":") or _is_state_sentence(text, state) or _FRAMING.search(text):
            continue
        kept.append(text)
    return kept


def _is_long_declarative(sentence: str) -> bool:
    if len(sentence.split()) < LONG_SENTENCE_WORDS:
        return False
    normalised = _normalise(sentence)
    if any(normalised == s or normalised.startswith(s + " ") for s in _NOT_DECLARATIVE_STARTS):
        return False  # a restatement of the learner
    return not (_PLEASANTRY.search(sentence) and " but " not in sentence)


def _check_g(reply: str, state: str) -> CheckResult:
    """Signals in order: S1 an explanation cue, S2 two long declarative sentences, S3 a fenced code block."""
    statements = _statements_for_g(reply.replace("’", "'"), state)  # a curly apostrophe is a plain one
    if any(_EXPLAIN_CUE.search(s) for s in statements):
        return CheckResult(False, "cue")
    if sum(1 for s in statements if _is_long_declarative(s)) >= 2:
        return CheckResult(False, "long_sentences")
    if "```" in reply:
        return CheckResult(False, "code_block")
    return CheckResult(True, "ok")


# --- turn-quality checks (SPEC-33 section 7): flags only, never part of "obeys" or "flagged" ---

# Words that are never counted as a name of the learner's, besides Python's keywords and builtins. Lower case.
ANCHOR_IGNORED_WORDS = frozenset({
    "a", "i", "an", "the", "and", "or", "not", "is", "it", "to", "of", "in", "on", "at", "as", "be", "do", "if",
    "for", "from", "you", "your", "we", "me", "my", "this", "that", "these", "those", "there", "here", "what",
    "which", "who", "when", "where", "why", "how", "with", "line", "lines", "error", "errors", "code", "file",
    "value", "values", "name", "names", "type", "types", "print", "read", "run", "check", "step", "lesson", "text",
    "message", "output", "input", "result", "see", "say", "traceback", "most", "recent", "call", "last", "module",
    "py",
})
_NOT_NAMES = frozenset(keyword.kwlist) | frozenset(keyword.softkwlist) | frozenset(dir(builtins))

# The listed actions, by phrase. Matched as whole words after the same normalising as the state sentence; two phrases
# of one action are one action. Frozen (tests/test_spec33_stage1.py pins the list).
ONE_ACTION_PHRASES: Dict[str, Tuple[str, ...]] = {
    "print_value": ("print a value", "print the value", "print out", "print it", "print that"),
    "read_last_line": (
        "last line of the error", "last line of your error", "last line of the traceback",
        "last line of the message", "final line of the error",
    ),
    "run_smaller": ("run one line", "run just one line", "run that line", "smaller input", "smaller example"),
    "expected_and_saw": ("what you expected", "what you expect", "what did you expect", "what do you expect"),
    "check_type": ("check what type", "check the type", "print the type"),
    "reread_lesson": (
        "reread this step", "reread the step", "reread the lesson", "re read this step", "re read the lesson",
        "step s lesson text",
    ),
    "decision": ("decision you lean", "decision you are leaning", "one reason and one risk", "a reason and a risk"),
}

_FILE_LINE = re.compile(r'^\s*File "([^"]*)", line \d+(?:, in (\S+))?')
_ERROR_LINE = re.compile(r"^(?:\w+\.)*\w*(?:Error|Exception|Warning|Interrupt|Exit)\b")
_QUOTED = re.compile(r"'([^'\n]*)'|\"([^\"\n]*)\"")
_IDENTIFIER = re.compile(r"(?<!\w)[^\W\d]\w*")
_STRING_OR_COMMENT = re.compile(r"'([^'\n]*)'|\"([^\"\n]*)\"|#[^\n]*")
# A line of a question that is code and not prose: indented, a block opener, an import, an assignment or a call.
_CODE_LINE = re.compile(
    r"^(?:(?: {2,}|\t)\s*\S"
    r"|(?:def|class|for|while|if|elif|else|try|except|with)\b.*:\s*(?:#.*)?$"
    r"|(?:from [\w.]+ import \w|import [\w.]+\s*$)"
    r"|[^\W\d][\w.\[\]'\"]*\s*[-+*/]?=(?!=)\s*\S"
    r"|[^\W\d][\w.]*\(.*\)\s*$)"
)
_REPLY_LINE_NUMBER = re.compile(r"(?<!\w)lines?\s+\d+", re.IGNORECASE)


def _is_name(word: str) -> bool:
    return word not in _NOT_NAMES and word.lower() not in ANCHOR_IGNORED_WORDS


def _code_names(code: str) -> Set[str]:
    """The names in code. Comments go; a string counts only when it is one word, such as a key."""

    def keep(found: "re.Match[str]") -> str:
        inside = found.group(1) or found.group(2) or ""
        return f" {inside} " if _IDENTIFIER.fullmatch(inside) else " "

    return {word for word in _IDENTIFIER.findall(_STRING_OR_COMMENT.sub(keep, code)) if _is_name(word)}


def _error_names(error_output: str) -> Set[str]:
    """The names in run output: the file and function of a frame, the source lines, and what an error quotes.

    The plain words of an error message are Python's, not the learner's, so they do not count.
    """
    names: Set[str] = set()
    for line in error_output.splitlines():
        frame = _FILE_LINE.match(line)
        if frame:
            stem = re.split(r"[\\/]", frame.group(1))[-1].split(".")[0]
            names |= {word for word in (stem, frame.group(2) or "") if _IDENTIFIER.fullmatch(word) and _is_name(word)}
        elif _ERROR_LINE.match(line):
            for found in _QUOTED.finditer(line):
                names |= _code_names(found.group(1) or found.group(2) or "")
        elif line[:1].isspace():
            names |= _code_names(line)
    return names


def _pasted(question: str) -> Tuple[str, str]:
    """(code, error output) the learner pasted into the question. Prose is in neither."""
    code: List[str] = []
    errors: List[str] = []
    in_traceback = False
    for line in question.splitlines():
        if line.startswith("Traceback (most recent call last)") or _FILE_LINE.match(line):
            in_traceback = True
        if in_traceback:
            errors.append(line)
            in_traceback = bool(line.strip()) and not _ERROR_LINE.match(line)
        elif _ERROR_LINE.match(line) and ":" in line:
            errors.append(line)
        elif _CODE_LINE.match(line):
            code.append(line)
    return "\n".join(code), "\n".join(errors)


_TRACEBACK_NOTE = re.compile(r"^[^\S\n]*\[Previous line repeated[^\n]*$", re.MULTILINE)


def check_anchored(reply: str, question: str, code: str = "", error_output: str = "") -> CheckResult:
    """The reply holds a name from the learner's code or error output, or a line number. None: nothing to anchor on.

    The words of the question do not count, only code or a traceback pasted into it (SPEC-33 section 12 reading 1).
    """
    pasted_code, pasted_errors = _pasted(question or "")
    code = "\n".join(part for part in (code or "", pasted_code) if part.strip())
    error_output = "\n".join(part for part in (error_output or "", pasted_errors) if part.strip())
    if not code and not error_output:
        return CheckResult(None, "not_applicable")
    # "[Previous line repeated 996 more times]" is Python talking, not a line of the learner's.
    code, error_output = _TRACEBACK_NOTE.sub("", code), _TRACEBACK_NOTE.sub("", error_output)
    reply = reply or ""
    if _REPLY_LINE_NUMBER.search(reply):
        return CheckResult(True, "line_number")
    if set(_IDENTIFIER.findall(reply)) & (_code_names(code) | _error_names(error_output)):
        return CheckResult(True, "name")
    return CheckResult(False, "no_anchor")


def is_bare(reply: str) -> bool:
    """No question outside code: the learner is given nothing to answer (SPEC-33 section 7)."""
    return "?" not in _INLINE_SPAN.sub(" ", _FENCED.sub(" ", reply or ""))


def check_one_question(reply: str) -> CheckResult:
    """Exactly one question mark outside code."""
    marks = _INLINE_SPAN.sub(" ", _FENCED.sub(" ", reply or "")).count("?")
    return CheckResult(marks == 1, "one" if marks == 1 else ("none" if marks == 0 else "several"))


def check_one_action(reply: str) -> CheckResult:
    """Exactly one of the listed actions, by its frozen phrases."""
    normalised = _normalise(reply or "")
    found = sum(
        1 for phrases in ONE_ACTION_PHRASES.values() if any(_phrase_start(normalised, p) >= 0 for p in phrases))
    return CheckResult(found == 1, "one" if found == 1 else ("none" if found == 0 else "several"))


# --- the entry point ---


def check_reply(reply: str, mode: Any, state: str, learner_text: str, made_up: Optional[str] = None) -> ObedienceResult:
    """Check one reply (R1). `mode` is Socratic, Hybrid or Coach; `state` is not_found, no_index or unavailable."""
    reply = reply or ""
    mode = str(getattr(mode, "value", mode))
    a, exact = _check_a(reply, state)
    learner_text = learner_text or ""
    b = _check_b(reply, learner_text)
    c = _check_c(reply)
    d = _check_d(reply, mode, learner_text)
    e = _check_e(reply, state, made_up)
    f = _check_f(reply, state, learner_text)
    g = _check_g(reply, state)
    obeys = a.passed is True and b.passed is True and c.passed is True and d.passed in (True, None)
    flagged = (not obeys) or e.passed is False or bool(f.new_terms) or g.passed is False  # g is flag-only
    return ObedienceResult(a=a, b=b, c=c, d=d, e=e, f=f, g=g, obeys=obeys, flagged=flagged, exact_wording=exact)
