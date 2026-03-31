"""
QuerySage — AlloyDB connection pool and query execution layer.
Uses asyncpg for async I/O with SQLAlchemy core for connection management.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection

from config import get_settings
from logger import get_logger

log = get_logger(__name__)

# ── Async engine (lazy init) ─────────────────────────────────────────────────
_engine: sa.ext.asyncio.AsyncEngine | None = None


def _get_engine() -> sa.ext.asyncio.AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        # Convert psycopg2 URL to asyncpg driver
        async_url = settings.alloydb_db_url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )
        _engine = create_async_engine(
            async_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,          # validates connections before use
            pool_recycle=1800,           # recycle connections every 30 min
            echo=False,
        )
        log.info("alloydb_engine_created", url_redacted=async_url.split("@")[-1])
    return _engine


@asynccontextmanager
async def get_connection() -> AsyncConnection:
    """Async context manager for a single AlloyDB connection."""
    engine = _get_engine()
    async with engine.connect() as conn:
        yield conn


async def execute_query(sql: str, params: dict | None = None) -> list[dict[str, Any]]:
    """
    Execute a raw SQL query against AlloyDB and return rows as dicts.
    IMPORTANT: Only SELECT statements routed through here — never DDL/DML
    from user-facing NL queries (enforced in the agent layer).
    """
    async with get_connection() as conn:
        result = await conn.execute(sa.text(sql), params or {})
        rows = result.mappings().all()
        return [dict(row) for row in rows]


async def execute_nl_to_sql(nl_query: str, config_name: str) -> dict[str, Any]:
    """
    Invoke AlloyDB AI's natural language translation function to convert
    a plain-English question into a SQL query, then execute it.
    Returns: {generated_sql, rows, row_count}
    """
    # Step 1: Translate NL → SQL using AlloyDB AI extension
    translate_sql = sa.text(
        "SELECT alloydb_ai_nl.translate(:config, :query) AS generated_sql"
    )

    async with get_connection() as conn:
        try:
            result = await conn.execute(translate_sql, {
                "config": config_name,
                "query":  nl_query,
            })
            row = result.mappings().first()
            generated_sql: str = row["generated_sql"] if row else ""
        except Exception as exc:
            log.warning("alloydb_ai_nl_unavailable", error=str(exc))
            # Fallback: pass through if AlloyDB AI NL not yet configured
            generated_sql = None

    if not generated_sql:
        return {
            "generated_sql": None,
            "rows": [],
            "row_count": 0,
            "error": "AlloyDB AI NL translation unavailable. Configure the NL extension first.",
        }

    # Step 2: Safety gate — only allow SELECT
    stripped = generated_sql.strip().upper()
    if not stripped.startswith("SELECT"):
        log.warning("unsafe_sql_blocked", sql_prefix=stripped[:50])
        return {
            "generated_sql": generated_sql,
            "rows": [],
            "row_count": 0,
            "error": "Generated SQL was not a SELECT statement — blocked for safety.",
        }

    # Step 3: Execute the generated SQL
    rows = await execute_query(generated_sql)
    return {
        "generated_sql": generated_sql,
        "rows":          rows,
        "row_count":     len(rows),
    }


async def health_check() -> bool:
    """Ping AlloyDB with a strict timeout — used by /health endpoint."""
    try:
        # Use a 5-second timeout for the health check to prevent startup deadlocks
        await asyncio.wait_for(execute_query("SELECT 1"), timeout=5.0)
        return True
    except Exception as exc:
        log.error("alloydb_health_check_failed", error=str(exc))
        return False
