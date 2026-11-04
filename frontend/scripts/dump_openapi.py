"""Write the API contract to frontend/openapi.json, the source of the TypeScript types (ADR-0014)."""

import json
import os
from pathlib import Path
import sys

os.environ["LMS_DB_PATH"] = ":memory:"

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)  # The app reads config/ and reference/ relative to the repository root.

from lms.adapters.ai.mock_axis import MockAxisCompanion  # noqa: E402
from lms.adapters.curriculum.loader import CurriculumCatalog  # noqa: E402
from lms.adapters.db.sqlite_repo import SQLiteLearnerRepository  # noqa: E402
from lms.adapters.runner.subprocess_runner import SubprocessRunner  # noqa: E402
from lms.api.app import create_app  # noqa: E402

repo = SQLiteLearnerRepository(db_path=":memory:")
repo.initialize()
app = create_app(repo=repo, runner=SubprocessRunner(), axis=MockAxisCompanion(), catalog=CurriculumCatalog())
target = Path(__file__).resolve().parents[1] / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"Wrote {target}")
