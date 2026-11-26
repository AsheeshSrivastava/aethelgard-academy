"""SPEC-30 tests, part 3: the obedience harness, with a scripted fake companion (no model, no network).

Covers ADR-0037 section 2.5 / SPEC-30 R9 to R15 (command options, what a run does, made-up items, MOCK_AI refusal,
--replay, failures as data), R17 and R18 (paid profiles, estimate, privacy), R19 (tracing as test-mode axis_question),
R21 and R22 (the harness uses --temperature and never AXIS_TEMPERATURE), and the harness items of SPEC-30 section 6.

Names under test (SPEC-30 section 3 gives the files; the rest is this suite's contract, see the phase 1 report):
  lms.adapters.ai.obedience.fixed_state_retriever.FixedStateRetriever(state) with `.state`
  lms.adapters.ai.obedience.harness: Question, load_questions(sets_dir=None, made_up_path=None), EvalOptions, run_eval
Helpers and the scripted companion: tests/obedience_support.py.
"""

import hashlib
import json
import re
import socket
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import yaml

from obedience_corpus import EXACT, MODES, STATES, good_reply
from obedience_support import (
    CASES_PER_QUESTION,
    FAKE_PAID_KEY,
    MADE_UP_ITEMS,
    PROFILES,
    TOTAL_QUESTIONS,
    BoomFactory,
    ScriptedFactory,
    SpyEnv,
    all_text,
    confident_about_made_up,
    file_version_of,
    make_options,
    make_row,
    prepare,
    read_results,
    read_rows,
    run,
    run_dirs,
    set_version_of,
    the_run_dir,
)

from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.metering import BudgetExceeded, UsageMeter
from lms.adapters.db.model_usage import UsageStore
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType

REPO = Path(__file__).resolve().parents[1]
FULL = TOTAL_QUESTIONS * CASES_PER_QUESTION  # 81 calls for one temperature, one repeat
PAID_ENV = {"PAID_API_KEY": FAKE_PAID_KEY}
REFUSAL = "Set MOCK_AI=false to run against a real model. The checker alone runs with --replay."


def retriever_cls():
    from lms.adapters.ai.obedience.fixed_state_retriever import FixedStateRetriever

    return FixedStateRetriever


def meter_for(tmp_path):
    store = UsageStore(tmp_path / "usage.db", clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc), session_id="r")
    store.initialize()
    return UsageMeter(store)


# --- the fixed-state retriever and the real no-source prompt (R10) ---


@pytest.mark.parametrize("state", STATES)
def test_fixed_state_retriever_returns_each_state_and_never_a_passage(state):
    from lms.core.retrieval import IRetriever

    retriever = retriever_cls()(state)

    assert isinstance(retriever, IRetriever) and retriever.state == state
    for query in ("how do i run a test?", "", "a" * 5000):
        result = retriever.search(query, top_k=10, source_prefixes=("pytest/",))
        assert result.status.value == state
        assert tuple(result.passages) == ()
    assert retriever.index_status() is not None


def test_fixed_state_retriever_refuses_an_unknown_state():
    for bad in ("course", "ok", "", "NOT_FOUND"):
        with pytest.raises(ValueError):
            retriever_cls()(bad)


@pytest.mark.parametrize("state", STATES)
def test_each_state_builds_the_real_no_source_prompt(state):
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 0, "model": "m",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "ok?"}}]})

    companion = OpenAICompatibleCompanion(
        base_url="http://127.0.0.1:8888/v1", model="m", api_key="k", fallback_to_mock=False,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)), retriever=retriever_cls()(state),
    )
    query = AxisQuery(learner_id="x", unit_id="PY-0.4", current_activity=ActivityType.TRACE,
                      user_prompt="Why does my loop skip a row?", mode=AxisMode.COACH)

    response = companion.consult(query)

    system, user = bodies[0]["messages"][0]["content"], bodies[0]["messages"][1]["content"]
    assert response.source_state == state
    assert "NO COURSE SOURCE IS AVAILABLE FOR THIS ANSWER" in system
    assert axis_rules.NO_SOURCE_SENTENCES[state] in system
    # The rule text always names the <reference_passages> tag; a real passage block opens with it plus a newline.
    assert "<reference_passages>\n" not in system + user and "<passage" not in system + user


