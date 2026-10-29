"""Inspect a curriculum notes or documentation folder. Usage:

    uv run python scripts/inspect_sources.py <folder> [--id ID] [--out reports]
    uv run python scripts/inspect_sources.py <folder> --loaders real --compare

Exit code 0 = gate passed, 1 = gate failed (report still written), 2 = bad input.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lms.adapters.ai.inspect_sources import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
