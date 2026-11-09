# Specification 02: Curriculum Ingestion & Catalog Specification

- **Status:** Accepted (2026-11-09, by the owner, as built). Was a draft.
- **Governed By:** 
  - `Python Subject Roadmap v3.md` (28 units across 13 stages)
  - `AI Engineering Roadmap v2.md`
  - `Learning Method v2` (10 activities, CO-6 soft gate)
  - `Proficiency & Progression System v1` (4 proficiency levels)
- **Domain:** Curriculum Parser, Dependency Graph & Unit Catalog
- **Date:** 2026-10-30

---

## 1. Purpose & Architectural Context

This specification defines the contract and mechanics for the **Curriculum Ingestion Engine** and **Curriculum Catalog**.

The platform does not hardcode lessons in application code. Instead:
1. Canonical curricula are defined in structured Markdown specifications (`reference/`).
2. The Ingestion Engine parses these specifications into strongly-typed `Unit` domain entities.
3. The Catalog organizes units into a validated **Directed Acyclic Graph (DAG)** of prerequisites.
4. The Catalog exposes query methods for unit retrieval, stage sequencing, and prerequisite validation.

---

## 2. Ingestion Data Contract & Grammar

### 2.1 Unit Markdown Section Grammar
Each unit in `## Unit details` matches the following canonical structure:

```markdown
#### <UNIT_ID> <TITLE> [(metadata)]

- **Objective:** <OBJECTIVE_TEXT>
- **The concept (Explain):** <CONCEPT_TEXT>
- **Target skills:** <SKILL_TARGETS_LIST>
- **Methods:** <METHODS_CHAIN>
- **Outcome (measured at unit end):** <OUTCOME_TEXT>
- **Topics:** <TOPICS_LIST>
- **Prerequisites:** <PREREQUISITES_STRING> | **Importance:** <IMPORTANCE> | **Integration link:** <LINK>
```

### 2.2 Target Skills Parsing Rules
- Target skills list format: `<SKILL_ID> to <LEVEL>[; <SKILL_ID> to <LEVEL>]...`
- Examples:
  - `CO-1 to Understand; VE-4 to Understand`
  - `CO-1 to Apply; CO-2 to Apply; CO-6 to Apply`
- Target skills are converted to `List[TargetSkill]` with `goal_level` matching `ProficiencyLevel`.

### 2.3 Methods Parsing Rules
- Methods chain format: `<Activity1> → <Activity2>[ → <Activity3>]...`
- Arrows can be `→` (`\u2192`) or `->`.
- Example: `Explain → Predict → Debug & Validate` $\longrightarrow$ `[ActivityType.EXPLAIN, ActivityType.PREDICT, ActivityType.DEBUG_VALIDATE]`.
- Rule: Every unit MUST begin with `ActivityType.EXPLAIN`.

### 2.4 Prerequisites Parsing Rules
- Prerequisites string format: `<Prereq1>[, <Prereq2>]` or `None`.
- Examples:
  - `None` $\longrightarrow$ `[]`
  - `PY-0.4` $\longrightarrow$ `["PY-0.4"]`
  - `PY-1.2, PY-1.7` $\longrightarrow$ `["PY-1.2", "PY-1.7"]`

---

## 3. Curriculum Catalog Interface (`ICurriculumCatalog`)

```python
from typing import List, Optional, Protocol, Dict
from lms.core.models import Unit

class ICurriculumCatalog(Protocol):
    """Port for querying the ingested curriculum catalog and dependency graph."""

    def get_unit(self, unit_id: str) -> Optional[Unit]: ...
    def list_all_units(self) -> List[Unit]: ...
    def get_stage_units(self, stage: int) -> List[Unit]: ...
    def get_prerequisites(self, unit_id: str) -> List[Unit]: ...
    def validate_dag(self) -> bool: ...
```

---

## 4. Non-Functional Requirements (NFRs)

1. **Sub-100ms Ingestion:**  
   Parsing the full 1,000+ line roadmap into in-memory `Unit` objects must execute in $< 100$ms.
2. **DAG Validation (Acyclic Integrity):**  
   The catalog must verify that no circular prerequisite dependencies exist (e.g. A $\rightarrow$ B $\rightarrow$ A).
3. **Graceful Degraded Parsing:**  
   If an optional metadata field is omitted in a unit draft, the parser provides sensible defaults rather than crashing.

---

## 5. Edge Cases & Falsification Matrix

1. **Unknown Skill IDs or Levels:** Malformed skill strings must raise a structured `CurriculumParseError` pointing to the exact unit ID.
2. **Missing Prerequisite Target:** If a unit references a non-existent prerequisite ID (e.g., `PY-99.9`), DAG validation raises an error.
3. **Empty or Missing Unit Sections:** The parser must skip non-unit commentary without dropping valid units.
