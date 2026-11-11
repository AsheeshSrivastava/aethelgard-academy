"""Curriculum Ingestion Engine and Catalog.

Parses Markdown roadmaps (such as Python Subject Roadmap v4) into strongly-typed
Unit domain models and validates the Directed Acyclic Graph (DAG) of prerequisites.
"""

from pathlib import Path
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from lms.adapters.curriculum.builds import answers_dir_from_env, load_builds
from lms.adapters.curriculum.rubric import check_concept_checks
from lms.adapters.curriculum.quick_checks import check_explain_blocks
from lms.adapters.curriculum.concepts import load_concepts
from lms.core.builds import StageBuildSpec, check_builds
from lms.core.concepts import check_concept_links
from lms.core.course_map import course_of
from lms.core.curriculum_checks import Finding, Severity, check_curriculum
from lms.core.exercises import PRIVATE_FIELDS, ExerciseSeed, SeedError, parse_seed
from lms.core.models import (
    ActivityType,
    MakeStep,
    MediaAsset,
    ProficiencyLevel,
    TargetSkill,
    Unit,
    UnitTopic,
    slotted_stage,
)

logger = logging.getLogger(__name__)

PYTHON_ROADMAP = "Python Subject Roadmap v4.md"
BACKEND_ROADMAP = "Backend Engineering Roadmap v3.md"
PATH_FILES = (PYTHON_ROADMAP, BACKEND_ROADMAP)  # Their Table 1 sets the path order (ADR-0020)
ROADMAP_FILES = (
    PYTHON_ROADMAP,
    BACKEND_ROADMAP,
    "AI Engineering Roadmap v2.md",
    "Practical DSA Roadmap v3.md",
    "Git Version Control Roadmap v2.md",
    "Software Design Roadmap v2.md",
    "AI-Assisted Engineering Roadmap v2.md",
    "Networking Web Foundations Roadmap v2.md",
    "Database SQL Roadmap v2.md",
    "Technical Writing Roadmap v1.md",
)
LEARNING_METHOD_FILE = "Learning Method v2.md"


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
    for item in cleaned.split(";"):
        # "soft:" and "link:" notes are advice, not prerequisites.
        if item.strip().lower().startswith(("soft:", "link:")):
            continue
        for part in item.split(","):
            p = re.sub(r"\s*\(.*$", "", part).strip()
            if p and p.lower() != "none":
                prereqs.append(p)
    return prereqs


def parse_make_step(outcome: str) -> Optional[MakeStep]:
    """Read 'Make (VE-6): a tip calculator...' from an outcome line, up to the next skill."""
    match = re.search(r"Make \(([A-Z]{2}-\d+)\):\s*(.+?)(?=\s+[A-Z]{2}-\d+(?: and [A-Z]{2}-\d+)?:|$)", outcome)
    return MakeStep(skill_id=match.group(1), task=match.group(2)) if match else None


_TOPIC_MARK = re.compile(r"\s*\(((?:awareness|new)(?:\s*,\s*(?:awareness|new))*)\)\s*$")


def parse_topics(text: str) -> List[UnitTopic]:
    """Read a roadmap Topics line; a "(awareness)" mark is kept as a flag (Amendment A1.4)."""
    topics: List[UnitTopic] = []
    for part in text.split(";"):
        name = part.strip()
        if not name:
            continue
        mark = _TOPIC_MARK.search(name)
        # v4 also writes some as "persistence awareness"; those are awareness topics too.
        awareness = bool(mark and "awareness" in mark.group(1)) or name.lower().endswith(" awareness")
        topics.append(UnitTopic(name=_TOPIC_MARK.sub("", name).strip(), awareness=awareness))
    return topics


def parse_unit_block(block: str, stage: int = 0) -> Unit:
    """Parse a single markdown unit block starting with '#### PY-...', '#### BE-...' or '#### AI-...'"""
    lines = [line.strip() for line in block.strip().split("\n") if line.strip()]

    # First line: #### <UNIT_ID> <TITLE> [(metadata)]
    header = lines[0].lstrip("#").strip()
    header_match = re.match(r"([A-Z]+-[\d.]+)\s+(.*?)(?:\s+\(.*?\))?$", header)
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
    make: Optional[MakeStep] = None
    topics: List[UnitTopic] = []

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
        elif line.startswith("- **Outcome"):
            make = parse_make_step(line)
        elif line.startswith("- **Topics:**"):
            topics = parse_topics(line.split("**Topics:**", 1)[1])

    if not concept_line:
        concept_line = f"Core concepts of {title}"

    return Unit(
        unit_id=unit_id,
        title=title,
        stage=slotted_stage(unit_id, stage),
        concept_line=concept_line,
        target_skills=target_skills,
        methods=methods,
        prerequisites=prerequisites,
        make=make,
        topics=topics,
    )


