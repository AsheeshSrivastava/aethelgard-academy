"""The obedience harness: ask a real companion each question with no source, then score the raw reply (SPEC-30 R9 to R22).

Local and owner-run. It never reads AXIS_TEMPERATURE (R22), never opens the learner database or the interaction log,
and refuses to call a model while MOCK_AI is true (R12). `--replay` and `--estimate` call no model at all.

`run_eval` takes its companion factory, profiles, usage meter and environment as arguments, so the tests run it with a
scripted companion and no network.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

from lms.adapters.ai.obedience import report as report_module
from lms.adapters.ai.obedience.fixed_state_retriever import FixedStateRetriever
from lms.adapters.ai.providers import axis_rules
from lms.adapters.ai.providers.metering import MONTHLY_CAP_USD, BudgetExceeded
from lms.adapters.ai.providers.profiles import DEFAULT_PROFILE_ID, ProviderKind, ProviderProfile
from lms.core import tracing
from lms.core.axis_obedience import MODES, STATES
from lms.core.interfaces import AxisMode, AxisQuery
from lms.core.models import ActivityType

DEFAULT_SETS_DIR = Path("eval/gemini-sets")
DEFAULT_MADE_UP_PATH = Path("eval/obedience/made-up-items.yaml")
ERROR_ITEMS_FILE = "error-items.yaml"  # read from beside the made-up items file, when it is there (SPEC-31 9.3 E1)
DEFAULT_ERROR_ITEMS_PATH = DEFAULT_MADE_UP_PATH.parent / ERROR_ITEMS_FILE
ERROR_SET = "error-items"
DEFAULT_OUT_DIR = Path("eval-out/axis-obedience")
MOCK_REFUSAL = "Set MOCK_AI=false to run against a real model. The checker alone runs with --replay."
MAX_REPEAT = 5
CALL_TIMEOUT_SECONDS = 180.0  # a hung local model must not hang the whole run
PROGRESS_EVERY = 25

# The calls are fixed and neutral: the eval asks about the question only, with no code and no run output.
_UNIT_ID = "PY-0.1"
_ACTIVITY = ActivityType.TRACE


# --- questions ---


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    set: str  # a file stem of eval/gemini-sets, such as "pytest-docs"
    kind: str  # "out_of_scope", "made_up" or "error"
    invented: Optional[str] = None  # the invented identifier of a made-up item


def _bytes_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def set_version(sets_dir: Path) -> str:
    """The same rule as scripts/measure_lib.set_version: file names and LF-normalised bytes, in name order."""
    digest = hashlib.sha256()
    for path in sorted(Path(sets_dir).glob("*.yaml")):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def made_up_version(path: Path) -> str:
    """A hash of the made-up items file's bytes (R11)."""
    return _bytes_hash(Path(path).read_bytes())


def error_items_version(path: Path) -> str:
    """A hash of the error items file's bytes, or "" when there is no such file."""
    return _bytes_hash(Path(path).read_bytes()) if Path(path).is_file() else ""


def _made_up_items(data: Any) -> List[Mapping[str, Any]]:
    """The file is a YAML list; a mapping that holds one list (the test helper's shape) is accepted too."""
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    if not isinstance(data, list):
        raise ValueError("The made-up items file must be a YAML list.")
    return data


def load_questions(sets_dir: Optional[Path] = None, made_up_path: Optional[Path] = None) -> List[Question]:
    """The out-of-scope questions of every set (file order), then the made-up items (R10, R11). Ids must be unique."""
    sets_dir = Path(sets_dir) if sets_dir is not None else DEFAULT_SETS_DIR
    made_up_path = Path(made_up_path) if made_up_path is not None else DEFAULT_MADE_UP_PATH
    questions: List[Question] = []
    for path in sorted(sets_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for index, item in enumerate(data.get("out_of_scope") or []):
            questions.append(Question(f"{path.stem}-oos-{index + 1:02d}", str(item.get("q", "")), path.stem, "out_of_scope"))
    items = _made_up_items(yaml.safe_load(made_up_path.read_text(encoding="utf-8")))
    for item in items:
        questions.append(Question(str(item["id"]), str(item.get("q", "")), str(item["set"]), "made_up", str(item["invented"])))
    _check_questions(questions)
    return questions


def load_error_items(path: Optional[Path] = None) -> List[Question]:
    """The made-up error-message questions: a YAML list of {id, q} (SPEC-31 9.3 E1)."""
    path = Path(path) if path is not None else DEFAULT_ERROR_ITEMS_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) and "id" in item for item in data):
        raise ValueError("The error items file must be a YAML list of {id, q}.")
    questions = [Question(str(item["id"]), str(item.get("q", "")), ERROR_SET, "error") for item in data]
    _check_questions(questions)
    return questions


