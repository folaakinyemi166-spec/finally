"""Positions repository — current holdings, one row per (user, ticker)."""

from __future__ import annotations

import uuid

from .connection import get_connection
from .models import Position
from .schema import DEFAULT_USER_ID
from .util import now_iso


def get_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> Position | None:
    """Fetch a single position, or None if the user holds no shares of it."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        ).fetchone()
    return Position.from_row(row) if row else None


def list_positions(user_id: str = DEFAULT_USER_ID) -> list[Position]:
    """List all positions for a user, alphabetical by ticker."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM positions WHERE user_id = ? ORDER BY ticker", (user_id,)
        ).fetchall()
    return [Position.from_row(r) for r in rows]


def upsert_position(
    ticker: str, quantity: float, avg_cost: float, user_id: str = DEFAULT_USER_ID
) -> Position:
    """Create or fully replace a position's quantity/avg_cost.

    Trade-execution logic (owned by the API layer) is responsible for
    computing the new quantity and weighted-average cost; this just persists
    the result in one statement.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        ).fetchone()
        position_id = row["id"] if row else str(uuid.uuid4())
        updated_at = now_iso()
        conn.execute(
            """
            INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id, ticker) DO UPDATE SET
                quantity = excluded.quantity,
                avg_cost = excluded.avg_cost,
                updated_at = excluded.updated_at
            """,
            (position_id, user_id, ticker, quantity, avg_cost, updated_at),
        )
    return Position(
        id=position_id,
        user_id=user_id,
        ticker=ticker,
        quantity=quantity,
        avg_cost=avg_cost,
        updated_at=updated_at,
    )


def delete_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> None:
    """Remove a position row entirely (e.g. quantity hit zero after a sell)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker))