class CurriculumCatalog:
    """In-memory catalog of parsed curriculum units with DAG validation."""

    def __init__(self) -> None:
        self._units: Dict[str, Unit] = {}
        self._stage_titles: Dict[Tuple[Optional[str], int], str] = {}
        self.findings: List[Finding] = []  # SPEC-12 section 3.1 checks, set by load_all_roadmaps
        self.main_activities: Dict[str, ActivityType] = {}  # Set by load_all_roadmaps
        self.seeds: Dict[str, List[ExerciseSeed]] = {}      # unit_id -> seeds, set by load_all_roadmaps
        self.builds: Dict[Tuple[str, int], StageBuildSpec] = {}  # (course, stage), set by load_all_roadmaps
        self.skill_names: Dict[str, str] = {}               # The framework's 27 skills, set by load_all_roadmaps

    def add_unit(self, unit: Unit) -> None:
        self._units[unit.unit_id] = unit

    def apply_path_order(self, unit_ids: List[str]) -> None:
        """Put the listed units first, in that order; any others keep their place after them."""
        ordered = {i: self._units[i] for i in unit_ids if i in self._units}
        self._units = {**ordered, **self._units}

    def set_stage_title(self, course_id: Optional[str], stage: int, title: str) -> None:
        self._stage_titles[(course_id, stage)] = title

    def get_stage_titles(self, course_id: str) -> Dict[int, str]:
        return {stage: title for (c, stage), title in self._stage_titles.items() if c == course_id}

    def get_unit(self, unit_id: str) -> Optional[Unit]:
        return self._units.get(unit_id)

    def list_all_units(self) -> List[Unit]:
        return list(self._units.values())

    def get_stage_units(self, stage: int) -> List[Unit]:
        return [u for u in self._units.values() if u.stage == stage]

    def get_course_units(self, course_id: str) -> List[Unit]:
        return [u for u in self._units.values() if course_of(u.unit_id) == course_id]

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


def load_path_order(file_path: Path) -> List[str]:
    """Read unit ids, in order, from a roadmap's Table 1."""
    if not file_path.exists():
        return []
    section = re.search(r"^## Table 1\b.*?(?=^## |\Z)", file_path.read_text(encoding="utf-8"), re.M | re.S)
    return re.findall(r"^\|\s*\d+\s*\|\s*([A-Z]+-[\d.]+)\s", section.group(0), re.M) if section else []


def load_main_activities(file_path: Path) -> Dict[str, ActivityType]:
    """Read skill -> main activity from the Learning Method skill-to-activity table."""
    if not file_path.exists():
        return {}
    activities = {a.value: a for a in ActivityType}
    table: Dict[str, ActivityType] = {}
    for line in file_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*\**([A-Z]{2}-\d+)\b[^|]*\|\s*([^|]+?)\s*\|", line)
        if match and match.group(2) in activities:
            table[match.group(1)] = activities[match.group(2)]
    return table


def load_skill_names(file_path: Path) -> Dict[str, str]:
    """Read skill -> plain name from the same Learning Method table."""
    if not file_path.exists():
        return {}
    pattern = r"^\|\s*\**([A-Z]{2}-\d+)\s+([^|*]+?)\**\s*\|"
    return dict(re.findall(pattern, file_path.read_text(encoding="utf-8"), re.M))


_FROM_ENV: Any = object()


def load_seeds(
    curriculum_dir: Path, answers_dir: Optional[Path] = _FROM_ENV
) -> Tuple[Dict[str, List[ExerciseSeed]], List[Finding]]:
    """Load every SPEC-13 seed, joining each public file to its private half (ADR-0021 amendment).

    A bad file, an answer left in the public file, or a missing private half is reported
    and the seed is skipped: it is never served ungraded, and the app still starts.
    """
    if answers_dir is _FROM_ENV:
        answers_dir = answers_dir_from_env()
    seeds: Dict[str, List[ExerciseSeed]] = {}
    problems: List[Finding] = []

    def report(code: str, unit_id: str, message: str) -> None:
        problems.append(
            Finding(severity=Severity.ERROR, code=code, message=message, unit_id=unit_id, course_id=course_of(unit_id))
        )

    for seed_file in sorted(curriculum_dir.glob("*/*/exercises/*.json")):
        unit_id = seed_file.parent.parent.name.upper()
        seed_id = f"{unit_id}/{seed_file.stem}"
        try:
            raw = json.loads(seed_file.read_text(encoding="utf-8"))
            blocks = [name for name, value in raw.items() if isinstance(value, dict) and name != "template"]
            leaked = sorted(PRIVATE_FIELDS & {field for name in blocks for field in raw[name]})
            if leaked:
                report("seed-answers-public", unit_id, f"{seed_id} holds {', '.join(leaked)} in the public tree.")
                continue
            private_file = (
                answers_dir / seed_file.parent.parent.parent.name / seed_file.parent.parent.name / "exercises" / seed_file.name
                if answers_dir is not None
                else None
            )
            private = json.loads(private_file.read_text(encoding="utf-8")) if private_file and private_file.exists() else None
            if private is None or private.get("seed_id") != raw.get("seed_id"):
                report("seed-answers-missing", unit_id, f"{seed_id} has no private answers, so it is not served.")
                continue
            for name in blocks:
                raw[name] = {**raw[name], **private.get(name, {})}
            seeds.setdefault(unit_id, []).append(parse_seed(raw, seed_file.stem, unit_id))
        except (SeedError, ValueError) as error:
            report("seed-invalid", unit_id, f"{unit_id}/{seed_file.name}: {error}")
    return seeds, problems


