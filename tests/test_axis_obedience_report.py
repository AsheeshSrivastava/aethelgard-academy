"""SPEC-30 tests, part 4: the run outputs (report.txt, results.json, replies.jsonl, review-sample.md).

Covers ADR-0037 section 2.5 / SPEC-30 R13 (the hand-review sample), R14 (outputs, run name, no timestamps, out-dir
rule) and R18 (counts and ids only in the report). Offline: the rows are made up here; no model, no harness.

Names under test (the file names are SPEC-30 R14; the functions and the results.json shape are this suite's contract,
see the phase 1 report):
  lms.adapters.ai.obedience.report:
    default_run_name(set_version, made_up_version, temperature, seed) -> str
    build_results(rows, meta) -> dict          rows are replies.jsonl rows (tests/obedience_support.make_row)
    render_report(results) -> str
    render_review_sample(rows, seed) -> str
    write_run(out_dir, run_name, rows, meta) -> Path   (the run folder; raises if it already exists)
    out_dir_problem(path) -> Optional[str]     None when the folder may be used, else a plain reason
  results.json: the scalar keys of `meta` (set_version, made_up_version, profile_id, model_answered, temperature,
    send_temperature, seed, repeat) plus
    counts: {"raw"|"visible": {mode: {state: {n, obeys, a, b, c, d, no_reply, flagged}}}}  (a to d = replies that pass;
    a reply for which (d) does not apply counts as passing it), made_up: {n, e}, new_terms_flagged: int,
    exact_wording_rate: float, failing_ids: {a, b, c, d, e: [question ids]}, flagged_ids: [question ids]
"""

import json
import random
import re
import subprocess
from pathlib import Path

import pytest

from obedience_corpus import BODY, EXACT, FENCED_BLOCK, MADE_UP, MADE_UP_LEARNER, MODES, STATES, good_reply
from obedience_support import make_row

REPO = Path(__file__).resolve().parents[1]
META = dict(set_version="a" * 64, made_up_version="b" * 64, profile_id="local", model_answered="scripted-model-1",
            temperature=0.0, send_temperature=True, seed=29, repeat=1)
BAR_LINE = "Obedience bar: report only on the first run; no pass mark is applied (ADR-0037 4.2)."
PROXY = "A person reads each reply and asks: did it answer, or did it refuse? This is a proxy for 'no facts from memory', not proof."


def report():
    from lms.adapters.ai.obedience import report as module

    return module


def table_rows():
    """Four or five rows in every (mode, state) cell: one good and one for each rule that can fail."""
    rows = []
    for mode in MODES:
        for state in STATES:
            good = good_reply(mode, state)
            cell = [
                make_row(f"good-{mode}-{state}", mode, state, good),
                make_row(f"bad-a-{mode}-{state}", mode, state, BODY[mode]),
                make_row(f"bad-b-{mode}-{state}", mode, state, good + " As the manual says [1]."),
                make_row(f"bad-c-{mode}-{state}", mode, state, good + " Not from the course: loops start at zero."),
            ]
            if mode == "Socratic":
                cell.append(make_row(f"bad-d-{mode}-{state}", mode, state, good + "\n" + FENCED_BLOCK))
            rows += cell
    return rows


def marked_rows(per_mode=40):
    """Rows with a unique marker in the question. Every 5th is bad, every 7th (not 5th) holds a new term."""
    rows = []
    for mode in MODES:
        for i in range(per_mode):
            state = STATES[i % 3]
            marker = f"zq{mode[0]}{i:03d}zq"
            if i % 5 == 0:
                raw = BODY[mode]
            elif i % 7 == 0:
                raw = good_reply(mode, state) + " Is `parse_row` the cause?"
            else:
                raw = good_reply(mode, state)
            rows.append(make_row(f"q{mode[0]}{i:03d}", mode, state, raw, question=f"Synthetic question {marker} about nothing real?"))
    return rows


def flagged_marker_set(per_mode=40):
    return {f"zq{mode[0]}{i:03d}zq" for mode in MODES for i in range(per_mode) if i % 5 == 0 or i % 7 == 0}


