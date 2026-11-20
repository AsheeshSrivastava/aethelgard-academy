"""SPEC-29 tests, part B: the latency and refusal summary from the SPEC-28 trace file (R9 to R16).

Written before the code. Offline, no model.
Names under test:
  lms.core.axis_report                         summarise_latency(records, include_test_mode=False, skipped_lines=0),
                                               format_latency_table(report, settings=None)
  lms.adapters.observability.report            read_trace_records(trace_dir) -> (records, skipped_lines)
  lms.cli                                      handle_report_command(["axis-latency", ...])
"""

import json
from pathlib import Path

import pytest

TRACE_FILE = "axis-trace.jsonl"


def core():
    import lms.core.axis_report as r

    return r


def reader():
    from lms.adapters.observability.report import read_trace_records

    return read_trace_records


_n = [0]


def rec(name, duration, trace_id="tr1", parent="root", status="ok", **attributes):
    _n[0] += 1
    return {
        "trace_id": trace_id, "span_id": f"sp{_n[0]:06d}", "parent_id": parent, "name": name,
        "started_at_ms": 1_700_000_000_000 + _n[0], "duration_ms": duration, "status": status, "attributes": attributes,
    }


def make_trace(trace_id, kind="axis_question", children=(), test_mode=False, duration=100):
    """A root span plus children given as (name, duration, attributes)."""
    root = rec(kind, duration, trace_id=trace_id, parent=None, kind=kind, test_mode=test_mode, interaction_id="01JCXYZABCDEFGHJKMNPQRSTVW")
    root["span_id"] = "root"
    return [root] + [rec(name, dur, trace_id=trace_id, **attrs) for name, dur, attrs in children]


def summarise(records, **kw):
    return core().summarise_latency(records, **kw)


def stage(rep, name):
    found = [s for s in rep["stages"] if s["name"] == name]
    assert len(found) == 1, (name, rep["stages"])
    return found[0]


def write_jsonl(directory: Path, name: str, lines):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text("".join(line if isinstance(line, str) else json.dumps(line) + "\n" for line in lines), encoding="utf-8")


# --- 1. Percentiles and tables (R9) ---


def test_nearest_rank_p50_p95_max():
    spans = [rec("retrieve", d, trace_id=f"t{d}") for d in range(1, 101)]  # 1..100 ms

    s = stage(summarise(spans), "retrieve")

    assert (s["n"], s["p50"], s["p95"], s["max"]) == (100, 50, 95, 100)


def test_nearest_rank_on_tiny_samples():
    s = stage(summarise([rec("retrieve", 40), rec("retrieve", 10), rec("retrieve", 30)]), "retrieve")

    assert (s["n"], s["p50"], s["p95"], s["max"]) == (3, 30, 40, 40)


def test_small_sample_is_marked_few():
    few = stage(summarise([rec("retrieve", 5)] * 19), "retrieve")
    enough = stage(summarise([rec("retrieve", 5)] * 20), "retrieve")

    assert few["few"] is True and enough["few"] is False
    assert "(few)" in core().format_latency_table(summarise([rec("retrieve", 5)] * 3))


def test_stage_and_trace_kind_tables():
    records = make_trace("a", children=[("retrieve", 30, {}), ("prompt_build", 2, {}), ("model_call", 900, {}), ("citation_check", 1, {})], duration=950)
    records += make_trace("b", kind="concept_check", children=[("model_call", 400, {})], duration=420)

    rep = summarise(records)

    assert {s["name"] for s in rep["stages"]} == {"retrieve", "prompt_build", "model_call", "citation_check"}
    assert stage(rep, "model_call")["n"] == 2
    assert {k["name"]: k["p50"] for k in rep["kinds"]} == {"axis_question": 950, "concept_check": 420}


# --- 2. Counts (R12) ---


def test_retrieval_status_downgraded_and_reason_counts():
    records = []
    for i, attrs in enumerate([
        {"retrieval_status": "ok"}, {"retrieval_status": "ok"},
        {"retrieval_status": "not_found"}, {"retrieval_status": "no_index"},
        {"retrieval_status": "unavailable", "retrieval_reason": "busy"},
        {"retrieval_status": "ok", "downgraded": True, "retrieval_reason": "timeout"},
        {"retrieval_status": "ok", "downgraded": True, "retrieval_reason": "stalled"},
        {"retrieval_status": "ok", "downgraded": True, "retrieval_reason": "model_fault"},
        {"retrieval_status": "ok", "downgraded": True, "retrieval_reason": "start_failed"},
    ]):
        records += make_trace(f"t{i}", children=[("retrieve", 20 + i, attrs)])

    r = summarise(records)["retrieval"]

    assert r["turns"] == 9
    assert r["status"] == {"ok": 6, "not_found": 1, "no_index": 1, "unavailable": 1}
    assert r["downgraded"] == 4
    assert r["reason"] == {"busy": 1, "timeout": 1, "stalled": 1, "start_failed": 1, "model_fault": 1}
    assert r["max_latency_ms"] == 28