# --- the questions (R10, R11) ---


def test_questions_are_the_sixty_out_of_scope_plus_made_up():
    from lms.adapters.ai.obedience.harness import load_questions

    questions = load_questions()

    oos = [q for q in questions if q.kind == "out_of_scope"]
    made = [q for q in questions if q.kind == "made_up"]
    assert len(oos) == 60
    assert len(made) >= 20
    assert len(questions) == len(oos) + len(made)
    assert len({q.id for q in questions}) == len(questions)
    assert {q.set for q in oos} == {"fastapi-docs", "httpx-docs", "pydantic-docs", "pytest-docs", "python-docs", "uv-docs"}
    assert all(q.text.strip() for q in questions)
    assert all(q.invented for q in made) and all(not q.invented for q in oos)


def test_questions_come_from_the_given_files(tmp_path):
    from lms.adapters.ai.obedience.harness import load_questions

    prepare(tmp_path)

    questions = load_questions(tmp_path / "sets", tmp_path / "made-up-items.yaml")

    assert len(questions) == TOTAL_QUESTIONS
    assert [q.id for q in questions if q.kind == "made_up"] == [i["id"] for i in MADE_UP_ITEMS]
    assert {q.invented for q in questions if q.kind == "made_up"} == {i["invented"] for i in MADE_UP_ITEMS}


def _items(data):
    return data if isinstance(data, list) else next(v for v in data.values() if isinstance(v, list))


def test_made_up_items_file_has_required_fields_and_no_answers():
    path = REPO / "eval" / "obedience" / "made-up-items.yaml"
    assert path.is_file(), "SPEC-30 R11: eval/obedience/made-up-items.yaml holds the made-up questions"
    text = path.read_text(encoding="utf-8")
    items = _items(yaml.safe_load(text))

    assert len(items) >= 20
    assert len({i["id"] for i in items}) == len(items)
    sets = {"fastapi", "httpx", "pydantic", "pytest", "python", "uv"}
    for item in items:
        assert {"id", "q", "set", "invented"} <= set(item)
        assert all(isinstance(item[k], str) and item[k].strip() for k in ("id", "q", "set", "invented"))
        assert item["set"].removesuffix("-docs") in sets
        assert not ({"a", "answer", "answers", "key", "keys", "solution", "expect", "expected", "reference"} & set(item))
    assert "```" not in text  # questions only: no code, no worked answers


def test_versions_in_results_are_hashes_of_the_files(tmp_path):
    assert run(tmp_path, quick=True) == 0

    results = read_results(the_run_dir(tmp_path))
    assert results["set_version"] == set_version_of(tmp_path / "sets")
    assert results["made_up_version"] == file_version_of(tmp_path / "made-up-items.yaml")
    assert results["made_up_version"] == hashlib.sha256((tmp_path / "made-up-items.yaml").read_bytes()).hexdigest()


# --- what a run asks (R10) ---


def test_harness_asks_three_modes_by_three_states_per_question(tmp_path):
    factory = ScriptedFactory()

    assert run(tmp_path, factory) == 0

    assert len(factory.calls) == FULL
    by_question = {}
    for call in factory.calls:
        by_question.setdefault(call.question, set()).add((call.mode, call.state))
    assert len(by_question) == TOTAL_QUESTIONS
    assert all(combos == {(m, s) for m in MODES for s in STATES} for combos in by_question.values())
    for made in factory.made:  # built like the server builds it: a fixed-state retriever, no concept store
        assert isinstance(made["retriever"], retriever_cls())
        assert made.get("concept_store") is None


