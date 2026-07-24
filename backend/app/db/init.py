"""Lazy schema creation and seed-data initialization."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.db.connection import get_connection
from app.db.schema import SCHEMA_STATEMENTS
from app.market.seed_prices import SEED_PRICES

DEFAULT_USER_ID = "default"
DEFAULT_CASH_BALANCE = 10000.0
DEFAULT_WATCHLIST_TICKERS: tuple[str, ...] = tuple(SEED_PRICES.keys())


def _now() -> str:
    return datetime.now(UTC).isoformat()


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't already exist. Safe to re-run."""
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    conn.commit()


def seed_default_data(conn: sqlite3.Connection) -> None:
    """Insert the default user profile and watchlist, if not already present.

    No-op when the default user profile already exists, so re-running against
    a populated database never duplicates or overwrites data.
    """
    existing = conn.execute(
        "SELECT id FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
    ).fetchone()
    if existing is not None:
        return

    conn.execute(
        "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
        (DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, _now()),
    )
    conn.executemany(
        "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
        [
            (str(uuid.uuid4()), DEFAULT_USER_ID, ticker, _now())
            for ticker in DEFAULT_WATCHLIST_TICKERS
        ],
    )
    conn.commit()


def init_db(conn: sqlite3.Connection) -> None:
    """Create schema and seed default data. Idempotent — safe to call every startup."""
    create_schema(conn)
    seed_default_data(conn)


def ensure_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection to the database, lazily creating and seeding it first.

    Intended for use on first request / app startup: if `db_path` is missing
    or empty, the schema is created and default data seeded; if it already
    exists and is populated, this is a no-op beyond opening the connection.
    """
    conn = get_connection(db_path)
    init_db(conn)
    return conn
