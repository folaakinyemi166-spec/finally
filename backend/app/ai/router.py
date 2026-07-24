"""FastAPI router for the AI chat endpoint.

Mirrors the factory pattern used by `app.portfolio.router`: the PriceCache
(and optional db_path override, mainly for tests) is injected rather than
imported as a module-level global.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.db.connection import get_connection
from app.market.cache import PriceCache

from .errors import LLMResponseError
from .schemas import ChatRequest, ChatResponseOut
from .service import process_chat


def create_chat_router(price_cache: PriceCache, db_path: str | Path | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/chat", tags=["chat"])

    @router.post("", response_model=ChatResponseOut)
    def post_chat(payload: ChatRequest) -> ChatResponseOut:
        conn = get_connection(db_path)
        try:
            return process_chat(conn, price_cache, payload.message)
        except LLMResponseError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        finally:
            conn.close()

    return router