def markers(text):
    return re.findall(r"zq[SHC]\d{3}zq", text)


# --- report.txt and results.json (R14) ---


def test_report_has_counts_per_mode_and_state_and_each_check_alone():
    results = report().build_results(table_rows(), META)

    for mode in MODES:
        for state in STATES:
            cell = results["counts"]["raw"][mode][state]
            n = 5 if mode == "Socratic" else 4
            assert cell["n"] == n and cell["obeys"] == 1
            assert (cell["a"], cell["b"], cell["c"]) == (n - 1, n - 1, n - 1)  # each check alone
            if mode == "Socratic":
                assert cell["d"] == n - 1
            assert cell["no_reply"] == 0

    text = report().render_report(results)
    for name in (*MODES, *STATES):
        assert name in text
    assert "exact" in text.lower()  # the exact-wording rate


def test_a_no_reply_has_its_own_column_and_fails_a():
    rows = [make_row("ok", "Coach", "not_found"),
            make_row("gone", "Coach", "not_found", raw=None, visible=None, no_reply=True, error_class="TimeoutError"),
            make_row("blank", "Coach", "not_found", raw="  ", visible="  ", no_reply=True)]

    cell = report().build_results(rows, META)["counts"]["raw"]["Coach"]["not_found"]

    assert (cell["n"], cell["no_reply"], cell["obeys"], cell["a"]) == (3, 2, 1, 1)


def test_the_visible_reply_is_scored_beside_the_raw_reply():
    good = good_reply("Hybrid", "not_found")
    rows = [make_row("q1", "Hybrid", "not_found", raw=good + " See [1].", visible=good),
            make_row("q2", "Hybrid", "not_found", raw=good, visible=good)]

    counts = report().build_results(rows, META)["counts"]

    assert counts["raw"]["Hybrid"]["not_found"]["obeys"] == 1
    assert counts["visible"]["Hybrid"]["not_found"]["obeys"] == 2


def test_made_up_set_result_for_e_and_new_term_flags():
    confident = f"{EXACT['not_found']} The fixture_cache_reset helper clears every cached fixture."
    rows = [
        make_row("mu-1", "Coach", "not_found", confident, question=MADE_UP_LEARNER, invented=MADE_UP),
        make_row("mu-2", "Coach", "not_found", f"{EXACT['not_found']} Where did you read about it?",
                 question=MADE_UP_LEARNER, invented=MADE_UP),
        make_row("t-1", "Coach", "not_found", good_reply("Coach", "not_found") + " Is `parse_row` the cause?"),
        make_row("t-2", "Coach", "not_found"),
    ]

    results = report().build_results(rows, META)

    assert results["made_up"] == {"n": 2, "e": 1}
    assert results["failing_ids"]["e"] == ["mu-1"]
    assert results["new_terms_flagged"] == 1
    assert set(results["flagged_ids"]) == {"mu-1", "t-1"}


def test_report_lists_failing_question_ids():
    results = report().build_results(table_rows(), META)

    assert "bad-a-Hybrid-not_found" in results["failing_ids"]["a"]
    assert "bad-b-Coach-no_index" in results["failing_ids"]["b"]
    assert "bad-c-Socratic-unavailable" in results["failing_ids"]["c"]
    assert "bad-d-Socratic-not_found" in results["failing_ids"]["d"]
    assert "good-Hybrid-not_found" not in sum(results["failing_ids"].values(), [])
    text = report().render_report(results)
    for qid in ("bad-a-Hybrid-not_found", "bad-b-Coach-no_index", "bad-c-Socratic-unavailable", "bad-d-Socratic-not_found"):
        assert qid in text


def test_report_says_bar_is_report_only():
    text = report().render_report(report().build_results(table_rows(), META))

    assert BAR_LINE in text.splitlines()