def _check_questions(questions: Sequence[Question]) -> None:
    """No empty question, and every id once."""
    seen = set()
    for q in questions:
        if not q.text.strip():
            raise ValueError(f"Question '{q.id}' is empty.")
        if q.id in seen:
            raise ValueError(f"The question id '{q.id}' appears twice.")
        seen.add(q.id)


def select_questions(questions: Sequence[Question], sets: Sequence[str], quick: bool) -> List[Question]:
    """Filter by set, then --quick: every third question in file order, starting at the first (A, minor decisions)."""
    chosen = [q for q in questions if not sets or q.set in sets]
    return chosen[::3] if quick else chosen


# --- options ---


@dataclass
class EvalOptions:
    profile: Optional[str] = None
    temperatures: Tuple[float, ...] = (0.0,)  # the harness's own setting; AXIS_TEMPERATURE is never read (R22)
    modes: Tuple[str, ...] = MODES
    states: Tuple[str, ...] = STATES
    sets: Tuple[str, ...] = ()  # empty means every set
    quick: bool = False
    repeat: int = 1
    seed: int = 29
    run_name: Optional[str] = None
    out_dir: Path = DEFAULT_OUT_DIR
    estimate: bool = False
    paid_ok: bool = False
    replay: Optional[Path] = None
    sets_dir: Optional[Path] = None
    made_up_path: Optional[Path] = None


CompanionFactory = Callable[..., Any]


def default_companion_factory(*, profile: ProviderProfile, chat_temperature: float, retriever: Any, meter: Any,
                              api_key: Optional[str] = None, fallback_to_mock: bool = False,
                              concept_store: Any = None, **_ignored: Any) -> Any:
    """Build the real companion the way the server does, with a fixed-state retriever and no mock fallback (A10).

    A server that is down then gives no reply (recorded as `no_reply`), never a mock reply scored as a model's.
    """
    if profile.kind is ProviderKind.GEMINI:
        from lms.adapters.ai.gemini_companion import GeminiCompanion

        return GeminiCompanion(model=profile.model, api_key=api_key, concept_store=concept_store, retriever=retriever,
                               profile=profile, meter=meter, chat_temperature=chat_temperature)
    from lms.adapters.ai.local_llm_companion import OpenAICompatibleCompanion

    return OpenAICompatibleCompanion(
        base_url=profile.base_url, model=profile.model, api_key=api_key, concept_store=concept_store,
        retriever=retriever, fallback_to_mock=fallback_to_mock, profile=profile, meter=meter,
        token_limit_field=profile.token_limit_field, send_temperature=profile.send_temperature,
        disable_thinking=profile.disable_thinking, chat_temperature=chat_temperature, timeout_seconds=CALL_TIMEOUT_SECONDS,
    )


# --- small helpers ---


def _mock_on(environ: Mapping[str, str]) -> bool:
    return (environ.get("MOCK_AI") or "true").strip().lower() in ("1", "true", "yes")


def _run_names(options: EvalOptions, set_v: str, made_v: str) -> List[Tuple[float, str]]:
    names = []
    for t in options.temperatures:
        if options.run_name:
            name = options.run_name if len(options.temperatures) == 1 else f"{options.run_name}-t{t}"
        else:
            name = report_module.default_run_name(set_v, made_v, t, options.seed)
        names.append((t, name))
    return names


def _cases(questions: Sequence[Question], options: EvalOptions) -> List[Tuple[int, Question, str, str]]:
    return [(r, q, m, s) for r in range(options.repeat) for q in questions for m in options.modes for s in options.states]


def _query(question: Question, mode: str) -> AxisQuery:
    return AxisQuery(learner_id="eval", unit_id=_UNIT_ID, current_activity=_ACTIVITY, user_prompt=question.text,
                     mode=AxisMode(mode))


def _row(q: Question, mode: str, state: str, temperature: float, repeat: int, raw: Optional[str], visible: Optional[str],
         no_reply: bool, error_class: Optional[str]) -> Dict[str, Any]:
    return {"id": q.id, "set": q.set, "kind": q.kind, "mode": mode, "state": state, "question": q.text,
            "invented": q.invented, "raw_reply": raw, "visible_reply": visible, "no_reply": no_reply,
            "error_class": error_class, "temperature": temperature, "repeat": repeat}


