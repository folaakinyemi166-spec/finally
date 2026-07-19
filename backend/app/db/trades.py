"""Trades repository — append-only trade execution log."""

from __future__ import annotations

import uuid

from .connection import get_connection
from .models import Trade
from .schema import DEFAULT_USER_ID
from .util import now_iso


def insert_trade(
    ticker: str, side: str, quantity: float, price: float, user_id: str = DEFAULT_USER_ID
) -> Trade:
    """Append a trade record.

    `side` must be 'buy' or 'sell' (enforced by a CHECK constraint at the DB
    level; validate before calling to get a friendlier error).
    """
    trade_id = str(uuid.uuid4())
    executed_at = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trade_id, user_id, ticker, side, quantity, price, executed_at),
        )
    return Trade(
        id=trade_id,
        user_id=user_id,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=price,
        executed_at=executed_at,
    )


def list_trades(user_id: str = DEFAULT_USER_ID, limit: int | None = None) -> list[Trade]:
    """List a user's trades, most recent first. Pass `limit` to cap the result."""
    query = "SELECT * FROM trades WHERE user_id = ? ORDER BY executed_at DESC"
    params: tuple = (user_id,)
    if limit is not None:
        query += " LIMIT ?"
        params = (user_id, limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Trade.from_row(r) for r in rows]
