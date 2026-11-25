"""Shared fakes and helpers for the SPEC-30 harness, report and CLI tests (ADR-0037 section 2.5 / SPEC-30 R9 to R15).

No model and no network. The "companion" is a scripted object that speaks the same few members the harness reads
from a real companion: `consult(query)`, `last_raw_reply`, `last_model_answered`, `retriever`.

The contract these helpers fix for the harness (see the phase 1 report, "Names chosen"):
  lms.adapters.ai.obedience.harness.EvalOptions(**fields)
  lms.adapters.ai.obedience.harness.run_eval(options, *, companion_factory, profiles, meter, environ) -> int
  companion_factory(*, profile, chat_temperature, retriever, meter, **ignored) -> companion
"""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from lms.adapters.ai.providers.profiles import parse_profiles
from lms.core.interfaces import AxisResponse
from obedience_corpus import EXACT, good_reply

SET_NAMES = ("alpha-docs", "beta-docs")
MADE_UP_ITEMS = [
    {"id": "m1", "q": "How do I use pytest.fixture_cache_reset to clear my fixtures between tests?",
     "set": "alpha-docs", "invented": "pytest.fixture_cache_reset"},
    {"id": "m2", "q": "What does uv.lockfile_freeze do to my project?", "set": "alpha-docs", "invented": "uv.lockfile_freeze"},
    {"id": "m3", "q": "How do I set httpx.Client.retry_all for every request?", "set": "beta-docs",
     "invented": "httpx.Client.retry_all"},
]
QUESTIONS_PER_SET = 3
TOTAL_QUESTIONS = QUESTIONS_PER_SET * len(SET_NAMES) + len(MADE_UP_ITEMS)  # 9
CASES_PER_QUESTION = 9  # 3 modes x 3 states
FAKE_PAID_KEY = "sk-FAKE-harness-key-0001"

PROFILES = parse_profiles({"profiles": [
    {"id": "local", "label": "Local", "kind": "openai_compatible", "base_url": "http://127.0.0.1:8888/v1",
     "model": "auto", "paid": False},
    {"id": "paid", "label": "Paid", "kind": "openai_compatible", "base_url": "https://api.example.test/v1",
     "model": "m-paid", "key_env": "PAID_API_KEY", "paid": True, "send_temperature": False,
     "price_per_million": {"input": 0.10, "output": 0.50}},
]})


# --- question files ---


