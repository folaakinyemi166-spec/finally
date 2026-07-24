"""Tests for schema constraints (uniqueness, checks)."""

import sqlite3

import pytest

from app.db.init import create_schema


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_schema(connection)
    yield connection
    connection.close()


class TestWatchlistConstraints:
    def test_unique_ticker_per_user(self, conn):
        conn.execute(
            "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            ("w1", "default", "AAPL", "2026-01-01T00:00:00"),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                ("w2", "default", "AAPL", "2026-01-01T00:00:00"),
            )


class TestPositionsConstraints:
    def test_unique_ticker_per_user(self, conn):
        conn.execute(
            "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("p1", "default", "AAPL", 10.0, 190.0, "2026-01-01T00:00:00"),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("p2", "default", "AAPL", 5.0, 200.0, "2026-01-01T00:00:00"),
            )


class TestTradesConstraints:
    def test_side_must_be_buy_or_sell(self, conn):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("t1", "default", "AAPL", "hold", 1.0, 190.0, "2026-01-01T00:00:00"),
            )

    def test_valid_sides_accepted(self, conn):
        for side in ("buy", "sell"):
            conn.execute(
                "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"t-{side}", "default", "AAPL", side, 1.0, 190.0, "2026-01-01T00:00:00"),
            )
        conn.commit()


class TestChatMessagesConstraints:
    def test_role_must_be_user_or_assistant(self, conn):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO chat_messages (id, user_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("m1", "default", "system", "hi", "2026-01-01T00:00:00"),
            )

    def test_actions_column_is_nullable(self, conn):
        conn.execute(
            "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("m1", "default", "user", "hi", None, "2026-01-01T00:00:00"),
        )
        conn.commit()
