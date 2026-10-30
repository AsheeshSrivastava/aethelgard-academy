"""FastAPI Production LMS Platform Gateway.

Provides versioned REST endpoints (/api/v1/) for:
- Curriculum catalog exploration
- Untrusted code execution in the hardened sandbox
- AXIS AI pedagogical companion (Coach, Hybrid, Socratic)
- Evidence Ledger queries and progress persistence
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lms.adapters.ai.local_llm_companion import get_axis_companion
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.loader import CurriculumCatalog, load_roadmap_from_file
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository
from lms.adapters.runner.docker_runner import get_code_runner
from lms.core.interfaces import (
    AxisMode,
    AxisQuery,
    AxisResponse,
    ExecutionResult,
    IAXISCompanion,
    ICodeRunner,
    ILearnerRepository,
)
from lms.core.models import EvidenceEntry, Unit


class ExecuteCodeRequest(BaseModel):
    code: str
    test_code: Optional[str] = None
    timeout_seconds: float = 5.0


class ProgressUpdateRequest(BaseModel):
    unit_id: str
    status: str


def create_app(
    repo: Optional[ILearnerRepository] = None,
    runner: Optional[ICodeRunner] = None,
    axis: Optional[IAXISCompanion] = None,
    catalog: Optional[CurriculumCatalog] = None,
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
        roadmap_path = Path("reference/Python Subject Roadmap v3.md")
        if roadmap_path.exists():
            catalog = load_roadmap_from_file(roadmap_path)
        else:
            catalog = CurriculumCatalog()

    app = FastAPI(
        title="LMS / KMS Production Platform Gateway",
        description="Capability-based adaptive learning platform API",
        version="0.1.0",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- System Routes ---
    @app.get("/api/v1/health")
    def health_check() -> Dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    # --- Curriculum Routes ---
    @app.get("/api/v1/units", response_model=List[Dict[str, Any]])
    def list_units(stage: Optional[int] = Query(None, description="Filter by stage number")):
        units = catalog.get_stage_units(stage) if stage is not None else catalog.list_all_units()
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

    # --- Code Execution Sandbox Routes ---
    @app.post("/api/v1/execute", response_model=ExecutionResult)
    def execute_code(payload: ExecuteCodeRequest):
        return runner.execute(
            code=payload.code,
            test_code=payload.test_code,
            timeout_seconds=payload.timeout_seconds,
        )

    # --- AXIS AI Companion Routes ---
    @app.post("/api/v1/axis/consult", response_model=AxisResponse)
    def consult_axis(query: AxisQuery):
        return axis.consult(query)

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
