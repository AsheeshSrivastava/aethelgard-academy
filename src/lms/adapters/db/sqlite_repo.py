"""SQLite implementation of ILearnerRepository.

Stores learner progress, session state, and the append-only Evidence Ledger.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Dict, List, Optional

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