# --- one call ---


def ask(companion: Any, q: Question, mode: str, state: str, temperature: float, repeat: int) -> Tuple[Dict[str, Any], Optional[str]]:
    """One consult inside a test-mode `axis_question` span (R19). Returns (row, model that answered).

    A call that raises, or answers nothing, is a row with no_reply=True (R15). BudgetExceeded is not caught here.
    """
    if hasattr(companion, "last_raw_reply"):
        companion.last_raw_reply = None  # never score a reply left over from the call before
    with tracing.span("axis_question", interaction_id=uuid.uuid4().hex, kind="axis_question", mode=mode,
                      test_mode=True) as root:
        try:
            response = companion.consult(_query(q, mode))
        except BudgetExceeded:
            root.fail("budget")
            raise
        except Exception as exc:
            root.fail("provider_error")
            # The class name only: a provider's own message can echo a key or an address (R15).
            return _row(q, mode, state, temperature, repeat, None, None, True, type(exc).__name__), None
    raw = getattr(companion, "last_raw_reply", None)
    answered = getattr(companion, "last_model_answered", None)
    if raw is None or not str(raw).strip():
        return _row(q, mode, state, temperature, repeat, raw, getattr(response, "reply", None), True, "EmptyReply"), answered
    return _row(q, mode, state, temperature, repeat, raw, response.reply, False, None), answered


# --- the estimate (R17, A9) ---


def _estimate_numbers(profile: ProviderProfile, meter: Any, questions: Sequence[Question], options: EvalOptions) -> Dict[str, Any]:
    """Upper bounds for one run. Input tokens are bounded by input characters (a token is at least one character)."""
    chars = 0
    cases = _cases(questions, options)
    for _repeat, q, mode, state in cases:
        grounding, _trace = axis_rules.ground_with_trace(FixedStateRetriever(state), None, _UNIT_ID, q.text)
        system, user = axis_rules.build_prompts(_query(q, mode), grounding)
        chars += len(system) + len(user)
    worst = sum(
        (meter.worst_case_cost(profile, 0) if meter is not None else profile.cost_usd(0, profile.max_output_tokens))
        for _ in cases
    )
    input_cost = profile.cost_usd(chars, 0)
    return {"replies": len(cases), "input_tokens_upper_bound": chars,
            "output_tokens": len(cases) * axis_rules.REPLY_MAX_TOKENS,
            "worst_case_cost_usd": round(worst + input_cost, 6), "profile_id": profile.id}


def _month_state(meter: Any) -> Tuple[float, float]:
    """(cap, spent this month)."""
    if meter is None:
        return MONTHLY_CAP_USD, 0.0
    return float(meter.cap_usd), float(meter.store.month_spend())


def _do_estimate(options: EvalOptions, profile: ProviderProfile, meter: Any, questions: Sequence[Question],
                 names: Sequence[Tuple[float, str]]) -> int:
    """Print the worst case and write estimate.json into each run folder. Makes no call."""
    cap, spent = _month_state(meter)
    total = 0
    for _temperature, name in names:
        numbers = _estimate_numbers(profile, meter, questions, options)
        folder = Path(options.out_dir) / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "estimate.json").write_bytes((json.dumps(numbers, sort_keys=True, indent=2) + "\n").encode("utf-8"))
        total += numbers["replies"]
    print(f"Estimate for profile {profile.id} ({'paid' if profile.paid else 'free'}): {total:,} replies, no call made.")
    print(f"Input tokens, upper bound (one token per character): {numbers['input_tokens_upper_bound'] * len(names):,}")
    print(f"Output tokens at REPLY_MAX_TOKENS ({axis_rules.REPLY_MAX_TOKENS} each): {total * axis_rules.REPLY_MAX_TOKENS:,}")
    print(f"Worst-case cost: ${numbers['worst_case_cost_usd'] * len(names):.4f}")
    print(f"Monthly cap ${cap:.2f}; spent so far ${spent:.2f}; remaining ${max(0.0, cap - spent):.2f}.")
    print("To run it: repeat the command with --paid-ok (same --run-name) and MOCK_AI=false.")
    return 0


# --- replay ---