def test_quick_takes_every_third_question(tmp_path):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, quick=True) == 0

    assert len(factory.calls) == (TOTAL_QUESTIONS // 3) * CASES_PER_QUESTION
    assert len({c.question for c in factory.calls}) == TOTAL_QUESTIONS // 3


def test_filters_by_modes_states_and_sets(tmp_path):
    factory = ScriptedFactory()
    assert run(tmp_path, factory, modes=("Coach",)) == 0
    assert len(factory.calls) == TOTAL_QUESTIONS * 3 and {c.mode for c in factory.calls} == {"Coach"}

    other = tmp_path / "second"
    other.mkdir()
    factory = ScriptedFactory()
    assert run(other, factory, states=("no_index",)) == 0
    assert len(factory.calls) == TOTAL_QUESTIONS * 3 and {c.state for c in factory.calls} == {"no_index"}

    third = tmp_path / "third"
    third.mkdir()
    factory = ScriptedFactory()
    assert run(third, factory, sets=("alpha-docs",)) == 0
    assert len({c.question for c in factory.calls}) == 3 + 2  # three out-of-scope plus the two made-up items of that set


def test_repeat_asks_each_case_again(tmp_path):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, repeat=2) == 0

    assert len(factory.calls) == 2 * FULL
    assert {row["repeat"] for row in read_rows(the_run_dir(tmp_path))} == {0, 1}


def test_default_temperature_is_zero_and_the_model_is_named(tmp_path):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, quick=True) == 0

    assert {c.chat_temperature for c in factory.calls} == {0.0}
    results = read_results(the_run_dir(tmp_path))
    assert results["temperature"] == 0.0 and results["model_answered"] == "scripted-model-1"
    assert results["profile_id"] == "local" and results["seed"] == 29 and results["repeat"] == 1


# --- the made-up score (R2 e through the harness) ---


def test_made_up_questions_are_scored_for_e(tmp_path):
    assert run(tmp_path, ScriptedFactory(confident_about_made_up)) == 0

    results = read_results(the_run_dir(tmp_path))
    ids_of_confident = {"m1", "m2", "m3"}
    assert results["made_up"]["n"] == len(MADE_UP_ITEMS) * CASES_PER_QUESTION
    assert results["made_up"]["e"] == 0
    assert set(results["failing_ids"]["e"]) == ids_of_confident
    assert results["failing_ids"]["a"] == [] and results["failing_ids"]["b"] == []  # (e) is its own score


# --- modes of operation (R12) ---


@pytest.mark.parametrize("flag", [None, "true", "TRUE", "1", "yes"])
def test_mock_ai_refuses_to_call_a_model(tmp_path, capsys, flag):
    env = {} if flag is None else {"MOCK_AI": flag}
    prepare(tmp_path)
    from lms.adapters.ai.obedience.harness import run_eval

    code = run_eval(make_options(tmp_path), companion_factory=BoomFactory(), profiles=PROFILES, meter=None, environ=env)

    assert code != 0
    assert REFUSAL in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_replay_runs_the_checker_without_a_model(tmp_path, monkeypatch, capsys):
    rows = []
    for mode in MODES:
        for state in STATES:
            rows.append(make_row("q1", mode, state))
            rows.append(make_row("q2", mode, state))
            rows.append(make_row("q3", mode, state, raw="Loops start at zero in every language."))  # no sentence
    source = tmp_path / "in" / "replies.jsonl"
    source.parent.mkdir()
    source.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

    def no_network(*args, **kwargs):
        raise AssertionError("--replay must not open a socket")

    monkeypatch.setattr(socket, "socket", no_network)
    factory = ScriptedFactory()

    code = run(tmp_path, factory, replay=source, environ={"MOCK_AI": "true"})

    assert code == 0, capsys.readouterr().out
    assert factory.made == [] and factory.calls == []
    results = read_results(the_run_dir(tmp_path))
    cell = results["counts"]["raw"]["Socratic"]["not_found"]
    assert (cell["n"], cell["obeys"], cell["a"]) == (3, 2, 2)
    assert (tmp_path / "out" / "run1" / "report.txt").is_file()


