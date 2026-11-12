"""Right and wrong answers to the made-up test items (tests/fixtures, A0 2026-11-11).

Tests never hold real answers. Each helper reads the fake private half of a made-up item
and returns the attempt fields that pass or fail it. Practice items take the first option;
Cold Check items take the second, so "A" is always a wrong Cold Check answer.
"""

import json
from pathlib import Path
from typing import Any, Dict

ANSWERS = Path(__file__).resolve().parent / "fixtures" / "answers"


def _private(seed_id: str) -> Dict[str, Any]:
    unit, stem = seed_id.split("/")[:2]
    data = json.loads((ANSWERS / "python" / unit.lower() / "exercises" / f"{stem}.json").read_text(encoding="utf-8"))
    return next((name, block) for name, block in data.items() if name != "seed_id")


def right(seed_id: str) -> Dict[str, Any]:
    """Fields of an attempt that passes the made-up item (an exercise id works too)."""
    item_type, block = _private(seed_id)
    if item_type == "trace":
        fields = {"trace_answers": block["expected_output"]}
        if block.get("line_states"):  # a Cold Check item ignores the table (ADR-0031), so sending it is safe
            fields["trace_states"] = [
                {"line": r["line"], "state": {k: str(v) for k, v in r["state"].items()}} for r in block["line_states"]
            ]
        return fields
    if item_type == "debug_locate":
        return {"locate": block["answer_key"]}
    if item_type == "specify_contract":
        return {"fields": block["answer_key"]}
    if "reference_solution" in block:
        return {"files": {"solution.py": "\n".join(block["reference_solution"])}}
    return {"choice": block["answer_key"]}


def wrong(seed_id: str) -> Dict[str, Any]:
    """Fields of an attempt that fails the made-up item."""
    item_type, block = _private(seed_id)
    if item_type == "trace":
        return {"trace_answers": ["wrong"]}
    if item_type == "debug_locate":
        return {"locate": {**block["answer_key"], "line": 1}}
    if item_type == "specify_contract":
        return {"fields": {}}
    if "wrong_solution" in block:
        return {"files": {"solution.py": "\n".join(block["wrong_solution"])}}
    return {"choice": "A" if block["answer_key"] != "A" else "B"}


SHOUT = "def shout(word):\n    return word.upper()\n"  # passes every made-up practice check (test_solution.py)
SOLID = "It names apples and rivers, the two made-up ideas in the test rubric."  # meets every made-up rubric
