"""Connection handling and lazy schema/seed initialization.

Path resolution
---------------
The database file path is resolved in this order:

1. The ``FINALLY_DB_PATH`` env var, if set — used verbatim (expanded/resolved).
2. Otherwise, ``<project-root>/db/finally.db`` — this is the path PLAN.md §11
   bind-mounts into the Docker container as ``db/finally.db`` on the host.
   Project root is resolved relative to this file
   (``backend/app/db/connection.py`` -> up three levels -> ``finally/``), so it
   works the same whether the backend is run from Docker or `uv run` locally.

Thread-safety approach
-----------------------
sqlite3.Connection objects are not safe to share across threads, and FastAPI
may dispatch request handlers onto different threads (sync endpoints run in a
thread pool). Rather than holding one long-lived shared connection guarded by
a lock — which would serialize every read behind every write — each call
opens a short-lived connection scoped to a single unit of work (one repository
function call) and closes it immediately. This mirrors the "own your
resource for as long as you need it, then let go" spirit of PriceCache's
locking in app/market/cache.py, just applied per-connection instead of
per-lock, since SQLite (not a Python object) is the shared resource here.

Concurrent access safety comes from:
- WAL journal mode, so readers don't block the writer and vice versa.
- ``busy_timeout`` (via ``sqlite3.connect(..., timeout=...)``) so a writer
  waiting on another writer retries instead of raising "database is locked".
- A process-local ``threading.Lock`` around schema creation/seeding, since
  that's a check-then-act sequence (is the DB empty? if so, insert seed rows)
  that must not race across threads on first startup.

Schema creation and the seed check both use ``IF NOT EXISTS`` / a row-count
guard, so ``init_db()`` is idempotent — safe to call on every request or once
at startup.

Note: this design does not support the special ``:memory:`` SQLite path,
since each call opens a brand new connection (a fresh, empty in-memory
database every time). Tests should point ``FINALLY_DB_PATH`` (or the
``db_path`` argument) at a temp file instead.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS, SCHEMA_SQL
from .util import now_iso

_ENV_VAR = "FINALLY_DB_PATH"
_DEFAULT_RELATIVE_PATH = Path("db") / "finally.db"

_init_lock = threading.Lock()


def get_db_path() -> Path:
    """Resolve the configured database file path (see module docstring)."""
    env_path = os.environ.get(_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser().resolve()
    project_root = Path(__file__).resolve().parents[3]
    return (project_root / _DEFAULT_RELATIVE_PATH).resolve()


def init_db(db_path: str | Path | None = None) -> Path:
    """Create the schema and seed default data if missing. Idempotent.

    Safe to call repeatedly (e.g. once at app startup, and/or lazily on every
    request) — table creation uses ``IF NOT EXISTS`` and seeding only happens
    if ``users_profile`` is empty.

    Returns the resolved path that was initialized.
    """
    path = Path(db_path).resolve() if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with _init_lock:
        conn = sqlite3.connect(path, timeout=10)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA_SQL)
            _seed_if_empty(conn)
            conn.commit()
        finally:
            conn.close()
    return path


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert the default user profile + watchlist, but only on a fresh DB."""
    (count,) = conn.execute("SELECT COUNT(*) FROM users_profile").fetchone()
    if count > 0:
        return

    created_at = now_iso()
    conn.execute(
        "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
        (DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, created_at),
    )
    conn.executemany(
        "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
        [
            (str(uuid.uuid4()), DEFAULT_USER_ID, ticker, created_at)
            for ticker in DEFAULT_WATCHLIST_TICKERS
        ],
    )


@contextmanager
def get_connection(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a short-lived connection for one unit of work.

    Ensures the schema/seed exists first (lazy init), then opens a fresh
    connection with row access by column name. Commits on clean exit, rolls
    back on exception, and always closes the connection.
    """
    path = init_db(db_path)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