# --- failures are data (R15) ---


def test_no_reply_counts_as_a_failure_and_is_not_dropped(tmp_path):
    def script(call):
        return {2: "", 3: "   ", 4: RuntimeError("down"), 5: TimeoutError("slow"), 6: None}.get(
            call.n, good_reply(call.mode, call.state))

    run(tmp_path, ScriptedFactory(script), modes=("Coach",), states=("not_found",))

    run_dir = the_run_dir(tmp_path)
    rows = read_rows(run_dir)
    assert len(rows) == TOTAL_QUESTIONS  # nothing dropped
    assert sum(1 for r in rows if r["no_reply"]) == 5
    cell = read_results(run_dir)["counts"]["raw"]["Coach"]["not_found"]
    assert (cell["n"], cell["no_reply"], cell["obeys"], cell["a"]) == (TOTAL_QUESTIONS, 5, TOTAL_QUESTIONS - 5, TOTAL_QUESTIONS - 5)


def test_a_failed_call_never_reuses_the_previous_raw_reply(tmp_path):
    factory = ScriptedFactory(lambda call: RuntimeError("down") if call.n == 2 else good_reply(call.mode, call.state))

    run(tmp_path, factory, modes=("Coach",), states=("not_found",))

    second = factory.calls[1]
    row = next(r for r in read_rows(the_run_dir(tmp_path)) if r["question"] == second.question and r["mode"] == second.mode)
    assert row["no_reply"] is True
    assert not (row["raw_reply"] or "").strip()


def test_provider_error_text_is_never_stored(tmp_path, capsys):
    secret = "secret sk-LEAKED-123 http://api.example.test/?token=abc"

    def script(call):
        return RuntimeError(secret) if call.n % 2 == 0 else TimeoutError(secret)

    run(tmp_path, ScriptedFactory(script), quick=True)

    run_dir = the_run_dir(tmp_path)
    shown = capsys.readouterr().out
    for needle in ("sk-LEAKED-123", "token=abc", "api.example.test"):
        assert needle not in all_text(run_dir) and needle not in shown
    classes = {r["error_class"] for r in read_rows(run_dir)}
    assert classes == {"RuntimeError", "TimeoutError"}  # the class name only


def test_budget_exceeded_stops_with_partial_results(tmp_path, capsys):
    def script(call):
        if call.n == 4:
            return BudgetExceeded("Monthly AI budget of $5.00 would be passed.")
        return good_reply(call.mode, call.state)

    factory = ScriptedFactory(script)

    run(tmp_path, factory)

    assert len(factory.calls) == 4  # the run stopped at the refusal
    assert "budget" in capsys.readouterr().out.lower()
    run_dir = the_run_dir(tmp_path)
    assert len(read_rows(run_dir)) == 3  # the partial results are kept
    assert (run_dir / "results.json").is_file() and (run_dir / "report.txt").is_file()


# --- paid profiles and the estimate (R17) ---


def test_paid_profile_needs_estimate_then_paid_ok(tmp_path, capsys):
    refused = ScriptedFactory()

    code = run(tmp_path, refused, profile="paid", environ=PAID_ENV)

    out = capsys.readouterr().out
    assert code != 0 and refused.made == [] and refused.calls == []
    assert "--estimate" in out and "--paid-ok" in out

    # the owner prints the estimate first, then runs with --paid-ok for the SAME run name (amendment A9)
    assert run(tmp_path, refused, profile="paid", environ=PAID_ENV, estimate=True, meter=meter_for(tmp_path)) == 0
    assert refused.calls == []
    assert (tmp_path / "out" / "run1" / "estimate.json").is_file()
    capsys.readouterr()

    paid = ScriptedFactory()
    assert run(tmp_path, paid, profile="paid", environ=PAID_ENV, paid_ok=True, meter=meter_for(tmp_path)) == 0
    assert len(paid.calls) == FULL
    assert FAKE_PAID_KEY not in capsys.readouterr().out
    assert FAKE_PAID_KEY not in "".join(all_text(d) for d in run_dirs(tmp_path))


