"""Tests for schema creation and lazy initialization."""

import sqlite3

from app.db.connection import get_connection, init_db
from app.db.schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS

EXPECTED_TABLES = {
    "users_profile",
    "watchlist",
    "positions",
    "trades",
    "portfolio_snapshots",
    "chat_messages",
}


class TestSchemaInit:
    """Fresh-DB schema creation and seeding."""

    def test_creates_all_tables(self, db_path):
        path = init_db()
        assert path == db_path.resolve()
        conn = sqlite3.connect(path)
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        table_names = {r[0] for r in rows}
        assert EXPECTED_TABLES.issubset(table_names)

    def test_seeds_default_user_profile(self, db_path):
        init_db()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
            ).fetchone()
        assert row is not None
        assert row["cash_balance"] == DEFAULT_CASH_BALANCE

    def test_seeds_default_watchlist(self, db_path):
        init_db()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ?", (DEFAULT_USER_ID,)
            ).fetchall()
        tickers = {r["ticker"] for r in rows}
        assert tickers == set(DEFAULT_WATCHLIST_TICKERS)
        assert len(rows) == 10

    def test_db_file_created_on_disk(self, db_path):
        assert not db_path.exists()
        init_db()
        assert db_path.exists()


class TestLazyInitIdempotency:
    """Calling init_db()/get_connection() repeatedly must not error or duplicate seed data."""

    def test_init_twice_does_not_duplicate_seed_rows(self, db_path):
        init_db()
        init_db()
        with get_connection() as conn:
            (user_count,) = conn.execute("SELECT COUNT(*) FROM users_profile").fetchone()
            (watchlist_count,) = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()
        assert user_count == 1
        assert watchlist_count == 10

    def test_init_twice_does_not_raise(self, db_path):
        init_db()
        init_db()  # should not raise

    def test_get_connection_triggers_lazy_init(self, db_path):
        assert not db_path.exists()
        with get_connection() as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM users_profile").fetchone()
        assert count == 1
