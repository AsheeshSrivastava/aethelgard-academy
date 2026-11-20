"""SPEC-29 tests, part C: the static HTML report (R18, R19).

Written before the code. Offline, no model.
Names under test:
  lms.adapters.observability.report   render_html(modes_report, latency_report, settings=None) -> str, write_html(path, html)
  lms.cli                             handle_report_command(["axis-html", "--out", FILE, "--db", DB, "--trace-dir", DIR])
"""

import os
import re

import pytest

from test_axis_report import LEARNER_MARKER, MONDAY, QUESTION_MARKER, ev, seed_db, vote
from test_axis_latency_report import TRACE_FILE, make_trace, write_jsonl

EVIL = "<script>alert(1)</script>\"'&</table>\x00"


def report_mod():
    from lms.adapters.observability import report

    return report


def reports_for(events, trace_records=()):
    import lms.core.axis_report as core

    modes = core.aggregate_modes(events)
    latency = core.summarise_latency(list(trace_records))
    return modes, latency


def html_for(events=(), trace_records=()):
    modes, latency = reports_for(list(events) or [ev("t1", "Coach")], trace_records)
    return report_mod().render_html(modes, latency, settings={"timeout_s": 10.0, "concurrency": 2})


def test_html_is_one_file_with_no_external_asset_or_script():
    page = html_for(trace_records=make_trace("a", children=[("retrieve", 12, {"retrieval_status": "ok"})]))

    lowered = page.lower()
    for forbidden in ("http://", "https://", "//cdn", "<script", "<link", "<img", "<iframe", "<object", "<embed",
                      "@import", "url(", " src=", "onload", "onclick", "javascript:"):
        assert forbidden not in lowered, forbidden
    assert lowered.lstrip().startswith("<!doctype html>") and "<style>" in lowered


def test_html_has_a_content_security_policy():
    page = html_for()

    assert re.search(r'<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">', page)


def test_html_supports_light_and_dark():
    assert "prefers-color-scheme: dark" in html_for()


def test_html_escapes_every_value():
    import lms.core.axis_report as core

    modes = {
        "test_mode": EVIL, "total_turns": 1, "multi_learner": False,
        "by_mode": [{"mode": EVIL, "turns": 1, "up": 0, "down": 0}],
        "by_mode_unit": [{"mode": EVIL, "unit": EVIL, "turns": 1}],
        "by_mode_week": [{"mode": EVIL, "week": EVIL, "turns": 1}],
    }
    latency = core.summarise_latency([])
    latency["stages"] = [{"name": EVIL, "n": 1, "p50": 1, "p95": 1, "max": 1, "few": True}]
    latency["kinds"] = [{"name": EVIL, "n": 1, "p50": 1, "p95": 1, "max": 1, "few": True}]

    page = report_mod().render_html(modes, latency, settings={"timeout_s": EVIL, "concurrency": EVIL})

    assert "<script>alert(1)</script>" not in page and "</table>\x00" not in page and "\x00" not in page
    assert "&lt;script&gt;" in page and "&quot;" in page and "&#x27;" in page and "&amp;" in page


def test_html_holds_no_learner_trace_span_interaction_or_passage_id_and_no_text(tmp_path):
    from lms.cli import handle_report_command

    db = seed_db(tmp_path, [ev("turn-id-aaaa1111", "Coach", learner=LEARNER_MARKER), vote("turn-id-aaaa1111", "up", learner=LEARNER_MARKER)])
    traces = tmp_path / "traces"
    marker_ref = {"passage_id": "docs/a.md@abcd1234#c0-9~0123456789ab", "source_id": "docs/private-doc.md", "score": 1.0}
    write_jsonl(traces, TRACE_FILE, make_trace("trace-marker-9", children=[("retrieve", 10, {"retrieval_status": "ok", "passage_refs": [marker_ref]})]))
    out = tmp_path / "report.html"

    assert handle_report_command(["axis-html", "--out", str(out), "--db", str(db), "--trace-dir", str(traces)]) == 0
    page = out.read_text(encoding="utf-8")

    for forbidden in (QUESTION_MARKER, "an answer", LEARNER_MARKER, "turn-id-aaaa1111", "trace-marker-9", "01JCXYZABCDEFGHJKMNPQRSTVW",
                      "docs/private-doc.md", "0123456789ab", "passage_id", "passage_refs", "span_id", "sp0000", str(MONDAY)):
        assert forbidden not in page, forbidden
    assert "Coach" in page  # but the aggregates are there


