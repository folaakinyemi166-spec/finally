"""Watchlist REST endpoints (PLAN.md §7 cap, §8 contract)."""

from __future__ import annotations

from fastapi import APIRouter

from app.errors import TickerNotFoundError
from app.market import MarketDataSource, PriceCache
from app.schemas import WatchlistAddRequest
from app.watchlist_service import add_to_watchlist, build_watchlist_view, remove_from_watchlist


def create_watchlist_router(price_cache: PriceCache, market_source: MarketDataSource) -> APIRouter:
    router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

    @router.get("")
    async def get_watchlist() -> list[dict]:
        return build_watchlist_view(price_cache)

    @router.post("")
    async def add_ticker(body: WatchlistAddRequest) -> dict:
        # WatchlistCapExceededError / DuplicateTickerError propagate to
        # main.py's global exception handlers (both are/behave as AppError).
        entry = await add_to_watchlist(body.ticker, market_source)
        return entry.to_dict()

    @router.delete("/{ticker}")
    async def remove_ticker(ticker: str) -> dict:
        ticker = ticker.strip().upper()
        removed = await remove_from_watchlist(ticker, market_source)
        if not removed:
            raise TickerNotFoundError(f"{ticker!r} is not on the watchlist")
        return {"ticker": ticker, "removed": True}

    return router
