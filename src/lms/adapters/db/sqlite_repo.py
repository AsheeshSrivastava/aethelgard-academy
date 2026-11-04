"""SQLite implementation of ILearnerRepository.

Stores learner progress, session state, and the append-only Evidence Ledger.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple

from lms.core.cold_check import ColdCheckTimer
from lms.core.events import EVIDENCE_RECORDED, EventBus, EvidenceRecorded, LedgerWriteRefused
from lms.core.exercises import CurrentExercise
from lms.core.models import (
    ActivityType,
    AssistanceLevel,
    EvidenceCategory,
    EvidenceEntry,
    EvidenceStrength,
)
from lms.core.interaction_log import InteractionEvent
from lms.core.review import ReviewItem, ReviewResult

# Added after the first release. initialize() adds any that are missing, so fresh
# and existing databases go through one path and old rows are never rewritten.
EVIDENCE_LEDGER_ADDED_COLUMNS = {
    "exercise_id": "TEXT",
    "activity": "TEXT",
    "cold_check": "INTEGER NOT NULL DEFAULT 0",
    "seed_id": "TEXT",
    "review_kind": "TEXT",
    "test_mode": "INTEGER NOT NULL DEFAULT 0",
    "interaction_id": "TEXT",
    "attempt_id": "TEXT",
}


RECENT_CONCEPTS = 5


class SQLiteLearnerRepository:
    """SQLite-backed repository for the Evidence Ledger and Progress Tracking."""

    def __init__(self, db_path: str = "lms_state.db"):
        self.db_path = db_path
        self.events = EventBus()
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
                CREATE TABLE IF NOT EXISTS assistance_log (
                    learner_id TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    assistance_level TEXT NOT NULL,
                    logged_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cold_check_item (
                    learner_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    attempted_at TEXT NOT NULL,
                    PRIMARY KEY (learner_id, unit_id, item_id)
                );
                """
            )
            # Rounds were per skill before SPEC-16; a part-done old round simply asks again.
            cold_columns = {row["name"] for row in conn.execute("PRAGMA table_info(cold_check_item)")}
            if "skill_id" in cold_columns:
                conn.execute("ALTER TABLE cold_check_item RENAME COLUMN skill_id TO item_id")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_item (
                    learner_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    exercise_id TEXT NOT NULL,
                    unit_id TEXT NOT NULL,
                    skill_id TEXT NOT NULL,
                    passed INTEGER,
                    PRIMARY KEY (learner_id, kind, scope, position)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interaction_log (
                    learner_id TEXT NOT NULL,
                    interaction_id TEXT NOT NULL,
                    recorded_at_ms INTEGER NOT NULL,
                    session_id TEXT,
                    attempt_id TEXT,
                    unit_id TEXT,
                    activity TEXT,
                    item_id TEXT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    test_mode INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (learner_id, interaction_id)
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_interaction_learner_time ON interaction_log (learner_id, recorded_at_ms)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attempt_receipt (
                    learner_id TEXT NOT NULL,
                    interaction_id TEXT NOT NULL,
                    claimed_at TEXT NOT NULL,
                    response TEXT,
                    PRIMARY KEY (learner_id, interaction_id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_result (
                    learner_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    last_attempt_at TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    PRIMARY KEY (learner_id, kind, scope)
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS concept_recent (
                    learner_id TEXT NOT NULL,
                    concept_id TEXT NOT NULL,
                    opened_order INTEGER NOT NULL,
                    PRIMARY KEY (learner_id, concept_id)
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

    def clear_current_exercise(self, learner_id: str, unit_id: str, activity: str) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                "DELETE FROM exercise_pointer WHERE learner_id = ? AND unit_id = ? AND activity = ?",
                (learner_id, unit_id, activity),
            )

    def log_assistance(
        self, learner_id: str, exercise_id: str, level: AssistanceLevel, logged_at: datetime
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                "INSERT INTO assistance_log VALUES (?, ?, ?, ?)",
                (learner_id, exercise_id, level.value, logged_at.isoformat()),
            )

    def get_assistance_levels(
        self, learner_id: str, exercise_id: str, since: datetime
    ) -> List[AssistanceLevel]:
        rows = self._get_conn().execute(
            """
            SELECT assistance_level, logged_at FROM assistance_log
            WHERE learner_id = ? AND exercise_id = ?
            """,
            (learner_id, exercise_id),
        ).fetchall()
        return [
            AssistanceLevel(r["assistance_level"])
            for r in rows
            if datetime.fromisoformat(r["logged_at"]) >= since
        ]

    def get_cold_items(self, learner_id: str, unit_id: str) -> Dict[str, bool]:
        """seed id -> passed, for this Cold Check round and earlier passes."""
        rows = self._get_conn().execute(
            "SELECT item_id, passed FROM cold_check_item WHERE learner_id = ? AND unit_id = ?",
            (learner_id, unit_id),
        ).fetchall()
        return {r["item_id"]: bool(r["passed"]) for r in rows}

    def record_cold_item(
        self, learner_id: str, unit_id: str, item_id: str, passed: bool, attempted_at: datetime
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO cold_check_item (learner_id, unit_id, item_id, passed, attempted_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, unit_id, item_id) DO UPDATE SET
                    passed = excluded.passed,
                    attempted_at = excluded.attempted_at
                """,
                (learner_id, unit_id, item_id, int(passed), attempted_at.isoformat()),
            )

    @staticmethod
    def _review_item(row: sqlite3.Row) -> ReviewItem:
        return ReviewItem(
            position=row["position"],
            exercise_id=row["exercise_id"],
            unit_id=row["unit_id"],
            skill_id=row["skill_id"],
            passed=None if row["passed"] is None else bool(row["passed"]),
        )

    def get_review_items(self, learner_id: str, kind: str, scope: str) -> List[ReviewItem]:
        rows = self._get_conn().execute(
            """
            SELECT * FROM review_item WHERE learner_id = ? AND kind = ? AND scope = ?
            ORDER BY position ASC
            """,
            (learner_id, kind, scope),
        ).fetchall()
        return [self._review_item(r) for r in rows]

    def save_review_items(
        self, learner_id: str, kind: str, scope: str, items: List[ReviewItem]
    ) -> None:
        """Store a round once. The first plan wins, so a round cannot change under a learner."""
        conn = self._get_conn()
        with conn:
            conn.executemany(
                """
                INSERT INTO review_item
                    (learner_id, kind, scope, position, exercise_id, unit_id, skill_id, passed)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(learner_id, kind, scope, position) DO NOTHING
                """,
                [
                    (learner_id, kind, scope, i.position, i.exercise_id, i.unit_id, i.skill_id)
                    for i in items
                ],
            )

    def find_open_review_item(
        self, learner_id: str, kind: str, exercise_id: str
    ) -> Optional[Tuple[str, ReviewItem]]:
        row = self._get_conn().execute(
            """
            SELECT * FROM review_item
            WHERE learner_id = ? AND kind = ? AND exercise_id = ? AND passed IS NULL
            """,
            (learner_id, kind, exercise_id),
        ).fetchone()
        return (row["scope"], self._review_item(row)) if row else None

    def answer_review_item(
        self, learner_id: str, kind: str, scope: str, position: int, passed: bool
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                UPDATE review_item SET passed = ?
                WHERE learner_id = ? AND kind = ? AND scope = ? AND position = ?
                """,
                (int(passed), learner_id, kind, scope, position),
            )

    def reopen_review_item(
        self, learner_id: str, kind: str, scope: str, position: int, exercise_id: str
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                UPDATE review_item SET passed = NULL, exercise_id = ?
                WHERE learner_id = ? AND kind = ? AND scope = ? AND position = ?
                """,
                (exercise_id, learner_id, kind, scope, position),
            )

    def get_review_result(self, learner_id: str, kind: str, scope: str) -> Optional[ReviewResult]:
        row = self._get_conn().execute(
            "SELECT * FROM review_result WHERE learner_id = ? AND kind = ? AND scope = ?",
            (learner_id, kind, scope),
        ).fetchone()
        if row is None:
            return None
        return ReviewResult(
            last_attempt_at=datetime.fromisoformat(row["last_attempt_at"]), passed=bool(row["passed"])
        )

    def record_review_result(
        self, learner_id: str, kind: str, scope: str, passed: bool, attempted_at: datetime
    ) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO review_result (learner_id, kind, scope, last_attempt_at, passed)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, kind, scope) DO UPDATE SET
                    last_attempt_at = excluded.last_attempt_at,
                    passed = excluded.passed
                """,
                (learner_id, kind, scope, attempted_at.isoformat(), int(passed)),
            )

    def get_finished_reviews(self, learner_id: str, kind: str) -> Set[str]:
        rows = self._get_conn().execute(
            "SELECT scope FROM review_result WHERE learner_id = ? AND kind = ?",
            (learner_id, kind),
        ).fetchall()
        return {r["scope"] for r in rows}

    def append_interaction(self, event: InteractionEvent) -> None:
        """Append one row. The log is never updated; a repeated id is ignored (ADR-0022)."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO interaction_log (
                    learner_id, interaction_id, recorded_at_ms, session_id, attempt_id,
                    unit_id, activity, item_id, event_type, payload, test_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.learner_id, event.interaction_id, event.recorded_at_ms, event.session_id,
                    event.attempt_id, event.unit_id, event.activity, event.item_id, event.event_type,
                    json.dumps(event.payload), int(event.test_mode),
                ),
            )

    def get_interactions(self, learner_id: str, limit: int = 1000) -> List[InteractionEvent]:
        """This learner's log, newest first."""
        rows = self._get_conn().execute(
            "SELECT * FROM interaction_log WHERE learner_id = ? ORDER BY recorded_at_ms DESC, interaction_id DESC LIMIT ?",
            (learner_id, limit),
        ).fetchall()
        return [
            InteractionEvent(
                interaction_id=r["interaction_id"], learner_id=r["learner_id"], recorded_at_ms=r["recorded_at_ms"],
                session_id=r["session_id"], attempt_id=r["attempt_id"], unit_id=r["unit_id"], activity=r["activity"],
                item_id=r["item_id"], event_type=r["event_type"], payload=json.loads(r["payload"]),
                test_mode=bool(r["test_mode"]),
            )
            for r in rows
        ]

    def claim_interaction(self, learner_id: str, interaction_id: str, claimed_at: datetime) -> bool:
        """Claim an idempotency key before grading; False if it was already claimed."""
        conn = self._get_conn()
        with conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO attempt_receipt (learner_id, interaction_id, claimed_at) VALUES (?, ?, ?)",
                (learner_id, interaction_id, claimed_at.isoformat()),
            )
        return cursor.rowcount == 1

    def get_interaction_response(self, learner_id: str, interaction_id: str) -> Optional[str]:
        row = self._get_conn().execute(
            "SELECT response FROM attempt_receipt WHERE learner_id = ? AND interaction_id = ?",
            (learner_id, interaction_id),
        ).fetchone()
        return row["response"] if row else None

    def finish_interaction(self, learner_id: str, interaction_id: str, response: str) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                "UPDATE attempt_receipt SET response = ? WHERE learner_id = ? AND interaction_id = ?",
                (response, learner_id, interaction_id),
            )

    def release_interaction(self, learner_id: str, interaction_id: str) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                "DELETE FROM attempt_receipt WHERE learner_id = ? AND interaction_id = ? AND response IS NULL",
                (learner_id, interaction_id),
            )

    def get_all_seen_exercises(self, learner_id: str) -> Set[str]:
        rows = self._get_conn().execute(
            "SELECT exercise_id FROM exercise_seen WHERE learner_id = ?", (learner_id,)
        ).fetchall()
        return {r["exercise_id"] for r in rows}

    def clear_failed_cold_items(self, learner_id: str, unit_id: str) -> None:
        """End of a failed round: failed skills come back, passed ones stay passed."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                "DELETE FROM cold_check_item WHERE learner_id = ? AND unit_id = ? AND passed = 0",
                (learner_id, unit_id),
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

    def record_concept_opened(self, learner_id: str, concept_id: str) -> None:
        """Move the note to the top of the learner's recent list. Not evidence (SPEC-14)."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO concept_recent (learner_id, concept_id, opened_order)
                VALUES (?, ?, (
                    SELECT COALESCE(MAX(opened_order), 0) + 1 FROM concept_recent WHERE learner_id = ?
                ))
                ON CONFLICT(learner_id, concept_id) DO UPDATE SET opened_order = excluded.opened_order
                """,
                (learner_id, concept_id, learner_id),
            )
            conn.execute(
                """
                DELETE FROM concept_recent WHERE learner_id = ? AND concept_id NOT IN (
                    SELECT concept_id FROM concept_recent WHERE learner_id = ?
                    ORDER BY opened_order DESC LIMIT ?
                )
                """,
                (learner_id, learner_id, RECENT_CONCEPTS),
            )

    def get_recent_concepts(self, learner_id: str) -> List[str]:
        rows = self._get_conn().execute(
            "SELECT concept_id FROM concept_recent WHERE learner_id = ? ORDER BY opened_order DESC",
            (learner_id,),
        ).fetchall()
        return [row["concept_id"] for row in rows]

    def reset_unit(self, learner_id: str, unit_id: str) -> None:
        """Clear a unit's working state. Keeps exercise_seen, and never touches evidence_ledger."""
        conn = self._get_conn()
        with conn:
            for table in (
                "unit_progress",
                "unit_cold_check",
                "cold_check_item",
                "exercise_pointer",
                "unit_state",
                "exercise_draft",
            ):
                conn.execute(
                    f"DELETE FROM {table} WHERE learner_id = ? AND unit_id = ?",
                    (learner_id, unit_id),
                )

    def record_evidence(self, entry: EvidenceEntry) -> None:
        if self.events.dispatching:
            raise LedgerWriteRefused("A subscriber to evidence.recorded cannot write to the ledger.")
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    entry_id, learner_id, unit_id, skill_id,
                    evidence_category, evidence_strength, assistance_level,
                    demonstration_context, observed_reasoning, recorded_at,
                    exercise_id, activity, cold_check, seed_id, review_kind, test_mode,
                    interaction_id, attempt_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    entry.seed_id,
                    entry.review_kind,
                    int(entry.test_mode),
                    entry.interaction_id,
                    entry.attempt_id,
                ),
            )
        self.events.publish(
            EVIDENCE_RECORDED,
            EvidenceRecorded(
                entry_id=entry.entry_id,
                learner_id=entry.learner_id,
                unit_id=entry.unit_id,
                skill_id=entry.skill_id,
                category=entry.evidence_category.value,
                strength=entry.evidence_strength.value,
                assistance_level=entry.assistance_level.value,
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
                    seed_id=r["seed_id"],
                    review_kind=r["review_kind"],
                    test_mode=bool(r["test_mode"]),
                    interaction_id=r["interaction_id"],
                    attempt_id=r["attempt_id"],
                )
            )
        return entries
