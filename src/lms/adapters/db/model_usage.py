"""Token counts per call and the active provider choice (SPEC-17 sections 2.2 and 4).

Stores counts only: never prompts, replies, learner code or keys. Kept in its own
tables so it does not touch the learner repository.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Literal, Optional, Union

Scope = Literal["session", "month"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UsageTotal:
    profile_id: str
    model: str
    calls: int
    input_tokens: Optional[int]   # None when no call in the group reported counts
    output_tokens: Optional[int]
    cost_usd: float
    estimated: bool               # True when any call was costed at its limit


class UsageStore:
    def __init__(
        self,
        db_path: Union[str, Path],
        clock: Callable[[], datetime] = _utc_now,
        session_id: Optional[str] = None,
    ) -> None:
        self.db_path = str(db_path)
        self.clock = clock
        self.session_id = session_id or uuid.uuid4().hex
        self._memory: Optional[sqlite3.Connection] = (
            sqlite3.connect(":memory:", check_same_thread=False) if self.db_path == ":memory:" else None
        )

    def _connect(self) -> sqlite3.Connection:
        if self._memory is not None:
            return self._memory
        return sqlite3.connect(self.db_path)

    def _run(self, sql: str, params: tuple = ()) -> List[tuple]:
        conn = self._connect()
        try:
            with conn:
                return conn.execute(sql, params).fetchall()
        finally:
            if self._memory is None:
                conn.close()

    def initialize(self) -> None:
        self._run(
            """
            CREATE TABLE IF NOT EXISTS model_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                at TEXT NOT NULL,
                session_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                model TEXT NOT NULL,
                call TEXT NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_usd REAL,
                estimated INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._run("CREATE INDEX IF NOT EXISTS idx_model_usage_at ON model_usage(at)")
        self._run(
            """
            CREATE TABLE IF NOT EXISTS model_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                active_profile TEXT NOT NULL
            )
            """
        )

    # --- usage ---------------------------------------------------------------

    def add(
        self,
        profile_id: str,
        model: str,
        call: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        cost_usd: Optional[float],
        estimated: bool,
    ) -> None:
        self._run(
            "INSERT INTO model_usage (at, session_id, profile_id, model, call, input_tokens,"
            " output_tokens, cost_usd, estimated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                self.clock().astimezone(timezone.utc).isoformat(),
                self.session_id,
                profile_id,
                model,
                call,
                input_tokens,
                output_tokens,
                cost_usd,
                int(estimated),
            ),
        )

    def _month_start(self) -> str:
        now = self.clock().astimezone(timezone.utc)
        return datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()

    def _month_end(self) -> str:
        now = self.clock().astimezone(timezone.utc)
        year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
        return datetime(year, month, 1, tzinfo=timezone.utc).isoformat()

    def month_spend(self) -> float:
        (row,) = self._run(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM model_usage WHERE at >= ? AND at < ?",
            (self._month_start(), self._month_end()),
        )
        return float(row[0])

    def totals(self, scope: Scope) -> List[UsageTotal]:
        if scope == "session":
            where, params = "session_id = ?", (self.session_id,)
        else:
            where, params = "at >= ? AND at < ?", (self._month_start(), self._month_end())
        rows = self._run(
            f"""
            SELECT profile_id, model, COUNT(*), SUM(input_tokens), SUM(output_tokens),
                   COALESCE(SUM(cost_usd), 0), MAX(estimated)
            FROM model_usage WHERE {where}
            GROUP BY profile_id, model ORDER BY MIN(id)
            """,
            params,
        )
        return [
            UsageTotal(r[0], r[1], int(r[2]), r[3], r[4], float(r[5]), bool(r[6])) for r in rows
        ]

    # --- active profile ------------------------------------------------------

    def get_active(self) -> Optional[str]:
        rows = self._run("SELECT active_profile FROM model_settings WHERE id = 1")
        return rows[0][0] if rows else None

    def set_active(self, profile_id: str) -> None:
        self._run(
            "INSERT INTO model_settings (id, active_profile) VALUES (1, ?)"
            " ON CONFLICT(id) DO UPDATE SET active_profile = excluded.active_profile",
            (profile_id,),
        )

    # --- inspection (tests, audits) -----------------------------------------

    def column_names(self) -> List[str]:
        return [r[1] for r in self._run("PRAGMA table_info(model_usage)")]

    def dump_text(self) -> str:
        """Every stored value as text, for key-leak checks."""
        rows = self._run("SELECT * FROM model_usage") + self._run("SELECT * FROM model_settings")
        return "\n".join(" ".join(map(str, r)) for r in rows)
