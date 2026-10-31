"""SQLite implementation of ILearnerRepository.

Stores learner progress, session state, and the append-only Evidence Ledger.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Dict, List, Optional

from lms.core.cold_check import ColdCheckTimer
from lms.core.exercises import CurrentExercise
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)

# Added after the first release. initialize() adds any that are missing, so fresh
# and existing databases go through one path and old rows are never rewritten.
EVIDENCE_LEDGER_ADDED_COLUMNS = {
    "exercise_id": "TEXT",
    "activity": "TEXT",
    "cold_check": "INTEGER NOT NULL DEFAULT 0",
}


class SQLiteLearnerRepository:
    """SQLite-backed repository for the Evidence Ledger and Progress Tracking."""

    def __init__(self, db_path: str = "lms_state.db"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._connection is None:
                self._connection = sqlite3.connect(":memory:", check_same_thread=False)
                self._connection.row_factory = sqlite3.Row
            return self._connection
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        """Create tables if they do not exist."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unit_progress (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (learner_id, unit_id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_ledger (
                    entry_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    skill_id TEXT NOT NULL,
                    evidence_category TEXT NOT NULL,
                    evidence_strength TEXT NOT NULL,
                    assistance_level TEXT NOT NULL,
                    demonstration_context TEXT NOT NULL,
                    observed_reasoning TEXT,
                    recorded_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_evidence_learner_skill 
                ON evidence_ledger (learner_id, skill_id);
                """
            )
            existing = {row["name"] for row in conn.execute("PRAGMA table_info(evidence_ledger)")}
            for column, definition in EVIDENCE_LEDGER_ADDED_COLUMNS.items():
                if column not in existing:
                    conn.execute(f"ALTER TABLE evidence_ledger ADD COLUMN {column} {definition}")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unit_cold_check (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    last_attempt_at TEXT,
                    last_attempt_passed INTEGER,
                    PRIMARY KEY (learner_id, unit_id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS exercise_pointer (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    activity TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    served_at TEXT NOT NULL,
                    PRIMARY KEY (learner_id, unit_id, activity)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS exercise_seen (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    activity TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    seen_order INTEGER NOT NULL,
                    PRIMARY KEY (learner_id, exercise_id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unit_state (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    step TEXT,
                    done_steps TEXT NOT NULL,
                    PRIMARY KEY (learner_id, unit_id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS exercise_draft (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    files TEXT NOT NULL,
                    PRIMARY KEY (learner_id, exercise_id)
                );
                """
            )

    def get_learner(self, learner_id: str) -> Optional[Dict[str, Any]]:
        return {"learner_id": learner_id}

    def get_unit_progress(self, learner_id: str, unit_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT learner_id, unit_id, status, updated_at FROM unit_progress WHERE learner_id = ? AND unit_id = ?",
            (learner_id, unit_id),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def save_unit_progress(self, learner_id: str, unit_id: str, status: str) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO unit_progress (learner_id, unit_id, status, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(learner_id, unit_id) DO UPDATE SET
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (learner_id, unit_id, status),
            )

    def get_cold_check_timer(self, learner_id: str, unit_id: str) -> Optional[ColdCheckTimer]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM unit_cold_check WHERE learner_id = ? AND unit_id = ?",
            (learner_id, unit_id),
        ).fetchone()
        if row is None:
            return None
        passed = row["last_attempt_passed"]
        return ColdCheckTimer(
            learner_id=row["learner_id"],
            unit_id=row["unit_id"],
            completed_at=datetime.fromisoformat(row["completed_at"]),
            last_attempt_at=(
                datetime.fromisoformat(row["last_attempt_at"]) if row["last_attempt_at"] else None
            ),
            last_attempt_passed=None if passed is None else bool(passed),
        )

    def mark_unit_activities_completed(
        self, learner_id: str, unit_id: str, completed_at: datetime
    ) -> None:
        """Start the clock. The first completion wins, so redoing an activity cannot push it back."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO unit_cold_check (learner_id, unit_id, completed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(learner_id, unit_id) DO NOTHING
                """,
                (learner_id, unit_id, completed_at.isoformat()),
            )

    def record_cold_check_attempt(
        self, learner_id: str, unit_id: str, passed: bool, attempted_at: datetime
    ) -> None:
        conn = self._get_conn()
        with conn:
            cursor = conn.execute(
                """
                UPDATE unit_cold_check
                SET last_attempt_at = ?, last_attempt_passed = ?
                WHERE learner_id = ? AND unit_id = ?
                """,
                (attempted_at.isoformat(), int(passed), learner_id, unit_id),
            )
        if cursor.rowcount == 0:
            raise ValueError(f"Unit '{unit_id}' has no completed activities to Cold Check.")

    def get_current_exercise(
        self, learner_id: str, unit_id: str, activity: str
    ) -> Optional[CurrentExercise]:
        row = self._get_conn().execute(
            """
            SELECT exercise_id, served_at FROM exercise_pointer
            WHERE learner_id = ? AND unit_id = ? AND activity = ?
            """,
            (learner_id, unit_id, activity),
        ).fetchone()
        if row is None:
            return None
        return CurrentExercise(
            exercise_id=row["exercise_id"], served_at=datetime.fromisoformat(row["served_at"])
        )

    def set_current_exercise(
        self, learner_id: str, unit_id: str, activity: str, exercise_id: str, served_at: datetime
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO exercise_pointer (learner_id, unit_id, activity, exercise_id, served_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, unit_id, activity) DO UPDATE SET
                    exercise_id = excluded.exercise_id,
                    served_at = excluded.served_at
                """,
                (learner_id, unit_id, activity, exercise_id, served_at.isoformat()),
            )
            conn.execute(
                """
                INSERT INTO exercise_seen (learner_id, unit_id, activity, exercise_id, seen_order)
                VALUES (?, ?, ?, ?, (
                    SELECT COALESCE(MAX(seen_order), 0) + 1 FROM exercise_seen WHERE learner_id = ?
                ))
                ON CONFLICT(learner_id, exercise_id) DO UPDATE SET seen_order = excluded.seen_order
                """,
                (learner_id, unit_id, activity, exercise_id, learner_id),
            )

    def get_seen_exercises(self, learner_id: str, unit_id: str, activity: str) -> List[str]:
        """Exercise ids this learner has been served, oldest first."""
        rows = self._get_conn().execute(
            """
            SELECT exercise_id FROM exercise_seen
            WHERE learner_id = ? AND unit_id = ? AND activity = ?
            ORDER BY seen_order ASC
            """,
            (learner_id, unit_id, activity),
        ).fetchall()
        return [r["exercise_id"] for r in rows]

    def get_unit_state(self, learner_id: str, unit_id: str) -> Dict[str, Any]:
        row = self._get_conn().execute(
            "SELECT step, done_steps FROM unit_state WHERE learner_id = ? AND unit_id = ?",
            (learner_id, unit_id),
        ).fetchone()
        if row is None:
            return {"step": None, "done_steps": []}
        return {"step": row["step"], "done_steps": json.loads(row["done_steps"])}

    def save_unit_state(
        self, learner_id: str, unit_id: str, step: Optional[str], done_steps: List[str]
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO unit_state (learner_id, unit_id, step, done_steps)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(learner_id, unit_id) DO UPDATE SET
                    step = excluded.step,
                    done_steps = excluded.done_steps
                """,
                (learner_id, unit_id, step, json.dumps(done_steps)),
            )

    def get_draft(self, learner_id: str, exercise_id: str) -> Dict[str, str]:
        row = self._get_conn().execute(
            "SELECT files FROM exercise_draft WHERE learner_id = ? AND exercise_id = ?",
            (learner_id, exercise_id),
        ).fetchone()
        return json.loads(row["files"]) if row else {}

    def save_draft(
        self, learner_id: str, unit_id: str, exercise_id: str, files: Dict[str, str]
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO exercise_draft (learner_id, unit_id, exercise_id, files)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(learner_id, exercise_id) DO UPDATE SET files = excluded.files
                """,
                (learner_id, unit_id, exercise_id, json.dumps(files)),
            )

    def reset_unit(self, learner_id: str, unit_id: str) -> None:
        """Clear a unit's working state. Keeps exercise_seen, and never touches evidence_ledger."""
        conn = self._get_conn()
        with conn:
            for table in (
                "unit_progress",
                "unit_cold_check",
                "exercise_pointer",
                "unit_state",
                "exercise_draft",
            ):
                conn.execute(
                    f"DELETE FROM {table} WHERE learner_id = ? AND unit_id = ?",
                    (learner_id, unit_id),
                )

    def record_evidence(self, entry: EvidenceEntry) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    entry_id, learner_id, unit_id, skill_id,
                    evidence_category, evidence_strength, assistance_level,
                    demonstration_context, observed_reasoning, recorded_at,
                    exercise_id, activity, cold_check
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.learner_id,
                    entry.unit_id,
                    entry.skill_id,
                    entry.evidence_category.value,
                    entry.evidence_strength.value,
                    entry.assistance_level.value,
                    entry.demonstration_context,
                    entry.observed_reasoning,
                    entry.recorded_at.isoformat(),
                    entry.exercise_id,
                    entry.activity.value if entry.activity else None,
                    int(entry.cold_check),
                ),
            )

    def get_evidence_ledger(
        self, learner_id: str, skill_id: Optional[str] = None
    ) -> List[EvidenceEntry]:
        conn = self._get_conn()
        if skill_id:
            cursor = conn.execute(
                """
                SELECT * FROM evidence_ledger 
                WHERE learner_id = ? AND skill_id = ?
                ORDER BY recorded_at ASC
                """,
                (learner_id, skill_id),
            )
        else:
            cursor = conn.execute(
                """
                SELECT * FROM evidence_ledger 
                WHERE learner_id = ?
                ORDER BY recorded_at ASC
                """,
                (learner_id,),
            )
        rows = cursor.fetchall()
        entries: List[EvidenceEntry] = []
        for r in rows:
            entries.append(
                EvidenceEntry(
                    entry_id=r["entry_id"],
                    learner_id=r["learner_id"],
                    unit_id=r["unit_id"],
                    skill_id=r["skill_id"],
                    evidence_category=EvidenceCategory(r["evidence_category"]),
                    evidence_strength=EvidenceStrength(r["evidence_strength"]),
                    assistance_level=AssistanceLevel(r["assistance_level"]),
                    demonstration_context=r["demonstration_context"],
                    observed_reasoning=r["observed_reasoning"],
                    recorded_at=datetime.fromisoformat(r["recorded_at"]),
                    exercise_id=r["exercise_id"],
                    activity=ActivityType(r["activity"]) if r["activity"] else None,
                    cold_check=bool(r["cold_check"]),
                )
            )
        return entries