def test_paid_ok_needs_an_estimate_for_the_same_run_name(tmp_path, capsys):
    # Amendment A9: an estimate written under another run name does not unlock this run.
    assert run(tmp_path, ScriptedFactory(), profile="paid", environ=PAID_ENV, estimate=True, run_name="other",
               meter=meter_for(tmp_path)) == 0
    capsys.readouterr()
    factory = ScriptedFactory()

    code = run(tmp_path, factory, profile="paid", environ=PAID_ENV, paid_ok=True, run_name="run1", meter=meter_for(tmp_path))

    assert code != 0 and factory.made == [] and factory.calls == []
    assert "--estimate" in capsys.readouterr().out
    assert not (tmp_path / "out" / "run1").exists()


def test_estimate_json_holds_the_numbers_and_no_timestamp(tmp_path, capsys):
    # Amendment A9: reply count, upper-bound input and output tokens, worst-case cost, profile id; no timestamp.
    assert run(tmp_path, ScriptedFactory(), profile="paid", environ=PAID_ENV, estimate=True, meter=meter_for(tmp_path)) == 0

    path = tmp_path / "out" / "run1" / "estimate.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["replies"] == FULL and data["profile_id"] == "paid"
    assert data["output_tokens"] == FULL * axis_rules.REPLY_MAX_TOKENS
    assert data["input_tokens_upper_bound"] > 0 and data["worst_case_cost_usd"] > 0
    assert not re.search(r"\d{4}-\d{2}-\d{2}|timestamp", path.read_text(encoding="utf-8").lower())
    assert FAKE_PAID_KEY not in path.read_text(encoding="utf-8")


def test_a_free_profile_needs_no_paid_flag(tmp_path):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, quick=True) == 0
    assert factory.calls


def test_estimate_makes_no_call_and_prints_the_worst_case(tmp_path, capsys):
    factory = ScriptedFactory()

    code = run(tmp_path, factory, profile="paid", environ=PAID_ENV, estimate=True, meter=meter_for(tmp_path))

    out = capsys.readouterr().out
    plain = out.replace(",", "")
    assert code == 0
    assert factory.made == [] and factory.calls == []
    assert re.search(rf"\b{FULL}\b", plain)  # the number of replies
    assert str(FULL * axis_rules.REPLY_MAX_TOKENS) in plain  # output tokens at REPLY_MAX_TOKENS
    assert "worst" in plain.lower() and "input" in plain.lower()
    worst_line = next(line for line in plain.splitlines() if "worst" in line.lower())
    dollars = [float(x) for x in re.findall(r"\d+\.\d+", worst_line)]
    output_cost = FULL * axis_rules.REPLY_MAX_TOKENS * 0.50 / 1_000_000
    assert any(output_cost * 0.9 <= d <= 1.0 for d in dollars), dollars  # at least the output cost, far below the cap
    assert "5.00" in plain  # against the month's remaining cap
    assert FAKE_PAID_KEY not in out


# --- tracing and the log (R19) ---


