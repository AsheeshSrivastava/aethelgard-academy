"""Exercise seeds, their variants, and the learner-safe Exercise view.

Governed by:
- SPEC-13 (Exercise Seed Format)
- SPEC-12 section 4 (Exercises, Regenerate and Reset)
- ADR-0017 (variants)

Deterministic and pure: no LLM, no I/O. An Exercise is built from models listing
only the fields a learner may see, so a hidden field can never leak by default.
"""

from datetime import datetime, timezone
import hashlib
from itertools import islice, zip_longest
import re
from typing import Any, Collection, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from pydantic import BaseModel, ValidationError

from lms.core.models import ActivityType, EvidenceEntry, EvidenceStrength, ProficiencyLevel, Unit
from lms.core.proficiency import concept_check_id, is_concept_check

SCHEMA_VERSION = 2
COLD_CHECK = "cold_check"
COLD_ITEMS_MIN = 3
COLD_ITEMS_MAX = 5
MAX_CONCEPT_PROMPTS = 3  # ADR-0032: `prompt` is v1, `more_prompts` are v2 and v3
MAX_HINT_CHARS = 300
_SLOT = re.compile(r"\{\{(\w+)\}\}")


class SeedError(ValueError):
    """A seed file breaks SPEC-13; the message says how."""


# --- Learner-safe blocks: only what SPEC-12 section 4 allows ---


class Choice(BaseModel):
    key: str
    text: str


class Task(BaseModel):
    id: str
    label: str


class PlanStep(BaseModel):
    id: str
    text: str


class ContractField(BaseModel):
    id: str
    label: str
    kind: str
    options: List[Choice]


class Structure(BaseModel):
    min_helpers: int
    max_lines_per_function: int


class PredictBlock(BaseModel):
    code: List[str]
    stdin: str
    options: List[Choice]


class StateRow(BaseModel):
    line: int
    names: List[str]


class TraceBlock(BaseModel):
    code: List[str]
    input: str
    state_rows: Optional[List[StateRow]] = None  # Practice items with line_states only (ADR-0031)


class PlaygroundBlock(BaseModel):
    starter: List[str]
    tasks: List[Task] = []
    make: bool = False                 # The unit's Make step (Amendment A1.3, SPEC-13)


class DebugBlock(BaseModel):
    broken_code: List[str]
    stdin: str = ""


class DebugLocateBlock(BaseModel):
    broken_code: List[str]
    stdin: str
    error_types: List[Choice]


class ChoiceBlock(BaseModel):
    material: List[str] = []
    options: List[Choice]


class SpecifyByTestsBlock(BaseModel):
    function_name: str
    signature: str
    starter_tests: List[str]


class SpecifyContractBlock(BaseModel):
    material: List[str] = []
    fields: List[ContractField]


class DecomposePlanBlock(BaseModel):
    material: List[str] = []
    steps: List[PlanStep]


class DecomposeCodeBlock(BaseModel):
    entry_function: str
    starter: List[str]
    structure: Structure


class ExplainSpotFlawBlock(BaseModel):
    sentences: List[Choice]


class ExplainModelChoiceBlock(BaseModel):
    material: List[str] = []
    options: List[Choice]


class Exercise(BaseModel):
    exercise_id: str
    unit_id: str
    activity: str                      # A slug
    origin: str = "authored"
    variant_no: int = 1
    item_type: str
    prompt_markdown: str
    predict: Optional[PredictBlock] = None
    trace: Optional[TraceBlock] = None
    playground: Optional[PlaygroundBlock] = None
    debug: Optional[DebugBlock] = None
    debug_locate: Optional[DebugLocateBlock] = None
    choice: Optional[ChoiceBlock] = None
    specify_by_tests: Optional[SpecifyByTestsBlock] = None
    specify_contract: Optional[SpecifyContractBlock] = None
    decompose_plan: Optional[DecomposePlanBlock] = None
    decompose_code: Optional[DecomposeCodeBlock] = None
    explain_spot_flaw: Optional[ExplainSpotFlawBlock] = None
    explain_model_choice: Optional[ExplainModelChoiceBlock] = None


BLOCKS: Dict[str, type] = {
    "predict": PredictBlock,
    "trace": TraceBlock,
    "playground": PlaygroundBlock,
    "debug": DebugBlock,
    "debug_locate": DebugLocateBlock,
    "choice": ChoiceBlock,
    "specify_by_tests": SpecifyByTestsBlock,
    "specify_contract": SpecifyContractBlock,
    "decompose_plan": DecomposePlanBlock,
    "decompose_code": DecomposeCodeBlock,
    "explain_spot_flaw": ExplainSpotFlawBlock,
    "explain_model_choice": ExplainModelChoiceBlock,
}

