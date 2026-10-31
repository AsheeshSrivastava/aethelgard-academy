"""Exercise seeds, their variants, and the learner-safe Exercise view.

Governed by:
- SPEC-13 (Exercise Seed Format)
- SPEC-12 section 4 (Exercises, Regenerate and Reset)
- ADR-0017 (variants)

Deterministic and pure: no LLM, no I/O. An Exercise is built from models listing
only the fields a learner may see, so a hidden field can never leak by default.
"""

from datetime import datetime
import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, ValidationError

from lms.core.models import ActivityType, ProficiencyLevel, Unit

SCHEMA_VERSION = 2
COLD_CHECK = "cold_check"
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


class TraceBlock(BaseModel):
    code: List[str]
    input: str


class PlaygroundBlock(BaseModel):
    starter: List[str]
    tasks: List[Task] = []


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


def cold_check_skills(unit: Unit, seeds: Sequence[ExerciseSeed]) -> List[str]:
    """Target skills with an approved Cold Check seed, in unit order."""
    covered = {s.skill_id for s in seeds if s.cold_check_eligible and s.curator_approved}
    return [s.skill_id for s in unit.target_skills if s.skill_id in covered]


def cold_pool_for_skill(seeds: Sequence[ExerciseSeed], skill_id: str) -> List[str]:
    return pool_for([s for s in seeds if s.skill_id == skill_id], COLD_CHECK)


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
    return Exercise(
        exercise_id=f"{seed.seed_id}/v{variant_no}",
        unit_id=seed.unit_id,
        activity=seed.activity.slug,
        variant_no=variant_no,
        item_type=seed.item_type,
        prompt_markdown="\n".join(seed.prompt_markdown),
        **{seed.item_type: BLOCKS[seed.item_type].model_validate(body)},
    )


def explain_exercise(unit: Unit) -> Optional[Exercise]:
    """The free-text concept check; its rubric and keywords stay on the server."""
    prompt = (unit.concept_check_config or {}).get("prompt")
    if not prompt:
        return None
    return Exercise(
        exercise_id=f"{unit.unit_id}/explain/v1",
        unit_id=unit.unit_id,
        activity=ActivityType.EXPLAIN.slug,
        item_type="concept_check",
        prompt_markdown=prompt,
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
        prompt_markdown=f"Practise {unit.title}. This is not graded.",
        playground=PlaygroundBlock(starter=unit.starter_code.splitlines()),
    )