def test_exact_wording_rate_is_information_only():
    exact = [make_row(f"e{i}", "Hybrid", STATES[i % 3]) for i in range(6)]
    paraphrase = [make_row(f"p{i}", "Hybrid", "not_found", good_reply("Hybrid", "not_found", paraphrase=True)) for i in range(6)]

    assert report().build_results(exact, META)["exact_wording_rate"] == 1.0
    assert report().build_results(paraphrase, META)["exact_wording_rate"] == 0.0
    mixed = report().build_results(exact + paraphrase, META)
    assert 0.0 < mixed["exact_wording_rate"] < 1.0
    assert mixed["counts"]["raw"]["Hybrid"]["not_found"]["obeys"] == 8  # a paraphrase obeys: the rate is not a pass mark


def test_results_json_is_sorted_and_has_versions_and_temperature_flags(tmp_path):
    run_dir = report().write_run(tmp_path, "run1", table_rows(), META)

    text = (run_dir / "results.json").read_text(encoding="utf-8")
    data = json.loads(text)
    for key, value in META.items():
        assert data[key] == value, key
    assert data["send_temperature"] is True and data["temperature"] == 0.0

    def ordered(pairs):
        keys = [k for k, _ in pairs]
        assert keys == sorted(keys), keys
        return dict(pairs)

    json.loads(text, object_pairs_hook=ordered)  # every object in the file has its keys in order


def test_the_report_and_results_hold_counts_and_ids_only(tmp_path):
    secret_question = "Synthetic question zebra-quartz-question about nothing real?"
    secret_reply = good_reply("Hybrid", "not_found") + " Zebra quartz reply sentinel."
    rows = [make_row("q1", "Hybrid", "not_found", secret_reply, question=secret_question)]

    run_dir = report().write_run(tmp_path, "run1", rows, META)

    for name in ("report.txt", "results.json"):
        text = (run_dir / name).read_text(encoding="utf-8")
        assert "zebra" not in text.lower() and "sentinel" not in text.lower(), name  # ids may appear; text never does


# --- names and bytes (R14) ---


def test_run_name_is_deterministic():
    name = report().default_run_name("a" * 64, "b" * 64, 0.0, 29)

    assert name == "aaaaaaaa-bbbbbbbb-t0.0-s29"
    assert report().default_run_name("a" * 64, "b" * 64, 0.0, 29) == name
    assert report().default_run_name("a" * 64, "b" * 64, 0.2, 29) == "aaaaaaaa-bbbbbbbb-t0.2-s29"
    assert report().default_run_name("a" * 64, "b" * 64, 0.0, 30) == "aaaaaaaa-bbbbbbbb-t0.0-s30"
    assert report().default_run_name("c" * 64, "b" * 64, 0.0, 29) != name


def test_no_timestamp_in_any_number_or_name(tmp_path):
    run_dir = report().write_run(tmp_path, report().default_run_name("a" * 64, "b" * 64, 0.0, 29), marked_rows(), META)

    assert not re.search(r"\d{4}-\d{2}-\d{2}", run_dir.name)
    for path in run_dir.iterdir():
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text), path.name
        assert not re.search(r"\b\d{2}:\d{2}:\d{2}\b", text), path.name
        assert "T00:" not in text and "timestamp" not in text.lower(), path.name


def test_the_same_run_writes_the_same_bytes(tmp_path):
    first = report().write_run(tmp_path / "one", "run1", marked_rows(), META)
    second = report().write_run(tmp_path / "two", "run1", list(reversed(marked_rows())), META)

    assert sorted(p.name for p in first.iterdir()) == ["replies.jsonl", "report.txt", "results.json", "review-sample.md"]
    for name in ("report.txt", "results.json", "review-sample.md"):  # replies.jsonl keeps the order it was given
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_an_existing_run_is_not_overwritten_and_is_named(tmp_path):
    report().write_run(tmp_path, "run1", table_rows(), META)

    with pytest.raises(Exception, match="run1"):
        report().write_run(tmp_path, "run1", table_rows(), META)


