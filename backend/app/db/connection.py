"""SQLite connection handling and database path resolution."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# backend/app/db/connection.py -> repo root (parent of backend/)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = _REPO_ROOT / "db" / "finally.db"

DB_PATH_ENV_VAR = "FINALLY_DB_PATH"


def get_db_path() -> Path:
    """Resolve the SQLite file path.

    Honors the `FINALLY_DB_PATH` env var (set in Docker to the mounted
    volume); otherwise defaults to `<repo root>/db/finally.db` for local dev.
    """
    override = os.environ.get(DB_PATH_ENV_VAR)
    return Path(override) if override else _DEFAULT_DB_PATH


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection, creating the parent directory if needed.

    Rows are returned as `sqlite3.Row` (dict-like access by column name).
    """
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
