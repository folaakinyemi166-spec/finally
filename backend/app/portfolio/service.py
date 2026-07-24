"""Portfolio business logic: valuation, trade execution, P&L, and snapshots.

Operates on a plain `sqlite3.Connection` (row_factory = sqlite3.Row) and a
`PriceCache`. Callers own the connection lifecycle (open/close per request or
per background tick) — this module never opens its own connections.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime

from app.db.init import DEFAULT_USER_ID
from app.market.cache import PriceCache

from .errors import InsufficientCashError, InsufficientSharesError, UnknownTickerError

# Tolerance for float comparisons on cash/share quantities, to avoid floating
# point noise (e.g. 9.999999999999998) rejecting a legitimate exact trade.
_EPSILON = 1e-9


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _get_cash_balance(conn: sqlite3.Connection, user_id: str) -> float:
    row = conn.execute(
        "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
    ).fetchone()
    return row["cash_balance"] if row is not None else 0.0


def _get_position(conn: sqlite3.Connection, user_id: str, ticker: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
        (user_id, ticker),
    ).fetchone()


def _positions_with_pnl(
    conn: sqlite3.Connection, price_cache: PriceCache, user_id: str
) -> list[dict]:
    rows = conn.execute(
        "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ? ORDER BY ticker",
        (user_id,),
    ).fetchall()

    positions = []
    for row in rows:
        ticker = row["ticker"]
        quantity = row["quantity"]
        avg_cost = row["avg_cost"]
        # Fall back to avg_cost (zero P&L) if the ticker has no live price,
        # e.g. it was dropped from the watchlist after the position was opened.
        current_price = price_cache.get_price(ticker)
        if current_price is None:
            current_price = avg_cost

        market_value = quantity * current_price
        unrealized_pnl = (current_price - avg_cost) * quantity
        unrealized_pnl_percent = (
            (current_price - avg_cost) / avg_cost * 100 if avg_cost else 0.0
        )

        positions.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": unrealized_pnl_percent,
            }
        )
    return positions


def get_portfolio(
    conn: sqlite3.Connection, price_cache: PriceCache, user_id: str = DEFAULT_USER_ID
) -> dict:
    """Current cash balance, positions (with live P&L), and total value."""
    cash_balance = _get_cash_balance(conn, user_id)
    positions = _positions_with_pnl(conn, price_cache, user_id)

    total_value = cash_balance + sum(p["market_value"] for p in positions)
    total_unrealized_pnl = sum(p["unrealized_pnl"] for p in positions)

    return {
        "cash_balance": cash_balance,
        "positions": positions,
        "total_value": total_value,
        "total_unrealized_pnl": total_unrealized_pnl,
    }


def execute_trade(
    conn: sqlite3.Connection,
    price_cache: PriceCache,
    ticker: str,
    side: str,
    quantity: float,
    user_id: str = DEFAULT_USER_ID,
) -> dict:
    """Execute a market order: instant fill at the current cached price.

    Raises:
        UnknownTickerError: no live price is cached for `ticker`.
        InsufficientCashError: a buy would cost more cash than is available.
        InsufficientSharesError: a sell quantity exceeds the shares held.

    All validation happens before any write, so a rejected trade never
    touches the database.
    """
    ticker = ticker.strip().upper()
    price = price_cache.get_price(ticker)
    if price is None:
        raise UnknownTickerError(f"No live price available for ticker '{ticker}'")

    cash_balance = _get_cash_balance(conn, user_id)
    position = _get_position(conn, user_id, ticker)
    now = _now()

    if side == "buy":
        cost = price * quantity
        if cost > cash_balance + _EPSILON:
            raise InsufficientCashError(
                f"Insufficient cash: trade costs {cost:.2f}, only {cash_balance:.2f} available"
            )
        new_cash = cash_balance - cost
        if position is None:
            conn.execute(
                "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, ticker, quantity, price, now),
            )
        else:
            old_qty = position["quantity"]
            old_avg = position["avg_cost"]
            new_qty = old_qty + quantity
            new_avg = (old_qty * old_avg + quantity * price) / new_qty
            conn.execute(
                "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? WHERE id = ?",
                (new_qty, new_avg, now, position["id"]),
            )
        conn.execute("UPDATE users_profile SET cash_balance = ? WHERE id = ?", (new_cash, user_id))

    elif side == "sell":
        owned = position["quantity"] if position is not None else 0.0
        if position is None or quantity > owned + _EPSILON:
            raise InsufficientSharesError(
                f"Insufficient shares: trying to sell {quantity}, only {owned} held"
            )
        proceeds = price * quantity
        new_cash = cash_balance + proceeds
        new_qty = owned - quantity
        if new_qty <= _EPSILON:
            conn.execute("DELETE FROM positions WHERE id = ?", (position["id"],))
        else:
            conn.execute(
                "UPDATE positions SET quantity = ?, updated_at = ? WHERE id = ?",
                (new_qty, now, position["id"]),
            )
        conn.execute("UPDATE users_profile SET cash_balance = ? WHERE id = ?", (new_cash, user_id))

    else:
        raise ValueError(f"Invalid side: {side!r}")

    conn.execute(
        "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, ticker, side, quantity, price, now),
    )
    conn.commit()

    record_snapshot(conn, price_cache, user_id)

    return {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": price,
        "executed_at": now,
        "portfolio": get_portfolio(conn, price_cache, user_id),
    }


def record_snapshot(
    conn: sqlite3.Connection, price_cache: PriceCache, user_id: str = DEFAULT_USER_ID
) -> None:
    """Insert a portfolio_snapshots row for the current total value.

    Called immediately after each trade, and on a 30s cadence by
    `app.portfolio.background.snapshot_loop`.
    """
    portfolio = get_portfolio(conn, price_cache, user_id)
    conn.execute(
        "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) "
        "VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, portfolio["total_value"], _now()),
    )
    conn.commit()


def get_history(conn: sqlite3.Connection, user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """Portfolio value snapshots over time, oldest first, for the P&L chart."""
    rows = conn.execute(
        "SELECT total_value, recorded_at FROM portfolio_snapshots "
        "WHERE user_id = ? ORDER BY recorded_at ASC",
        (user_id,),
    ).fetchall()
    return [{"total_value": row["total_value"], "recorded_at": row["recorded_at"]} for row in rows]