def write_sets(root: Path, per_set: int = QUESTIONS_PER_SET) -> Path:
    folder = root / "sets"
    folder.mkdir(parents=True, exist_ok=True)
    for name in SET_NAMES:
        data = {
            "questions": [{"q": f"A plain synthetic question for {name}?", "kind": "plain", "expect": [f"{name}/x"]}],
            "out_of_scope": [
                {"q": f"Synthetic neighbouring question {i} for {name} about nothing real?", "kind": "neighbouring",
                 "why": "synthetic"} for i in range(per_set)
            ],
        }
        (folder / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return folder


def write_made_up(root: Path, items: Optional[List[Dict[str, str]]] = None) -> Path:
    path = root / "made-up-items.yaml"
    path.write_text(yaml.safe_dump({"questions": items or MADE_UP_ITEMS}, sort_keys=False), encoding="utf-8")
    return path


def set_version_of(folder: Path) -> str:
    """The same rule as scripts/measure_lib.set_version: sha256 over name + NUL + LF-normalised bytes."""
    digest = hashlib.sha256()
    for path in sorted(Path(folder).glob("*.yaml")):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def file_version_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- the scripted companion ---


@dataclass
class Call:
    n: int  # 1-based position of this call in the whole run
    question: str
    mode: str
    state: str
    chat_temperature: float


class ScriptedFactory:
    """A companion_factory. `script(call)` returns the raw reply text, None, or an exception to raise."""

    def __init__(self, script: Optional[Callable[[Call], Any]] = None):
        self.script = script or (lambda call: good_reply(call.mode, call.state))
        self.calls: List[Call] = []
        self.made: List[Dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> "ScriptedCompanion":
        self.made.append(kwargs)
        return ScriptedCompanion(self, kwargs)


class ScriptedCompanion:
    def __init__(self, factory: ScriptedFactory, kwargs: Dict[str, Any]):
        self.factory = factory
        self.chat_temperature = kwargs.get("chat_temperature")
        self.retriever = kwargs.get("retriever")
        self.last_raw_reply: Optional[str] = None  # never reset on a failure: a harness must not trust a stale value
        self.last_model_answered = "scripted-model-1"

    def consult(self, query: Any) -> AxisResponse:
        state = self.retriever.state
        call = Call(len(self.factory.calls) + 1, query.user_prompt, query.mode.value, state, self.chat_temperature)
        self.factory.calls.append(call)
        out = self.factory.script(call)
        if isinstance(out, BaseException):
            raise out
        self.last_raw_reply = out
        visible = re.sub(r"\s*\[\d+\]", "", out or "")
        return AxisResponse(reply=visible, source_state=state)


class BoomFactory:
    """A companion_factory that must never be used."""

    def __call__(self, **kwargs: Any) -> Any:
        raise AssertionError("no companion may be built in this run")


def confident_about_made_up(call: Call) -> str:
    """Good replies, except that the made-up questions get a confident explanation of the invented name."""
    for item in MADE_UP_ITEMS:
        if call.question == item["q"]:
            last = item["invented"].split(".")[-1]
            return f"{EXACT[call.state]} The {last} helper clears every cached value."
    return good_reply(call.mode, call.state)


# --- options and runs ---


def make_options(tmp_path: Path, **overrides: Any):
    from lms.adapters.ai.obedience.harness import EvalOptions

    fields = dict(sets_dir=tmp_path / "sets", made_up_path=tmp_path / "made-up-items.yaml",
                  out_dir=tmp_path / "out", run_name="run1")
    fields.update(overrides)
    return EvalOptions(**fields)


def prepare(tmp_path: Path) -> Path:
    write_sets(tmp_path)
    write_made_up(tmp_path)
    return tmp_path


def run(tmp_path: Path, factory: Any = None, *, environ: Optional[Dict[str, str]] = None, profiles: Any = None,
        meter: Any = None, **options: Any) -> int:
    from lms.adapters.ai.obedience.harness import run_eval

    prepare(tmp_path)
    if hasattr(environ, "touched"):  # a spy that records which names are read
        env = environ
    else:
        env = {"MOCK_AI": "false"}
        env.update(environ or {})
    return run_eval(make_options(tmp_path, **options), companion_factory=factory or ScriptedFactory(),
                    profiles=profiles or PROFILES, meter=meter, environ=env)


def run_dirs(tmp_path: Path) -> List[Path]:
    out = tmp_path / "out"
    return sorted(p for p in out.iterdir() if p.is_dir()) if out.exists() else []


def the_run_dir(tmp_path: Path) -> Path:
    (only,) = run_dirs(tmp_path)
    return only


def read_results(run_dir: Path) -> Dict[str, Any]:
    return json.loads((run_dir / "results.json").read_text(encoding="utf-8"))


def read_rows(run_dir: Path) -> List[Dict[str, Any]]:
    text = (run_dir / "replies.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def all_text(run_dir: Path) -> str:
    return "".join(p.read_text(encoding="utf-8") for p in sorted(run_dir.iterdir()) if p.is_file())


def make_row(qid: str, mode: str = "Hybrid", state: str = "not_found", raw: Optional[str] = "default", *,
             question: Optional[str] = None, invented: Optional[str] = None, visible: Optional[str] = "default",
             set_name: str = "alpha-docs", kind: Optional[str] = None, temperature: float = 0.0, repeat: int = 0,
             no_reply: bool = False, error_class: Optional[str] = None) -> Dict[str, Any]:
    """One replies.jsonl row (the keys are this test suite's contract for the file and for --replay)."""
    if raw == "default":
        raw = good_reply(mode, state)
    if visible == "default":
        visible = raw
    return {
        "id": qid, "set": set_name, "kind": kind or ("made_up" if invented else "out_of_scope"), "mode": mode,
        "state": state, "question": question or f"Synthetic question {qid} about nothing real?", "invented": invented,
        "raw_reply": raw, "visible_reply": visible, "no_reply": no_reply, "error_class": error_class,
        "temperature": temperature, "repeat": repeat,
    }


class SpyEnv(dict):
    """An environment that remembers which names were looked at."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.touched: List[str] = []

    def get(self, key: str, default: Any = None) -> Any:
        self.touched.append(key)
        return super().get(key, default)

    def __getitem__(self, key: str) -> Any:
        self.touched.append(key)
        return super().__getitem__(key)

    def __contains__(self, key: object) -> bool:
        self.touched.append(str(key))
        return super().__contains__(key)
