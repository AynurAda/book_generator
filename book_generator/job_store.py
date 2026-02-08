"""
SQLite-backed job store for the book generation API.

Replaces the in-memory dict so that jobs survive server restarts
and are safe for concurrent access.
"""

import json
import sqlite3
import threading
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Default location: data/jobs.db relative to project root
_DEFAULT_DB_PATH = "data/jobs.db"


class JobStore:
    """Persistent job storage using SQLite with WAL mode."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self):
        """Create the jobs table if it doesn't exist."""
        import os
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL DEFAULT 'pending',
                        progress INTEGER NOT NULL DEFAULT 0,
                        current_stage TEXT NOT NULL DEFAULT 'Initializing',
                        message TEXT NOT NULL DEFAULT 'Job created, waiting to start',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        book_name TEXT,
                        pdf_path TEXT,
                        error TEXT,
                        request_json TEXT NOT NULL,
                        logs_json TEXT NOT NULL DEFAULT '[]'
                    )
                """)
                # Add logs_json column to existing tables (idempotent)
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN logs_json TEXT NOT NULL DEFAULT '[]'")
                except sqlite3.OperationalError:
                    pass  # column already exists
                conn.commit()
            finally:
                conn.close()

    def create(self, job_id: str, request_data: dict) -> dict:
        """Insert a new job. Returns the job as a dict."""
        now = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """INSERT INTO jobs
                       (job_id, status, progress, current_stage, message,
                        created_at, updated_at, request_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (job_id, "pending", 0, "Initializing",
                     "Job created, waiting to start", now, now,
                     json.dumps(request_data)),
                )
                conn.commit()
            finally:
                conn.close()

        return self.get(job_id)

    def get(self, job_id: str) -> Optional[dict]:
        """Fetch a single job by ID. Returns None if not found."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_dict(row)
        finally:
            conn.close()

    def update(self, job_id: str, **fields) -> Optional[dict]:
        """
        Update one or more fields on a job.

        Accepted fields: status, progress, current_stage, message,
                         book_name, pdf_path, error.
        """
        allowed = {
            "status", "progress", "current_stage", "message",
            "book_name", "pdf_path", "error",
        }
        to_set = {k: v for k, v in fields.items() if k in allowed}
        if not to_set:
            return self.get(job_id)

        now = datetime.utcnow().isoformat()
        to_set["updated_at"] = now

        set_clause = ", ".join(f"{k} = ?" for k in to_set)
        values = list(to_set.values()) + [job_id]

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    f"UPDATE jobs SET {set_clause} WHERE job_id = ?",
                    values,
                )
                # Append to log if message is provided
                if "message" in fields:
                    row = conn.execute(
                        "SELECT logs_json FROM jobs WHERE job_id = ?", (job_id,)
                    ).fetchone()
                    logs = json.loads(row[0]) if row and row[0] else []
                    logs.append({"t": now, "msg": fields["message"]})
                    # Keep last 50 entries
                    if len(logs) > 50:
                        logs = logs[-50:]
                    conn.execute(
                        "UPDATE jobs SET logs_json = ? WHERE job_id = ?",
                        (json.dumps(logs), job_id),
                    )
                conn.commit()
            finally:
                conn.close()

        return self.get(job_id)

    def list_all(self) -> list[dict]:
        """Return all jobs, most recent first."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def count(self) -> int:
        """Return total number of jobs."""
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
            return row[0]
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["request"] = json.loads(d.pop("request_json"))
        d["logs"] = json.loads(d.pop("logs_json", "[]") or "[]")
        return d