def test_html_tables_have_captions_and_scoped_headers():
    page = html_for(trace_records=make_trace("a", children=[("retrieve", 12, {"retrieval_status": "ok"})]))

    tables = re.findall(r"<table.*?</table>", page, flags=re.S)
    assert len(tables) >= 4
    for table in tables:
        assert "<caption>" in table and 'scope="col"' in table
    assert "<th>" not in page  # every header says what it heads


def test_html_says_it_is_a_local_owner_view():
    page = html_for()

    assert "local owner view" in page.lower() and "not a learner page" in page.lower()


def test_html_writes_a_small_sample_in_words_not_colour():
    page = html_for(trace_records=make_trace("a", children=[("retrieve", 12, {"retrieval_status": "ok"})]))

    assert "(few)" in page  # one span is far below 20: the state is written, never only coloured


def test_html_write_is_atomic_and_keeps_the_old_file_on_failure(tmp_path, monkeypatch):
    rep = report_mod()
    target = tmp_path / "out" / "axis-report.html"
    rep.write_html(target, "<!doctype html>old")

    def boom(src, dst):
        raise OSError("disk full internal-detail")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(Exception) as raised:
        rep.write_html(target, "<!doctype html>new")

    assert target.read_text(encoding="utf-8") == "<!doctype html>old"
    assert "internal-detail" not in str(raised.value)
    assert [p.name for p in target.parent.iterdir()] == ["axis-report.html"]  # the temporary file is cleaned up


def test_html_default_path_and_folder_created(tmp_path, monkeypatch, capsys):
    from lms.cli import handle_report_command

    monkeypatch.chdir(tmp_path)
    db = seed_db(tmp_path, [ev("t1")])

    assert handle_report_command(["axis-html", "--db", str(db), "--trace-dir", str(tmp_path / "none")]) == 0

    assert (tmp_path / "data" / "reports" / "axis-report.html").exists()
    assert "axis-report.html" in capsys.readouterr().out


def test_html_refuses_to_overwrite_the_database_or_a_trace_file(tmp_path, capsys):
    from lms.cli import handle_report_command

    db = seed_db(tmp_path, [ev("t1")])
    traces = tmp_path / "traces"
    write_jsonl(traces, TRACE_FILE, make_trace("a"))
    before_db, before_trace = db.read_bytes(), (traces / TRACE_FILE).read_bytes()

    assert handle_report_command(["axis-html", "--out", str(db), "--db", str(db), "--trace-dir", str(traces)]) != 0
    assert handle_report_command(["axis-html", "--out", str(traces / TRACE_FILE), "--db", str(db), "--trace-dir", str(traces)]) != 0

    assert db.read_bytes() == before_db and (traces / TRACE_FILE).read_bytes() == before_trace
    assert "refus" in capsys.readouterr().out.lower()


def test_html_works_with_no_data_at_all(tmp_path):
    from lms.cli import handle_report_command

    out = tmp_path / "empty.html"

    assert handle_report_command(["axis-html", "--out", str(out), "--db", str(tmp_path / "none.db"), "--trace-dir", str(tmp_path / "none")]) == 0
    page = out.read_text(encoding="utf-8")

    assert "No AXIS turns recorded." in page and "No traces recorded yet." in page


def test_html_is_deterministic():
    events = [ev("t1", "Coach"), ev("t2", "Hybrid", unit="PY-0.2")]

    assert html_for(events) == html_for(list(reversed(events)))
    assert not re.search(r"\b20\d\d-\d\d-\d\dT\d\d:", html_for(events))  # no generation timestamp
