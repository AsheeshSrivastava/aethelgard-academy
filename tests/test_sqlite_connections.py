"""Audit step A2 (independent audit 2026-11-09): the SQLite repository must not leak connections,
and a file database must use WAL with a busy timeout so a reader never blocks a writer."""

import sqlite3
from datetime import datetime, timezone

import pytest

from lms.adapters.db import sqlite_repo
from lms.adapters.db.sqlite_repo import BUSY_TIMEOUT_MS, SQLiteLearnerRepository
from lms.core.models import AssistanceLevel, EvidenceCategory, EvidenceEntry, EvidenceStrength

LEARNER = "learner_a2"
UNIT = "PY-0.1"


@pytest.fixture
def opened(monkeypatch):
    """Every connection the repository module opens, so a test can check each was closed."""
    connections: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        connections.append(conn)
        return conn

    monkeypatch.setattr(sqlite_repo.sqlite3, "connect", tracking_connect)
    return connections


def still_open(connections):
    alive = []
    for conn in connections:
        try:
            conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            continue
        alive.append(conn)
    return alive


def entry(entry_id: str) -> EvidenceEntry:
    return EvidenceEntry(
        entry_id=entry_id,
        learner_id=LEARNER,
        unit_id=UNIT,
        skill_id="CO-1",
        evidence_category=EvidenceCategory.EXPLAIN_REASON,
        evidence_strength=EvidenceStrength.STRONG,
        assistance_level=AssistanceLevel.NONE,
        demonstration_context="A2 connection test",
    )


def workout(repo: SQLiteLearnerRepository) -> None:
    """Reads and writes across the repository's tables."""
    repo.save_unit_progress(LEARNER, UNIT, "In progress")
    repo.get_unit_progress(LEARNER, UNIT)
    repo.record_evidence(entry("a2-1"))
    repo.get_evidence_ledger(LEARNER)
    repo.get_cold_check_timer(LEARNER, UNIT)
    repo.get_cold_items(LEARNER, UNIT)
    repo.get_all_seen_exercises(LEARNER)
    repo.get_seen_exercises(LEARNER, UNIT, "predict")
    repo.get_unit_state(LEARNER, UNIT)
    repo.get_draft(LEARNER, "PY-0.1/predict-1")
    repo.record_concept_opened(LEARNER, "variables")
    repo.get_recent_concepts(LEARNER)
    repo.get_interactions(LEARNER)
    repo.progress_resets(LEARNER)
    repo.reset_unit(LEARNER, UNIT, datetime.now(timezone.utc))


def test_a_file_repository_closes_every_connection_it_opens(tmp_path, opened):
    repo = SQLiteLearnerRepository(str(tmp_path / "lms.db"))
    repo.initialize()
    workout(repo)

    assert len(opened) > 10
    assert still_open(opened) == []


def test_an_in_memory_repository_keeps_its_one_connection(opened):
    repo = SQLiteLearnerRepository(":memory:")
    repo.initialize()
    workout(repo)

    assert len(opened) == 1
    assert repo.get_unit_progress(LEARNER, UNIT) is None  # reset_unit cleared it; data survived calls


def test_a_file_database_uses_wal(tmp_path):
    path = tmp_path / "lms.db"
    SQLiteLearnerRepository(str(path)).initialize()

    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_each_connection_waits_for_a_lock_instead_of_failing_at_once(tmp_path, opened):
    repo = SQLiteLearnerRepository(str(tmp_path / "lms.db"))
    repo.initialize()

    with repo._connect() as conn:
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == BUSY_TIMEOUT_MS
    assert BUSY_TIMEOUT_MS >= 1000


def test_a_reader_does_not_block_a_writer(tmp_path):
    """With WAL, an open read transaction no longer locks out an evidence write."""
    path = tmp_path / "lms.db"
    repo = SQLiteLearnerRepository(str(path))
    repo.initialize()
    repo.record_evidence(entry("a2-before"))

    reader = sqlite3.connect(path)
    reader.execute("BEGIN")
    reader.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()
    try:
        repo.record_evidence(entry("a2-during"))
    finally:
        reader.rollback()
        reader.close()

    assert {e.entry_id for e in repo.get_evidence_ledger(LEARNER)} >= {"a2-before", "a2-during"}
