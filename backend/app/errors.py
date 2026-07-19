"""Business-rule exceptions raised by the API/service layer.

Distinct from app.db.errors, which covers raw persistence-layer failures.
Each carries an HTTP status code so a single FastAPI exception handler in
main.py can translate any of them into a clean JSON error response instead
of an unhandled 500.
"""

from __future__ import annotations


class AppError(Exception):
    """Base for service-layer errors that carry an HTTP status code.

    A single FastAPI exception handler in main.py catches this (and reads
    status_code) so every subclass below gets a clean JSON error response
    without its own handler.
    """

    status_code = 400


class TradingError(AppError):
    """Base for trading/watchlist business-rule violations. Maps to HTTP 400 by default."""


class NoPriceAvailableError(TradingError):
    """Raised when a trade targets a ticker with no cached price (PLAN.md §8)."""


class InsufficientFundsError(TradingError):
    """Raised when a buy would cost more than the user's cash balance."""


class InsufficientSharesError(TradingError):
    """Raised when a sell exceeds the user's held quantity."""


class WatchlistCapExceededError(TradingError):
    """Raised when adding a ticker would exceed the 30-ticker soft cap (PLAN.md §7)."""


class TickerNotFoundError(TradingError):
    """Raised when removing a ticker that isn't on the watchlist."""

    status_code = 404


class LLMError(AppError):
    """Raised when the upstream LLM call fails or returns unparseable output (PLAN.md §9)."""

    status_code = 502
