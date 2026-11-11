"""Write the made-up test items and their fake answers (tests/fixtures, A0 2026-11-11).

Run from the repo root: `uv run python scripts/make_test_fixtures.py`

Each real public seed in curriculum/ gets a made-up twin with the same id, activity, skill,
level and Cold Check flags, but made-up text, code and options. Its fake private half goes to
tests/fixtures/answers. Nothing is read from the private answers folder, so no real answer can
end up here. Re-run after adding seeds, then fix any test that counted the old items.
"""
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_PUB = REPO / "tests/fixtures/curriculum"
OUT_ANS = REPO / "tests/fixtures/answers"
for d in (OUT_PUB, OUT_ANS):
    shutil.rmtree(d, ignore_errors=True)

BLOCKS = ["predict","trace","playground","debug","debug_locate","choice","specify_by_tests",
          "specify_contract","decompose_plan","decompose_code","explain_spot_flaw","explain_model_choice"]
KEEP = ["schema_version","seed_id","unit_id","activity","skill_id","level","topic",
        "cold_check_eligible","curator_approved","hint_approved"]

def opts(options, word):
    return [{"key": o["key"], "text": f"{word} {o['key'].lower()}"} for o in options]

def made_up(raw, n):
    t = next(b for b in BLOCKS if isinstance(raw.get(b), dict))
    pub = {k: raw[k] for k in KEEP if k in raw}
    pub["prompt_markdown"] = [f"Made-up test item {raw['seed_id']}. It is not real course content."]
    if raw.get("template"):
        pub["prompt_markdown"].append("The word is {{word}}.")
    if "hint" in raw:
        pub["hint"] = "Made-up hint for tests."
    slot = None
    if raw.get("template"):
        count = max(len(s["values"]) for s in raw["template"]["slots"].values())
        pub["template"] = {"slots": {"word": {"kind": "word", "values": ["alpha", "beta", "gamma", "delta", "omega"][:count]}}}
        slot = "{{word}}"
    b = raw[t]
    # Practice items: the first option is right. Cold Check items: the second, so "A" is a wrong answer there.
    k = 1 if raw.get("cold_check_eligible") else 0
    if t == "predict":
        word = slot or f"item-{n}"
        options = [{"key": o["key"], "text": word if i == k else f"{word} {o['key'].lower()}"} for i, o in enumerate(b["options"])]
        pub[t] = {"code": [f"print('{word}')"], "stdin": "", "options": options}
        priv = {"answer_key": options[k]["key"], "why": ["Made-up: print shows its argument."]}
    elif t == "trace":
        pub[t] = {"code": [f"print('item-{n}')", "print('done')"], "input": ""}
        priv = {"expected_output": [f"item-{n}", "done"]}
    elif t in ("choice", "explain_model_choice"):
        options = opts(b["options"], "Made-up option")
        pub[t] = {"material": ["Made-up material for tests."], "options": options}
        priv = {"answer_key": options[k]["key"], "why": ["Made-up reason."]}
    elif t == "explain_spot_flaw":
        sentences = opts(b["sentences"], "Made-up sentence")
        pub[t] = {"sentences": sentences}
        priv = {"answer_key": sentences[k]["key"], "why": ["Made-up reason."]}
    elif t == "debug_locate":
        types = b["error_types"]
        name_error = next((o["key"] for o in types if "Name" in o["text"] or "Name" in o["key"]), types[0]["key"])
        pub[t] = {"broken_code": ["total = 1", "print(totl)"], "stdin": "", "error_types": types}
        priv = {"answer_key": {"error_type": name_error, "line": 2}, "why": ["Made-up: the name is misspelt."]}
    elif t == "debug":
        pub[t] = {"broken_code": ["def add(a, b):", "    return a - b"], "stdin": ""}
        priv = {"reference_solution": ["def add(a, b):", "    return a + b"],
                "hidden_checks": ["def test_add():", "    assert add(2, 3) == 5"],
                "wrong_solution": ["def add(a, b):", "    return a * b"]}
    elif t == "playground":
        pub[t] = {"starter": ["# Made-up task: write shout(word) that returns the word in capitals.", ""],
                  "tasks": [{"id": task["id"], "label": f"Made-up task {task['id']}"} for task in b.get("tasks", [])],
                  "make": b.get("make", False)}
        priv = {"reference_solution": ["def shout(word):", "    return word.upper()"],
                "hidden_checks": ["def test_shout():", "    assert shout('hi') == 'HI'"],
                "wrong_solution": ["def shout(word):", "    return word"]}
    elif t == "specify_contract":
        fields = [{"id": f["id"], "label": f"Made-up field {f['id']}", "kind": f["kind"],
                   "options": opts(f["options"], "Made-up choice")} for f in b["fields"]]
        pub[t] = {"material": ["Made-up material for tests."], "fields": fields}
        priv = {"answer_key": {f["id"]: ([f["options"][0]["key"]] if f["kind"] == "multi" else f["options"][0]["key"]) for f in fields},
                "why": ["Made-up reason."]}
    else:
        raise SystemExit(f"no made-up form for {t}")
    return pub, {"seed_id": raw["seed_id"], t: priv}

n = 0
for f in sorted((REPO / "curriculum").glob("*/*/exercises/*.json")):
    n += 1
    rel = f.relative_to(REPO / "curriculum")
    pub, priv = made_up(json.loads(f.read_text()), n)
    for root, data in ((OUT_PUB, pub), (OUT_ANS, priv)):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2) + "\n")
print(n, "seeds")

for pkg in sorted((REPO / "curriculum").glob("*/*")):
    if not pkg.is_dir() or pkg.name == "builds":
        continue
    ans = OUT_ANS / pkg.parent.name / pkg.name
    meta = pkg / "meta.json"
    if meta.exists() and isinstance(json.loads(meta.read_text()).get("concept_check"), dict):
        ans.mkdir(parents=True, exist_ok=True)
        (ans / "concept_check.json").write_text(json.dumps({"ideas": [
            {"id": "made-up-1", "text": "apples"},
            {"id": "made-up-2", "text": "rivers"}]}, indent=2) + "\n")
    if (pkg / "starter.py").exists():
        ans.mkdir(parents=True, exist_ok=True)
        (ans / "test_solution.py").write_text(
            '"""Made-up practice check for tests: the learner writes shout(word)."""\n\n\n'
            "def test_shout():\n    assert shout('hi') == 'HI'  # noqa: F821\n")
    lesson = pkg / "lesson.md"
    ids = re.findall(r"```quickcheck\nid: (\S+)", lesson.read_text()) if lesson.exists() else []
    if ids:
        ans.mkdir(parents=True, exist_ok=True)
        (ans / "quick_checks.json").write_text(json.dumps(
            {i: {"answer": "B", "why": "Made-up reason for tests."} for i in ids}, indent=2) + "\n")
print("extras done")
