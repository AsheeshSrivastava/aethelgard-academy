"""Curriculum Ingestion Engine and Catalog.

Parses Markdown roadmaps (such as Python Subject Roadmap v3) into strongly-typed
Unit domain models and validates the Directed Acyclic Graph (DAG) of prerequisites.
"""

from pathlib import Path
import json
import re
from typing import Dict, List, Optional, Set

from lms.core.models import ActivityType, MediaAsset, ProficiencyLevel, TargetSkill, Unit


def parse_skills_string(text: str) -> List[TargetSkill]:
    """Parse skill string like: 'CO-1 to Understand; VE-4 to Understand'"""
    targets: List[TargetSkill] = []
    # Split by semicolon or comma
    items = [item.strip() for item in text.split(";") if item.strip()]
    for item in items:
        # Match '<SKILL_ID> to <LEVEL>'
        match = re.match(r"([A-Z]{2}-[\d.]+)\s+to\s+([A-Za-z]+)", item)
        if match:
            skill_id, level_str = match.groups()
            try:
                level = ProficiencyLevel(level_str.capitalize())
            except ValueError:
                level = ProficiencyLevel.UNDERSTAND

            targets.append(
                TargetSkill(
                    skill_id=skill_id,
                    skill_name=skill_id,
                    goal_level=level,
                )
            )
    return targets


def parse_methods_string(text: str) -> List[ActivityType]:
    """Parse methods string like: 'Explain → Predict → Debug & Validate'"""
    # Replace unicode arrow or ascii arrow with standard delimiter
    normalized = text.replace("→", "->")
    tokens = [t.strip() for t in normalized.split("->") if t.strip()]
    methods: List[ActivityType] = []

    activity_map = {
        "explain": ActivityType.EXPLAIN,
        "predict": ActivityType.PREDICT,
        "trace": ActivityType.TRACE,
        "specify": ActivityType.SPECIFY,
        "decompose": ActivityType.DECOMPOSE,
        "modify": ActivityType.MODIFY,
        "debug & validate": ActivityType.DEBUG_VALIDATE,
        "debug and validate": ActivityType.DEBUG_VALIDATE,
        "build": ActivityType.BUILD,
        "evaluate": ActivityType.EVALUATE,
        "direct": ActivityType.DIRECT,
    }

    for token in tokens:
        cleaned = token.lower()
        if cleaned in activity_map:
            methods.append(activity_map[cleaned])

    if not methods or methods[0] != ActivityType.EXPLAIN:
        # Enforce canonical rule: Explain is always first
        if ActivityType.EXPLAIN not in methods:
            methods.insert(0, ActivityType.EXPLAIN)

    return methods


def parse_prerequisites_string(text: str) -> List[str]:
    """Parse prerequisites like 'None' or 'PY-0.4' or 'PY-1.2, PY-1.7'"""
    cleaned = text.strip()
    if not cleaned or cleaned.lower() == "none":
        return []

    # Strip any trailing importance notes if pipe is present
    if "|" in cleaned:
        cleaned = cleaned.split("|")[0].strip()

    prereqs: List[str] = []
    for part in cleaned.split(","):
        p = part.strip()
        if p and p.lower() != "none":
            prereqs.append(p)
    return prereqs


def parse_unit_block(block: str, stage: int = 0) -> Unit:
    """Parse a single markdown unit block starting with '#### PY-...'"""
    lines = [line.strip() for line in block.strip().split("\n") if line.strip()]

    # First line: #### <UNIT_ID> <TITLE> [(metadata)]
    header = lines[0].lstrip("#").strip()
    header_match = re.match(r"(PY-[\d.]+)\s+(.*?)(?:\s+\(.*?\))?$", header)
    if header_match:
        unit_id, title = header_match.groups()
    else:
        parts = header.split(" ", 1)
        unit_id = parts[0]
        title = parts[1] if len(parts) > 1 else unit_id

    # Strip trailing annotations like (new unit)
    title = re.sub(r"\s+\(.*?\)$", "", title).strip()

    concept_line = ""
    target_skills: List[TargetSkill] = []
    methods: List[ActivityType] = [ActivityType.EXPLAIN]
    prerequisites: List[str] = []

    for line in lines[1:]:
        if line.startswith("- **The concept (Explain):**"):
            concept_line = line.split("**The concept (Explain):**", 1)[1].strip()
        elif line.startswith("- **Target skills:**"):
            skills_part = line.split("**Target skills:**", 1)[1].strip()
            target_skills = parse_skills_string(skills_part)
        elif line.startswith("- **Methods:**"):
            methods_part = line.split("**Methods:**", 1)[1].strip()
            methods = parse_methods_string(methods_part)
        elif line.startswith("- **Prerequisites:**"):
            prereqs_part = line.split("**Prerequisites:**", 1)[1].strip()
            prerequisites = parse_prerequisites_string(prereqs_part)

    if not concept_line:
        concept_line = f"Core concepts of {title}"

    return Unit(
        unit_id=unit_id,
        title=title,
        stage=stage,
        concept_line=concept_line,
        target_skills=target_skills,
        methods=methods,
        prerequisites=prerequisites,
    )