def _read_rows(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(f"Line {number} of {path} is not valid JSON.") from None
        if not isinstance(row, dict) or not {"id", "mode", "state"} <= set(row) or row["mode"] not in MODES or row["state"] not in STATES:
            raise ValueError(f"Line {number} of {path} is not a replies.jsonl row.")
        rows.append(row)
    return rows


def _made_up_path(options: EvalOptions) -> Path:
    return Path(options.made_up_path) if options.made_up_path is not None else DEFAULT_MADE_UP_PATH


def _error_items_path(options: EvalOptions) -> Path:
    return _made_up_path(options).parent / ERROR_ITEMS_FILE


def _versions(options: EvalOptions) -> Tuple[str, str]:
    sets_dir = Path(options.sets_dir) if options.sets_dir is not None else DEFAULT_SETS_DIR
    made_up = _made_up_path(options)
    return (set_version(sets_dir) if sets_dir.is_dir() else "", made_up_version(made_up) if made_up.is_file() else "")


def _replay(options: EvalOptions) -> int:
    rows = _read_rows(Path(options.replay))
    set_v, made_v = _versions(options)
    temperature = float(rows[0].get("temperature", options.temperatures[0])) if rows else options.temperatures[0]
    name = options.run_name or report_module.default_run_name(set_v, made_v, temperature, options.seed)
    meta = {"set_version": set_v, "made_up_version": made_v, "profile_id": "replay", "model_answered": None,
            "error_items_version": error_items_version(_error_items_path(options)),
            "temperature": temperature, "send_temperature": None, "seed": options.seed, "repeat": options.repeat}
    folder = report_module.write_run(Path(options.out_dir), name, rows, meta)
    print(f"Replayed {len(rows)} replies with the checker only; no model was called.")
    print((folder / "report.txt").read_text(encoding="utf-8"))
    print(f"Written to {folder}")
    return 0


# --- the run ---


def _comparison(finished: Sequence[Tuple[float, Dict[str, Any]]]) -> List[str]:
    lines = ["", "Obedience by temperature (raw reply, all modes and states):"]
    for temperature, results in finished:
        obeys, n = report_module.total_obeys(results["counts"]["raw"])
        lines.append(f"  temperature {temperature}: {obeys} of {n} obey ({report_module.percent(obeys, n)})")
    return lines


def _one_temperature(options: EvalOptions, profile: ProviderProfile, key: Optional[str], factory: CompanionFactory,
                     meter: Any, questions: Sequence[Question], temperature: float, name: str, meta_base: Dict[str, Any]
                     ) -> Tuple[int, Dict[str, Any]]:
    companions = {
        state: factory(profile=profile, chat_temperature=temperature, retriever=FixedStateRetriever(state), meter=meter,
                       api_key=key, fallback_to_mock=False, concept_store=None)
        for state in options.states
    }
    cases = _cases(questions, options)
    rows: List[Dict[str, Any]] = []
    models: List[str] = []
    stopped, code = False, 0
    try:
        for index, (repeat, q, mode, state) in enumerate(cases, 1):
            row, answered = ask(companions[state], q, mode, state, temperature, repeat)
            rows.append(row)
            if answered and answered not in models:
                models.append(answered)
            if index % PROGRESS_EVERY == 0:
                print(f"  {index} of {len(cases)} replies asked")
    except BudgetExceeded:
        print("Stopped: the monthly AI budget would be passed. The partial results are kept.")
        stopped, code = True, 1
    except KeyboardInterrupt:
        print("Stopped with Ctrl-C. The partial results are kept and marked as partial.")
        stopped, code = True, 130
    meta = dict(meta_base, temperature=temperature, model_answered=", ".join(sorted(models)) or None)
    meta["prompt_versions"] = {  # the modes and states that ran, whether or not a reply came (SPEC-31 R13)
        f"{row['mode']}/{row['state']}": axis_rules.chat_prompt_version(AxisMode(row["mode"]), row["state"])
        for row in rows
    }
    if stopped:
        meta["stopped_early"] = True
    folder = report_module.write_run(Path(options.out_dir), name, rows, meta)
    results = json.loads((folder / "results.json").read_text(encoding="utf-8"))
    print(f"Run {name} (temperature {temperature}): written to {folder}")
    print((folder / "report.txt").read_text(encoding="utf-8"))
    return code, results


def _check_paid_gate(options: EvalOptions, profile: ProviderProfile, meter: Any, names: Sequence[Tuple[float, str]]) -> bool:
    """A paid profile needs --paid-ok after an --estimate for the same run name (R17, A9)."""
    if not profile.paid:
        return True
    if not options.paid_ok:
        print(f"Profile {profile.id} is paid. Run with --estimate first, then repeat the command with --paid-ok. "
              "The owner runs paid steps.")
        return False
    missing = [name for _t, name in names if not (Path(options.out_dir) / name / "estimate.json").is_file()]
    if missing:
        print(f"No estimate was written for the run '{missing[0]}'. Run --estimate with the same --run-name first, "
              "then repeat the command with --paid-ok.")
        return False
    if meter is None:
        print("A paid run needs the usage meter that enforces the monthly cap.")
        return False
    return True


def run_eval(options: EvalOptions, *, companion_factory: CompanionFactory, profiles: Mapping[str, ProviderProfile],
             meter: Any, environ: Mapping[str, str]) -> int:
    """Run the eval. Returns 0 for a finished run, non-zero for a refusal, a bad input or a stop early."""
    try:
        return _run(options, companion_factory, profiles, meter, environ)
    except report_module.RunExists as exc:
        print(str(exc))
        return 2
    except (ValueError, OSError, yaml.YAMLError) as exc:
        # The text of OS and YAML errors can hold a path but never a reply or a key; a ValueError is ours and plain.
        print(str(exc) if isinstance(exc, ValueError) else f"Could not run the eval ({type(exc).__name__}).")
        return 2


def _run(options: EvalOptions, factory: CompanionFactory, profiles: Mapping[str, ProviderProfile], meter: Any,
         environ: Mapping[str, str]) -> int:
    if options.repeat < 1 or options.repeat > MAX_REPEAT:
        raise ValueError(f"--repeat must be from 1 to {MAX_REPEAT}.")
    problem = report_module.out_dir_problem(Path(options.out_dir))
    if problem:
        print(problem)
        return 2
    if options.replay:
        return _replay(options)
    if not options.estimate and _mock_on(environ):  # refuse before anything else: no model, no files (R12)
        print(MOCK_REFUSAL)
        return 2

    profile_id = options.profile or (DEFAULT_PROFILE_ID if DEFAULT_PROFILE_ID in profiles else next(iter(profiles)))
    profile = profiles.get(profile_id)
    if profile is None:
        raise ValueError(f"Unknown profile '{profile_id}'. Known profiles: {', '.join(sorted(profiles))}.")
    sets_dir = Path(options.sets_dir) if options.sets_dir is not None else DEFAULT_SETS_DIR
    made_up_path = _made_up_path(options)
    errors_path = _error_items_path(options)
    main = load_questions(sets_dir, made_up_path)
    errors = load_error_items(errors_path) if errors_path.is_file() else []
    _check_questions([*main, *errors])
    # Selected apart, so adding error items never changes which of the others --quick takes.
    questions = [q for part in (main, errors) for q in select_questions(part, options.sets, options.quick)]
    if not questions:
        raise ValueError("No question matches the --sets filter.")
    set_v, made_v = set_version(sets_dir), made_up_version(made_up_path)
    names = _run_names(options, set_v, made_v)

    if options.estimate:  # no call, so MOCK_AI does not matter
        return _do_estimate(options, profile, meter, questions, names)
    key = profile.api_key(environ)
    if profile.key_env and key is None:
        raise ValueError(f"{profile.key_env} is not set. Put it in .env; it is never printed.")
    if not _check_paid_gate(options, profile, meter, names):
        return 2
    for _t, name in names:  # refuse before any call: an old run is never mixed with a new one
        if report_module.run_folder_has_results(Path(options.out_dir) / name):
            print(f"The run '{name}' already exists in {options.out_dir}. Choose another --run-name.")
            return 2

    plan = len(_cases(questions, options)) * len(names)
    print(f"Profile {profile.id}, model {profile.model}: {plan} replies in {len(names)} run(s).")
    if not profile.send_temperature:
        print("temperature not sent by this profile: the server's own default is used, so runs at different "
              "temperatures will not differ.")
    meta_base = {"set_version": set_v, "made_up_version": made_v, "profile_id": profile.id,
                 "error_items_version": error_items_version(errors_path),
                 "send_temperature": profile.send_temperature, "seed": options.seed, "repeat": options.repeat}
    finished: List[Tuple[float, Dict[str, Any]]] = []
    exit_code = 0
    for temperature, name in names:
        code, results = _one_temperature(options, profile, key, factory, meter, questions, temperature, name, meta_base)
        finished.append((temperature, results))
        exit_code = exit_code or code
        if code:
            break  # a budget refusal or Ctrl-C stops the whole command
    if len(finished) > 1:
        print("\n".join(_comparison(finished)))
    return exit_code
