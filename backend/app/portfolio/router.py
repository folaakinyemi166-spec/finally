"""FastAPI router for portfolio endpoints.

Mirrors the factory pattern used by `app.market.stream.create_stream_router`:
the PriceCache (and optional db_path override, mainly for tests) is injected
rather than imported as a module-level global.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.db.connection import get_connection
from app.market.cache import PriceCache

from .errors import InsufficientCashError, InsufficientSharesError, UnknownTickerError
from .schemas import HistoryOut, PortfolioOut, TradeOut, TradeRequest
from .service import execute_trade, get_history, get_portfolio


def create_portfolio_router(price_cache: PriceCache, db_path: str | Path | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

    @router.get("", response_model=PortfolioOut)
    def read_portfolio() -> dict:
        conn = get_connection(db_path)
        try:
            return get_portfolio(conn, price_cache)
        finally:
            conn.close()

    @router.post("/trade", response_model=TradeOut)
    def post_trade(payload: TradeRequest) -> dict:
        conn = get_connection(db_path)
        try:
            return execute_trade(conn, price_cache, payload.ticker, payload.side, payload.quantity)
        except UnknownTickerError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except InsufficientCashError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except InsufficientSharesError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            conn.close()

    @router.get("/history", response_model=HistoryOut)
    def read_history() -> dict:
        conn = get_connection(db_path)
        try:
            return {"history": get_history(conn)}
        finally:
            conn.close()

    return router
