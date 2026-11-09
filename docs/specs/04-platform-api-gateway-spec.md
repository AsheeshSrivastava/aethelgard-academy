# Specification 04: LMS Platform API Gateway Specification

- **Status:** Accepted (2026-11-09, by the owner, as built). Was a draft.
- **Governed By:** 
  - `docs/specs/01-lesson-and-curriculum-spec.md` (Domain Schemas & Ports)
  - `docs/specs/02-curriculum-ingestion-and-catalog-spec.md` (Unit Catalog)
  - `docs/specs/03-code-runner-and-sandbox-spec.md` (Execution Sandbox)
  - `ADR-0001: Hexagonal Architecture and Pluggable Boundary Ports`
- **Domain:** Production HTTP REST API Gateway
- **Date:** 2026-10-30

---

## 1. Purpose & Architectural Context

The **FastAPI LMS Platform Gateway** exposes the core platform capabilities to web browsers, mobile clients, and local CLI tools over a clean, versioned REST API (`/api/v1/`).

It orchestrates:
1. Serving the canonical curriculum catalog (290 units across the three courses; ADR-0020).
2. Routing untrusted code execution to the hardened sandbox (`ICodeRunner`).
3. Interacting with the AXIS AI Companion in tri-modal operation (`Coach`, `Hybrid`, `Socratic`).
4. Querying and updating the append-only **Evidence Ledger** and learner progression state.

---

## 2. API Endpoints Contract

### 2.1 System & Curriculum Routes
* `GET /api/v1/health`
  * Response: `{"status": "ok", "version": "0.1.0"}`
* `GET /api/v1/units`
  * Query parameters: `stage: Optional[int]`
  * Response: `List[UnitSummary]`
* `GET /api/v1/units/{unit_id}`
  * Response: Full `Unit` domain model or 404.

### 2.2 Execution Sandbox Route
* `POST /api/v1/execute`
  * Request Body:
    ```json
    {
      "code": "print('hello')",
      "test_code": "assert True",
      "timeout_seconds": 5.0
    }
    ```
  * Response: `ExecutionResult` schema.

### 2.3 AXIS AI Companion Route
* `POST /api/v1/axis/consult`
  * Request Body: `AxisQuery` schema (`learner_id`, `unit_id`, `mode`, `current_activity`, `user_prompt`, `learner_code`).
  * Response: `AxisResponse` schema (`reply`, `suggested_action`, `cited_concepts`, `detected_assistance_level`).

### 2.4 Learner Evidence & Progress Routes
* `GET /api/v1/learners/{learner_id}/ledger`
  * Query parameters: `skill_id: Optional[str]`
  * Response: `List[EvidenceEntry]`
* `POST /api/v1/learners/{learner_id}/progress`
  * Request Body: `{"unit_id": "PY-0.4", "status": "Completed"}`
  * Response: `{"success": true, "updated_at": "..."}`

---

## 3. Non-Functional Requirements (NFRs)

1. **Sub-50ms API Latency:** Catalog retrieval and health endpoints must respond in $< 50$ms.
2. **CORS & OpenAPI Documentation:** Automatic interactive OpenAPI documentation available at `/docs` with configurable CORS origins.
3. **Structured Error Handling:** All errors return standard JSON payloads `{"detail": "..."}` with correct HTTP status codes (400, 404, 422, 500).
