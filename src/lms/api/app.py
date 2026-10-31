"""FastAPI Production LMS Platform Gateway.

Provides versioned REST endpoints (/api/v1/) for:
- Curriculum catalog exploration
- Untrusted code execution in the hardened sandbox
- AXIS AI pedagogical companion (Coach, Hybrid, Socratic)
- Evidence Ledger queries and progress persistence
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lms.adapters.ai.local_llm_companion import get_axis_companion
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.concepts import ConceptCatalog
from lms.adapters.curriculum.loader import CurriculumCatalog, load_all_roadmaps
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.docker_runner import get_code_runner
from lms.core.cold_check import ColdCheckStatus, cold_check_status
from lms.core.course_map import (
    COURSES,
    Course,
    CourseMap,
    build_course,
    build_course_map,
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
    Unit,
)
from lms.core.proficiency_view import ProficiencyView, build_proficiency_view

logger = logging.getLogger(__name__)

LOCAL_LEARNER_ID = "default_learner"

# The Vite dev server. The built frontend is served from this app's own origin.
DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


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
    learner_id: str = "default_learner"


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
        return unit

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

    # --- AXIS AI Companion Routes ---
    @app.post("/api/v1/axis/consult", response_model=AxisResponse)
    def consult_axis(query: AxisQuery):
        return axis.consult(query)

    # --- CO-6 Concept Check & Mental Model Route ---
    @app.post("/api/v1/explain", response_model=ExplainResponse)
    def evaluate_explanation(payload: ExplainRequest):
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
            learner_id=payload.learner_id,
            unit_id=clean_unit,
            skill_id="CO-6",
            evidence_category=EvidenceCategory.EXPLAIN_REASON,
            evidence_strength=EvidenceStrength.STRONG if is_solid else EvidenceStrength.WEAK,
            assistance_level=AssistanceLevel.NONE,
            demonstration_context=f"CO-6 Concept Check for {clean_unit}",
            observed_reasoning=f"Mental model evaluated as {status}: {feedback}",
        )
        repo.record_evidence(entry)

        return ExplainResponse(
            unit_id=clean_unit,
            status=status,
            feedback=feedback,
            evidence_logged=True,
        )

    # --- Socratic Error Diagnostic Route ---
    @app.post("/api/v1/explain-error")
    def explain_runtime_error(payload: Dict[str, Any]):
        unit_id = payload.get("unit_id", "PY-0.1").upper()
        code = payload.get("code", "")
        error_msg = payload.get("error", "")
        query = AxisQuery(
            learner_id=payload.get("learner_id", "default_learner"),
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
        if stage is not None:
            units = [u for u in units if u.stage == stage]

        now = clock()
        return build_proficiency_view(
            units,
            repo.get_evidence_ledger(learner_id),
            lambda unit_id: cold_check_status(repo.get_cold_check_timer(learner_id, unit_id), now),
            now=now,
        )

    @app.get("/api/v1/learners/me/units/{unit_id}/cold-check", response_model=ColdCheckStatus)
    def get_my_cold_check(unit_id: str, learner_id: str = Depends(current_learner_id)):
        if not catalog.get_unit(unit_id):
            return problem(404, "Unit not found", f"Unit '{unit_id}' does not exist.")
        return cold_check_status(repo.get_cold_check_timer(learner_id, unit_id), clock())

    # --- Learner Progress & Evidence Ledger Routes ---
    @app.get("/api/v1/learners/{learner_id}/ledger", response_model=List[EvidenceEntry])
    def get_ledger(learner_id: str, skill_id: Optional[str] = Query(None)):
        return repo.get_evidence_ledger(learner_id=learner_id, skill_id=skill_id)

    @app.post("/api/v1/learners/{learner_id}/progress")
    def update_progress(learner_id: str, payload: ProgressUpdateRequest):
        repo.save_unit_progress(
            learner_id=learner_id, unit_id=payload.unit_id, status=payload.status
        )
        return {"success": True, "learner_id": learner_id, "unit_id": payload.unit_id}

    return app


# Default ASGI application instance for uvicorn
app = create_app()