def test_refusal_rate():
    records = []
    for i, status in enumerate(["ok", "ok", "not_found", "unavailable"]):
        records += make_trace(f"t{i}", children=[("retrieve", 10, {"retrieval_status": status})])

    assert summarise(records)["retrieval"]["refusal_rate"] == 0.5


def test_refusal_rate_is_none_without_retrieval_turns():
    r = summarise(make_trace("t1", kind="concept_check", children=[("model_call", 10, {})]))["retrieval"]

    assert r["turns"] == 0 and r["refusal_rate"] is None


def test_only_axis_question_traces_with_a_retrieve_span_count_as_retrieval_turns():
    records = make_trace("a", children=[("retrieve", 10, {"retrieval_status": "ok"})])
    records += make_trace("b", children=[("model_call", 10, {})])                 # axis_question without retrieve
    records += make_trace("c", kind="readme_draft", children=[("retrieve", 10, {"retrieval_status": "ok"})])

    assert summarise(records)["retrieval"]["turns"] == 1


def test_model_call_error_reason_and_mock_counts():
    records = make_trace("a", children=[("model_call", 5, {"mock": True})])
    records += make_trace("b", children=[("model_call", 5, {"mock": False, "fallback": "mock"})])
    records += make_trace("c", children=[("model_call", 5, {"mock": False})])
    records += [dict(rec("model_call", 5, trace_id="d", status="error", reason="budget"))]
    records += [dict(rec("model_call", 5, trace_id="e", status="error", reason="provider_error"))]

    m = summarise(records)["model_calls"]

    assert m["errors"] == {"budget": 1, "provider_error": 1}
    assert m["mock"] == 1 and m["fallback_mock"] == 1


# --- 3. test_mode and rootless spans (R11) ---


def test_test_mode_traces_excluded_with_their_children():
    records = make_trace("live", children=[("retrieve", 10, {"retrieval_status": "ok"})])
    records += make_trace("test", test_mode=True, children=[("retrieve", 99, {"retrieval_status": "not_found"})])

    excluded = summarise(records)
    included = summarise(records, include_test_mode=True)

    assert stage(excluded, "retrieve")["n"] == 1 and excluded["retrieval"]["turns"] == 1
    assert stage(included, "retrieve")["n"] == 2 and included["retrieval"]["turns"] == 2
    assert excluded["test_mode"] == "excluded" and included["test_mode"] == "included"


def test_rootless_spans_count_by_stage():
    orphan = rec("retrieve", 12, trace_id="gone", parent="rotated-away-parent")

    s = stage(summarise([orphan]), "retrieve")

    assert s["n"] == 1  # a rotated-away root or a call from `lms ask`: still counted, never test mode


# --- 4. Reading the file (R10, R14) ---


def test_missing_dir_empty_file_and_missing_rotated_file(tmp_path):
    read = reader()

    assert read(tmp_path / "nowhere") == ([], 0)
    write_jsonl(tmp_path, TRACE_FILE, [])
    assert read(tmp_path) == ([], 0)
    write_jsonl(tmp_path, TRACE_FILE, [rec("retrieve", 5)])  # no .1 file: fine
    records, skipped = read(tmp_path)
    assert len(records) == 1 and skipped == 0


def test_torn_and_non_json_lines_are_skipped_and_counted(tmp_path):
    write_jsonl(tmp_path, TRACE_FILE, [rec("retrieve", 5), "not json at all\n", "[1, 2]\n", '{"name": "half a lin', ])

    records, skipped = reader()(tmp_path)

    assert len(records) == 1 and skipped == 3


@pytest.mark.parametrize("bad", [
    {"name": "retrieve", "duration_ms": -1}, {"name": "retrieve", "duration_ms": 1e9}, {"name": "retrieve", "duration_ms": True},
    {"name": "retrieve", "duration_ms": "12"}, {"duration_ms": 5}, {"name": 7, "duration_ms": 5}, {"name": "retrieve"},
])
def test_unknown_fields_and_bad_duration_are_tolerated(bad):
    rep = summarise([bad, rec("retrieve", 7)])

    assert stage(rep, "retrieve")["n"] == 1  # only the good span counts; nothing raised


def test_attributes_null_or_wrong_type_are_tolerated():
    weird = rec("retrieve", 5)
    weird["attributes"] = None
    other = rec("retrieve", 6)
    other["attributes"] = ["not", "a", "dict"]

    assert stage(summarise([weird, other]), "retrieve")["n"] == 2


