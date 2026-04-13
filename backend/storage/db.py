"""SQLite persistence for research runs, results, and events."""

import json
import logging
from datetime import datetime, timezone

import aiosqlite

from backend.config import settings

logger = logging.getLogger(__name__)

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS research_runs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    depth TEXT NOT NULL DEFAULT 'standard',
    status TEXT NOT NULL DEFAULT 'running',
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_results (
    id TEXT PRIMARY KEY,
    research_id TEXT NOT NULL REFERENCES research_runs(id),
    document_md TEXT,
    sources_json TEXT,
    verification_json TEXT
);

CREATE TABLE IF NOT EXISTS research_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id TEXT NOT NULL REFERENCES research_runs(id),
    stage TEXT NOT NULL,
    data_json TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_research_results_research_id
    ON research_results(research_id);

CREATE INDEX IF NOT EXISTS idx_research_events_research_id
    ON research_events(research_id);
"""


def _db_path() -> str:
    return settings.DATABASE_PATH


async def init_db() -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(_db_path()) as db:
        await db.executescript(_SCHEMA)
        await db.commit()
    logger.info("Database initialised at %s", _db_path())


async def create_run(run_id: str, query: str, depth: str) -> None:
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "INSERT INTO research_runs (id, query, depth) VALUES (?, ?, ?)",
            (run_id, query, depth),
        )
        await db.commit()


async def update_run(
    run_id: str,
    status: str,
    cost_usd: float | None = None,
    completed_at: datetime | None = None,
) -> None:
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "UPDATE research_runs SET status = ?, cost_usd = ?, completed_at = ? WHERE id = ?",
            (status, cost_usd, completed_at or datetime.now(timezone.utc), run_id),
        )
        await db.commit()


async def save_result(
    research_id: str,
    document_md: str,
    sources_json: str,
    verification_json: str,
) -> None:
    result_id = f"{research_id}_result"
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "INSERT INTO research_results (id, research_id, document_md, sources_json, verification_json) VALUES (?, ?, ?, ?, ?)",
            (result_id, research_id, document_md, sources_json, verification_json),
        )
        await db.commit()


async def save_event(research_id: str, stage: str, data_json: str) -> None:
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "INSERT INTO research_events (research_id, stage, data_json) VALUES (?, ?, ?)",
            (research_id, stage, data_json),
        )
        await db.commit()


async def get_run(run_id: str) -> dict | None:
    async with aiosqlite.connect(_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM research_runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_result(research_id: str) -> dict | None:
    async with aiosqlite.connect(_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM research_results WHERE research_id = ?", (research_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        # Parse JSON strings back to objects for the API response.
        for key in ("sources_json", "verification_json"):
            if result.get(key):
                result[key] = json.loads(result[key])
        return result


async def delete_run(run_id: str) -> bool:
    """Delete a research run and its associated results and events."""
    async with aiosqlite.connect(_db_path()) as conn:
        await conn.execute("DELETE FROM research_events WHERE research_id = ?", (run_id,))
        await conn.execute("DELETE FROM research_results WHERE research_id = ?", (run_id,))
        cursor = await conn.execute("DELETE FROM research_runs WHERE id = ?", (run_id,))
        await conn.commit()
        return cursor.rowcount > 0


async def list_runs(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, query, depth, status, cost_usd, created_at, completed_at "
            "FROM research_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
