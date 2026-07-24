"""SQLite persistence layer: schema, connections, lazy init, and seed data."""

from app.db.connection import get_connection, get_db_path
from app.db.init import (
    DEFAULT_CASH_BALANCE,
    DEFAULT_USER_ID,
    DEFAULT_WATCHLIST_TICKERS,
    create_schema,
    ensure_db,
    init_db,
    seed_default_data,
)
from app.db.schema import TABLE_NAMES

__all__ = [
    "DEFAULT_CASH_BALANCE",
    "DEFAULT_USER_ID",
    "DEFAULT_WATCHLIST_TICKERS",
    "TABLE_NAMES",
    "create_schema",
    "ensure_db",
    "get_connection",
    "get_db_path",
    "init_db",
    "seed_default_data",
]
