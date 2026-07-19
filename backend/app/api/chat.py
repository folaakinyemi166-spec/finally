"""Chat REST endpoint (PLAN.md §8, §9)."""

from __future__ import annotations

from fastapi import APIRouter

from app.chat import handle_chat_message
from app.market import MarketDataSource, PriceCache
from app.schemas import ChatRequest


def create_chat_router(price_cache: PriceCache, market_source: MarketDataSource) -> APIRouter:
    router = APIRouter(prefix="/api/chat", tags=["chat"])

    @router.post("")
    async def post_chat(body: ChatRequest) -> dict:
        return await handle_chat_message(body.message, price_cache, market_source)

    return router
