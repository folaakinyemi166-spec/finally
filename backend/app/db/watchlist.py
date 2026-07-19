"""Watchlist repository — tickers the user is tracking.

The 30-ticker soft cap (PLAN.md §7) is enforced by the API layer, not here —
use count_tickers() to check before calling add_ticker().
"""

from __future__ import annotations

import sqlite3
import uuid

from .connection import get_connection
from .errors import DuplicateTickerError
from .models import WatchlistEntry
from .schema import DEFAULT_USER_ID
from .util import now_iso


def list_watchlist(user_id: str = DEFAULT_USER_ID) -> list[WatchlistEntry]:
    """Return all watchlist entries for a user, oldest-added first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? ORDER BY added_at", (user_id,)
        ).fetchall()
    return [WatchlistEntry.from_row(r) for r in rows]


def count_tickers(user_id: str = DEFAULT_USER_ID) -> int:
    """Count tickers on the user's watchlist — used by the API layer for the cap check."""
    with get_connection() as conn:
        (count,) = conn.execute(
            "SELECT COUNT(*) FROM watchlist WHERE user_id = ?", (user_id,)
        ).fetchone()
    return count


def add_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> WatchlistEntry:
    """Add a ticker to the watchlist.

    Raises DuplicateTickerError if (user_id, ticker) already exists, so the
    API layer can return a clean validation error instead of a raw DB
    constraint failure (PLAN.md §8).
    """
    entry_id = str(uuid.uuid4())
    added_at = now_iso()
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                (entry_id, user_id, ticker, added_at),
            )
    except sqlite3.IntegrityError as exc:
        raise DuplicateTickerError(f"{ticker!r} is already on the watchlist") from exc
    return WatchlistEntry(id=entry_id, user_id=user_id, ticker=ticker, added_at=added_at)


def remove_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Remove a ticker from the watchlist. Returns True if a row was deleted."""
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        )
    return cur.rowcount > 0
