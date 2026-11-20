"""SPEC-28 tests, part 1: the tracer port, NoopTracer, LocalTracer, LMS_TRACER settings, the attribute allow-list.

Written before the code (Build order, ADR-0037 / SPEC-28). Offline: no model, no network.
Module names under test (the contract these tests fix; SPEC-28 sections 2 and 3):
  lms.core.tracing                         ITracer, NoopTracer, ALLOWED_ATTRIBUTES, span, event, set_tracer, sanitise_attributes
  lms.adapters.observability.local_tracer  LocalTracer(directory, max_bytes=...)
  lms.adapters.observability.startup       build_tracer(environ), TracerConfigError
Each test imports lazily so a missing module fails that test alone, for the right reason.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path

import pytest

ID = "01JCXYZABCDEFGHJKMNPQRSTVW"  # a valid interaction id shape (8 to 64 of A-Za-z0-9_-)
TRACE_FILE = "axis-trace.jsonl"


def core():
    import lms.core.tracing as tracing

    return tracing


def local(directory, **kw):
    from lms.adapters.observability.local_tracer import LocalTracer

    return LocalTracer(directory, **kw)


def read_spans(directory):
    """Every recorded span, oldest file first: the rotated file, then the current one."""
    spans = []
    for name in (TRACE_FILE + ".1", TRACE_FILE):
        path = Path(directory) / name
        if path.exists():
            spans += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return spans


@pytest.fixture(autouse=True)
def reset_process_tracer():
    yield
    try:
        t = core()
        t.set_tracer(t.NoopTracer())
    except ImportError:
        pass


# --- 1. The port and its rules (R1 to R4) ---


def test_noop_tracer_does_nothing():
    t = core()
    tracer = t.NoopTracer()

    with tracer.span("axis_question", mode="Coach") as handle:
        handle.set(unit_id="PY-0.1")
        tracer.event("note", mode="Coach")

    assert isinstance(tracer, t.ITracer)


def test_spans_nest_through_ambient_context(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with t.span("axis_question", interaction_id=ID):
        with t.span("retrieve"):
            pass

    root = next(s for s in read_spans(tmp_path) if s["name"] == "axis_question")
    child = next(s for s in read_spans(tmp_path) if s["name"] == "retrieve")
    assert child["parent_id"] == root["span_id"]
    assert child["trace_id"] == root["trace_id"]
    assert root["parent_id"] is None


def test_a_span_records_its_required_fields(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with t.span("axis_question", interaction_id=ID, mode="Coach"):
        pass

    (span,) = read_spans(tmp_path)
    for key in ("trace_id", "span_id", "parent_id", "name", "started_at_ms", "duration_ms", "status", "attributes"):
        assert key in span
    assert span["status"] == "ok" and span["duration_ms"] >= 0
    assert span["attributes"]["mode"] == "Coach" and span["attributes"]["interaction_id"] == ID


class ExplodingTracer:
    """Raises from every method, to prove a tracer can never break a turn (R2)."""

    def span(self, name, **attributes):
        raise RuntimeError("tracer is broken")

    def event(self, name, **attributes):
        raise RuntimeError("tracer is broken")


def test_a_failing_tracer_never_raises_into_the_caller():
    t = core()
    t.set_tracer(ExplodingTracer())

    with t.span("axis_question", interaction_id=ID) as handle:
        handle.set(mode="Coach")
        result = 40 + 2
    t.event("note", mode="Coach")

    assert result == 42


def test_tracer_fault_is_logged_once_per_process(caplog):
    t = core()
    t.set_tracer(ExplodingTracer())

    with caplog.at_level(logging.WARNING):
        for _ in range(5):
            with t.span("axis_question"):
                pass
            t.event("note")

    faults = [r for r in caplog.records if "tracing" in r.getMessage().lower()]
    assert len(faults) == 1
    assert "RuntimeError" in faults[0].getMessage()


def test_exception_in_caller_code_propagates_and_marks_span_error_with_class_name_only(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with pytest.raises(ValueError):
        with t.span("axis_question", interaction_id=ID):
            raise ValueError("learner said zebra-quartz-secret")

    (span,) = read_spans(tmp_path)
    assert span["status"] == "error"
    assert span["attributes"]["error_class"] == "ValueError"
    assert "zebra-quartz-secret" not in json.dumps(span)


def test_a_keyboard_interrupt_is_not_swallowed(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with pytest.raises(KeyboardInterrupt):
        with t.span("axis_question"):
            raise KeyboardInterrupt()


# --- 2. LocalTracer (R4, R6, R18) ---


def test_local_tracer_writes_one_sorted_json_line_per_span(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with t.span("axis_question", interaction_id=ID, mode="Coach", unit_id="PY-0.1"):
        with t.span("retrieve", passages_retrieved=2):
            pass

    lines = (tmp_path / TRACE_FILE).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert list(obj) == sorted(obj)
        assert list(obj["attributes"]) == sorted(obj["attributes"])


def spam(t, count):
    for n in range(count):
        with t.span("retrieve", terms_total=n):
            pass


def test_local_tracer_rotates_to_one_file_at_the_cap(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path, max_bytes=2_000))

    spam(t, 60)

    assert (tmp_path / (TRACE_FILE + ".1")).exists()
    assert (tmp_path / TRACE_FILE).stat().st_size <= 2_000
    assert not (tmp_path / (TRACE_FILE + ".2")).exists()


def test_local_tracer_second_rotation_replaces_the_old_one(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path, max_bytes=2_000))

    spam(t, 400)

    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == [TRACE_FILE, TRACE_FILE + ".1"]
    oldest_kept = min(s["attributes"]["terms_total"] for s in read_spans(tmp_path))
    assert oldest_kept > 0  # the first spans are gone: only the two newest files remain


def break_dir(path: Path):
    shutil.rmtree(path)
    path.write_text("i am a file now", encoding="utf-8")


def test_local_tracer_survives_unwritable_dir_after_startup(tmp_path):
    t = core()
    folder = tmp_path / "traces"
    t.set_tracer(local(folder))
    break_dir(folder)

    with t.span("axis_question", interaction_id=ID) as handle:
        handle.set(mode="Coach")
        value = "reply unchanged"

    assert value == "reply unchanged"


def test_local_tracer_disables_after_second_consecutive_write_failure(tmp_path, caplog):
    t = core()
    folder = tmp_path / "traces"
    t.set_tracer(local(folder))
    break_dir(folder)

    with caplog.at_level(logging.WARNING):
        for _ in range(2):
            with t.span("retrieve"):
                pass
        folder.unlink()
        folder.mkdir()  # the disk is healthy again, but the tracer has given up for this run
        for _ in range(3):
            with t.span("retrieve"):
                pass

    assert not (folder / TRACE_FILE).exists()
    assert len([r for r in caplog.records if "disabled" in r.getMessage().lower()]) == 1


def test_local_tracer_cap_smaller_than_one_line_still_works(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path, max_bytes=10))

    spam(t, 5)

    assert read_spans(tmp_path)  # something is kept; nothing raised


def test_a_torn_last_line_does_not_break_the_next_write(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))
    (tmp_path / TRACE_FILE).write_text('{"name": "half a lin', encoding="utf-8")  # a crash mid-write, no newline

    with t.span("retrieve", passages_retrieved=1):
        pass

    good = []
    for line in (tmp_path / TRACE_FILE).read_text(encoding="utf-8").splitlines():
        try:
            good.append(json.loads(line))
        except ValueError:
            pass
    assert any(s.get("name") == "retrieve" for s in good)


# --- 3. LMS_TRACER and the other settings (R5, R7, section 3) ---


def build(environ):
    from lms.adapters.observability.startup import build_tracer

    return build_tracer(environ)


def test_tracer_setting_default_is_noop():
    t = core()

    assert isinstance(build({}), t.NoopTracer)
    assert isinstance(build({"LMS_TRACER": ""}), t.NoopTracer)
    assert isinstance(build({"LMS_TRACER": " NOOP "}), t.NoopTracer)


def test_tracer_setting_local_builds_a_local_tracer(tmp_path):
    from lms.adapters.observability.local_tracer import LocalTracer

    tracer = build({"LMS_TRACER": " Local ", "LMS_TRACE_DIR": str(tmp_path)})

    assert isinstance(tracer, LocalTracer) and tracer.max_bytes == 10_000_000


@pytest.mark.parametrize("value", ["jaeger", "otel", "langsmith", "0", "on"])
def test_tracer_setting_rejects_unknown_value_even_with_mock_ai(value):
    from lms.adapters.observability.startup import TracerConfigError

    with pytest.raises(TracerConfigError) as raised:
        build({"LMS_TRACER": value, "MOCK_AI": "true"})

    assert "noop" in str(raised.value) and "local" in str(raised.value)


@pytest.mark.parametrize("value", ["abc", "-1", "99999", "1000000001", "1e9", "10000000000000"])
def test_trace_max_bytes_rejects_bad_values(value, tmp_path):
    from lms.adapters.observability.startup import TracerConfigError

    with pytest.raises(TracerConfigError):
        build({"LMS_TRACER": "local", "LMS_TRACE_DIR": str(tmp_path), "LMS_TRACE_MAX_BYTES": value})


@pytest.mark.parametrize("value, expected", [("100000", 100_000), ("1000000000", 1_000_000_000)])
def test_trace_max_bytes_accepts_the_bounds(value, expected, tmp_path):
    tracer = build({"LMS_TRACER": "local", "LMS_TRACE_DIR": str(tmp_path), "LMS_TRACE_MAX_BYTES": value})

    assert tracer.max_bytes == expected


def test_a_trace_folder_that_cannot_be_made_is_a_startup_message(tmp_path):
    from lms.adapters.observability.startup import TracerConfigError

    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")

    with pytest.raises(TracerConfigError):
        build({"LMS_TRACER": "local", "LMS_TRACE_DIR": str(blocker / "sub")})


def run_serve(monkeypatch, tracer_env=None):
    """Run `lms serve` with uvicorn faked; return the LMS_TRACER the server would have started with."""
    import lms

    seen = {}
    import uvicorn

    monkeypatch.setenv("LMS_TRACER", "placeholder")
    monkeypatch.delenv("LMS_TRACER")  # remembered, so the test leaves the variable as it found it
    if tracer_env is not None:
        monkeypatch.setenv("LMS_TRACER", tracer_env)
    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: seen.update(tracer=os.environ.get("LMS_TRACER")))
    monkeypatch.setattr(sys, "argv", ["lms", "serve"])
    lms.main()
    return seen["tracer"]


def test_lms_serve_defaults_tracer_to_local(monkeypatch):
    assert run_serve(monkeypatch) == "local"


def test_lms_serve_keeps_an_explicit_tracer_setting(monkeypatch):
    assert run_serve(monkeypatch, "noop") == "noop"


# --- 4. The attribute allow-list (R14, R15) ---


def test_non_allow_listed_key_is_dropped_and_counted():
    t = core()

    clean, dropped = t.sanitise_attributes({"mode": "Coach", "question": "hello", "answer": "world"})

    assert clean == {"mode": "Coach"} and dropped == 2


def test_dropped_attributes_are_counted_on_the_span_and_never_written(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with t.span("axis_question", interaction_id=ID, question="zebra-quartz-question", answer="zebra-quartz-answer"):
        pass

    (span,) = read_spans(tmp_path)
    assert span["attributes"]["dropped_attributes"] == 2
    assert "zebra-quartz" not in json.dumps(span)


GOOD_REF = {"passage_id": "ab12cd34ef56ab12", "source_id": "how-to/tmp_path", "score": 1.2345}


@pytest.mark.parametrize(
    "key, value",
    [
        ("unit_id", "x" * 10_000),
        ("mode", "x" * 81),
        ("mode", "two  spaces"),
        ("terms_total", -1),
        ("terms_total", True),
        ("downgraded", "yes"),
        ("index_version", "zz not hex"),
        ("interaction_id", "short"),
        ("input_tokens", 1.5),
        ("passage_refs", [dict(GOOD_REF, passage_id="not hex!")]),
        ("passage_refs", [dict(GOOD_REF, score=float("nan"))]),
        ("passage_refs", [dict(GOOD_REF, score=float("inf"))]),
        ("passage_refs", [dict(GOOD_REF, text="the passage text")]),
        ("passage_refs", [dict(GOOD_REF, source_id="has a space")]),
        ("passage_refs", [GOOD_REF] * 11),
        ("cited_passage_ids", ["ab12cd34ef56ab12"] * 11),
        ("cited_passage_ids", ["not hex!"]),
        ("duration_ms", -5),
    ],
)
def test_value_type_rules_are_enforced(key, value):
    t = core()

    clean, dropped = t.sanitise_attributes({key: value})

    assert clean == {} and dropped == 1


def test_valid_values_pass_unchanged():
    t = core()
    attrs = {
        "interaction_id": ID, "kind": "axis_question", "call": "consult", "mode": "Coach", "unit_id": "PY-0.1",
        "source_state": "grounded", "retrieval_mode": "keyword_only", "retrieval_status": "ok",
        "index_version": "ab12cd34ef56", "downgraded": False, "mock": True, "test_mode": False,
        "terms_matched": 3, "terms_total": 4, "passages_retrieved": 2, "passages_cited": 1,
        "input_tokens": 7, "output_tokens": 3, "latency_ms": 12, "profile_id": "local",
        "model_answered": "fake-model-1", "passage_refs": [GOOD_REF], "cited_passage_ids": ["ab12cd34ef56ab12"],
    }

    clean, dropped = t.sanitise_attributes(attrs)

    assert dropped == 0 and clean == {**attrs, "passage_refs": [dict(GOOD_REF, score=1.2345)]}


def test_the_allow_list_is_a_frozen_set_of_known_keys():
    t = core()

    assert isinstance(t.ALLOWED_ATTRIBUTES, frozenset)
    for forbidden in ("question", "answer", "code", "readme", "explanation", "text", "passage_text", "api_key", "url"):
        assert forbidden not in t.ALLOWED_ATTRIBUTES
    for needed in ("interaction_id", "passage_refs", "cited_passage_ids", "test_mode", "index_version", "mode"):
        assert needed in t.ALLOWED_ATTRIBUTES


def test_a_score_is_rounded_to_four_places():
    t = core()

    clean, _ = t.sanitise_attributes({"passage_refs": [dict(GOOD_REF, score=0.123456789)]})

    assert clean["passage_refs"][0]["score"] == 0.1235


def test_threads_never_share_a_parent(tmp_path):
    import threading

    t = core()
    t.set_tracer(local(tmp_path))

    def work(n):
        with t.span("axis_question", interaction_id=f"thread-{n:04d}-abcd"):
            with t.span("retrieve", terms_total=n):
                pass

    threads = [threading.Thread(target=work, args=(n,)) for n in range(30)]
    [th.start() for th in threads]
    [th.join() for th in threads]

    spans = read_spans(tmp_path)
    roots = {s["trace_id"]: s for s in spans if s["name"] == "axis_question"}
    assert len(roots) == 30
    for child in (s for s in spans if s["name"] == "retrieve"):
        assert roots[child["trace_id"]]["span_id"] == child["parent_id"]
        assert roots[child["trace_id"]]["attributes"]["interaction_id"] == f"thread-{child['attributes']['terms_total']:04d}-abcd"


def test_a_finished_request_leaves_no_ambient_parent_behind(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))

    with t.span("axis_question", interaction_id=ID):
        pass
    with t.span("retrieve"):
        pass

    after = next(s for s in read_spans(tmp_path) if s["name"] == "retrieve")
    assert after["parent_id"] is None


# --- 5. A stream read step by step (R10: closes at done, on error and when the reader leaves) ---


def pinned_stream(t, fail=False):
    def stream():
        with t.span("axis_question", interaction_id=ID):
            with t.span("model_call", call="stream"):
                yield "a"
                yield "b"
                if fail:
                    raise RuntimeError("model died secret-zebra")
            t.annotate(passages_cited=1)

    return t.pinned_context(stream())


def test_a_pinned_stream_keeps_its_parent_when_each_step_runs_in_a_fresh_context(tmp_path):
    import contextvars

    t = core()
    t.set_tracer(local(tmp_path))
    gen = pinned_stream(t)

    # a server may run each step in a copy of the caller's context; the pinned stream must not care
    steps = [contextvars.copy_context().run(next, gen) for _ in range(2)]
    assert steps == ["a", "b"]
    assert list(gen) == []

    spans = read_spans(tmp_path)
    root = next(s for s in spans if s["name"] == "axis_question")
    call = next(s for s in spans if s["name"] == "model_call")
    assert call["parent_id"] == root["span_id"] and call["trace_id"] == root["trace_id"]
    assert root["status"] == "ok" and call["status"] == "ok"


def test_a_pinned_stream_closes_its_spans_when_the_reader_leaves(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))
    gen = pinned_stream(t)
    assert next(gen) == "a"

    gen.close()  # the client disconnected mid-reply

    spans = {s["name"]: s for s in read_spans(tmp_path)}
    assert set(spans) == {"axis_question", "model_call"}  # both closed, none left open
    assert spans["axis_question"]["status"] == "ok"  # leaving is not an error
    with t.span("retrieve"):  # nothing is left open: the next span has no parent
        pass
    assert next(s for s in read_spans(tmp_path) if s["name"] == "retrieve")["parent_id"] is None


def test_a_pinned_stream_closes_its_spans_on_error_and_hides_the_message(tmp_path):
    t = core()
    t.set_tracer(local(tmp_path))
    gen = pinned_stream(t, fail=True)

    with pytest.raises(RuntimeError):
        list(gen)

    spans = {s["name"]: s for s in read_spans(tmp_path)}
    assert spans["model_call"]["status"] == "error" and spans["axis_question"]["status"] == "error"
    assert spans["model_call"]["attributes"]["error_class"] == "RuntimeError"
    assert "secret-zebra" not in json.dumps(list(spans.values()))