def test_replies_file_has_one_row_each_and_no_key_or_url_token(tmp_path):
    rows = table_rows()

    run_dir = report().write_run(tmp_path, "run1", rows, META)

    lines = (run_dir / "replies.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(rows)
    parsed = [json.loads(line) for line in lines]
    for key in ("id", "mode", "state", "question", "raw_reply", "visible_reply"):
        assert all(key in row for row in parsed)
    everything = "".join(p.read_text(encoding="utf-8") for p in run_dir.iterdir())
    assert "://" not in everything and "token=" not in everything and "sk-" not in everything  # nothing of ours adds one
    assert "://" not in (run_dir / "results.json").read_text(encoding="utf-8")


def test_a_reply_that_echoes_a_url_with_a_token(tmp_path):
    # Amendment A8: the reply is stored as the model wrote it (local files only); the report only counts such replies.
    echoed = good_reply("Hybrid", "not_found") + " Try https://api.example.test/v1/x?token=abc123 yourself."
    rows = [make_row("q1", "Hybrid", "not_found", echoed), make_row("q2", "Hybrid", "not_found"),
            make_row("q3", "Coach", "not_found", good_reply("Coach", "not_found") + " See docs.example.test/page/1 too.")]

    run_dir = report().write_run(tmp_path, "run1", rows, META)

    stored = [json.loads(line) for line in (run_dir / "replies.jsonl").read_text(encoding="utf-8").splitlines()]
    assert stored[0]["raw_reply"] == echoed  # as written, not redacted
    assert "token=abc123" in (run_dir / "review-sample.md").read_text(encoding="utf-8")
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    assert results["replies_with_url"] == 2
    text = (run_dir / "report.txt").read_text(encoding="utf-8")
    assert "Warning: 2 replies hold a URL. Check replies.jsonl before sharing it." in text.splitlines()
    for name in ("report.txt", "results.json"):  # the address itself never reaches the report or the numbers
        body = (run_dir / name).read_text(encoding="utf-8")
        assert "token=abc123" not in body and "example.test" not in body and "://" not in body


def test_no_url_warning_when_no_reply_holds_one(tmp_path):
    run_dir = report().write_run(tmp_path, "run1", table_rows(), META)

    assert "hold a URL" not in (run_dir / "report.txt").read_text(encoding="utf-8")


# --- the hand-review sample (R13) ---


def test_review_sample_is_flagged_plus_ten_random_per_mode():
    sample = report().render_review_sample(marked_rows(), 29)

    found = markers(sample)
    flagged = flagged_marker_set()
    assert flagged <= set(found)  # every flagged reply
    extra = [m for m in set(found) if m not in flagged]
    assert len(extra) == 30
    for mode in MODES:
        assert len([m for m in extra if m[2] == mode[0]]) == 10  # ten per mode
    assert len(flagged) == 36


def test_review_sample_takes_every_unflagged_reply_when_a_mode_has_fewer_than_ten():
    rows = [make_row(f"c{i}", "Coach", "not_found", good_reply("Coach", "not_found") if i < 4 else BODY["Coach"],
                     question=f"Synthetic question zqC{i:03d}zq about nothing?") for i in range(10)]

    found = markers(report().render_review_sample(rows, 29))

    assert sorted(set(found)) == [f"zqC{i:03d}zq" for i in range(10)]  # 6 flagged + the only 4 that are left


def test_review_sample_is_the_same_for_the_same_seed_and_different_for_another():
    rows = marked_rows()
    shuffled = list(rows)
    random.Random(7).shuffle(shuffled)

    first = report().render_review_sample(rows, 29)

    assert report().render_review_sample(rows, 29) == first
    assert set(markers(report().render_review_sample(shuffled, 29))) == set(markers(first))  # input order does not matter
    assert set(markers(report().render_review_sample(rows, 30))) != set(markers(first))
    assert flagged_marker_set() <= set(markers(report().render_review_sample(rows, 30)))  # flagged are always there


def test_review_sample_never_picks_a_flagged_reply_twice():
    found = markers(report().render_review_sample(marked_rows(), 29))

    assert len(found) == len(set(found))  # one entry for each reply


def test_review_sample_shows_what_the_owner_needs_to_read():
    rows = [make_row("flag-1", "Coach", "not_found", BODY["Coach"] + " Zebra raw sentinel.",
                     question="Synthetic question zqC001zq about nothing?")]

    sample = report().render_review_sample(rows, 29)

    for needle in ("flag-1", "Coach", "not_found", "zqC001zq", "Zebra raw sentinel."):
        assert needle in sample, needle


def test_review_sample_says_it_is_a_proxy():
    sample = report().render_review_sample(marked_rows(), 29)

    assert PROXY in sample
    assert sample.index(PROXY) < sample.index("zq")  # at the top, before the first entry


# --- where the files may go (R14) and git (R18) ---


def test_out_dir_outside_eval_out_is_refused_unless_git_ignored(tmp_path):
    problem = report().out_dir_problem

    assert problem(REPO / "docs" / "zz-out") is not None  # a tracked folder
    assert problem(REPO / "src" / "lms" / "zz-out") is not None
    assert problem(REPO / "tests" / "zz-out") is not None
    assert problem(REPO / "eval-out" / "axis-obedience") is None  # the usual place
    assert problem(REPO / "workspace" / "zz-out") is None  # git-ignored (.gitignore: workspace/)
    assert problem(tmp_path / "somewhere") is None  # not inside the repository at all
    assert isinstance(problem(REPO / "docs" / "zz-out"), str) and problem(REPO / "docs" / "zz-out").strip()
    assert not (REPO / "docs" / "zz-out").exists()


def test_eval_out_is_git_ignored():
    for name in ("replies.jsonl", "review-sample.md", "report.txt", "results.json"):
        result = subprocess.run(
            ["git", "check-ignore", "-q", f"eval-out/axis-obedience/some-run/{name}"], cwd=REPO, capture_output=True)
        assert result.returncode == 0, name


# =====================================================================================================
# ADR-0037 section 2.5 B / SPEC-30 section 11 (B5): checker_version, the "Explains flags" line, and the (g) mark in the
# hand-review file. Rows are synthetic; no model.
# =====================================================================================================

EXPLAINS_TEXT = " Quick note, this works because the loop ends early."  # an explain cue (g), nothing else wrong
NEW_TERMS_PREFIX = "New-terms flags, check (f):"


def explain_rows():
    """Five rows: two replies that explain (g), one that fails (a) only, two clean."""
    return [
        make_row("g-1", "Coach", "not_found", good_reply("Coach", "not_found") + EXPLAINS_TEXT),
        make_row("g-2", "Hybrid", "no_index", good_reply("Hybrid", "no_index") + "\n" + FENCED_BLOCK),
        make_row("a-1", "Coach", "unavailable", BODY["Coach"]),
        make_row("ok-1", "Coach", "not_found"),
        make_row("ok-2", "Socratic", "not_found"),
    ]


def test_b5_results_json_has_checker_version_b_and_the_explains_flag_count(tmp_path):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5)."""
    results = report().build_results(explain_rows(), META)

    assert results["checker_version"] == "C"  # SPEC-31 9.3 C3
    assert results["explains_flagged"] == 2 and isinstance(results["explains_flagged"], int)
    for key in ("counts", "made_up", "new_terms_flagged", "exact_wording_rate", "failing_ids", "flagged_ids", "set_version"):
        assert key in results  # the existing keys stay
    run_dir = report().write_run(tmp_path, "run1", explain_rows(), META)
    data = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    assert data["checker_version"] == "C" and data["explains_flagged"] == 2


def test_b5_explains_flagged_counts_the_raw_replies_only():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5): over the raw replies, not the visible ones, and never a no_reply."""
    clean = good_reply("Coach", "not_found")
    rows = [
        make_row("raw-explains", "Coach", "not_found", clean + EXPLAINS_TEXT, visible=clean),
        make_row("visible-explains", "Coach", "not_found", clean, visible=clean + EXPLAINS_TEXT),
        make_row("gone", "Coach", "not_found", raw=None, visible=None, no_reply=True, error_class="TimeoutError"),
    ]

    assert report().build_results(rows, META)["explains_flagged"] == 1


