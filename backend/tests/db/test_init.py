"""Tests for schema creation, lazy init, and seed data."""

import sqlite3

import pytest

from app.db.connection import get_connection
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


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()


class TestCreateSchema:
    def test_creates_all_tables(self, conn):
        create_schema(conn)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        table_names = {row["name"] for row in rows}
        for expected in TABLE_NAMES:
            assert expected in table_names

    def test_rerun_is_noop(self, conn):
        create_schema(conn)
        create_schema(conn)  # Should not raise
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        table_names = [row["name"] for row in rows]
        for expected in TABLE_NAMES:
            assert table_names.count(expected) == 1


class TestSeedDefaultData:
    def test_seeds_user_profile(self, conn):
        create_schema(conn)
        seed_default_data(conn)
        row = conn.execute(
            "SELECT * FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
        ).fetchone()
        assert row is not None
        assert row["cash_balance"] == DEFAULT_CASH_BALANCE
        assert row["created_at"]

    def test_seeds_ten_watchlist_tickers(self, conn):
        create_schema(conn)
        seed_default_data(conn)
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ?", (DEFAULT_USER_ID,)
        ).fetchall()
        tickers = {row["ticker"] for row in rows}
        assert len(tickers) == 10
        assert tickers == set(DEFAULT_WATCHLIST_TICKERS)

    def test_rerun_does_not_duplicate(self, conn):
        create_schema(conn)
        seed_default_data(conn)
        seed_default_data(conn)  # Should be a no-op
        profiles = conn.execute("SELECT * FROM users_profile").fetchall()
        assert len(profiles) == 1
        watchlist = conn.execute("SELECT * FROM watchlist").fetchall()
        assert len(watchlist) == 10

    def test_does_not_overwrite_modified_cash_balance(self, conn):
        create_schema(conn)
        seed_default_data(conn)
        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
            (5000.0, DEFAULT_USER_ID),
        )
        conn.commit()
        seed_default_data(conn)  # Re-running must not reset the balance
        row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (DEFAULT_USER_ID,),
        ).fetchone()
        assert row["cash_balance"] == 5000.0


class TestInitDb:
    def test_creates_schema_and_seeds(self, conn):
        init_db(conn)
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        for expected in TABLE_NAMES:
            assert expected in tables
        assert (
            conn.execute("SELECT COUNT(*) AS c FROM users_profile").fetchone()["c"]
            == 1
        )
        assert (
            conn.execute("SELECT COUNT(*) AS c FROM watchlist").fetchone()["c"] == 10
        )

    def test_rerun_against_populated_db_is_noop(self, conn):
        init_db(conn)
        init_db(conn)
        assert (
            conn.execute("SELECT COUNT(*) AS c FROM users_profile").fetchone()["c"]
            == 1
        )
        assert (
            conn.execute("SELECT COUNT(*) AS c FROM watchlist").fetchone()["c"] == 10
        )


class TestEnsureDb:
    def test_fresh_db_file_is_created_and_seeded(self, tmp_path):
        db_path = tmp_path / "nested" / "finally.db"
        assert not db_path.exists()

        conn = ensure_db(db_path)
        try:
            assert db_path.exists()
            assert (
                conn.execute(
                    "SELECT COUNT(*) AS c FROM users_profile"
                ).fetchone()["c"]
                == 1
            )
            assert (
                conn.execute("SELECT COUNT(*) AS c FROM watchlist").fetchone()["c"]
                == 10
            )
        finally:
            conn.close()

    def test_reopening_existing_db_does_not_reseed(self, tmp_path):
        db_path = tmp_path / "finally.db"

        first = ensure_db(db_path)
        first.execute(
            "UPDATE users_profile SET cash_balance = 42.0 WHERE id = 'default'"
        )
        first.commit()
        first.close()

        second = ensure_db(db_path)
        try:
            row = second.execute(
                "SELECT cash_balance FROM users_profile WHERE id = 'default'"
            ).fetchone()
            assert row["cash_balance"] == 42.0
            assert (
                second.execute("SELECT COUNT(*) AS c FROM watchlist").fetchone()["c"]
                == 10
            )
        finally:
            second.close()


class TestGetConnection:
    def test_creates_parent_directory(self, tmp_path):
        db_path = tmp_path / "does" / "not" / "exist" / "finally.db"
        conn = get_connection(db_path)
        try:
            assert db_path.parent.is_dir()
        finally:
            conn.close()

    def test_row_factory_allows_dict_style_access(self, tmp_path):
        db_path = tmp_path / "finally.db"
        conn = get_connection(db_path)
        try:
            create_schema(conn)
            seed_default_data(conn)
            row = conn.execute(
                "SELECT * FROM users_profile WHERE id = 'default'"
            ).fetchone()
            assert row["id"] == "default"
        finally:
            conn.close()
