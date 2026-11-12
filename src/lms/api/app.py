"""FastAPI Production LMS Platform Gateway.

Provides versioned REST endpoints (/api/v1/) for:
- Curriculum catalog exploration
- Untrusted code execution in the hardened sandbox
- AXIS AI pedagogical companion (Coach, Hybrid, Socratic)
- Evidence Ledger queries and progress persistence
"""

import asyncio
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union
from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from lms.adapters.ai.axis_stream import citation_title, stream_axis
from lms.adapters.ai.providers.router import DraftFailed, ProviderRouter, build_default_router
from lms.api.model_settings import model_settings_routes
from lms.adapters.ai.socratic_guardrail import AssistanceClassifier, SocraticGuardrail
from lms.adapters.curriculum.concepts import ConceptCatalog
from lms.adapters.curriculum.builds import answers_dir_from_env
from lms.adapters.curriculum.loader import CurriculumCatalog, load_all_roadmaps
from lms.adapters.curriculum.rubric import load_rubric
from lms.adapters.curriculum.quick_checks import load_quick_check_key, parse_quick_checks
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.docker_runner import get_code_runner
from lms.adapters.runner.interactive import InteractiveRun, RunLimits, valid_start
from lms.core import ai_judgement
from lms.core.ai_judgement import AiJudgement, not_judged
from lms.core.builds import (
    RequirementResult,
    StageBuild,
    StageBuildSpec,
    check_requirements,
    exercise_id_of,
    parse_exercise_id,
    public_build,
    scope_of,
)
from lms.core.cold_check import ColdCheckState, ColdCheckStatus, cold_check_status
from lms.core.concepts import used_in
from lms.core.course_map import (
    COURSES,
    AuthoredBuild,
    Course,
    CourseMap,
    build_course,
    build_course_map,
    course_of,
)
from lms.core.curriculum_checks import ACTIVITY_EVIDENCE
from lms.core.models import stage_label
from lms.core.timing import timing_for
from lms.core.feedback import ColdCheckFeedback, cold_check_feedback
from lms.core.interaction_log import (
    ClientEvent,
    InteractionEvent,
    clean_payload,
    new_ulid,
    valid_id,
)
from lms.adapters.ai.local_llm_companion import load_dotenv_if_present
from lms.core.review import (
    RECHECK,
    STAGE_REVIEW,
    DueReview,
    ReviewItem,
    ReviewState,
    StageReviewStatus,
    build_is_open,
    due_reviews,
    plan_recheck,
    plan_stage_review,
    recheck_scope,
    stage_review_status,
    stage_scope,
)
from lms.core.exercises import (
    COLD_CHECK,
    Exercise,
    ExerciseSeed,
    choose_next,
    cold_round,
    explain_exercise,
    find_seed_variant,
    find_variant,
    playground_exercise,
    pool_for,
    spare_cold_items,
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
    ConceptDetail,
    ConceptRef,
    ConceptSummary,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    ProgressionDecision,
    Unit,
)
from lms.core.proficiency import EstimatorConfig, concept_check_id
from lms.core.skills_view import SkillsOverview, build_skills_overview
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
MAX_CONCEPT_QUERY = 200
BUILD_ACTIVITY = "build"