class CurriculumCatalog:
    """In-memory catalog of parsed curriculum units with DAG validation."""

    def __init__(self) -> None:
        self._units: Dict[str, Unit] = {}

    def add_unit(self, unit: Unit) -> None:
        self._units[unit.unit_id] = unit

    def get_unit(self, unit_id: str) -> Optional[Unit]:
        return self._units.get(unit_id)

    def list_all_units(self) -> List[Unit]:
        return list(self._units.values())

    def get_stage_units(self, stage: int) -> List[Unit]:
        return [u for u in self._units.values() if u.stage == stage]

    def validate_dag(self) -> bool:
        """Verify that the prerequisite graph is a valid Directed Acyclic Graph."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(u_id: str) -> bool:
            visited.add(u_id)
            rec_stack.add(u_id)

            unit = self._units.get(u_id)
            if unit:
                for prereq_id in unit.prerequisites:
                    if prereq_id not in visited:
                        if has_cycle(prereq_id):
                            return True
                    elif prereq_id in rec_stack:
                        return True

            rec_stack.remove(u_id)
            return False

        for unit_id in self._units:
            if unit_id not in visited:
                if has_cycle(unit_id):
                    return False
        return True


def load_roadmap_from_file(file_path: Path) -> CurriculumCatalog:
    """Parse an entire markdown roadmap file and populate a CurriculumCatalog."""
    content = file_path.read_text(encoding="utf-8")
    catalog = CurriculumCatalog()

    current_stage = 0
    # Split content by markdown headers
    stage_sections = re.split(r"\n###\s+Stage\s+(\d+)", content)

    # First section contains pre-stage content
    for i in range(1, len(stage_sections), 2):
        stage_num = int(stage_sections[i])
        stage_body = stage_sections[i + 1]

        # Find unit blocks starting with #### PY-
        unit_blocks = re.split(r"\n(?=####\s+PY-)", stage_body)
        for block in unit_blocks:
            if block.strip().startswith("#### PY-"):
                unit = parse_unit_block(block, stage=stage_num)
                catalog.add_unit(unit)

    curriculum_path = Path("curriculum")
    if curriculum_path.exists():
        overlay_curriculum_packages(catalog, curriculum_path)

    return catalog


def overlay_curriculum_packages(catalog: CurriculumCatalog, curriculum_dir: Path) -> None:
    """Scan authored lesson packages and overlay starter code, tests, and media onto units."""
    if not curriculum_dir.exists():
        return

    for pkg_dir in curriculum_dir.glob("*/*"):
        if not pkg_dir.is_dir():
            continue
        unit_id = pkg_dir.name.upper()
        unit = catalog.get_unit(unit_id)
        if not unit:
            continue

        starter_file = pkg_dir / "starter.py"
        test_file = pkg_dir / "test_solution.py"
        meta_file = pkg_dir / "meta.json"
        lesson_file = pkg_dir / "lesson.md"

        if starter_file.exists():
            unit.starter_code = starter_file.read_text(encoding="utf-8")
        if test_file.exists():
            unit.test_code = test_file.read_text(encoding="utf-8")
        if lesson_file.exists():
            unit.lesson_markdown = lesson_file.read_text(encoding="utf-8")
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                media_list = []
                for item in meta.get("media", []):
                    media_list.append(MediaAsset(**item))
                if media_list:
                    unit.media = media_list
                if "concept_check" in meta:
                    unit.concept_check_config = meta["concept_check"]
            except Exception:
                pass

