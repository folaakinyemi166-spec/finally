"""Portfolio REST endpoints (PLAN.md §8)."""

from __future__ import annotations

from fastapi import APIRouter

from app.db import snapshots
from app.market import PriceCache
from app.schemas import TradeRequest
from app.trading import execute_trade, get_portfolio_summary


def create_portfolio_router(price_cache: PriceCache) -> APIRouter:
    router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

    @router.get("")
    async def get_portfolio() -> dict:
        return get_portfolio_summary(price_cache)

    @router.post("/trade")
    async def post_trade(body: TradeRequest) -> dict:
        return execute_trade(body.ticker, body.side, body.quantity, price_cache)

    @router.get("/history")
    async def get_history() -> list[dict]:
        return [s.to_dict() for s in snapshots.list_snapshots()]

    return router
