"""Audit log: every triage outcome, stored in SQLite.

If a priority is ever questioned, this table is the answer: the item, the
classification, the rule that fired, the actions taken, and when — all
replayable because classification + rules are recorded, not just the result.
Uses only the standard library (sqlite3), so it adds no dependencies.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from .schemas import TriageResult


class AuditLog:
    """Append-only SQLite store for TriageResults."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False + a lock: the API serves requests from a
        # thread pool, so the connection is shared — the lock keeps writes safe.
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS triage_results (
                run_id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                priority TEXT NOT NULL,
                rule_fired TEXT NOT NULL,
                auto_routed INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                processed_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, result: TriageResult) -> None:
        """Store one triage result."""
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO triage_results VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    result.run_id,
                    result.item_id,
                    result.decision.priority.value,
                    result.decision.rule_fired,
                    int(result.auto_routed),
                    result.model_dump_json(),
                    result.processed_at.isoformat(),
                ),
            )
            self._conn.commit()

    def list_results(self, limit: int = 50) -> list[TriageResult]:
        """Return the most recent results, newest first."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT result_json FROM triage_results ORDER BY processed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [TriageResult.model_validate(json.loads(row[0])) for row in rows]