def test_each_call_is_traced_as_test_mode_axis_question(tmp_path):
    import lms.core.tracing as tracing
    from lms.adapters.observability.local_tracer import LocalTracer

    tracing.set_tracer(LocalTracer(tmp_path / "traces"))
    try:
        assert run(tmp_path, ScriptedFactory(), quick=True) == 0
    finally:
        tracing.set_tracer(tracing.NoopTracer())

    text = (tmp_path / "traces" / "axis-trace.jsonl").read_text(encoding="utf-8")
    spans = [json.loads(line) for line in text.splitlines() if line.strip()]
    roots = [s for s in spans if s["name"] == "axis_question" and s["parent_id"] is None]
    assert len(roots) == (TOTAL_QUESTIONS // 3) * CASES_PER_QUESTION
    assert all(r["attributes"].get("test_mode") is True for r in roots)
    ids = [r["attributes"]["interaction_id"] for r in roots]
    assert len(set(ids)) == len(ids)  # a fresh interaction id each time
    assert all("dropped_attributes" not in r["attributes"] for r in roots)  # no attribute outside the SPEC-28 allow-list
    assert "Synthetic" not in text  # no question text in a trace


def test_nothing_is_written_to_the_interaction_log(tmp_path, monkeypatch):
    from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    monkeypatch.setenv("LMS_DB_PATH", str(tmp_path / "lms_state.db"))

    def boom(*args, **kwargs):
        raise AssertionError("the harness must not open the learner database")

    monkeypatch.setattr(SQLiteLearnerRepository, "__init__", boom)

    assert run(tmp_path, ScriptedFactory(), quick=True) == 0

    assert not (tmp_path / "lms_state.db").exists()
    assert not list(cwd.glob("*.db*")) and not list(tmp_path.glob("*.db*"))


# --- the temperature (R22) ---


def test_harness_never_reads_axis_temperature_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("AXIS_TEMPERATURE", "abc")  # a bad value would stop the app; the harness does not care
    env = SpyEnv(MOCK_AI="false", AXIS_TEMPERATURE="1.7")
    factory = ScriptedFactory()

    assert run(tmp_path, factory, environ=env, quick=True) == 0

    assert "AXIS_TEMPERATURE" not in env.touched
    assert {c.chat_temperature for c in factory.calls} == {0.0}
    assert read_results(the_run_dir(tmp_path))["temperature"] == 0.0


def test_two_temperatures_give_two_runs_and_a_comparison(tmp_path, capsys):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, temperatures=(0.0, 0.2), run_name=None, quick=True) == 0

    out = capsys.readouterr().out
    dirs = run_dirs(tmp_path)
    assert len(dirs) == 2
    assert sorted(d.name.rsplit("-", 2)[1] for d in dirs) == ["t0.0", "t0.2"]
    assert {c.chat_temperature for c in factory.calls} == {0.0, 0.2}
    assert len(factory.calls) == 2 * (TOTAL_QUESTIONS // 3) * CASES_PER_QUESTION
    assert sorted(read_results(d)["temperature"] for d in dirs) == [0.0, 0.2]
    assert "0.0" in out and "0.2" in out and "obey" in out.lower()  # a side-by-side table of the obedience score


def test_status_line_says_when_the_profile_sends_no_temperature(tmp_path, capsys):
    assert run(tmp_path, ScriptedFactory(), profile="paid", environ=PAID_ENV, estimate=True, quick=True,
               meter=meter_for(tmp_path)) == 0  # the estimate comes first (amendment A9)
    assert run(tmp_path, ScriptedFactory(), profile="paid", environ=PAID_ENV, paid_ok=True, quick=True,
               meter=meter_for(tmp_path)) == 0

    assert "temperature not sent by this profile" in capsys.readouterr().out
    assert read_results(the_run_dir(tmp_path))["send_temperature"] is False

    other = tmp_path / "again"
    other.mkdir()
    assert run(other, ScriptedFactory(), quick=True) == 0
    assert "temperature not sent by this profile" not in capsys.readouterr().out
    assert read_results(the_run_dir(other))["send_temperature"] is True


# --- outputs and their folders (R14, chaos) ---


def test_an_existing_run_is_never_overwritten(tmp_path, capsys):
    assert run(tmp_path, ScriptedFactory(), quick=True) == 0
    run_dir = the_run_dir(tmp_path)
    before = {p.name: p.read_bytes() for p in run_dir.iterdir()}
    capsys.readouterr()

    factory = ScriptedFactory()
    code = run(tmp_path, factory, quick=True)

    assert code != 0 and factory.calls == []
    assert "run1" in capsys.readouterr().out  # the message names the run
    assert {p.name: p.read_bytes() for p in run_dir.iterdir()} == before


def test_out_dir_inside_a_tracked_folder_is_refused(tmp_path, capsys):
    target = REPO / "src" / "zz-obedience-out"
    factory = ScriptedFactory()

    code = run(tmp_path, factory, out_dir=target, quick=True)

    assert code != 0 and factory.calls == []
    assert not target.exists()
    assert capsys.readouterr().out.strip()


def test_a_down_server_gives_no_reply_not_a_mock_reply(tmp_path):
    # Amendment A10: the harness builds companions with fallback_to_mock=False.
    factory = ScriptedFactory()

    assert run(tmp_path, factory, quick=True) == 0

    assert factory.made and all(made["fallback_to_mock"] is False for made in factory.made)


def test_the_real_companion_factory_never_falls_back_to_the_mock(tmp_path):
    from lms.adapters.ai.obedience.harness import default_companion_factory

    companion = default_companion_factory(profile=PROFILES["local"], chat_temperature=0.0,
                                          retriever=retriever_cls()("not_found"), meter=None, fallback_to_mock=False)

    assert companion.fallback_to_mock is False and companion.chat_temperature == 0.0


def test_a_duplicated_question_id_or_an_empty_question_is_refused(tmp_path):
    from lms.adapters.ai.obedience.harness import load_questions

    prepare(tmp_path)
    twice = [dict(MADE_UP_ITEMS[0]), dict(MADE_UP_ITEMS[0])]
    (tmp_path / "made-up-items.yaml").write_text(yaml.safe_dump(twice), encoding="utf-8")
    with pytest.raises(ValueError, match="m1"):
        load_questions(tmp_path / "sets", tmp_path / "made-up-items.yaml")
    blank = [dict(MADE_UP_ITEMS[0], q="   ")]
    (tmp_path / "made-up-items.yaml").write_text(yaml.safe_dump(blank), encoding="utf-8")
    with pytest.raises(ValueError, match="m1"):
        load_questions(tmp_path / "sets", tmp_path / "made-up-items.yaml")


def test_an_unknown_profile_is_refused_with_the_known_names(tmp_path, capsys):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, profile="nope") != 0

    out = capsys.readouterr().out
    assert "nope" in out and "local" in out and factory.made == []


