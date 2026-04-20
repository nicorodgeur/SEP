"""
utils/database.py — Persistance SQLite des offres et des cycles.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

from config import DATABASE_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    source          TEXT,
    location        TEXT,
    contract_type   TEXT,
    description     TEXT,
    relevance_score INTEGER DEFAULT 0,
    recruiter_name  TEXT,
    recruiter_email TEXT,
    status          TEXT DEFAULT 'new',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_score  ON jobs(relevance_score);

CREATE TABLE IF NOT EXISTS cycles (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at        TEXT NOT NULL,
    ended_at          TEXT,
    jobs_found        INTEGER DEFAULT 0,
    jobs_processed    INTEGER DEFAULT 0,
    applications_sent INTEGER DEFAULT 0,
    errors            TEXT
);
"""


@contextmanager
def _conn():
    c = sqlite3.connect(DATABASE_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_database() -> None:
    with _conn() as c:
        c.executescript(SCHEMA)


def upsert_job(job: Dict) -> int:
    fields = (
        "url", "title", "company", "source", "location", "contract_type",
        "description", "relevance_score", "recruiter_name", "recruiter_email",
        "status",
    )
    values = [job.get(f) for f in fields]
    placeholders = ", ".join(["?"] * len(fields))
    update_clause = ", ".join([f"{f}=excluded.{f}" for f in fields if f != "url"])

    with _conn() as c:
        cur = c.execute(
            f"INSERT INTO jobs ({', '.join(fields)}) VALUES ({placeholders}) "
            f"ON CONFLICT(url) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP",
            values,
        )
        return cur.lastrowid


def get_jobs_by_status(status: str) -> List[Dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY relevance_score DESC",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]


def set_job_status(job_url: str, status: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE url = ?",
            (status, job_url),
        )


def get_stats() -> Dict[str, int]:
    with _conn() as c:
        rows = c.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status").fetchall()
        stats = {r["status"]: r["n"] for r in rows}
        stats["total"] = sum(stats.values())
        return stats


def start_cycle() -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO cycles (started_at) VALUES (?)",
            (datetime.utcnow().isoformat(),),
        )
        return cur.lastrowid


def end_cycle(cycle_id: int, jobs_found: int, jobs_processed: int,
              applications_sent: int, errors: Optional[str] = None) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE cycles SET ended_at = ?, jobs_found = ?, jobs_processed = ?, "
            "applications_sent = ?, errors = ? WHERE id = ?",
            (
                datetime.utcnow().isoformat(),
                jobs_found, jobs_processed, applications_sent,
                errors or None, cycle_id,
            ),
        )
