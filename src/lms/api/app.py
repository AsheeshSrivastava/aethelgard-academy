"""FastAPI Production LMS Platform Gateway.

Provides versioned REST endpoints (/api/v1/) for:
- Curriculum catalog exploration
- Untrusted code execution in the hardened sandbox
- AXIS AI pedagogical companion (Coach, Hybrid, Socratic)
- Evidence Ledger queries and progress persistence
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lms.adapters.ai.axis_stream import stream_axis
from lms.adapters.ai.local_llm_companion import get_axis_companion
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.adapters.curriculum.concepts import ConceptCatalog
from lms.adapters.curriculum.loader import CurriculumCatalog, load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.docker_runner import get_code_runner
from lms.adapters.runner.interactive import InteractiveRun, RunLimits, valid_start
from lms.core.cold_check import ColdCheckState, ColdCheckStatus, cold_check_status
from lms.core.course_map import (
    COURSES,
    Course,
    CourseMap,
    build_course,
    build_course_map,
    course_of,
)
from lms.core.curriculum_checks import ACTIVITY_EVIDENCE
from lms.core.exercises import (
    COLD_CHECK,
    Exercise,
    ExerciseSeed,
    choose_next,
    cold_check_skills,
    cold_pool_for_skill,
    explain_exercise,
    find_seed_variant,
    find_variant,
    playground_exercise,
    pool_for,
)
from lms.core.grading import (
    Attempt,
    Check,
    Reveal,
    Score,
    evidence_strength,
    grade,
    highest_assistance,
)
from lms.core.interfaces import (
    AxisMode,
    AxisQuery,
    AxisResponse,
    ExecutionResult,
    IAXISCompanion,
    ICodeRunner,
    ILearnerRepository,
)
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    ConceptItem,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProgressionDecision,
    Unit,
)
from lms.core.proficiency import EstimatorConfig
from lms.core.proficiency_view import (
    ProficiencyView,
    activities_attempted,
    build_proficiency_view,
    first_unfinished_unit,
    unit_decision,
)

logger = logging.getLogger(__name__)

LOCAL_LEARNER_ID = "default_learner"

# The Vite dev server. The built frontend is served from this app's own origin.
DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

MAX_DRAFT_CHARS = 256_000


def allowed_origins() -> List[str]:
    """Origins from LMS_ALLOWED_ORIGINS. Never a wildcard: credentials are allowed (ADR-0015)."""
    configured = os.environ.get("LMS_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if "*" in origins:
        logger.warning("Ignoring '*' in LMS_ALLOWED_ORIGINS: credentials are allowed.")
    return [origin for origin in origins if origin != "*"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_learner_id() -> str:
    """Local-single mode (ADR-0015): "me" is always the one local learner."""
    return LOCAL_LEARNER_ID


def problem(status: int, title: str, detail: str) -> JSONResponse:
    """RFC 9457 error body (SPEC-12 section 1)."""
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={"type": "about:blank", "title": title, "status": status, "detail": detail},
    )


class LearnerProfile(BaseModel):
    learner_id: str
    display_name: str
    auth_mode: str


class UnitState(BaseModel):
    step: Optional[str] = None
    done_steps: List[str] = []


class Draft(BaseModel):
    files: Dict[str, str]


class VerifyRequest(BaseModel):
    code: str


class AxisStreamRequest(AxisQuery):
    page: Optional[str] = None         # "video", "explain", "predict", "trace", "playground", "build", "progress"


class AttemptResult(BaseModel):
    outcome: str                       # "passed" | "failed"
    feedback: str
    checks: Optional[List[Check]] = None
    score: Optional[Score] = None
    reveal: Optional[Reveal] = None
    evidence_entry_id: Optional[str] = None
    unit_decision: ProgressionDecision


def public_unit(unit: Unit) -> Unit:
    """A unit for the browser: no hidden checks, no concept check rubric or keywords."""
    config = unit.concept_check_config or {}
    return unit.model_copy(
        update={
            "test_code": None,
            "concept_check_config": {"prompt": config["prompt"]} if "prompt" in config else None,
        }
    )


class ExecuteCodeRequest(BaseModel):
    code: str
    test_code: Optional[str] = None
    timeout_seconds: float = 5.0
    stdin_input: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    unit_id: str
    status: str


class ExplainRequest(BaseModel):
    unit_id: str
    explanation: str


class ExplainResponse(BaseModel):
    unit_id: str
    status: str
    feedback: str
    evidence_logged: bool


def create_app(
    repo: Optional[ILearnerRepository] = None,
    runner: Optional[ICodeRunner] = None,
    axis: Optional[IAXISCompanion] = None,
    catalog: Optional[CurriculumCatalog] = None,
    concepts: Optional[ConceptCatalog] = None,
    clock: Optional[Callable[[], datetime]] = None,
    run_limits: Optional[RunLimits] = None,
) -> FastAPI:
    """Application factory for the LMS API Gateway."""

    # Default dependencies
    if repo is None:
        sqlite_repo = SQLiteLearnerRepository()
        sqlite_repo.initialize()
        repo = sqlite_repo

    if runner is None:
        runner = get_code_runner()

    if axis is None:
        axis = get_axis_companion()

    if catalog is None:
        catalog = load_all_roadmaps(Path("reference"))

    if concepts is None:
        concepts = ConceptCatalog()

    if clock is None:
        clock = utc_now

    app = FastAPI(
        title="LMS / KMS Production Platform Gateway",
        description="Capability-based adaptive learning platform API",
        version="0.1.0",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Static Files & Frontend Shell ---
    web_dir = Path("src/lms/web")
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>Aethelgard Academy Platform Shell Initializing...</h1>")

    # --- System Routes ---
    @app.get("/api/v1/health")
    def health_check() -> Dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    # --- Concept Library (KMS) Routes ---
    @app.get("/api/v1/concepts", response_model=List[ConceptItem])
    def get_concepts(search: Optional[str] = Query(None)):
        if search:
            return concepts.search(search)
        return concepts.list_all()

    @app.get("/api/v1/concepts/{concept_id}", response_model=ConceptItem)
    def get_concept_by_id(concept_id: str):
        concept = concepts.get(concept_id)
        if not concept:
            raise HTTPException(status_code=404, detail=f"Concept '{concept_id}' not found.")
        return concept

    # --- Curriculum Routes ---
    @app.get("/api/v1/units", response_model=List[Dict[str, Any]])
    def list_units(
        stage: Optional[int] = Query(None, description="Filter by stage number"),
        course_id: Optional[str] = Query(None, description="Filter by course"),
    ):
        units = catalog.get_stage_units(stage) if stage is not None else catalog.list_all_units()
        if course_id is not None:
            if course_id not in COURSES:
                return problem(404, "Course not found", f"Course '{course_id}' does not exist.")
            course_units = {u.unit_id for u in catalog.get_course_units(course_id)}
            units = [u for u in units if u.unit_id in course_units]
        return [
            {
                "unit_id": u.unit_id,
                "title": u.title,
                "stage": u.stage,
                "concept_line": u.concept_line,
                "methods": [m.value for m in u.methods],
                "target_skills": [
                    {"skill_id": s.skill_id, "goal_level": s.goal_level.value}
                    for s in u.target_skills
                ],
                "prerequisites": u.prerequisites,
            }
            for u in units
        ]

    @app.get("/api/v1/units/{unit_id}", response_model=Unit)
    def get_unit(unit_id: str):
        unit = catalog.get_unit(unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found.")
        return public_unit(unit)

    @app.get("/api/v1/courses", response_model=List[Course])
    def list_courses():
        return [build_course(c, catalog.get_course_units(c)) for c in COURSES]

    @app.get("/api/v1/courses/{course_id}", response_model=CourseMap)
    def get_course_map(course_id: str, learner_id: str = Depends(current_learner_id)):
        if course_id not in COURSES:
            return problem(404, "Course not found", f"Course '{course_id}' does not exist.")
        now = clock()
        return build_course_map(
            course_id,
            catalog.get_course_units(course_id),
            catalog.get_stage_titles(course_id),
            lambda unit_id: cold_check_status(
                repo.get_cold_check_timer(learner_id, unit_id), now
            ).state,
        )

    # --- Code Execution Sandbox Routes ---
    @app.post("/api/v1/execute", response_model=ExecutionResult)
    def execute_code(payload: ExecuteCodeRequest):
        return runner.execute(
            code=payload.code,
            test_code=payload.test_code,
            timeout_seconds=payload.timeout_seconds,
            stdin_input=payload.stdin_input,
        )

    # --- Interactive Runs (SPEC-12 section 7) ---
    @app.websocket("/api/v1/runs")
    async def run_interactively(websocket: WebSocket):
        await websocket.accept()
        start = await websocket.receive_json()
        files = start.get("files") or {}
        entry = start.get("entry") or ""
        problem_text = (
            "The first message must be start."
            if start.get("type") != "start"
            else valid_start(files, entry)
        )
        if problem_text:
            await websocket.send_json({"type": "error", "message": problem_text})
            await websocket.close()
            return

        interactive = InteractiveRun(files, entry, run_limits or RunLimits())

        async def send_events() -> None:
            while True:
                event = await asyncio.to_thread(interactive.next_event, 0.1)
                if event is None:
                    continue
                await websocket.send_json(event)
                if event["type"] == "exit":
                    return

        async def receive_stdin() -> None:
            while True:
                message = await websocket.receive_json()
                if message.get("type") == "stdin":
                    interactive.send_stdin(str(message.get("data", "")))

        sender = asyncio.create_task(send_events())
        receiver = asyncio.create_task(receive_stdin())
        try:
            await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()
            receiver.cancel()
            interactive.stop()
        if sender.done() and not sender.cancelled():
            await websocket.close()

    # --- AXIS AI Companion Routes ---
    guardrail = SocraticGuardrail()
    classifier = AssistanceClassifier()

    def is_cold_check_exercise(exercise_id: Optional[str]) -> bool:
        if not exercise_id:
            return False
        found = find_seed_variant(catalog.seeds.get(exercise_id.split("/")[0], []), exercise_id)
        return found is not None and found[0].cold_check_eligible

    def axis_blocked() -> JSONResponse:
        return problem(403, "AXIS is off", "AXIS does not help during a Cold Check.")

    def citation_for(name: str) -> Dict[str, str]:
        concept = concepts.get(name) or next(iter(concepts.search(name)), None)
        if concept:
            return {"concept_id": concept.concept_id, "title": concept.name, "doc_url": concept.doc_url}
        return {"concept_id": name, "title": name, "doc_url": ""}

    @app.post("/api/v1/axis/stream", response_model=None)
    def stream_axis_reply(request: AxisStreamRequest, learner_id: str = Depends(current_learner_id)):
        if is_cold_check_exercise(request.exercise_id):
            return axis_blocked()
        query = request.model_copy(update={"learner_id": learner_id})

        def sse(event: str, data: Dict[str, Any]) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        def events() -> Iterator[str]:
            try:
                for event, data in stream_axis(axis, query, guardrail, classifier):
                    if event == "citation":
                        yield sse(event, citation_for(data["name"]))
                        continue
                    if event == "done" and query.exercise_id:
                        repo.log_assistance(
                            learner_id,
                            query.exercise_id,
                            AssistanceLevel(data["assistance_level"]),
                            clock(),
                        )
                    yield sse(event, data)
            except Exception:
                # Provider details can hold addresses or tokens, so none reach the browser.
                logger.exception("AXIS stream failed.")
                yield sse("error", {"message": "AXIS is unavailable right now."})

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.post("/api/v1/axis/consult", response_model=AxisResponse)
    def consult_axis(query: AxisQuery, learner_id: str = Depends(current_learner_id)):
        if is_cold_check_exercise(query.exercise_id):
            return axis_blocked()
        response = axis.consult(query.model_copy(update={"learner_id": learner_id}))
        if query.exercise_id:
            repo.log_assistance(
                learner_id, query.exercise_id, response.detected_assistance_level, clock()
            )
        return response

    # --- CO-6 Concept Check & Mental Model Route ---
    @app.post("/api/v1/explain", response_model=ExplainResponse)
    def evaluate_explanation(payload: ExplainRequest, learner_id: str = Depends(current_learner_id)):
        clean_unit = payload.unit_id.upper()
        keywords = ["string", "text", "typeerror", "convert", "int"]
        concept_line = "A program takes input, transforms it, and produces output; input() always returns a string."

        meta_path = Path(f"curriculum/python/{clean_unit.lower()}/meta.json")
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                check_cfg = meta.get("concept_check", {})
                if "solid_keywords" in check_cfg:
                    keywords = check_cfg["solid_keywords"]
                if "concept_line" in check_cfg:
                    concept_line = check_cfg["concept_line"]
            except Exception:
                pass

        if hasattr(axis, "evaluate_concept_check"):
            eval_res = axis.evaluate_concept_check(
                unit_id=clean_unit,
                concept_line=concept_line,
                explanation=payload.explanation,
                solid_keywords=keywords,
            )
            status = eval_res["status"]
            feedback = eval_res["feedback"]
            is_solid = status == "Solid"
        else:
            lower_exp = payload.explanation.lower()
            matches = sum(1 for kw in keywords if kw.lower() in lower_exp)
            is_solid = matches >= 2
            status = "Solid" if is_solid else "Shaky"
            feedback = (
                "Explanation demonstrates solid operational mental model."
                if is_solid
                else "Explanation is emerging or shaky; remember to reflect on types and boundaries."
            )

        entry = EvidenceEntry(
            learner_id=learner_id,
            unit_id=clean_unit,
            skill_id="CO-6",
            evidence_category=EvidenceCategory.EXPLAIN_REASON,
            evidence_strength=EvidenceStrength.STRONG if is_solid else EvidenceStrength.WEAK,
            assistance_level=AssistanceLevel.NONE,
            demonstration_context=f"CO-6 Concept Check for {clean_unit}",
            observed_reasoning=f"Mental model evaluated as {status}: {feedback}",
            recorded_at=clock(),
        )
        repo.record_evidence(entry)
        unit = catalog.get_unit(clean_unit)
        if unit:
            maybe_start_cold_check_clock(unit, learner_id)

        return ExplainResponse(
            unit_id=clean_unit,
            status=status,
            feedback=feedback,
            evidence_logged=True,
        )

    # --- Socratic Error Diagnostic Route ---
    @app.post("/api/v1/explain-error")
    def explain_runtime_error(payload: Dict[str, Any], learner_id: str = Depends(current_learner_id)):
        unit_id = payload.get("unit_id", "PY-0.1").upper()
        code = payload.get("code", "")
        error_msg = payload.get("error", "")
        query = AxisQuery(
            learner_id=learner_id,
            unit_id=unit_id,
            mode=AxisMode.SOCRATIC,
            current_activity=ActivityType.DEBUG_VALIDATE,
            user_prompt=f"I ran my code and received this runtime error:\n{error_msg}\nCan you guide me Socratically to inspect my own logic and find where the error came from?",
            learner_code=code,
        )
        resp = axis.consult(query)
        return {"unit_id": unit_id, "explanation": resp.reply}

    # --- Learner-Scoped /me Routes (SPEC-12, ADR-0015) ---
    @app.get("/api/v1/learners/me", response_model=LearnerProfile)
    def get_me(learner_id: str = Depends(current_learner_id)):
        return LearnerProfile(
            learner_id=learner_id, display_name="Local learner", auth_mode="local-single"
        )

    @app.get("/api/v1/learners/me/proficiency", response_model=ProficiencyView)
    def get_my_proficiency(
        course_id: Optional[str] = Query(None),
        stage: Optional[int] = Query(None),
        learner_id: str = Depends(current_learner_id),
    ):
        if course_id is None:
            units = catalog.list_all_units()
        elif course_id in COURSES:
            units = catalog.get_course_units(course_id)
        else:
            return problem(404, "Course not found", f"Course '{course_id}' does not exist.")

        now = clock()
        ledger = repo.get_evidence_ledger(learner_id)
        config = EstimatorConfig(main_activities=catalog.main_activities)

        # My progress opens on the learner's current stage (owner decision, 2026-10-31).
        if stage is None and units:
            anchor = first_unfinished_unit(units, ledger, now, config) or units[-1]
            stage = anchor.stage
            units = [u for u in units if course_of(u.unit_id) == course_of(anchor.unit_id)]
        if stage is not None:
            units = [u for u in units if u.stage == stage]

        return build_proficiency_view(
            units,
            ledger,
            lambda unit_id: cold_check_status(repo.get_cold_check_timer(learner_id, unit_id), now),
            now=now,
            stage=stage,
            config=config,
        )

    @app.get("/api/v1/learners/me/units/{unit_id}/cold-check", response_model=ColdCheckStatus)
    def get_my_cold_check(unit_id: str, learner_id: str = Depends(current_learner_id)):
        if not catalog.get_unit(unit_id):
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        return cold_check_status(repo.get_cold_check_timer(learner_id, unit_id), clock())

    @app.get("/api/v1/learners/me/ledger", response_model=List[EvidenceEntry])
    def get_my_ledger(
        skill_id: Optional[str] = Query(None),
        unit_id: Optional[str] = Query(None),
        learner_id: str = Depends(current_learner_id),
    ):
        entries = repo.get_evidence_ledger(learner_id=learner_id, skill_id=skill_id)
        if unit_id is not None:
            entries = [e for e in entries if e.unit_id == unit_id]
        return sorted(entries, key=lambda e: e.recorded_at, reverse=True)

    # --- Exercises, Regenerate, Reset, State and Drafts (SPEC-12 section 4) ---
    def cold_check_blocked(unit_id: str, learner_id: str) -> Optional[JSONResponse]:
        status = cold_check_status(repo.get_cold_check_timer(learner_id, unit_id), clock())
        if status.state == ColdCheckState.PASSED:
            return problem(409, "Cold Check passed", f"The Cold Check for {unit_id} is already passed.")
        if status.state != ColdCheckState.AVAILABLE:
            return problem(423, "Cold Check locked", f"Available at: {status.available_at}.")
        return None

    def serve(unit: Unit, activity: str, exercise_id: str, learner_id: str) -> Optional[Exercise]:
        repo.set_current_exercise(learner_id, unit.unit_id, activity, exercise_id, clock())
        return find_variant(catalog.seeds.get(unit.unit_id, []), exercise_id)

    def serving_pool(unit: Unit, activity: str, learner_id: str) -> List[str]:
        seeds = catalog.seeds.get(unit.unit_id, [])
        if activity != COLD_CHECK:
            return pool_for(seeds, activity)
        finished = repo.get_cold_items(learner_id, unit.unit_id)
        pending = [s for s in cold_check_skills(unit, seeds) if s not in finished]
        return cold_pool_for_skill(seeds, pending[0]) if pending else []

    def maybe_start_cold_check_clock(unit: Unit, learner_id: str) -> None:
        if activities_attempted(unit, repo.get_evidence_ledger(learner_id)):
            repo.mark_unit_activities_completed(learner_id, unit.unit_id, clock())

    def finish_cold_item(unit: Unit, seed: ExerciseSeed, passed: bool, learner_id: str) -> None:
        now = clock()
        repo.record_cold_item(learner_id, unit.unit_id, seed.skill_id, passed, now)
        repo.clear_current_exercise(learner_id, unit.unit_id, COLD_CHECK)
        items = repo.get_cold_items(learner_id, unit.unit_id)
        required = cold_check_skills(unit, catalog.seeds.get(unit.unit_id, []))
        if all(skill in items for skill in required):
            round_passed = all(items[skill] for skill in required)
            repo.record_cold_check_attempt(learner_id, unit.unit_id, round_passed, now)
            if not round_passed:
                repo.clear_failed_cold_items(learner_id, unit.unit_id)

    def current_exercise(unit: Unit, activity: str, learner_id: str) -> Optional[Exercise]:
        if activity == ActivityType.EXPLAIN.slug:
            return explain_exercise(unit)
        if activity == "playground":
            return playground_exercise(unit)
        seeds = catalog.seeds.get(unit.unit_id, [])
        pool = serving_pool(unit, activity, learner_id)
        if not pool:
            return None
        current = repo.get_current_exercise(learner_id, unit.unit_id, activity)
        if current and current.exercise_id in pool:
            return find_variant(seeds, current.exercise_id)
        seen = repo.get_seen_exercises(learner_id, unit.unit_id, activity)
        return serve(unit, activity, choose_next(pool, seen, None), learner_id)

    def known_exercise(exercise_id: str) -> Optional[str]:
        """The unit an exercise id belongs to, if it is a real exercise."""
        unit = catalog.get_unit(exercise_id.split("/")[0])
        if not unit:
            return None
        built_in = {f"{unit.unit_id}/explain/v1", f"{unit.unit_id}/playground/v1"}
        seeds = catalog.seeds.get(unit.unit_id, [])
        return unit.unit_id if exercise_id in built_in or find_variant(seeds, exercise_id) else None

    @app.get(
        "/api/v1/learners/me/units/{unit_id}/activities/{activity}/exercise",
        response_model=Exercise,
        response_model_exclude_none=True,
    )
    def get_my_exercise(unit_id: str, activity: str, learner_id: str = Depends(current_learner_id)):
        unit = catalog.get_unit(unit_id)
        if not unit:
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        if activity not in unit.activities or activity == "video":
            return problem(404, "No such activity", f"{unit_id} has no exercise for '{activity}'.")
        if activity == COLD_CHECK:
            blocked = cold_check_blocked(unit_id, learner_id)
            if blocked:
                return blocked
        exercise = current_exercise(unit, activity, learner_id)
        if exercise is None:
            return problem(404, "No exercise yet", f"{unit_id} has no '{activity}' exercise yet.")
        return exercise

    @app.post(
        "/api/v1/learners/me/units/{unit_id}/activities/{activity}/exercises:regenerate",
        response_model=Exercise,
        response_model_exclude_none=True,
    )
    def regenerate_my_exercise(
        unit_id: str, activity: str, learner_id: str = Depends(current_learner_id)
    ):
        unit = catalog.get_unit(unit_id)
        if not unit:
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        if activity == ActivityType.EXPLAIN.slug:
            return problem(409, "Cannot regenerate", "Explain cannot be regenerated.")
        if activity not in unit.activities or activity == "video":
            return problem(404, "No such activity", f"{unit_id} has no exercise for '{activity}'.")
        if activity == "playground":
            exercise = playground_exercise(unit)
            if exercise is None:
                return problem(404, "No exercise yet", f"{unit_id} has no playground yet.")
            return exercise

        current = repo.get_current_exercise(learner_id, unit_id, activity)
        if activity == COLD_CHECK:
            blocked = cold_check_blocked(unit_id, learner_id)
            if blocked:
                return blocked
            timer = repo.get_cold_check_timer(learner_id, unit_id)
            attempted = (
                current is not None
                and timer.last_attempt_at is not None
                and timer.last_attempt_at >= current.served_at
            )
            if not attempted:
                return problem(409, "Cannot regenerate", "Attempt this Cold Check first.")

        pool = serving_pool(unit, activity, learner_id)
        if not pool:
            return problem(404, "No exercise yet", f"{unit_id} has no '{activity}' exercise yet.")
        seen = repo.get_seen_exercises(learner_id, unit_id, activity)
        next_id = choose_next(pool, seen, current.exercise_id if current else None)
        return serve(unit, activity, next_id, learner_id)

    # --- Attempts and Evidence (SPEC-12 section 5) ---
    def check_playground(unit: Unit, code: str) -> ExecutionResult:
        return runner.execute(code=code, test_code=unit.test_code)

    @app.post("/api/v1/learners/me/units/{unit_id}/playground:verify", response_model=ExecutionResult)
    def verify_my_playground(
        unit_id: str, payload: VerifyRequest, learner_id: str = Depends(current_learner_id)
    ):
        unit = catalog.get_unit(unit_id)
        if not unit or not unit.test_code:
            return problem(404, "No checks", f"{unit_id} has no playground checks.")
        return check_playground(unit, payload.code)

    @app.post(
        "/api/v1/learners/me/attempts",
        response_model=AttemptResult,
        response_model_exclude_none=True,
    )
    def post_my_attempt(attempt: Attempt, learner_id: str = Depends(current_learner_id)):
        unit_id = known_exercise(attempt.exercise_id)
        if not unit_id:
            return problem(404, "Exercise not found", f"Exercise '{attempt.exercise_id}' does not exist.")
        unit = catalog.get_unit(unit_id)
        activity = attempt.activity
        config = EstimatorConfig(main_activities=catalog.main_activities)

        if activity not in unit.activities or activity == "video":
            return problem(422, "Unknown activity", f"{unit_id} has no '{activity}' activity.")
        if activity == ActivityType.EXPLAIN.slug:
            return problem(409, "Use the concept check", "Explain is submitted to /api/v1/explain.")
        if activity == "playground":
            code = (attempt.files or {}).get("solution.py", "")
            result = check_playground(unit, code)
            ledger = repo.get_evidence_ledger(learner_id)
            return AttemptResult(
                outcome="passed" if result.success else "failed",
                feedback="All checks passed." if result.success else "Some checks failed.",
                unit_decision=unit_decision(unit, ledger, clock(), config),
            )

        is_cold = activity == COLD_CHECK
        if is_cold:
            blocked = cold_check_blocked(unit_id, learner_id)
            if blocked:
                return blocked
        current = repo.get_current_exercise(learner_id, unit_id, activity)
        if current is None or current.exercise_id != attempt.exercise_id:
            return problem(409, "Not your current exercise", "Fetch the current exercise and try again.")

        seed, _ = find_seed_variant(catalog.seeds.get(unit_id, []), attempt.exercise_id)
        graded = grade(seed, attempt, runner)

        assistance = AssistanceLevel.NONE
        if not is_cold:
            assistance = highest_assistance(
                repo.get_assistance_levels(learner_id, attempt.exercise_id, current.served_at)
            )
        prior = [e for e in repo.get_evidence_ledger(learner_id) if e.seed_id == seed.seed_id]
        entry = EvidenceEntry(
            learner_id=learner_id,
            unit_id=unit_id,
            skill_id=seed.skill_id,
            evidence_category=ACTIVITY_EVIDENCE[seed.activity],
            evidence_strength=evidence_strength(
                seed.item_type, graded.passed, len(prior), assistance, is_cold
            ),
            assistance_level=assistance,
            demonstration_context=f"{seed.activity.value} attempt on {attempt.exercise_id}",
            recorded_at=clock(),
            exercise_id=attempt.exercise_id,
            seed_id=seed.seed_id,
            activity=seed.activity,
            cold_check=is_cold,
        )
        repo.record_evidence(entry)

        if is_cold:
            finish_cold_item(unit, seed, graded.passed, learner_id)
        else:
            maybe_start_cold_check_clock(unit, learner_id)

        # A failed Cold Check item can come back, so it must not show its answer.
        reveal = None if is_cold and not graded.passed else graded.reveal
        return AttemptResult(
            outcome="passed" if graded.passed else "failed",
            feedback=graded.feedback,
            checks=graded.checks,
            score=graded.score,
            reveal=reveal,
            evidence_entry_id=entry.entry_id,
            unit_decision=unit_decision(unit, repo.get_evidence_ledger(learner_id), clock(), config),
        )

    @app.post("/api/v1/learners/me/units/{unit_id}/reset", status_code=204, response_model=None)
    def reset_my_unit(unit_id: str, learner_id: str = Depends(current_learner_id)):
        if not catalog.get_unit(unit_id):
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        repo.reset_unit(learner_id, unit_id)
        return None

    @app.get("/api/v1/learners/me/units/{unit_id}/state", response_model=UnitState)
    def get_my_unit_state(unit_id: str, learner_id: str = Depends(current_learner_id)):
        if not catalog.get_unit(unit_id):
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        return repo.get_unit_state(learner_id, unit_id)

    @app.put("/api/v1/learners/me/units/{unit_id}/state", response_model=UnitState)
    def put_my_unit_state(
        unit_id: str, payload: UnitState, learner_id: str = Depends(current_learner_id)
    ):
        unit = catalog.get_unit(unit_id)
        if not unit:
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        steps = set(payload.done_steps) | ({payload.step} if payload.step else set())
        if not steps <= set(unit.activities):
            return problem(422, "Unknown step", f"Steps must come from {unit.activities}.")
        repo.save_unit_state(learner_id, unit_id, payload.step, payload.done_steps)
        return payload

    @app.get("/api/v1/learners/me/drafts/{exercise_id:path}", response_model=Draft)
    def get_my_draft(exercise_id: str, learner_id: str = Depends(current_learner_id)):
        if not known_exercise(exercise_id):
            return problem(404, "Exercise not found", f"Exercise '{exercise_id}' does not exist.")
        return Draft(files=repo.get_draft(learner_id, exercise_id))

    @app.put(
        "/api/v1/learners/me/drafts/{exercise_id:path}", status_code=204, response_model=None
    )
    def put_my_draft(
        exercise_id: str, payload: Draft, learner_id: str = Depends(current_learner_id)
    ):
        unit_id = known_exercise(exercise_id)
        if not unit_id:
            return problem(404, "Exercise not found", f"Exercise '{exercise_id}' does not exist.")
        if sum(len(content) for content in payload.files.values()) > MAX_DRAFT_CHARS:
            return problem(413, "Draft too large", f"Drafts are limited to {MAX_DRAFT_CHARS} characters.")
        repo.save_draft(learner_id, unit_id, exercise_id, payload.files)
        return None

    # --- Learner Progress & Evidence Ledger Routes ---
    # Older routes that name a learner; they answer only for the signed-in learner.
    # Keep them after the /me routes so "me" is never read as a learner id.
    @app.get("/api/v1/learners/{learner_id}/ledger", response_model=List[EvidenceEntry])
    def get_ledger(
        learner_id: str,
        skill_id: Optional[str] = Query(None),
        me: str = Depends(current_learner_id),
    ):
        if learner_id != me:
            return problem(404, "Learner not found", f"Learner '{learner_id}' does not exist.")
        return repo.get_evidence_ledger(learner_id=learner_id, skill_id=skill_id)

    @app.post("/api/v1/learners/{learner_id}/progress")
    def update_progress(
        learner_id: str,
        payload: ProgressUpdateRequest,
        me: str = Depends(current_learner_id),
    ):
        if learner_id != me:
            return problem(404, "Learner not found", f"Learner '{learner_id}' does not exist.")
        repo.save_unit_progress(
            learner_id=learner_id, unit_id=payload.unit_id, status=payload.status
        )
        return {"success": True, "learner_id": learner_id, "unit_id": payload.unit_id}

    return app


# Default ASGI application instance for uvicorn
app = create_app()
