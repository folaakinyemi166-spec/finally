"""Watchlist mutations and view-building shared by the manual REST endpoint
(app.api.watchlist) and the LLM-driven chat flow (app.chat) — PLAN.md §7
(30-ticker cap) and §9 point 6 (LLM actions reuse manual-trade validation).
"""

from __future__ import annotations

from app.db import watchlist
from app.db.models import WatchlistEntry
from app.errors import WatchlistCapExceededError
from app.market import MarketDataSource, PriceCache

# Soft cap enforced here, not in the db layer (PLAN.md §7).
WATCHLIST_CAP = 30

# Shape returned for a ticker with no cached price yet — e.g. just added and
# not yet picked up by the market data source (PLAN.md §8).
_NULL_PRICE_FIELDS = {
    "price": None,
    "previous_price": None,
    "timestamp": None,
    "change": None,
    "change_percent": None,
    "direction": None,
}


def build_watchlist_view(price_cache: PriceCache) -> list[dict]:
    """Watchlist entries joined with their latest cached price."""
    result = []
    for entry in watchlist.list_watchlist():
        update = price_cache.get(entry.ticker)
        price_fields = update.to_dict() if update is not None else _NULL_PRICE_FIELDS
        result.append({**entry.to_dict(), **price_fields})
    return result


async def add_to_watchlist(ticker: str, market_source: MarketDataSource) -> WatchlistEntry:
    """Add a ticker to the watchlist and register it with the market data source.

    Raises WatchlistCapExceededError at the 30-ticker cap, or
    app.db.errors.DuplicateTickerError if already present — both are
    AppError subclasses (or map cleanly via main.py's exception handlers),
    so callers can let them propagate.
    """
    if watchlist.count_tickers() >= WATCHLIST_CAP:
        raise WatchlistCapExceededError(f"Watchlist is at the {WATCHLIST_CAP}-ticker limit")
    entry = watchlist.add_ticker(ticker)
    await market_source.add_ticker(ticker)
    return entry


async def remove_from_watchlist(ticker: str, market_source: MarketDataSource) -> bool:
    """Remove a ticker from the watchlist and the market data source.

    Returns False if the ticker wasn't on the watchlist (a no-op).
    """
    removed = watchlist.remove_ticker(ticker)
    if removed:
        await market_source.remove_ticker(ticker)
    return removed
