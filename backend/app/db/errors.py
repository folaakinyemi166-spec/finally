"""Exceptions raised by the db package.

Repository functions translate raw sqlite3 constraint failures into these
typed errors so callers (the API layer) can return clean validation messages
instead of leaking DB internals (PLAN.md §8).
"""

from __future__ import annotations


class DuplicateTickerError(Exception):
    """Raised by watchlist.add_ticker() when (user_id, ticker) already exists."""