def allowed_origins() -> List[str]:
    """Origins from LMS_ALLOWED_ORIGINS. Never a wildcard: credentials are allowed (ADR-0015)."""
    configured = os.environ.get("LMS_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if "*" in origins:
        logger.warning("Ignoring '*' in LMS_ALLOWED_ORIGINS: credentials are allowed.")
    return [origin for origin in origins if origin != "*"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# The interaction and attempt behind the evidence being recorded in this request (ADR-0022).
_EVIDENCE_LINK: ContextVar[Tuple[Optional[str], Optional[str]]] = ContextVar("evidence_link", default=(None, None))


def current_session(x_session_id: Optional[str] = Header(None)) -> Optional[str]:
    """One id per app visit, sent by the client; a malformed one is dropped (ADR-0022)."""
    return x_session_id if valid_id(x_session_id) else None


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


class Features(BaseModel):
    """Modules that are switched on (SPEC-12 section 9). The frontend hides routes for the rest."""

    live_sessions: bool = False
    forums: bool = False
    gamification: bool = False
    test_mode: bool = False            # Every wait is zero (ADR-0019 amendment 2026-11-04)


class BuildCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: Dict[str, str]
    ownership_note: Optional[str] = None
    review_note: Optional[str] = None
    run_checks: bool = False


class BuildCheckResult(BaseModel):
    requirements: List[RequirementResult]


class DraftReadmeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: Dict[str, str]


class DraftReadmeResult(BaseModel):
    markdown: str
    status: str                        # "drafted"
    model: str                         # What answered; never written in code


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


class QuickCheckRequest(BaseModel):
    """A learner's choice in a quick check (SPEC-19 section 4)."""

    choice: str


class QuickCheckResult(BaseModel):
    """Right or not; the why only when right, so a wrong try does not reveal the answer."""

    correct: bool
    why: Optional[str] = None


class ExplainResponse(AiJudgement):
    """The verdict (SPEC-18 section 2) plus the unit and whether a ledger entry was written."""

    unit_id: str
    evidence_logged: bool


def env_test_mode() -> bool:
    """Only a clear yes turns test mode on; anything else keeps the real waits."""
    return os.environ.get("LMS_TEST_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def create_app(
    repo: Optional[ILearnerRepository] = None,
    runner: Optional[ICodeRunner] = None,
    axis: Optional[IAXISCompanion] = None,
    catalog: Optional[CurriculumCatalog] = None,
    concepts: Optional[ConceptCatalog] = None,
    clock: Optional[Callable[[], datetime]] = None,
    run_limits: Optional[RunLimits] = None,
    dist_dir: Optional[Path] = None,
    test_mode: Optional[bool] = None,
    providers: Optional[ProviderRouter] = None,
) -> FastAPI:
    """Application factory for the LMS API Gateway."""

    # Test mode sets every wait to zero and tags the evidence (ADR-0019 amendment 2026-11-04).
    if test_mode is None:
        load_dotenv_if_present()  # Settings may come from a local .env, as for AXIS
        test_mode = env_test_mode()
    timing = timing_for(test_mode)
    cold_config = timing.cold_check

    # Default dependencies
    if repo is None:
        sqlite_repo = SQLiteLearnerRepository(os.environ.get("LMS_DB_PATH", "lms_state.db"))
        sqlite_repo.initialize()
        repo = sqlite_repo

    if runner is None:
        runner = get_code_runner()

    # AXIS goes through the provider switcher unless a test injects a companion (SPEC-17).
    if axis is None:
        if providers is None:
            providers = build_default_router(os.environ.get("LMS_DB_PATH", "lms_state.db"))
        axis = providers

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

    if providers is not None:
        app.include_router(model_settings_routes(providers, current_learner_id))

    # --- Static Files & Frontend Shell ---
    web_dir = Path("src/lms/web")
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    dist = (dist_dir or web_dir / "dist").resolve()

    @app.get("/legacy", response_class=HTMLResponse)
    def serve_legacy_shell():
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>Aethelgard Academy Platform Shell Initializing...</h1>")

    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        index_file = dist / "index.html"
        return FileResponse(index_file) if index_file.exists() else serve_legacy_shell()

    # --- System Routes ---
    def record_evidence(entry: EvidenceEntry) -> None:
        interaction_id, attempt_id = _EVIDENCE_LINK.get()
        update: Dict[str, Any] = {"test_mode": test_mode}
        if interaction_id:
            update.update(interaction_id=interaction_id, attempt_id=attempt_id)
        repo.record_evidence(entry.model_copy(update=update))

    def now_ms() -> int:
        return int(clock().timestamp() * 1000)

    def log_event(
        learner_id: str,
        event_type: str,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        activity: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> None:
        """Append to the interaction log. A failed write is reported and never breaks learning."""
        try:
            moment = now_ms()
            repo.append_interaction(
                InteractionEvent(
                    interaction_id=interaction_id or new_ulid(moment),
                    learner_id=learner_id,
                    recorded_at_ms=moment,
                    event_type=event_type,
                    payload=clean_payload(payload),
                    session_id=session_id,
                    attempt_id=attempt_id,
                    unit_id=unit_id,
                    activity=activity,
                    item_id=item_id,
                    test_mode=test_mode,
                )
            )
        except Exception:
            logger.exception("Interaction log write failed.")

    @app.post("/api/v1/learners/me/interactions", status_code=204, response_model=None)
    def post_my_interaction(
        event: ClientEvent,
        learner_id: str = Depends(current_learner_id),
        session_id: Optional[str] = Depends(current_session),
    ):
        log_event(
            learner_id,
            event.event_type,
            event.payload.model_dump(exclude_none=True),
            session_id=session_id,
            interaction_id=event.interaction_id,
            unit_id=event.unit_id,
            activity=event.activity,
            item_id=event.item_id,
        )
        return None

    @app.get("/api/v1/learners/me/interactions", response_model=List[InteractionEvent])
    def get_my_interactions(
        limit: int = Query(1000, ge=1, le=10000), learner_id: str = Depends(current_learner_id)
    ):
        return repo.get_interactions(learner_id, limit)

    @app.get("/api/v1/health")
    def health_check() -> Dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/v1/features", response_model=Features)
    def get_features():
        return Features(test_mode=test_mode)

    # --- Concept Library (KMS) Routes ---
    @app.get("/api/v1/concepts", response_model=List[ConceptSummary])
    def get_concepts(
        q: Optional[str] = Query(None, max_length=MAX_CONCEPT_QUERY),
        search: Optional[str] = Query(None, max_length=MAX_CONCEPT_QUERY),
    ):
        query = (q or search or "").strip()
        return concepts.search(query) if query else concepts.list_all()

    def concept_not_found(concept_id: str) -> JSONResponse:
        return problem(404, "Concept not found", f"Concept '{concept_id}' does not exist.")

    @app.get("/api/v1/concepts/{concept_id}", response_model=ConceptDetail)
    def get_concept_by_id(concept_id: str):
        concept = concepts.get(concept_id)
        if not concept:
            return concept_not_found(concept_id)
        related = [concepts.get(slug) for slug in concept.related]
        return ConceptDetail(
            **concept.model_dump(exclude={"related"}),
            related=[ConceptRef(concept_id=c.concept_id, name=c.name) for c in related if c],
            used_in=used_in(concept, catalog.list_all_units()),
        )

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
        ledger = repo.get_evidence_ledger(learner_id)
        config = EstimatorConfig(main_activities=catalog.main_activities)
        return build_course_map(
            course_id,
            catalog.get_course_units(course_id),
            catalog.get_stage_titles(course_id),
            lambda unit_id: unit_cold_status(unit_id, learner_id, now).state,
            lambda unit: unit_decision(unit, ledger, now, config, repo.progress_resets(learner_id)),
            {
                stage: AuthoredBuild(build.title, build.kind, build.status, build.maturity)
                for (course, stage), build in catalog.builds.items()
                if course == course_id
            },
            {
                stage: review_status(course_id, stage, learner_id).state
                for stage in {u.stage for u in catalog.get_course_units(course_id)}
            },
            {
                u.stage
                for u in catalog.get_course_units(course_id)
                if spare_cold_items(u, catalog.seeds.get(u.unit_id, [])) > 0
            },
        )

    # --- Stage Builds (SPEC-15) ---
    def stage_units(course_id: str, stage: int) -> List[Unit]:
        return [u for u in catalog.get_course_units(course_id) if u.stage == stage]

    # --- Stage Review and Rechecks (SPEC-16) ---
    def review_status(course_id: str, stage: int, learner_id: str) -> StageReviewStatus:
        units = stage_units(course_id, stage)
        now = clock()
        pending = [
            u.unit_id
            for u in units
            if unit_cold_status(u.unit_id, learner_id, now).state
            != ColdCheckState.PASSED
        ]
        scope = stage_scope(course_id, stage)
        items = repo.get_review_items(learner_id, STAGE_REVIEW, scope)
        has_items = bool(items) or (
            not pending
            and bool(plan_stage_review(units, catalog.seeds, repo.get_all_seen_exercises(learner_id)))
        )
        result = repo.get_review_result(learner_id, STAGE_REVIEW, scope)
        return stage_review_status(pending, has_items, result, items, now, cold_config)

    def open_stage_round(course_id: str, stage: int, learner_id: str) -> List[ReviewItem]:
        """The stored round: made once, and after a fail its failed items are replaced."""
        scope = stage_scope(course_id, stage)
        items = repo.get_review_items(learner_id, STAGE_REVIEW, scope)
        seen = repo.get_all_seen_exercises(learner_id)
        if not items:
            repo.save_review_items(
                learner_id, STAGE_REVIEW, scope, plan_stage_review(stage_units(course_id, stage), catalog.seeds, seen)
            )
        elif all(i.passed is not None for i in items):
            for item in (i for i in items if i.passed is False):
                skill_seeds = [s for s in catalog.seeds.get(item.unit_id, []) if s.skill_id == item.skill_id]
                pool = pool_for(skill_seeds, COLD_CHECK)
                fresh = [e for e in pool if e not in seen] or [e for e in pool if e != item.exercise_id]
                replacement = fresh[0] if fresh else item.exercise_id
                repo.reopen_review_item(learner_id, STAGE_REVIEW, scope, item.position, replacement)
                seen = seen | {replacement}
        return repo.get_review_items(learner_id, STAGE_REVIEW, scope)

    def serve_review_item(items: List[ReviewItem], kind: str, learner_id: str) -> Optional[Exercise]:
        item = next((i for i in items if i.passed is None), None)
        if item is None:
            return None
        repo.set_current_exercise(learner_id, item.unit_id, kind, item.exercise_id, clock())
        return find_variant(catalog.seeds.get(item.unit_id, []), item.exercise_id)

    def attempt_review(attempt: Attempt, learner_id: str) -> Union[AttemptResult, JSONResponse]:
        kind = attempt.activity
        found = repo.find_open_review_item(learner_id, kind, attempt.exercise_id)
        not_current = problem(409, "Not your current exercise", "Fetch the current review item and try again.")
        if found is None:
            return not_current
        scope, item = found
        items = repo.get_review_items(learner_id, kind, scope)
        if next(i for i in items if i.passed is None).position != item.position:
            return not_current
        unit = catalog.get_unit(item.unit_id)
        variant = find_seed_variant(catalog.seeds.get(item.unit_id, []), attempt.exercise_id)
        if unit is None or variant is None:
            return problem(404, "Exercise not found", f"Exercise '{attempt.exercise_id}' does not exist.")

        seed, _ = variant
        graded = grade(seed, attempt, runner)
        now = clock()
        entry = EvidenceEntry(
            learner_id=learner_id,
            unit_id=item.unit_id,
            skill_id=seed.skill_id,
            evidence_category=ACTIVITY_EVIDENCE[seed.activity],
            evidence_strength=evidence_strength(seed.item_type, graded.passed, 0, AssistanceLevel.NONE, True),
            assistance_level=AssistanceLevel.NONE,
            demonstration_context=f"{seed.activity.value} {kind} on {attempt.exercise_id}",
            recorded_at=now,
            exercise_id=attempt.exercise_id,
            seed_id=seed.seed_id,
            activity=seed.activity,
            cold_check=True,
            review_kind=kind,
        )
        record_evidence(entry)
        repo.answer_review_item(learner_id, kind, scope, item.position, graded.passed)
        items = repo.get_review_items(learner_id, kind, scope)
        if all(i.passed is not None for i in items):
            repo.record_review_result(learner_id, kind, scope, all(i.passed for i in items), now)

        config = EstimatorConfig(main_activities=catalog.main_activities)
        return AttemptResult(
            outcome="passed" if graded.passed else "failed",
            feedback=graded.feedback,
            checks=graded.checks,
            score=graded.score,
            # A failed item can come back, so it must not show its answer.
            reveal=graded.reveal if graded.passed else None,
            evidence_entry_id=entry.entry_id,
            unit_decision=unit_decision(unit, repo.get_evidence_ledger(learner_id), now, config, repo.progress_resets(learner_id)),
        )

    def rechecks_due(learner_id: str) -> List[DueReview]:
        ledger = repo.get_evidence_ledger(learner_id)
        finished = repo.get_finished_reviews(learner_id, RECHECK)
        seen = repo.get_all_seen_exercises(learner_id)
        names = {s.skill_id: s.skill_name for u in catalog.list_all_units() for s in u.target_skills}
        due: List[DueReview] = []
        for review in due_reviews(ledger, finished, clock(), timing.recheck_days):
            stored = repo.get_review_items(
                learner_id, RECHECK, recheck_scope(review.skill_id, review.days)
            )
            count = len(stored or plan_recheck(review.skill_id, catalog.seeds, seen))
            if count:
                due.append(
                    review.model_copy(
                        update={"items": count, "skill_name": names.get(review.skill_id, review.skill_id)}
                    )
                )
        return due

    @app.get("/api/v1/learners/me/courses/{course_id}/stages/{stage}/review", response_model=StageReviewStatus)
    def get_my_stage_review(course_id: str, stage: int, learner_id: str = Depends(current_learner_id)):
        if course_id not in COURSES or not stage_units(course_id, stage):
            return problem(404, "Module not found", f"{course_id} has no module {stage}.")
        return review_status(course_id, stage, learner_id)

    @app.post("/api/v1/learners/me/courses/{course_id}/stages/{stage}/review:reset", status_code=204, response_model=None)
    def reset_my_stage_review(course_id: str, stage: int, learner_id: str = Depends(current_learner_id)):
        """Restart the stage review: its rounds and result go, the ledger stays (ADR-0016 amendment)."""
        if course_id not in COURSES or not stage_units(course_id, stage):
            return problem(404, "Module not found", f"{course_id} has no module {stage}.")
        repo.reset_stage_review(learner_id, stage_scope(course_id, stage), at=clock())
        log_event(learner_id, "reset", {"stage_review": stage_scope(course_id, stage)}, unit_id=scope_of(course_id, stage))
        return None

    @app.get(
        "/api/v1/learners/me/courses/{course_id}/stages/{stage}/review/exercise",
        response_model=Exercise,
        response_model_exclude_none=True,
    )
    def get_my_stage_review_exercise(
        course_id: str, stage: int, learner_id: str = Depends(current_learner_id)
    ):
        if course_id not in COURSES or not stage_units(course_id, stage):
            return problem(404, "Module not found", f"{course_id} has no module {stage}.")
        status = review_status(course_id, stage, learner_id)
        if status.state == ReviewState.PASSED:
            return problem(409, "Module review passed", "This module review is already passed.")
        if status.state == ReviewState.UNAVAILABLE:
            return problem(404, "No review yet", "This module has no review items yet.")
        if status.state != ReviewState.AVAILABLE:
            return problem(423, "Module review locked", f"Available at: {status.available_at}.")
        exercise = serve_review_item(open_stage_round(course_id, stage, learner_id), STAGE_REVIEW, learner_id)
        if exercise is None:
            return problem(404, "No review yet", "This module has no review items yet.")
        return exercise

    @app.get("/api/v1/learners/me/reviews/due", response_model=List[DueReview])
    def get_my_due_reviews(learner_id: str = Depends(current_learner_id)):
        return rechecks_due(learner_id)

    @app.get(
        "/api/v1/learners/me/reviews/{skill_id}/{days}/exercise",
        response_model=Exercise,
        response_model_exclude_none=True,
    )
    def get_my_recheck_exercise(skill_id: str, days: int, learner_id: str = Depends(current_learner_id)):
        not_due = problem(404, "Recheck not due", f"No {days}-day recheck is due for {skill_id}.")
        if not any(d.skill_id == skill_id and d.days == days for d in rechecks_due(learner_id)):
            return not_due
        scope = recheck_scope(skill_id, days)
        if not repo.get_review_items(learner_id, RECHECK, scope):
            seen = repo.get_all_seen_exercises(learner_id)
            repo.save_review_items(learner_id, RECHECK, scope, plan_recheck(skill_id, catalog.seeds, seen))
        exercise = serve_review_item(repo.get_review_items(learner_id, RECHECK, scope), RECHECK, learner_id)
        return exercise if exercise else not_due

    def open_build(course_id: str, stage: int, learner_id: str) -> Union[StageBuildSpec, JSONResponse]:
        """The build if this learner may have it, otherwise the problem to answer with."""
        units = stage_units(course_id, stage) if course_id in COURSES else []
        if not units:
            return problem(404, "Module not found", f"{course_id} has no module {stage}.")
        review = review_status(course_id, stage, learner_id)
        if not build_is_open(review.state):
            if review.pending_units:
                return problem(423, "Build locked", f"Pass the Cold Check in: {', '.join(review.pending_units)}.")
            return problem(423, "Build locked", "Pass the module review first.")
        build = catalog.builds.get((course_id, stage))
        if not build:
            return problem(404, "No build yet", f"The build for {stage_label(stage)} is not written yet.")
        return build

    def too_large(files: Dict[str, str], *notes: Optional[str]) -> bool:
        return sum(len(content) for content in files.values()) + sum(len(n or "") for n in notes) > MAX_DRAFT_CHARS

    @app.get("/api/v1/courses/{course_id}/stages/{stage}/build", response_model=StageBuild)
    def get_stage_build(course_id: str, stage: int, learner_id: str = Depends(current_learner_id)):
        build = open_build(course_id, stage, learner_id)
        if isinstance(build, JSONResponse):
            return build
        exercise_id = exercise_id_of(course_id, stage)
        scope = scope_of(course_id, stage)
        if repo.get_current_exercise(learner_id, scope, BUILD_ACTIVITY) is None:
            repo.set_current_exercise(learner_id, scope, BUILD_ACTIVITY, exercise_id, clock())
        ledger = repo.get_evidence_ledger(learner_id)
        return public_build(build, submitted=any(e.seed_id == exercise_id for e in ledger))

    @app.post(
        "/api/v1/learners/me/courses/{course_id}/stages/{stage}/build:check",
        response_model=BuildCheckResult,
    )
    def check_my_build(
        course_id: str,
        stage: int,
        payload: BuildCheckRequest,
        learner_id: str = Depends(current_learner_id),
    ):
        build = open_build(course_id, stage, learner_id)
        if isinstance(build, JSONResponse):
            return build
        if too_large(payload.files, payload.ownership_note, payload.review_note):
            return problem(413, "Build too large", f"A build is limited to {MAX_DRAFT_CHARS} characters.")
        results = check_requirements(
            build, payload.files, payload.ownership_note, runner, payload.run_checks, payload.review_note
        )
        log_event(
            learner_id, "verify",
            {"files": payload.files, "run_checks": payload.run_checks, "met": {r.id: r.met for r in results}},
            unit_id=scope_of(course_id, stage), activity=BUILD_ACTIVITY, item_id=exercise_id_of(course_id, stage),
        )
        return BuildCheckResult(requirements=results)

    @app.post(
        "/api/v1/learners/me/courses/{course_id}/stages/{stage}/build:draft-readme",
        response_model=DraftReadmeResult,
    )
    def draft_my_readme(
        course_id: str,
        stage: int,
        payload: DraftReadmeRequest,
        learner_id: str = Depends(current_learner_id),
    ):
        """AXIS drafts the README (SPEC-15 section 9.4, ADR-0028). Document help, so it is logged as a
        document_draft with no exercise id: it never counts as help on the build's code."""
        build = open_build(course_id, stage, learner_id)
        if isinstance(build, JSONResponse):
            return build
        if too_large(payload.files):
            return problem(413, "Build too large", f"A build is limited to {MAX_DRAFT_CHARS} characters.")
        if not hasattr(axis, "draft_readme"):
            return problem(503, "Draft unavailable", "Drafting is not available right now.")
        entry = next(f for f in build.files if f.path == build.entry)
        code = payload.files.get(build.entry, "\n".join(entry.starter))
        try:
            markdown, model = axis.draft_readme(build.entry, code, build.brief_markdown)
        except DraftFailed as failure:
            log_event(learner_id, "document_draft", {"course_id": course_id, "stage": stage, "status": "failed"})
            return problem(502, "Draft unavailable", str(failure))
        log_event(
            learner_id, "document_draft",
            {"course_id": course_id, "stage": stage, "status": "drafted", "model": model, "markdown": markdown},
        )
        return DraftReadmeResult(markdown=markdown, status="drafted", model=model)

    @app.post(
        "/api/v1/learners/me/courses/{course_id}/stages/{stage}/build:reset",
        status_code=204,
        response_model=None,
    )
    def reset_my_build(course_id: str, stage: int, learner_id: str = Depends(current_learner_id)):
        if course_id not in COURSES or not stage_units(course_id, stage):
            return problem(404, "Module not found", f"{course_id} has no module {stage}.")
        repo.reset_unit(learner_id, scope_of(course_id, stage), at=clock())
        return None

    def attempt_build(target: Tuple[str, int], attempt: Attempt, learner_id: str):
        course_id, stage = target
        build = open_build(course_id, stage, learner_id)
        if isinstance(build, JSONResponse):
            return build
        if attempt.activity != BUILD_ACTIVITY:
            return problem(422, "Unknown activity", "A build takes the 'build' activity.")
        files = attempt.files or {}
        if too_large(files, attempt.ownership_note, attempt.review_note):
            return problem(413, "Build too large", f"A build is limited to {MAX_DRAFT_CHARS} characters.")

        results = check_requirements(
            build, files, attempt.ownership_note, runner, run_checks=True, review_note=attempt.review_note
        )
        labels = {r.id: r.label for r in build.requirements}
        checks = [Check(label=labels[r.id], passed=bool(r.met), detail=r.detail) for r in results]
        met = sum(1 for check in checks if check.passed)
        passed = met == len(checks)

        exercise_id = exercise_id_of(course_id, stage)
        entries: List[EvidenceEntry] = []
        if passed:
            current = repo.get_current_exercise(learner_id, scope_of(course_id, stage), BUILD_ACTIVITY)
            served_at = current.served_at if current else datetime.min.replace(tzinfo=timezone.utc)
            assistance = highest_assistance(repo.get_assistance_levels(learner_id, exercise_id, served_at))
            for proof in build.proves:
                entry = EvidenceEntry(
                    learner_id=learner_id,
                    unit_id=proof.unit_id,
                    skill_id=proof.skill_id,
                    evidence_category=ACTIVITY_EVIDENCE[ActivityType.BUILD],
                    evidence_strength=evidence_strength(BUILD_ACTIVITY, True, 0, assistance, False),
                    assistance_level=assistance,
                    demonstration_context=f"Stage build {exercise_id}",
                    observed_reasoning=attempt.ownership_note,
                    review_note=attempt.review_note,
                    recorded_at=clock(),
                    exercise_id=exercise_id,
                    seed_id=exercise_id,
                    activity=ActivityType.BUILD,
                )
                record_evidence(entry)
                entries.append(entry)

        config = EstimatorConfig(main_activities=catalog.main_activities)
        return AttemptResult(
            outcome="passed" if passed else "failed",
            feedback="This build is in your ledger." if passed else "Some requirements are not met yet.",
            checks=checks,
            score=Score(passed=met, total=len(checks)),
            evidence_entry_id=entries[0].entry_id if entries else None,
            unit_decision=unit_decision(
                stage_units(course_id, stage)[0], repo.get_evidence_ledger(learner_id), clock(), config,
                repo.progress_resets(learner_id),
            ),
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
                    log_event(
                        current_learner_id(), "run",
                        {"files": files, "entry": entry, "exit_code": event.get("code"), "timed_out": event.get("timed_out")},
                        item_id=start.get("exercise_id"),
                    )
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
        title = citation_title(name)
        if title:
            return {"concept_id": name, "title": title, "doc_url": ""}
        concept = concepts.get(name) or next(iter(concepts.search(name)), None)
        if concept:
            return {"concept_id": concept.concept_id, "title": concept.name, "doc_url": concept.doc_url}
        return {"concept_id": name, "title": name, "doc_url": ""}

    def axis_query(query: AxisQuery, learner_id: str) -> AxisQuery:
        """The server sets the learner, and keeps AXIS Socratic on a build whatever was asked (SPEC-15)."""
        update: Dict[str, Any] = {"learner_id": learner_id}
        if parse_exercise_id(query.exercise_id or ""):
            update["mode"] = AxisMode.SOCRATIC
        return query.model_copy(update=update)

    @app.post("/api/v1/axis/stream", response_model=None)
    def stream_axis_reply(request: AxisStreamRequest, learner_id: str = Depends(current_learner_id)):
        if is_cold_check_exercise(request.exercise_id):
            return axis_blocked()
        query = axis_query(request, learner_id)

        def sse(event: str, data: Dict[str, Any]) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        def events() -> Iterator[str]:
            shown = set()
            said: List[str] = []
            try:
                for event, data in stream_axis(axis, query, guardrail, classifier):
                    if event == "token":
                        said.append(data.get("text", ""))
                    if event == "done":
                        log_event(
                            learner_id, "axis",
                            {"mode": query.mode.value, "question": query.user_prompt, "answer": "".join(said),
                             "assistance": data["assistance_level"]},
                            unit_id=query.unit_id, activity=query.current_activity, item_id=query.exercise_id,
                        )
                    if event == "citation":
                        citation = citation_for(data["name"])
                        if citation["title"] not in shown:
                            shown.add(citation["title"])
                            yield sse(event, citation)
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
        response = axis.consult(axis_query(query, learner_id))
        log_event(
            learner_id, "axis",
            {"mode": query.mode.value, "question": query.user_prompt, "answer": response.reply,
             "assistance": response.detected_assistance_level.value},
            unit_id=query.unit_id, activity=query.current_activity, item_id=query.exercise_id,
        )
        if query.exercise_id:
            repo.log_assistance(
                learner_id, query.exercise_id, response.detected_assistance_level, clock()
            )
        return response

    # --- CO-6 Concept Check & Mental Model Route ---
    @app.post("/api/v1/units/{unit_id}/quick-checks/{check_id}", response_model=QuickCheckResult)
    def check_quick_check(unit_id: str, check_id: str, payload: QuickCheckRequest):
        """Mark a quick check in an Explain part (SPEC-19 section 4). Practice only: no evidence."""
        unit = catalog.get_unit(unit_id.upper())
        if unit is None:
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        checks, _ = parse_quick_checks(unit.lesson_markdown or "")
        quick_check = next((c for c in checks if c.id == check_id), None)
        if quick_check is None:
            return problem(404, "Quick check not found", f"{unit.unit_id} has no quick check '{check_id}'.")
        if payload.choice not in quick_check.options:
            return problem(422, "Not an option", f"Choose one of {', '.join(quick_check.options)}.")
        key = load_quick_check_key(answers_dir_from_env(), unit.unit_id, check_id)
        if key is None or key.answer not in quick_check.options:
            return problem(503, "Quick check not available", "This quick check can't be marked here.")
        correct = payload.choice == key.answer
        return QuickCheckResult(correct=correct, why=key.why if correct else None)

    @app.post("/api/v1/explain", response_model=ExplainResponse)
    def evaluate_explanation(
        payload: ExplainRequest,
        learner_id: str = Depends(current_learner_id),
        session_id: Optional[str] = Depends(current_session),
    ):
        clean_unit = payload.unit_id.upper()
        unit = catalog.get_unit(clean_unit)
        rubric = load_rubric(answers_dir_from_env(), clean_unit)
        if rubric is None:
            judgement = not_judged("no_rubric")
        elif not hasattr(axis, "judge_explanation"):
            judgement = not_judged("ai_off")
        else:
            prompt = ((unit.concept_check_config or {}).get("prompt") if unit else None) or (
                unit.concept_line if unit else clean_unit
            )
            judgement = axis.judge_explanation(clean_unit, prompt, payload.explanation, rubric)

        interaction_id = new_ulid(now_ms())
        judgement = judgement.model_copy(update={"interaction_id": interaction_id})
        is_judged = judgement.status == "judged"
        writes = is_judged and ai_judgement.CONCEPT_CHECK_WRITES_EVIDENCE
        if writes:
            met = [i.id for i in judgement.ideas if i.met]
            missed = [i.id for i in judgement.ideas if not i.met]
            record_evidence(
                EvidenceEntry(
                    learner_id=learner_id,
                    unit_id=clean_unit,
                    skill_id="CO-6",
                    evidence_category=EvidenceCategory.EXPLAIN_REASON,
                    evidence_strength=EvidenceStrength.STRONG if judgement.verdict == "Solid" else EvidenceStrength.WEAK,
                    exercise_id=concept_check_id(clean_unit),
                    assistance_level=AssistanceLevel.NONE,
                    demonstration_context=f"CO-6 Concept Check for {clean_unit}, judged by {judgement.model}",
                    observed_reasoning=(
                        f"AI judged {judgement.verdict}. Ideas met: {', '.join(met) or 'none'}. "
                        f"Ideas missed: {', '.join(missed) or 'none'}."
                    ),
                    recorded_at=clock(),
                )
            )
        if unit:
            maybe_start_cold_check_clock(unit, learner_id)

        log_event(
            learner_id, "concept_check",
            {
                "explanation": payload.explanation,
                "status": judgement.verdict or "not_judged",
                "judged": is_judged,
                "reason": judgement.reason,
                "model": judgement.model,
                "ideas": [{"id": i.id, "met": i.met} for i in judgement.ideas],
            },
            session_id=session_id, interaction_id=interaction_id, unit_id=clean_unit, activity="explain",
        )
        return ExplainResponse(**judgement.model_dump(), unit_id=clean_unit, evidence_logged=bool(writes))

    @app.post("/api/v1/learners/me/judgements/{interaction_id}:dispute", status_code=204, response_model=None)
    def dispute_judgement(
        interaction_id: str,
        learner_id: str = Depends(current_learner_id),
        session_id: Optional[str] = Depends(current_session),
    ):
        """Log that the learner thinks a judgement is wrong (SPEC-18 section 6). Changes nothing else."""
        judged_event = next(
            (
                e for e in repo.get_interactions(learner_id, 10000)
                if e.interaction_id == interaction_id and e.event_type == "concept_check"
            ),
            None,
        )
        if judged_event is None:
            return problem(404, "Judgement not found", "No judgement with that id.")
        log_event(
            learner_id, "judgement_disputed", {"interaction_id": interaction_id},
            session_id=session_id, unit_id=judged_event.unit_id, activity=judged_event.activity,
        )
        return None

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
        resets = repo.progress_resets(learner_id)

        # My progress opens on the learner's current stage (owner decision, 2026-10-31).
        if stage is None and units:
            anchor = first_unfinished_unit(units, ledger, now, config, resets) or units[-1]
            stage = anchor.stage
            units = [u for u in units if course_of(u.unit_id) == course_of(anchor.unit_id)]
        if stage is not None:
            units = [u for u in units if u.stage == stage]

        return build_proficiency_view(
            units,
            ledger,
            lambda unit_id: unit_cold_status(unit_id, learner_id, now),
            now=now,
            stage=stage,
            config=config,
            unseen_activities=lambda unit: unseen_activities(unit, learner_id),
            resets=resets,
        )

    @app.get("/api/v1/learners/me/skills", response_model=SkillsOverview)
    def get_my_skills(learner_id: str = Depends(current_learner_id)):
        """Every framework skill once, by area, from the whole ledger (SPEC-12 section 6.1)."""
        return build_skills_overview(
            catalog.skill_names,
            catalog.list_all_units(),
            repo.get_evidence_ledger(learner_id),
            clock(),
            EstimatorConfig(main_activities=catalog.main_activities),
        )

    @app.get("/api/v1/learners/me/units/{unit_id}/cold-check/feedback", response_model=ColdCheckFeedback)
    def get_my_cold_check_feedback(unit_id: str, learner_id: str = Depends(current_learner_id)):
        """Each item of the round, the learner's own answer, and what to revisit (ADR-0022 section 2.5)."""
        unit = catalog.get_unit(unit_id)
        if not unit:
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        answers: Dict[str, Dict[str, Any]] = {}
        for event in repo.get_interactions(learner_id, 10000):  # Newest first, so the first one wins.
            if event.event_type == "answer_submitted" and event.activity == COLD_CHECK and event.unit_id == unit_id:
                if event.item_id and "outcome" in event.payload:
                    answers.setdefault(event.item_id, event.payload.get("answer") or {})
        return cold_check_feedback(
            unit, catalog.seeds.get(unit_id, []), repo.get_evidence_ledger(learner_id), answers, catalog.main_activities
        )

    @app.get("/api/v1/learners/me/units/{unit_id}/cold-check", response_model=ColdCheckStatus)
    def get_my_cold_check(unit_id: str, learner_id: str = Depends(current_learner_id)):
        if not catalog.get_unit(unit_id):
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        return unit_cold_status(unit_id, learner_id, clock())

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
        status = unit_cold_status(unit_id, learner_id, clock())
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
        pending = [s for s in cold_round(unit, seeds) if s.seed_id not in finished]
        return pool_for(pending[:1], COLD_CHECK)

    def maybe_start_cold_check_clock(unit: Unit, learner_id: str) -> None:
        if activities_attempted(unit, repo.get_evidence_ledger(learner_id), repo.progress_resets(learner_id).get(unit.unit_id)):
            repo.mark_unit_activities_completed(learner_id, unit.unit_id, clock())

    def unit_cold_status(unit_id: str, learner_id: str, now: Optional[datetime] = None) -> ColdCheckStatus:
        """The Cold Check status; starts a missing clock when the activities are already done.

        An old reset (before reset markers) could clear the record after every activity was done,
        and then no new event restarted the clock (owner's PY-0.3, 2026-11-11).
        """
        timer = repo.get_cold_check_timer(learner_id, unit_id)
        unit = catalog.get_unit(unit_id)
        if timer is None and unit is not None:
            maybe_start_cold_check_clock(unit, learner_id)
            timer = repo.get_cold_check_timer(learner_id, unit_id)
        return cold_check_status(timer, now or clock(), cold_config)

    def finish_cold_item(unit: Unit, seed: ExerciseSeed, passed: bool, learner_id: str) -> None:
        now = clock()
        repo.record_cold_item(learner_id, unit.unit_id, seed.seed_id, passed, now)
        repo.clear_current_exercise(learner_id, unit.unit_id, COLD_CHECK)
        items = repo.get_cold_items(learner_id, unit.unit_id)
        required = [s.seed_id for s in cold_round(unit, catalog.seeds.get(unit.unit_id, []))]
        if all(seed_id in items for seed_id in required):
            round_passed = all(items[seed_id] for seed_id in required)
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
            # An attempted item is not served again by default (SPEC-12 section 4).
            if activity == COLD_CHECK or not attempted_since_served(current, learner_id):
                return find_variant(seeds, current.exercise_id)
        seen = repo.get_seen_exercises(learner_id, unit.unit_id, activity)
        return serve(unit, activity, choose_next(pool, seen, current.exercise_id if current else None), learner_id)

    def attempted_since_served(current, learner_id: str) -> bool:
        return any(
            e.exercise_id == current.exercise_id and e.recorded_at >= current.served_at
            for e in repo.get_evidence_ledger(learner_id)
        )

    def unseen_activities(unit: Unit, learner_id: str) -> List[str]:
        """Practice activities of the unit that still have an item this learner has not seen."""
        seeds = catalog.seeds.get(unit.unit_id, [])
        return [
            m.slug
            for m in unit.methods
            if m != ActivityType.EXPLAIN
            and set(pool_for(seeds, m.slug)) - set(repo.get_seen_exercises(learner_id, unit.unit_id, m.slug))
        ]

    def known_exercise(exercise_id: str) -> Optional[str]:
        """The unit an exercise id belongs to, if it is a real exercise."""
        build_target = parse_exercise_id(exercise_id)
        if build_target in catalog.builds:
            return scope_of(*build_target)
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
        log_event(learner_id, "regenerate", {"served": next_id}, unit_id=unit_id, activity=activity, item_id=next_id)
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
        result = check_playground(unit, payload.code)
        log_event(
            learner_id, "verify", {"code": payload.code, "passed": result.success},
            unit_id=unit_id, activity="playground",
        )
        return result

    @app.post(
        "/api/v1/learners/me/attempts",
        response_model=AttemptResult,
        response_model_exclude_none=True,
    )
    def post_my_attempt(
        attempt: Attempt,
        learner_id: str = Depends(current_learner_id),
        session_id: Optional[str] = Depends(current_session),
    ):
        """Every answer is logged exactly and linked to its evidence (ADR-0022)."""
        link_id = attempt.interaction_id or new_ulid(now_ms())
        try:
            attempt_id, unit_id = locate_attempt(attempt, learner_id)
        except Exception:
            logger.exception("Could not place the attempt.")
            attempt_id, unit_id = None, None
        token = _EVIDENCE_LINK.set((link_id, attempt_id))
        try:
            result, replayed = submit_attempt(attempt, learner_id)
        finally:
            _EVIDENCE_LINK.reset(token)
        if replayed:
            return result
        answer = attempt.model_dump(exclude_none=True, exclude={"exercise_id", "activity", "interaction_id"})
        if isinstance(result, JSONResponse):
            body = json.loads(result.body)
            payload = {"answer": answer, "status": result.status_code, "detail": body.get("detail")}
            logged_id = None  # A refused answer keeps its id free to be sent again.
        else:
            payload = {
                "answer": answer,
                "outcome": result.outcome,
                "score": result.score.model_dump() if result.score else None,
                "evidence_entry_id": result.evidence_entry_id,
            }
            logged_id = link_id
        log_event(
            learner_id, "answer_submitted", payload, session_id=session_id, interaction_id=logged_id,
            attempt_id=attempt_id, unit_id=unit_id, activity=attempt.activity, item_id=attempt.exercise_id,
        )
        return result

    def locate_attempt(attempt: Attempt, learner_id: str) -> Tuple[Optional[str], Optional[str]]:
        """The attempt id and unit of an answer, read before it is graded (ADR-0022 section 2.2)."""
        if attempt.activity in (STAGE_REVIEW, RECHECK):
            found = repo.find_open_review_item(learner_id, attempt.activity, attempt.exercise_id)
            return (f"{attempt.activity}/{found[0]}", found[1].unit_id) if found else (None, None)
        target = parse_exercise_id(attempt.exercise_id)
        if target:
            scope = scope_of(*target)
            current = repo.get_current_exercise(learner_id, scope, BUILD_ACTIVITY)
            return (f"{attempt.exercise_id}@{current.served_at.isoformat()}" if current else None), scope
        unit_id = known_exercise(attempt.exercise_id)
        if not unit_id:
            return None, None
        if attempt.activity == COLD_CHECK:
            timer = repo.get_cold_check_timer(learner_id, unit_id)
            if timer is None:
                return None, unit_id
            retry = timer.last_attempt_passed is False and timer.last_attempt_at is not None
            start = timer.last_attempt_at if retry else timer.completed_at
            return f"{unit_id}/cold_check@{start.isoformat()}", unit_id
        current = repo.get_current_exercise(learner_id, unit_id, attempt.activity)
        return (f"{current.exercise_id}@{current.served_at.isoformat()}" if current else None), unit_id

    def submit_attempt(attempt: Attempt, learner_id: str) -> Tuple[Any, bool]:
        """Idempotent per interaction_id (SPEC-12 section 5). True when a stored result is replayed."""
        key = attempt.interaction_id
        if key is None:
            return handle_attempt(attempt, learner_id), False
        if not repo.claim_interaction(learner_id, key, clock()):
            stored = repo.get_interaction_response(learner_id, key)
            if stored is None:
                return problem(409, "Already submitted", "This answer is still being checked."), True
            return JSONResponse(json.loads(stored)), True
        try:
            result = handle_attempt(attempt, learner_id)
        except Exception:
            repo.release_interaction(learner_id, key)
            raise
        if isinstance(result, JSONResponse):
            repo.release_interaction(learner_id, key)  # A refused attempt can be sent again.
            return result, False
        repo.finish_interaction(learner_id, key, result.model_dump_json(exclude_none=True))
        return result, False

    def handle_attempt(attempt: Attempt, learner_id: str):
        if attempt.activity in (STAGE_REVIEW, RECHECK):
            return attempt_review(attempt, learner_id)
        build_target = parse_exercise_id(attempt.exercise_id)
        if build_target:
            return attempt_build(build_target, attempt, learner_id)
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
                unit_decision=unit_decision(unit, ledger, clock(), config, repo.progress_resets(learner_id)),
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
        record_evidence(entry)

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
            unit_decision=unit_decision(unit, repo.get_evidence_ledger(learner_id), clock(), config, repo.progress_resets(learner_id)),
        )

    @app.get("/api/v1/learners/me/concepts/recent", response_model=List[ConceptSummary])
    def get_my_recent_concepts(learner_id: str = Depends(current_learner_id)):
        found = [concepts.get(slug) for slug in repo.get_recent_concepts(learner_id)]
        return [concept for concept in found if concept]

    @app.put("/api/v1/learners/me/concepts/recent/{concept_id}", status_code=204, response_model=None)
    def put_my_recent_concept(concept_id: str, learner_id: str = Depends(current_learner_id)):
        if not concepts.get(concept_id):
            return concept_not_found(concept_id)
        repo.record_concept_opened(learner_id, concept_id)
        return None

    @app.post("/api/v1/learners/me/units/{unit_id}/reset", status_code=204, response_model=None)
    def reset_my_unit(unit_id: str, learner_id: str = Depends(current_learner_id)):
        if not catalog.get_unit(unit_id):
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        repo.reset_unit(learner_id, unit_id, at=clock())
        log_event(learner_id, "reset", {}, unit_id=unit_id)
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

    # --- Frontend (ADR-0014): built files, then the app for client-side routes ---
    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str):
        if path.startswith("api/"):
            return problem(404, "Not found", f"No route for /{path}.")
        candidate = (dist / path).resolve()
        if candidate.is_relative_to(dist) and candidate.is_file():
            return FileResponse(candidate)
        index_file = dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return problem(404, "Not found", f"No route for /{path}.")

    return app


# Default ASGI application instance for uvicorn
app = create_app()