def test_a_later_version_with_new_keys_is_read(tmp_path):
    newer = rec("retrieve", 5)
    newer["new_top_level_key"] = {"x": 1}
    newer["attributes"]["some_future_attribute"] = "ok"
    write_jsonl(tmp_path, TRACE_FILE, [newer])

    records, skipped = reader()(tmp_path)

    assert skipped == 0 and stage(summarise(records), "retrieve")["n"] == 1


def test_rotated_file_is_read_before_the_current_one(tmp_path):
    write_jsonl(tmp_path, TRACE_FILE + ".1", [rec("retrieve", 1)])
    write_jsonl(tmp_path, TRACE_FILE, [rec("retrieve", 2)])

    records, _ = reader()(tmp_path)

    assert [r["duration_ms"] for r in records] == [1, 2]


def test_a_trace_path_that_is_a_directory_is_not_a_crash(tmp_path):
    (tmp_path / TRACE_FILE).mkdir()

    assert reader()(tmp_path) == ([], 0)


def test_ten_thousand_spans_in_one_trace(tmp_path):
    write_jsonl(tmp_path, TRACE_FILE, [rec("retrieve", i % 50, trace_id="big") for i in range(10_000)])

    records, skipped = reader()(tmp_path)

    assert len(records) == 10_000 and stage(summarise(records), "retrieve")["n"] == 10_000


# --- 5. Output (R13, R14) ---


def test_header_prints_settings_in_force():
    text = core().format_latency_table(summarise([rec("retrieve", 5)]), settings={"timeout_s": 10.0, "concurrency": 2})

    assert "LMS_RETRIEVAL_TIMEOUT_S" in text and "10" in text
    assert "LMS_RERANK_CONCURRENCY" in text
    for verdict in ("too high", "too low", "should", "recommend"):
        assert verdict not in text.lower()


def test_no_traces_message(tmp_path, capsys):
    from lms.cli import handle_report_command

    code = handle_report_command(["axis-latency", "--trace-dir", str(tmp_path / "none")])

    assert code == 0 and "No traces recorded yet. Set LMS_TRACER=local" in capsys.readouterr().out


def test_skipped_lines_are_printed_only_when_above_zero(tmp_path, capsys):
    from lms.cli import handle_report_command

    write_jsonl(tmp_path, TRACE_FILE, [rec("retrieve", 5)])
    handle_report_command(["axis-latency", "--trace-dir", str(tmp_path)])
    clean = capsys.readouterr().out
    write_jsonl(tmp_path, TRACE_FILE, [rec("retrieve", 5), "garbage\n"])
    handle_report_command(["axis-latency", "--trace-dir", str(tmp_path)])
    dirty = capsys.readouterr().out

    assert "skipped_lines" not in clean and "skipped_lines" in dirty


def test_latency_json_matches_the_table(tmp_path, capsys):
    from lms.cli import handle_report_command

    write_jsonl(tmp_path, TRACE_FILE, make_trace("a", children=[("retrieve", 33, {"retrieval_status": "ok"})]))

    assert handle_report_command(["axis-latency", "--json", "--trace-dir", str(tmp_path)]) == 0
    data = json.loads(capsys.readouterr().out)

    assert {s["name"]: s["p50"] for s in data["stages"]}["retrieve"] == 33
    assert data["retrieval"]["status"]["ok"] == 1


def test_latency_report_is_deterministic_and_has_no_text_or_ids():
    records = make_trace("trace-marker-9", children=[("retrieve", 10, {"retrieval_status": "ok", "passage_refs": [
        {"passage_id": "docs/a.md@abcd1234#c0-9~0123456789ab", "source_id": "docs/a.md", "score": 1.0}]})])
    r = core()

    shown = json.dumps(r.summarise_latency(records)) + r.format_latency_table(r.summarise_latency(records))

    assert json.dumps(r.summarise_latency(records)) == json.dumps(r.summarise_latency(list(records)))
    for forbidden in ("trace-marker-9", "01JCXYZABCDEFGHJKMNPQRSTVW", "docs/a.md", "passage_id", "span_id", "sp0000"):
        assert forbidden not in shown


# --- review round 1 ---


def test_largest_search_latency_covers_every_retrieve_span_not_only_the_first():
    records = make_trace("a", children=[("retrieve", 10, {"retrieval_status": "ok"}), ("retrieve", 777, {"retrieval_status": "ok"})])
    records += [rec("retrieve", 9000, trace_id="orphan")]  # a rootless search still counts toward the largest latency

    assert summarise(records)["retrieval"]["max_latency_ms"] == 9000


def test_the_reason_vocabularies_agree():
    import lms.core.tracing as tracing

    assert set(core().RETRIEVAL_REASONS) == set(tracing.RETRIEVAL_REASONS)