def load_all_roadmaps(reference_dir: Path) -> CurriculumCatalog:
    """Load every roadmap into one catalog, in course then path order."""
    catalog = CurriculumCatalog()
    for file_name in ROADMAP_FILES:
        path = reference_dir / file_name
        if path.exists():
            load_roadmap_from_file(path, catalog)
    catalog.apply_path_order([i for name in PATH_FILES for i in load_path_order(reference_dir / name)])

    # Findings are reported, never fatal: the curriculum belongs to the curator.
    catalog.main_activities = load_main_activities(reference_dir / LEARNING_METHOD_FILE)
    skill_names = load_skill_names(reference_dir / LEARNING_METHOD_FILE)
    catalog.skill_names = skill_names
    for unit in catalog.list_all_units():
        for skill in unit.target_skills:
            skill.skill_name = skill_names.get(skill.skill_id, skill.skill_id)
    catalog.seeds, seed_problems = load_seeds(reference_dir.parent / "curriculum")
    concepts, concept_problems = load_concepts(reference_dir.parent / "curriculum" / "concepts")
    catalog.builds, build_problems = load_builds(reference_dir.parent / "curriculum", answers_dir_from_env())
    rubric_problems = check_concept_checks(reference_dir.parent / "curriculum", answers_dir_from_env())
    rubric_problems += check_explain_blocks(reference_dir.parent / "curriculum", answers_dir_from_env())
    catalog.findings = (
        seed_problems
        + check_curriculum(
            catalog.list_all_units(),
            stages_with_build=set(catalog.builds),
            main_activities=catalog.main_activities,
            seeds=catalog.seeds,
        )
        + concept_problems
        + check_concept_links(concepts, catalog.list_all_units())
        + build_problems
        + rubric_problems
        + check_builds(catalog.builds, catalog.list_all_units())
    )
    errors = sum(1 for f in catalog.findings if f.severity == Severity.ERROR)
    if catalog.findings:
        logger.warning(
            "Curriculum checks: %d errors, %d warnings.", errors, len(catalog.findings) - errors
        )
    return catalog


def load_roadmap_from_file(
    file_path: Path, catalog: Optional[CurriculumCatalog] = None
) -> CurriculumCatalog:
    """Parse an entire markdown roadmap file and populate a CurriculumCatalog."""
    content = file_path.read_text(encoding="utf-8")
    catalog = catalog if catalog is not None else CurriculumCatalog()

    # Split content by markdown headers; a stage may appear more than once
    stage_sections = re.split(r"\n###\s+Stage\s+(\d+)([^\n]*)", content)

    # First section contains pre-stage content
    for i in range(1, len(stage_sections), 3):
        stage_num = int(stage_sections[i])
        stage_title = re.sub(r"\s*\(.*\)$", "", stage_sections[i + 1].lstrip(": ")).strip()
        stage_body = stage_sections[i + 2]

        # Find unit blocks starting with an id such as #### PY-0.1
        unit_blocks = re.split(r"\n(?=####\s+[A-Z]+-\d)", stage_body)
        for block in unit_blocks:
            if re.match(r"####\s+[A-Z]+-\d", block.strip()):
                unit = parse_unit_block(block, stage=stage_num)
                catalog.add_unit(unit)
                if stage_title:
                    catalog.set_stage_title(course_of(unit.unit_id), unit.stage, stage_title)

    curriculum_path = Path("curriculum")
    if curriculum_path.exists():
        overlay_curriculum_packages(catalog, curriculum_path)

    return catalog


def overlay_curriculum_packages(
    catalog: CurriculumCatalog, curriculum_dir: Path, answers_dir: Optional[Path] = _FROM_ENV
) -> None:
    """Scan authored lesson packages and overlay starter code, tests, and media onto units.

    A unit's playground practice checks (`test_solution.py`) live in the private answers
    folder, beside its seed answers (decision 3.2, ADR-0021 amendment).
    """
    if answers_dir is _FROM_ENV:
        answers_dir = answers_dir_from_env()
    if not curriculum_dir.exists():
        return

    # Curator stage titles live with the packages; roadmap files stay unchanged.
    for stages_file in curriculum_dir.glob("*/stages.json"):
        stages = json.loads(stages_file.read_text(encoding="utf-8"))
        for stage, title in stages["stages"].items():
            catalog.set_stage_title(stages["course_id"], int(stage), title)

    for pkg_dir in curriculum_dir.glob("*/*"):
        if not pkg_dir.is_dir():
            continue
        unit_id = pkg_dir.name.upper()
        unit = catalog.get_unit(unit_id)
        if not unit:
            continue

        starter_file = pkg_dir / "starter.py"
        test_file = (
            answers_dir / pkg_dir.parent.name / pkg_dir.name / "test_solution.py"
            if answers_dir is not None
            else pkg_dir / "no-answers-folder"
        )
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

