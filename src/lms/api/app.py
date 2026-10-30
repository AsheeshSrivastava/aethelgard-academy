"""FastAPI Production LMS Platform Gateway.

Provides versioned REST endpoints (/api/v1/) for:
- Curriculum catalog exploration
- Untrusted code execution in the hardened sandbox
- AXIS AI pedagogical companion (Coach, Hybrid, Socratic)
- Evidence Ledger queries and progress persistence
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lms.adapters.ai.local_llm_companion import get_axis_companion
from lms.adapters.ai.mock_axis import MockAxisCompanion
from lms.adapters.curriculum.concepts import ConceptCatalog
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
from lms.core.models import (
    AssistanceLevel,
    ConceptItem,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
    Unit,
)


class ExecuteCodeRequest(BaseModel):
    code: str
    test_code: Optional[str] = None
    timeout_seconds: float = 5.0


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

    if concepts is None:
        concepts = ConceptCatalog()

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