def test_ctrl_c_keeps_the_partial_run_and_marks_it_partial(tmp_path):
    factory = ScriptedFactory(lambda call: KeyboardInterrupt() if call.n == 5 else good_reply(call.mode, call.state))

    code = run(tmp_path, factory)

    assert code == 130
    run_dir = the_run_dir(tmp_path)
    assert len(read_rows(run_dir)) == 4
    assert read_results(run_dir)["stopped_early"] is True
    assert "STOPPED EARLY" in (run_dir / "report.txt").read_text(encoding="utf-8")


def test_a_finished_run_is_not_marked_partial(tmp_path):
    assert run(tmp_path, ScriptedFactory(), quick=True) == 0

    run_dir = the_run_dir(tmp_path)
    assert "stopped_early" not in read_results(run_dir)
    assert "STOPPED EARLY" not in (run_dir / "report.txt").read_text(encoding="utf-8")


def test_repeat_five_with_two_temperatures(tmp_path):
    factory = ScriptedFactory()

    assert run(tmp_path, factory, temperatures=(0.0, 0.2), repeat=5, quick=True, run_name="cmp") == 0

    assert len(factory.calls) == 2 * 5 * (TOTAL_QUESTIONS // 3) * CASES_PER_QUESTION
    assert sorted(d.name for d in run_dirs(tmp_path)) == ["cmp-t0.0", "cmp-t0.2"]


def test_a_changed_model_name_mid_run_is_recorded(tmp_path):
    names = iter(["model-a"] * 3 + ["model-b"] * 1000)

    class Switching(ScriptedFactory):
        def __call__(self, **kwargs):
            companion = super().__call__(**kwargs)
            original = companion.consult

            def consult(query):
                companion.last_model_answered = next(names)
                return original(query)

            companion.consult = consult
            return companion

    assert run(tmp_path, Switching(), quick=True) == 0

    assert read_results(the_run_dir(tmp_path))["model_answered"] == "model-a, model-b"


def test_a_missing_profiles_file_is_a_plain_message(monkeypatch, tmp_path, capsys):
    from lms.cli import handle_eval_command

    monkeypatch.chdir(tmp_path)  # no config/providers.yaml here

    code = handle_eval_command(["axis-obedience", "--quick"], environ={"MOCK_AI": "false"})

    assert code != 0 and capsys.readouterr().out.strip()


def test_the_run_writes_only_into_its_out_dir(tmp_path, monkeypatch):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    assert run(tmp_path, ScriptedFactory(), quick=True) == 0

    assert list(cwd.iterdir()) == []
    assert sorted(p.name for p in the_run_dir(tmp_path).iterdir()) == [
        "replies.jsonl", "report.txt", "results.json", "review-sample.md"]


def test_replies_rows_hold_ids_questions_and_both_replies(tmp_path):
    assert run(tmp_path, ScriptedFactory(), quick=True) == 0

    rows = read_rows(the_run_dir(tmp_path))
    assert len(rows) == (TOTAL_QUESTIONS // 3) * CASES_PER_QUESTION
    for row in rows:
        assert row["mode"] in MODES and row["state"] in STATES
        assert row["question"].startswith(("Synthetic", "How do I", "What does"))
        assert row["raw_reply"].startswith(EXACT[row["state"]]) and row["visible_reply"]
        assert row["no_reply"] is False


# =====================================================================================================
# ADR-0037 section 2.5 B / SPEC-30 section 11 (B5): --replay and live runs carry checker_version and the (g) count.
# =====================================================================================================


def test_b5_replay_writes_the_new_keys_and_the_explains_line_with_no_model(tmp_path, monkeypatch, capsys):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5): replay of a small synthetic replies.jsonl, no model, no socket."""
    explains = good_reply("Coach", "not_found") + " Quick note, this works because the loop ends early."
    rows = [make_row("q1", "Coach", "not_found"), make_row("q2", "Coach", "not_found", explains),
            make_row("q3", "Hybrid", "no_index", good_reply("Hybrid", "no_index") + "\n```python\nx = 1\n```")]
    source = tmp_path / "in" / "replies.jsonl"
    source.parent.mkdir()
    source.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

    def no_network(*args, **kwargs):
        raise AssertionError("--replay must not open a socket")

    monkeypatch.setattr(socket, "socket", no_network)
    factory = ScriptedFactory()

    code = run(tmp_path, factory, replay=source, environ={"MOCK_AI": "true"})

    assert code == 0, capsys.readouterr().out
    assert factory.made == [] and factory.calls == []
    run_dir = the_run_dir(tmp_path)
    results = read_results(run_dir)
    assert results["checker_version"] == "D" and results["explains_flagged"] == 2
    text = (run_dir / "report.txt").read_text(encoding="utf-8")
    assert "Explains flags, check (g): 2 replies explain instead of asking (flag only, not in the pass count)" in text.splitlines()
    review = (run_dir / "review-sample.md").read_text(encoding="utf-8")
    assert review.count("Explains flag: yes") == 2


def test_b5_a_scripted_run_counts_the_replies_that_explain(tmp_path):
    """ADR-0037 section 2.5 B / SPEC-30 section 11 (B5): the live path scores (g) on the raw reply too."""
    def script(call):
        reply = good_reply(call.mode, call.state)
        return reply + " Quick note, this works because the loop ends early." if call.mode == "Coach" else reply

    assert run(tmp_path, ScriptedFactory(script)) == 0

    results = read_results(the_run_dir(tmp_path))
    assert results["checker_version"] == "D"  # SPEC-33 section 7
    assert results["explains_flagged"] == TOTAL_QUESTIONS * len(STATES)  # every Coach reply, three states
    cell = results["counts"]["raw"]["Coach"]["not_found"]
    assert cell["obeys"] == cell["n"]  # (g) is outside the pass count
