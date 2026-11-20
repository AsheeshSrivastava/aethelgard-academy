"""SPEC-29 tests, part A: the mode-usage report (R1 to R8) and the thumbs counts in it (R5).

Written before the code (Build order, ADR-0037 / SPEC-29). Offline, no model.
Names under test (the contract these tests fix):
  lms.core.axis_report                 aggregate_modes(events, include_test_mode=False), week_of(ms), format_modes_table(report)
  SQLiteLearnerRepository              read_only=True, iter_interactions(event_types), get_interaction(learner_id, interaction_id)
  lms.cli                              handle_report_command(args, environ=None) -> int
Each test imports lazily so a missing module fails that test alone, for the right reason.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lms.core.interaction_log import InteractionEvent

LEARNER_MARKER = "learner-marker-zebra-1"
QUESTION_MARKER = "zebra-quartz-question-text"


def ms(y, m, d, h=0, mi=0, s=0, milli=0):
    return int(datetime(y, m, d, h, mi, s, milli * 1000, tzinfo=timezone.utc).timestamp() * 1000)


MONDAY = ms(2026, 11, 16, 9)  # 2026-11-16 is a Monday


def ev(turn_id, mode="Coach", unit="PY-0.1", at=MONDAY, learner="me", test_mode=False, payload=None):
    if payload is None:
        payload = {"mode": mode, "question": QUESTION_MARKER, "answer": "an answer"} if mode is not None else {"question": QUESTION_MARKER}
    return InteractionEvent(
        interaction_id=turn_id, learner_id=learner, recorded_at_ms=at, event_type="axis",
        payload=payload, unit_id=unit, test_mode=test_mode,
    )


def vote(turn_id, value, learner="me", at=MONDAY + 1000, test_mode=False, vote_id=None):
    return InteractionEvent(
        interaction_id=vote_id or f"vote-{turn_id}-{at}-{value}", learner_id=learner, recorded_at_ms=at,
        event_type="axis_feedback", payload={"turn_id": turn_id, "vote": value}, unit_id="PY-0.1", test_mode=test_mode,
    )


def report_mod():
    import lms.core.axis_report as r

    return r


def modes(events, **kw):
    return report_mod().aggregate_modes(events, **kw)


def row(report, key, **match):
    rows = [r for r in report[key] if all(r.get(k) == v for k, v in match.items())]
    assert len(rows) == 1, (key, match, report[key])
    return rows[0]


# --- 1. Counts (R1) ---


def test_report_counts_turns_per_mode():
    rep = modes([ev("t1", "Coach"), ev("t2", "Coach"), ev("t3", "Socratic"), ev("t4", "Hybrid")])

    assert row(rep, "by_mode", mode="Coach")["turns"] == 2
    assert row(rep, "by_mode", mode="Socratic")["turns"] == 1
    assert row(rep, "by_mode", mode="Hybrid")["turns"] == 1
    assert rep["total_turns"] == 4


def test_report_groups_per_mode_and_unit():
    rep = modes([ev("t1", "Coach", unit="PY-0.1"), ev("t2", "Coach", unit="PY-0.2"), ev("t3", "Coach", unit="PY-0.2")])

    assert row(rep, "by_mode_unit", mode="Coach", unit="PY-0.1")["turns"] == 1
    assert row(rep, "by_mode_unit", mode="Coach", unit="PY-0.2")["turns"] == 2


def test_report_groups_per_mode_and_week():
    rep = modes([ev("t1", "Coach", at=ms(2026, 11, 16, 9)), ev("t2", "Coach", at=ms(2026, 11, 18)), ev("t3", "Coach", at=ms(2026, 11, 24))])

    assert row(rep, "by_mode_week", mode="Coach", week="2026-11-16")["turns"] == 2
    assert row(rep, "by_mode_week", mode="Coach", week="2026-11-23")["turns"] == 1


def test_week_starts_on_utc_monday_at_the_exact_millisecond():
    week_of = report_mod().week_of

    assert week_of(ms(2026, 11, 22, 23, 59, 59, 999)) == "2026-11-16"  # Sunday's last millisecond
    assert week_of(ms(2026, 11, 23, 0, 0, 0, 0)) == "2026-11-23"        # Monday's first
    assert week_of(ms(2026, 11, 16, 0, 0, 0, 0)) == "2026-11-16"
    assert week_of(ms(2026, 1, 1)) == "2025-12-29"                      # across a year boundary


@pytest.mark.parametrize("mode", [None, "", "coach", "   ", "x" * 10_000, "Coach\nSocratic", 7])
def test_missing_empty_and_bad_mode_counts_as_unknown(mode):
    payload = {"mode": mode} if mode is not None else {}

    rep = modes([ev("t1", payload=payload)])

    assert row(rep, "by_mode", mode="unknown")["turns"] == 1
    assert rep["total_turns"] == 1


def test_non_object_payload_counts_as_unknown_not_dropped():
    broken = InteractionEvent.model_construct(
        interaction_id="t1", learner_id="me", recorded_at_ms=MONDAY, event_type="axis", payload=[], unit_id=None,
        session_id=None, attempt_id=None, activity=None, item_id=None, test_mode=False,
    )

    rep = modes([broken])

    assert row(rep, "by_mode", mode="unknown")["turns"] == 1
    assert row(rep, "by_mode_unit", mode="unknown", unit="(none)")["turns"] == 1


def test_unit_none_groups_under_none():
    rep = modes([ev("t1", "Coach", unit=None)])

    assert row(rep, "by_mode_unit", mode="Coach", unit="(none)")["turns"] == 1


# --- 2. test_mode (R3) ---


def test_test_mode_rows_are_excluded_by_default():
    rep = modes([ev("t1", "Coach"), ev("t2", "Coach", test_mode=True)])

    assert rep["total_turns"] == 1 and rep["test_mode"] == "excluded"


def test_include_test_mode_flag_includes_them():
    rep = modes([ev("t1", "Coach"), ev("t2", "Coach", test_mode=True)], include_test_mode=True)

    assert rep["total_turns"] == 2 and rep["test_mode"] == "included"


# --- 3. Learners column (R1) ---


def test_learners_column_only_when_more_than_one_learner():
    one = modes([ev("t1", learner="a"), ev("t2", learner="a")])
    two = modes([ev("t1", learner="a"), ev("t2", learner="a"), ev("t3", learner="b")])

    assert one["multi_learner"] is False and "learners" not in one["by_mode"][0]
    assert two["multi_learner"] is True
    assert row(two, "by_mode", mode="Coach")["learners"] == 2


# --- 4. What the report must never contain (R1, R6, R8) ---


def test_report_output_has_no_text_ids_or_timestamps():
    r = report_mod()
    events = [ev("turn-id-aaaa1111", "Coach", learner=LEARNER_MARKER), vote("turn-id-aaaa1111", "up", learner=LEARNER_MARKER)]

    rep = r.aggregate_modes(events)
    shown = json.dumps(rep) + r.format_modes_table(rep)

    for forbidden in (QUESTION_MARKER, "an answer", LEARNER_MARKER, "turn-id-aaaa1111", "vote-"):
        assert forbidden not in shown
    assert str(MONDAY) not in shown and "generated" not in shown.lower()


def test_report_header_states_utc_weeks_and_test_mode_rows():
    r = report_mod()

    text = r.format_modes_table(r.aggregate_modes([ev("t1")]))

    assert "Weeks run Monday to Sunday, UTC." in text
    assert "test_mode rows: excluded" in text
    assert "test_mode rows: included" in r.format_modes_table(r.aggregate_modes([ev("t1")], include_test_mode=True))


def test_report_json_matches_the_table_numbers(tmp_path, capsys):
    from lms.cli import handle_report_command

    db = seed_db(tmp_path, [ev("t1", "Coach"), ev("t2", "Coach"), ev("t3", "Socratic")])

    assert handle_report_command(["axis-modes", "--json", "--db", str(db)]) == 0
    data = json.loads(capsys.readouterr().out)

    assert {r["mode"]: r["turns"] for r in data["by_mode"]} == {"Coach": 2, "Socratic": 1}
    assert data["total_turns"] == 3


def test_report_is_deterministic():
    events = [ev(f"t{i}", mode, unit=unit, at=MONDAY + i * 86_400_000) for i, (mode, unit) in
              enumerate([("Coach", "PY-0.1"), ("Hybrid", "PY-0.2"), ("Socratic", "PY-0.1"), ("Coach", "PY-0.2")] * 3)]
    r = report_mod()

    assert json.dumps(r.aggregate_modes(events), sort_keys=True) == json.dumps(r.aggregate_modes(list(reversed(events))), sort_keys=True)
    assert r.format_modes_table(r.aggregate_modes(events)) == r.format_modes_table(r.aggregate_modes(list(reversed(events))))


# --- 5. Thumbs counts (R5) ---


def test_latest_vote_per_learner_and_turn_wins():
    rep = modes([
        ev("t1", "Coach"),
        vote("t1", "up", at=MONDAY + 1000), vote("t1", "down", at=MONDAY + 2000), vote("t1", "up", at=MONDAY + 3000),
    ])

    assert (row(rep, "by_mode", mode="Coach")["up"], row(rep, "by_mode", mode="Coach")["down"]) == (1, 0)


def test_latest_vote_ties_break_by_interaction_id():
    rep = modes([ev("t1", "Coach"), vote("t1", "up", at=MONDAY + 5, vote_id="vote-a"), vote("t1", "down", at=MONDAY + 5, vote_id="vote-b")])

    assert (row(rep, "by_mode", mode="Coach")["up"], row(rep, "by_mode", mode="Coach")["down"]) == (0, 1)


def test_clear_removes_the_vote():
    rep = modes([ev("t1", "Coach"), vote("t1", "up", at=MONDAY + 1000), vote("t1", "clear", at=MONDAY + 2000)])

    assert (row(rep, "by_mode", mode="Coach")["up"], row(rep, "by_mode", mode="Coach")["down"]) == (0, 0)


def test_vote_on_an_excluded_or_missing_turn_is_not_counted():
    rep = modes([
        ev("t1", "Coach", test_mode=True), vote("t1", "up"),   # the turn is excluded by R3
        ev("t2", "Coach"), vote("ghost", "down"),              # no such turn in the data
    ])

    assert (row(rep, "by_mode", mode="Coach")["up"], row(rep, "by_mode", mode="Coach")["down"]) == (0, 0)


def test_vote_mode_is_the_turns_mode():
    rep = modes([ev("t1", "Socratic"), ev("t2", "Coach"), vote("t1", "down"), vote("t2", "up")])

    assert row(rep, "by_mode", mode="Socratic")["down"] == 1 and row(rep, "by_mode", mode="Coach")["up"] == 1


def test_two_learners_voting_on_the_same_turn_id_are_counted_separately():
    rep = modes([ev("t1", "Coach", learner="a"), vote("t1", "up", learner="a"), vote("t1", "down", learner="b")])

    assert (row(rep, "by_mode", mode="Coach")["up"], row(rep, "by_mode", mode="Coach")["down"]) == (1, 0)  # b has no such turn


# --- 6. Repository reads and the CLI (R6, R7) ---


def seed_db(tmp_path, events):
    from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository

    db = tmp_path / "lms_state.db"
    repo = SQLiteLearnerRepository(str(db))
    repo.initialize()
    for e in events:
        repo.append_interaction(e)
    return db


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_iter_interactions_reads_across_learners_and_never_writes(tmp_path):
    from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository

    db = seed_db(tmp_path, [ev("t1", learner="a"), ev("t2", learner="b"), vote("t1", "up", learner="a")])
    before = digest(db)
    repo = SQLiteLearnerRepository(str(db), read_only=True)

    rows = list(repo.iter_interactions(["axis", "axis_feedback"]))
    only_axis = list(repo.iter_interactions(["axis"]))

    assert {(r.learner_id, r.event_type) for r in rows} == {("a", "axis"), ("b", "axis"), ("a", "axis_feedback")}
    assert len(only_axis) == 2
    assert digest(db) == before
    with pytest.raises(Exception):
        repo.append_interaction(ev("t9"))  # a read-only handle cannot write
    assert digest(db) == before


def test_repository_get_interaction_is_per_learner(tmp_path):
    from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository

    db = seed_db(tmp_path, [ev("t1", learner="a")])
    repo = SQLiteLearnerRepository(str(db), read_only=True)

    assert repo.get_interaction("a", "t1").event_type == "axis"
    assert repo.get_interaction("b", "t1") is None
    assert repo.get_interaction("a", "missing") is None


def test_report_never_writes_or_creates_the_database(tmp_path, capsys):
    from lms.cli import handle_report_command

    db = seed_db(tmp_path, [ev("t1")])
    before = digest(db)
    handle_report_command(["axis-modes", "--db", str(db)])
    capsys.readouterr()
    missing = tmp_path / "nope.db"

    handle_report_command(["axis-modes", "--db", str(missing)])

    assert digest(db) == before and not missing.exists()
    assert not list(tmp_path.glob("nope*"))


def test_missing_database_says_so_and_exits_zero(tmp_path, capsys):
    from lms.cli import handle_report_command

    missing = tmp_path / "nope.db"

    code = handle_report_command(["axis-modes", "--db", str(missing)])

    out = capsys.readouterr().out
    assert code == 0 and "No interaction log found at" in out and str(missing) in out


def test_empty_log_says_no_turns(tmp_path, capsys):
    from lms.cli import handle_report_command

    db = seed_db(tmp_path, [])

    code = handle_report_command(["axis-modes", "--db", str(db)])

    out = capsys.readouterr().out
    assert code == 0 and "No AXIS turns recorded." in out and "Weeks run Monday to Sunday, UTC." in out


def test_a_file_that_is_not_sqlite_is_a_plain_message_not_a_crash(tmp_path, capsys):
    from lms.cli import handle_report_command

    bad = tmp_path / "bad.db"
    bad.write_text("this is not a database", encoding="utf-8")

    code = handle_report_command(["axis-modes", "--db", str(bad)])

    assert code != 0 and "Could not read" in capsys.readouterr().out


# --- 7. Review round 1 ---


def test_a_database_with_no_log_table_is_an_empty_log_not_a_failure(tmp_path, capsys):
    import sqlite3

    from lms.cli import handle_report_command

    db = tmp_path / "bare.db"
    sqlite3.connect(db).close()  # a valid SQLite file that has never logged anything

    code = handle_report_command(["axis-modes", "--db", str(db)])

    assert code == 0 and "No AXIS turns recorded." in capsys.readouterr().out


def test_control_characters_in_a_unit_id_never_reach_the_terminal_table():
    r = report_mod()

    text = r.format_modes_table(r.aggregate_modes([ev("t1", "Coach", unit="PY-0.1\n\x1b[31mevil\x07")]))

    assert "\x1b" not in text and "\x07" not in text and "\r" not in text
    assert all("evil" not in line or line.startswith("Coach") for line in text.splitlines())  # the row stays on one line