# Fields a seed must have that learners never see (SPEC-13 section 4).
HIDDEN_REQUIRED: Dict[str, Tuple[str, ...]] = {
    "predict": ("answer_key", "why"),
    "trace": ("expected_output",),
    "playground": ("reference_solution", "hidden_checks", "wrong_solution"),
    "debug": ("reference_solution", "hidden_checks", "wrong_solution"),
    "debug_locate": ("answer_key", "why"),
    "choice": ("answer_key", "why"),
    "specify_by_tests": ("reference", "mutants", "sample_tests"),
    "specify_contract": ("answer_key", "why"),
    "decompose_plan": ("needed", "order_constraints"),
    "decompose_code": ("reference_solution", "hidden_checks", "wrong_solution"),
    "explain_spot_flaw": ("answer_key", "why"),
    "explain_model_choice": ("answer_key", "why"),
}

# Hidden fields live in the private answers folder, never in the public seed file (ADR-0021 amendment).
PRIVATE_FIELDS = {field for fields in HIDDEN_REQUIRED.values() for field in fields} | {"line_states", "why"}


def public_and_private(raw: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Split one full seed into its public file and its private half (SPEC-13)."""
    item_type = next(name for name in BLOCKS if isinstance(raw.get(name), dict))
    block = raw[item_type]
    public = {**raw, item_type: {k: v for k, v in block.items() if k not in PRIVATE_FIELDS}}
    private = {"seed_id": raw["seed_id"], item_type: {k: v for k, v in block.items() if k in PRIVATE_FIELDS}}
    return public, private


ALLOWED_ITEM_TYPES: Dict[ActivityType, Tuple[str, ...]] = {
    ActivityType.PREDICT: ("predict",),
    ActivityType.TRACE: ("trace",),
    ActivityType.MODIFY: ("playground",),
    ActivityType.BUILD: ("playground",),
    ActivityType.DEBUG_VALIDATE: ("debug", "debug_locate"),
    ActivityType.EVALUATE: ("choice",),
    ActivityType.DIRECT: ("choice",),
    ActivityType.SPECIFY: ("specify_by_tests", "specify_contract"),
    ActivityType.DECOMPOSE: ("decompose_plan", "decompose_code"),
    ActivityType.EXPLAIN: ("explain_spot_flaw", "explain_model_choice"),
}


class CurrentExercise(BaseModel):
    """The learner's pointer for one activity of a unit."""

    exercise_id: str
    served_at: datetime


class ExerciseSeed(BaseModel):
    """A parsed seed. It holds hidden fields, so it must never be returned to a learner."""

    seed_id: str
    unit_id: str
    activity: ActivityType
    skill_id: str
    level: ProficiencyLevel
    prompt_markdown: List[str]
    cold_check_eligible: bool
    curator_approved: bool
    item_type: str
    body: Dict[str, Any]
    template: Optional[Dict[str, Any]] = None
    hint: Optional[str] = None         # Shown after a failed Cold Check item, once approved (ADR-0022)
    hint_approved: bool = False
    topic: Optional[str] = None        # One topic of the unit's roadmap Topics line (Amendment A1.4)


def _options_of(item_type: str, body: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
    return body.get("sentences") if item_type == "explain_spot_flaw" else body.get("options")


def _check_answer_key(item_type: str, body: Dict[str, Any]) -> None:
    key = body.get("answer_key")
    if item_type in ("predict", "choice", "explain_spot_flaw", "explain_model_choice"):
        if key not in [o["key"] for o in _options_of(item_type, body)]:
            raise SeedError(f"answer_key '{key}' is not one of the options.")
    elif item_type == "debug_locate":
        if key.get("error_type") not in [o["key"] for o in body["error_types"]]:
            raise SeedError(f"answer_key error_type '{key.get('error_type')}' is not listed.")
        if not 1 <= key.get("line", 0) <= len(body["broken_code"]):
            raise SeedError(f"answer_key line {key.get('line')} is not in the code.")
    elif item_type == "specify_contract":
        for field in body["fields"]:
            keys = {o["key"] for o in field["options"]}
            answer = key.get(field["id"])
            picked = {answer} if isinstance(answer, str) else set(answer or [None])
            if not picked <= keys:
                raise SeedError(f"answer_key for '{field['id']}' is not one of its options.")
    elif item_type == "decompose_plan":
        ids = {s["id"] for s in body["steps"]}
        if not set(body["needed"]) <= ids:
            raise SeedError("needed lists a step that does not exist.")
        if any(a not in body["needed"] or b not in body["needed"] for a, b in body["order_constraints"]):
            raise SeedError("order_constraints must use needed steps.")


def _check_slots(raw: Dict[str, Any], template: Optional[Dict[str, Any]]) -> None:
    text = str({k: v for k, v in raw.items() if k != "template"})
    used = set(_SLOT.findall(text))
    defined = set((template or {}).get("slots", {}))
    if used != defined:
        raise SeedError(f"Template slots do not match: used {sorted(used)}, defined {sorted(defined)}.")


def parse_seed(raw: Dict[str, Any], file_stem: str, unit_id: str) -> ExerciseSeed:
    """Validate one seed against SPEC-13 section 8, rules 1, 2, 4 and 9. Raises SeedError."""
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise SeedError(f"schema_version must be {SCHEMA_VERSION}.")
    if raw.get("seed_id") != f"{unit_id}/{file_stem}":
        raise SeedError(f"seed_id must be {unit_id}/{file_stem}.")
    if raw.get("unit_id") != unit_id:
        raise SeedError(f"unit_id must be {unit_id}.")

    bodies = [name for name in BLOCKS if raw.get(name) is not None]
    if len(bodies) != 1:
        raise SeedError(f"A seed needs exactly one body block, found {bodies}.")
    item_type = bodies[0]
    body = raw[item_type]

    try:
        activity = ActivityType(raw.get("activity"))
    except ValueError:
        raise SeedError(f"activity '{raw.get('activity')}' is not an ActivityType.") from None
    if item_type not in ALLOWED_ITEM_TYPES[activity]:
        raise SeedError(f"{item_type} is not allowed for {activity.value}.")

    hint = raw.get("hint")
    if hint is not None and not (isinstance(hint, str) and 1 <= len(hint.strip()) and len(hint) <= MAX_HINT_CHARS):
        raise SeedError(f"hint must be text of 1 to {MAX_HINT_CHARS} characters.")

    missing = [f for f in HIDDEN_REQUIRED[item_type] if f not in body]
    if missing:
        raise SeedError(f"{item_type} is missing: {', '.join(missing)}.")
    try:
        BLOCKS[item_type].model_validate(body)
        seed = ExerciseSeed(
            **{k: raw.get(k) for k in ("seed_id", "unit_id", "skill_id", "level", "prompt_markdown")},
            activity=activity,
            cold_check_eligible=raw.get("cold_check_eligible"),
            curator_approved=raw.get("curator_approved"),
            item_type=item_type,
            body=body,
            template=raw.get("template"),
            hint=hint,
            hint_approved=bool(raw.get("hint_approved", False)),
            topic=raw.get("topic"),
        )
    except ValidationError as error:
        first = error.errors()[0]
        raise SeedError(f"{'.'.join(map(str, first['loc']))}: {first['msg']}") from None

    _check_answer_key(item_type, body)
    _check_slots(raw, seed.template)
    return seed


# --- Variants ---


def fill_slots(value: Any, slots: Dict[str, str]) -> Any:
    """Replace every {{slot}} in nested text."""
    if isinstance(value, str):
        return _SLOT.sub(lambda m: slots[m.group(1)], value)
    if isinstance(value, list):
        return [fill_slots(v, slots) for v in value]
    if isinstance(value, dict):
        return {k: fill_slots(v, slots) for k, v in value.items()}
    return value


def seed_variants(seed: ExerciseSeed) -> List[Tuple[int, ExerciseSeed]]:
    """One (variant_no, filled seed) per slot value; v1 of a plain seed is the seed itself."""
    slots = (seed.template or {}).get("slots")
    if not slots:
        return [(1, seed)]
    count = max(len(s["values"]) for s in slots.values())
    variants = []
    for i in range(count):
        chosen = {name: s["values"][i % len(s["values"])] for name, s in slots.items()}
        variants.append(
            (
                i + 1,
                seed.model_copy(
                    update={
                        "prompt_markdown": fill_slots(seed.prompt_markdown, chosen),
                        "body": fill_slots(seed.body, chosen),
                    }
                ),
            )
        )
    return variants


def pool_for(seeds: Sequence[ExerciseSeed], activity: str) -> List[str]:
    """Exercise ids an activity can serve. Cold Check seeds stay reserved (SPEC-13 section 5)."""
    if activity == COLD_CHECK:
        chosen = [s for s in seeds if s.cold_check_eligible and s.curator_approved]
    else:
        chosen = [s for s in seeds if s.activity.slug == activity and not s.cold_check_eligible]
    return [f"{s.seed_id}/v{n}" for s in chosen for n, _ in seed_variants(s)]


def find_seed_variant(
    seeds: Sequence[ExerciseSeed], exercise_id: str
) -> Optional[Tuple[ExerciseSeed, int]]:
    """The filled seed behind an exercise id. It holds hidden fields: for the server only."""
    for seed in seeds:
        for n, variant in seed_variants(seed):
            if f"{seed.seed_id}/v{n}" == exercise_id:
                return variant, n
    return None


def find_variant(seeds: Sequence[ExerciseSeed], exercise_id: str) -> Optional[Exercise]:
    found = find_seed_variant(seeds, exercise_id)
    return to_exercise(*found) if found else None


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def cold_history(ledger: Iterable[EvidenceEntry], unit_id: str) -> Dict[str, bool]:
    """seed id -> did the learner's newest unit Cold Check answer pass? A seed never answered is absent.

    Read from the evidence ledger (ADR-0032), which a reset never clears. Stage reviews
    and rechecks are not unit Cold Check answers.
    """
    answers = sorted(
        (e for e in ledger if e.unit_id == unit_id and e.cold_check and e.review_kind is None and e.seed_id),
        key=lambda e: _aware(e.recorded_at),
    )
    return {e.seed_id: e.evidence_strength == EvidenceStrength.STRONG for e in answers}


def cold_round(
    unit: Unit,
    seeds: Sequence[ExerciseSeed],
    history: Optional[Mapping[str, bool]] = None,
    in_round: Collection[str] = (),
) -> List[ExerciseSeed]:
    """The unit Cold Check's items: skills first, then round again to 3, at most 5 (SPEC-16 section 2).

    Within a skill the items go in this order (ADR-0032): ones already answered in this round
    (`in_round`), never answered, failed, passed; each group in seed order. `history` is
    `cold_history`; empty gives the round of a learner who has answered nothing. How many items
    each skill gives does not depend on the history, so the round keeps its size and can complete.
    """
    history = history or {}

    def rank(seed: ExerciseSeed) -> int:
        if seed.seed_id in in_round:
            return -1
        answered = history.get(seed.seed_id)
        return 0 if answered is None else (2 if answered else 1)

    by_skill = [
        sorted(
            (s for s in seeds if s.skill_id == skill.skill_id and s.cold_check_eligible and s.curator_approved),
            key=rank,
        )
        for skill in unit.target_skills
    ]
    by_skill = [group for group in by_skill if group]
    size = min(COLD_ITEMS_MAX, max(COLD_ITEMS_MIN, len(by_skill)))
    in_turn = (s for row in zip_longest(*by_skill) for s in row if s is not None)
    return list(islice(in_turn, size))


def shown_cold_round(
    unit: Unit,
    seeds: Sequence[ExerciseSeed],
    ledger: Iterable[EvidenceEntry],
    reset_at: Optional[datetime] = None,
) -> List[ExerciseSeed]:
    """The round the Cold Check feedback shows: the one the learner answered last.

    After a failed round the next round holds replacements, but the learner still needs to see
    which items failed. Replaying the unit's Cold Check answers in order finds that round
    (ADR-0032). With no answers since a reset, it is the current round.
    """
    approved = {s.seed_id for s in seeds if s.cold_check_eligible and s.curator_approved}
    answers = sorted(
        (
            e for e in ledger
            if e.unit_id == unit.unit_id and e.cold_check and e.review_kind is None and e.seed_id in approved
        ),
        key=lambda e: _aware(e.recorded_at),
    )
    history: Dict[str, bool] = {}
    kept: Dict[str, bool] = {}
    last_done: Optional[List[ExerciseSeed]] = None
    in_wave = crossed = False
    for entry in answers:
        if reset_at is not None and not crossed and _aware(entry.recorded_at) >= _aware(reset_at):
            kept.clear()
            last_done, in_wave, crossed = None, False, True
        passed = entry.evidence_strength == EvidenceStrength.STRONG
        if entry.seed_id not in {s.seed_id for s in cold_round(unit, seeds, history, kept)}:
            history[entry.seed_id] = passed  # Not in the round in force: history only
            continue
        history[entry.seed_id] = kept[entry.seed_id] = passed
        in_wave = True
        round_now = cold_round(unit, seeds, history, kept)
        if all(s.seed_id in kept for s in round_now):
            last_done, in_wave = round_now, False
            kept = {seed_id: ok for seed_id, ok in kept.items() if ok}  # A failed item leaves the round
    if reset_at is not None and not crossed:
        return cold_round(unit, seeds, history)
    if in_wave or last_done is None:
        return cold_round(unit, seeds, history, kept)
    return last_done


def spare_cold_items(unit: Unit, seeds: Sequence[ExerciseSeed]) -> int:
    """Approved items the unit's own round does not use, so a stage review can."""
    return len(pool_for(seeds, COLD_CHECK)) - len(cold_round(unit, seeds))


def choose_next(pool: Sequence[str], seen: Sequence[str], current: Optional[str]) -> str:
    """First unseen item; when none is left, the oldest seen other than the current one."""
    for exercise_id in pool:
        if exercise_id not in seen:
            return exercise_id
    for exercise_id in seen:
        if exercise_id in pool and exercise_id != current:
            return exercise_id
    return current if current in pool else pool[0]


# --- The learner-safe view ---


def to_exercise(seed: ExerciseSeed, variant_no: int) -> Exercise:
    body = dict(seed.body)
    if seed.item_type == "decompose_plan":
        # Stable, but not the curator's order: that order would give the plan away.
        body["steps"] = sorted(
            body["steps"],
            key=lambda s: hashlib.sha256(f"{seed.seed_id}:{s['id']}".encode()).hexdigest(),
        )
    rows = body.get("line_states")
    if seed.item_type == "trace" and rows and not seed.cold_check_eligible:
        # Line numbers and names only; the values stay private (ADR-0031).
        body["state_rows"] = [{"line": r["line"], "names": sorted(r["state"])} for r in rows]
    return Exercise(
        exercise_id=f"{seed.seed_id}/v{variant_no}",
        unit_id=seed.unit_id,
        activity=seed.activity.slug,
        variant_no=variant_no,
        item_type=seed.item_type,
        prompt_markdown="\n".join(seed.prompt_markdown),
        **{seed.item_type: BLOCKS[seed.item_type].model_validate(body)},
    )


def concept_prompts(config: Optional[Mapping[str, Any]]) -> List[str]:
    """A unit's concept-check prompts in order: `prompt` is v1, then `more_prompts` (ADR-0032), at most 3."""
    config = config or {}
    first = config.get("prompt")
    if not isinstance(first, str) or not first:
        return []
    more = config.get("more_prompts")
    extra = [p for p in more if isinstance(p, str) and p] if isinstance(more, list) else []
    return [first, *extra][:MAX_CONCEPT_PROMPTS]


def explain_exercise(
    unit: Unit,
    evidence: Iterable[EvidenceEntry] = (),
    reset_at: Optional[datetime] = None,
) -> Optional[Exercise]:
    """The free-text concept check; its rubric and keywords stay on the server.

    With several prompts it serves the lowest-numbered one not answered since the learner's last
    reset of the unit, else the one answered longest ago (ADR-0032). No history serves v1.
    """
    prompts = concept_prompts(unit.concept_check_config)
    if not prompts:
        return None
    answered: Dict[str, datetime] = {}
    for e in evidence:
        if e.unit_id != unit.unit_id or not is_concept_check(e):
            continue
        at = _aware(e.recorded_at)
        if reset_at is not None and at < _aware(reset_at):
            continue
        key = e.exercise_id or concept_check_id(unit.unit_id)  # Rows from before amendment G are v1
        answered[key] = max(answered.get(key, at), at)
    ids = [concept_check_id(unit.unit_id, n) for n in range(1, len(prompts) + 1)]
    unanswered = [n for n, key in enumerate(ids) if key not in answered]
    chosen = unanswered[0] if unanswered else min(range(len(ids)), key=lambda n: answered[ids[n]])
    return Exercise(
        exercise_id=ids[chosen],
        unit_id=unit.unit_id,
        activity=ActivityType.EXPLAIN.slug,
        item_type="concept_check",
        prompt_markdown=prompts[chosen],
    )


def playground_exercise(unit: Unit) -> Optional[Exercise]:
    """Ungraded practice from the package's starter.py (SPEC-12 section 3.2)."""
    if unit.starter_code is None:
        return None
    return Exercise(
        exercise_id=f"{unit.unit_id}/playground/v1",
        unit_id=unit.unit_id,
        activity="playground",
        item_type="playground",
        prompt_markdown="Try it yourself. This practice is not graded.",
        playground=PlaygroundBlock(starter=unit.starter_code.splitlines()),
    )