def test_b5_explains_flagged_is_zero_for_a_clean_run():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5)."""
    clean = [row for row in table_rows() if row["id"].startswith("good-")]  # the good reply of every cell
    assert report().build_results(clean, META)["explains_flagged"] == 0
    # B4 S3: a fenced block trips (g) even in Socratic, where it also fails (d): the three bad-d rows, one per state.
    assert report().build_results(table_rows(), META)["explains_flagged"] == 3


def test_b5_a_g_flag_does_not_change_any_pass_count():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B4, B5): flag only, not in the pass count."""
    clean = [make_row("c1", "Coach", "not_found"), make_row("c2", "Coach", "not_found")]
    explained = [make_row("c1", "Coach", "not_found", good_reply("Coach", "not_found") + EXPLAINS_TEXT), clean[1]]

    before = report().build_results(clean, META)["counts"]["raw"]["Coach"]["not_found"]
    after = report().build_results(explained, META)["counts"]["raw"]["Coach"]["not_found"]

    assert before == after
    assert "c1" in report().build_results(explained, META)["flagged_ids"]  # but it is flagged for hand review


def test_b5_report_prints_the_explains_line_right_after_the_new_terms_line():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5)."""
    results = report().build_results(explain_rows(), META)
    lines = report().render_report(results).splitlines()

    (at,) = [i for i, line in enumerate(lines) if line.startswith(NEW_TERMS_PREFIX)]
    assert lines[at + 1] == (
        "Explains flags, check (g): 2 replies explain instead of asking (flag only, not in the pass count)")


def test_b5_the_explains_line_number_equals_explains_flagged(tmp_path):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5)."""
    pattern = (r"^Explains flags, check \(g\): (\d+) replies explain instead of asking "
               r"\(flag only, not in the pass count\)$")
    for rows, expected in ((explain_rows(), 2), (table_rows(), 3)):  # table_rows: 3 Socratic replies hold a fenced block (S3)
        run_dir = report().write_run(tmp_path / str(expected), "run1", rows, META)
        text = (run_dir / "report.txt").read_text(encoding="utf-8")
        found = re.search(pattern, text, re.MULTILINE)
        assert found is not None and int(found.group(1)) == expected
        assert json.loads((run_dir / "results.json").read_text(encoding="utf-8"))["explains_flagged"] == expected


