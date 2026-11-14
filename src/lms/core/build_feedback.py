"""Data-based build feedback, layer 1 (SPEC-15 section 10).

Points are built from facts we can measure: the requirement results, words under README headings and
the length of the review note. No model, no network. A pointer says where to look; it never gives code.
"""

import re
from typing import List, Literal, Mapping, Optional, Sequence

from pydantic import BaseModel

from lms.core.builds import RequirementCheck, RequirementResult, StageBuildSpec, _sections_of

_CODE_BLOCK = re.compile(r"```.*?(```|\Z)", re.DOTALL)


def strip_code_blocks(text: str) -> str:
    """The AXIS summary may explain, but never hands over code: fenced blocks are removed."""
    return _CODE_BLOCK.sub("(code left out)", text).strip()


Status = Literal["not_met", "not_checked", "met"]
_ORDER = {"not_met": 0, "not_checked": 1, "met": 2}


class FeedbackPoint(BaseModel):
    requirement_id: str
    status: Status
    where: str
    found: str
    why: str
    looked_for: str                    # What the rule checks, so a learner can see why a good file missed
    look: str


def _where(build: StageBuildSpec, check: RequirementCheck) -> str:
    path = check.path or build.entry
    if check.kind == "readme_sample_run" and check.heading:
        return f'{path}, "{check.heading}"'
    if check.kind in ("review_note", "ownership_note"):
        return "Review note" if check.kind == "review_note" else "Ownership note"
    return path


def _facts(check: RequirementCheck, files: Mapping[str, str], review_note: Optional[str]) -> Optional[str]:
    if check.kind == "markdown_sections":
        sections = _sections_of(files.get(check.path or "", ""))
        parts = []
        for rule in check.sections or []:
            body = sections.get(rule.heading.strip().lower())
            if body is None:
                parts.append(f"{rule.heading}: missing")
            else:
                needs = f" (needs {rule.min_words})" if rule.min_words else ""
                parts.append(f"{rule.heading}: {len(body.split())} words{needs}")
        return "; ".join(parts) or None
    if check.kind == "review_note":
        return f"The note has {len((review_note or '').strip())} characters (needs {check.min_chars or 0})."
    return None


def _looked_for(check: RequirementCheck) -> str:
    if check.kind == "markdown_sections":
        rules = [
            f"'{r.heading}'" + (f" with at least {r.min_words} words" if r.min_words else "")
            + (f", mentioning one of: {', '.join(r.any)}" if r.any else "")
            for r in check.sections or []
        ]
        return "These headings: " + "; ".join(rules) + "."
    if check.kind == "readme_sample_run":
        return (f"A code block under '{check.heading}' with one run: what you typed and what your script "
                "printed, in the same order.")
    if check.kind == "review_note":
        return f"A note of at least {check.min_chars or 0} characters."
    if check.kind == "ownership_note":
        return f"A note of at least {check.min_chars or 0} characters."
    if check.kind == "file_contains":
        return f"One of these in {check.path}: {', '.join(check.any or [])}."
    if check.kind == "behaviour":
        return "Your script, run with practice input, behaves as the brief describes."
    return "The requirement as written on the page."


def _look(check: RequirementCheck, status: Status) -> str:
    if status == "met":
        return "Nothing to change here."
    if status == "not_checked":
        return "Press Verify so your script is run, then ask for feedback again."
    where = {
        "markdown_sections": "the README headings listed in the checklist",
        "readme_sample_run": "your pasted run next to what your script really prints",
        "review_note": "your review note against the question on the page",
        "file_contains": "the README text for the exact command",
    }.get(check.kind, "the requirement on the page and your file")
    return f"Compare {where}."


def build_feedback_points(
    build: StageBuildSpec,
    files: Mapping[str, str],
    results: Sequence[RequirementResult],
    review_note: Optional[str],
) -> List[FeedbackPoint]:
    by_id = {r.id: r for r in results}
    points: List[FeedbackPoint] = []
    for requirement in build.requirements:
        result = by_id.get(requirement.id)
        if result is None:
            continue
        status: Status = "not_checked" if result.met is None else ("met" if result.met else "not_met")
        check = requirement.check
        measured = _facts(check, files, review_note)
        found = result.detail or measured or ("Met." if status == "met" else "Not met yet." if status == "not_met"
                                              else "Not checked yet.")
        if result.detail and measured and status == "not_met" and check.kind == "markdown_sections":
            found = f"{result.detail} ({measured})"
        if status == "not_met":
            found = f"The check did not find what it looks for. {found}"
        points.append(FeedbackPoint(
            requirement_id=requirement.id, status=status, where=_where(build, check),
            found=found, why=requirement.label,
            looked_for=_looked_for(check), look=_look(check, status),
        ))
    return sorted(points, key=lambda p: _ORDER[p.status])
