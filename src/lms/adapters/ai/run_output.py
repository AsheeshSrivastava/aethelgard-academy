"""The learner's run error output, made ready for a model (ADR-0041, SPEC-33 section 4 and section 12).

One function, `error_for_model`, for every companion: full file paths become file names, so a folder name from the
machine is never sent; a closing `</execution_stderr>` tag is removed; and the END of a long output is kept, where
the cause line is. Paths are replaced before the cap, so a cut path never leaves a folder name behind.

The output can be very long, so every pattern is linear: the repeats are possessive (no backtracking) and each
look-ahead over spaces is bounded. Nothing here logs or traces the text.
"""

from __future__ import annotations

import re

# Windows and network paths: `C:\...`, `C:/...`, `\\server\share\...`, also with the doubled backslashes of a repr.
_WINDOWS_START = r"(?:(?<![A-Za-z])[A-Za-z]:(?=[\\/])|(?<![\w\\])(?=\\\\++[A-Za-z0-9._$-]{2,}+\\))"
# Inside double quotes a name may hold an apostrophe. A name never runs on into a second drive letter.
_WINDOWS_QUOTED = r"(?:[^\\/:*?\"<>|\r\n \t]|[ \t](?![ \t]{0,7}[A-Za-z]:[\\/]))"
# Elsewhere an apostrophe belongs to the name only inside a word (O'Brien) or before a separator, and a name stops
# before a space that leads to the next path.
_WINDOWS_PLAIN = (
    r"(?:[^\\/:*?\"<>|'\r\n \t]|[ \t](?![ \t]{0,7}(?:[A-Za-z]:)?[\\/])|(?<=\w)'(?=\w)|'(?=[\\/]))"
)
_WINDOWS_PATH = re.compile(
    rf"(?<=\"){_WINDOWS_START}(?:[\\/]++{_WINDOWS_QUOTED}++)++[\\/]*+"
    rf"|{_WINDOWS_START}(?:[\\/]++{_WINDOWS_PLAIN}++)++[\\/]*+"
)

# POSIX paths. The start is never inside a word, a relative path or a web address (`file://` is the exception).
_POSIX_START = r"(?:(?<![\w./\\~)\]}-])|(?<=file://))(?=/[^\s/])"
_POSIX_QUOTED = r"[^/\\:*?\"<>|\r\n]"
_POSIX_PLAIN = r"(?:[^/\\:*?\"<>|'\r\n \t]|[ \t](?![ \t]{0,7}/)|(?<=\w)'(?=\w)|'(?=/))"
_POSIX_PATH = re.compile(
    rf"(?<=\"){_POSIX_START}(?:/++{_POSIX_QUOTED}++)++/*+"
    rf"|{_POSIX_START}(?:/++{_POSIX_PLAIN}++)++/*+"
)

# A POSIX path starting here is a path on the machine, whatever it ends in.
_SYSTEM_FOLDERS = frozenset({
    "home", "Users", "usr", "var", "tmp", "etc", "opt", "root", "srv", "mnt", "media", "private", "Volumes",
    "Library", "Applications", "System", "bin", "sbin", "lib", "lib64", "proc", "dev", "run", "sys", "workspace",
    "nix", "snap",
})
# The folder right under one of these is named after a user.
_HOME_PARENTS = frozenset({"home", "homes", "users", "documents and settings"})
_FILE_NAME = re.compile(r"\.[A-Za-z][A-Za-z0-9]{0,9}$")
_SEPARATORS = re.compile(r"[\\/]++")
_CLOSING_TAG = re.compile(r"</\s*+execution_stderr\b[^<>]*+>", re.IGNORECASE)


def _last_part(parts: list) -> str:
    """The last part of a path, or "~" when that part is a user's home folder."""
    if len(parts) >= 2 and parts[-2].lower() in _HOME_PARENTS:
        return "~"
    return parts[-1]


def _windows(found: "re.Match[str]") -> str:
    parts = [p for p in _SEPARATORS.split(found.group(0)) if p]
    return _last_part(parts) if len(parts) >= 2 else found.group(0)


def _posix(found: "re.Match[str]") -> str:
    """Cut when the path starts at a usual system folder or ends in a file name; a web route is left alone."""
    parts = [p for p in _SEPARATORS.split(found.group(0)) if p]
    if len(parts) < 2:
        return found.group(0)  # no folder to hide
    system = parts[0] in _SYSTEM_FOLDERS or (len(parts[0]) == 1 and parts[1] == "Users")  # /c/Users/...
    return _last_part(parts) if system or _ends_in_a_file_name(parts[-1], found) else found.group(0)


def _ends_in_a_file_name(last: str, found: "re.Match[str]") -> bool:
    words = last.split(None, 1)  # prose may follow an unquoted path
    if words and _FILE_NAME.search(words[0].rstrip(".,;)]}")):
        return True
    # A file name with a space, where the end of the path is clear: in quotes, or before ":<line>".
    text = found.string
    bounded = text[found.start() - 1: found.start()] in ('"', "'") or text[found.end(): found.end() + 1] == ":"
    return bounded and bool(_FILE_NAME.search(last))


def error_for_model(stderr: str, limit: int) -> str:
    """The run's error output as any model may see it, at most `limit` characters from its end."""
    text = _POSIX_PATH.sub(_posix, _WINDOWS_PATH.sub(_windows, stderr))[-limit:]
    while True:  # until none is left, so a tag split by a tag cannot rebuild itself; the cap bounds the passes
        cleaned = _CLOSING_TAG.sub("", text)
        if cleaned == text:
            return text
        text = cleaned