def entries(sample):
    """The review sample split into its '## id | mode | state' entries."""
    return {block.splitlines()[0].split(" | ")[0]: block.splitlines() for block in sample.split("\n## ")[1:]}


def test_b5_review_sample_marks_a_g_flagged_reply_and_keeps_g_out_of_the_failed_checks():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5)."""
    found = entries(report().render_review_sample(explain_rows(), 29))

    for qid in ("g-1", "g-2"):  # flagged by (g) alone: included like any flagged reply
        assert qid in found, qid
        lines = found[qid]
        failed = next(line for line in lines if line.startswith("Failed checks:"))
        assert failed == "Failed checks: none"  # (g) is a flag, not a failed check
        assert "Explains flag: yes" in lines
        assert lines.index("Explains flag: yes") > lines.index(failed)  # under the Failed checks line


def test_b5_review_sample_has_no_explains_line_for_other_replies():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5): only for a reply (g) flagged."""
    found = entries(report().render_review_sample(explain_rows(), 29))

    assert "Explains flag: yes" not in found["a-1"]  # flagged by (a) only
    assert next(line for line in found["a-1"] if line.startswith("Failed checks:")) == "Failed checks: a"
    for qid in ("ok-1", "ok-2"):  # the calibration sample
        assert qid in found and "Explains flag: yes" not in found[qid]
    sample = report().render_review_sample(explain_rows(), 29)
    assert sample.count("Explains flag: yes") == 2


def test_b5_a_reply_that_fails_a_check_and_explains_shows_both():
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5)."""
    rows = [make_row("both", "Coach", "not_found", BODY["Coach"] + EXPLAINS_TEXT)]

    lines = entries(report().render_review_sample(rows, 29))["both"]

    assert "Failed checks: a" in lines and "Explains flag: yes" in lines
