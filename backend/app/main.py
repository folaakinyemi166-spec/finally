"""FastAPI application entrypoint.

Wires together the market data stream, portfolio, watchlist, and chat
routers behind a single app, manages the market data source and snapshot
background tasks via the app lifespan, and serves the static frontend
export (when present) from the same origin.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.ai import create_chat_router
from app.api import create_watchlist_router
from app.db import DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS, ensure_db
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.portfolio import create_portfolio_router, snapshot_loop

logger = logging.getLogger(__name__)

# Populated by the Docker build (frontend `next build` export copied here);
# absent in local dev unless the frontend has been built. Overridable so the
# Docker image can point at wherever the build stage placed it.
STATIC_DIR_ENV_VAR = "FINALLY_STATIC_DIR"
_DEFAULT_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def _get_static_dir() -> Path:
    override = os.environ.get(STATIC_DIR_ENV_VAR)
    return Path(override) if override else _DEFAULT_STATIC_DIR


def _load_watchlist_tickers() -> list[str]:
    """Read the persisted watchlist so the market source tracks the right tickers.

    Falls back to the default seed tickers if the watchlist is somehow empty.
    """
    conn = ensure_db()
    try:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at",
            (DEFAULT_USER_ID,),
        ).fetchall()
    finally:
        conn.close()
    tickers = [row["ticker"] for row in rows]
    return tickers or list(DEFAULT_WATCHLIST_TICKERS)


def create_app() -> FastAPI:
    price_cache = PriceCache()
    market_source = create_market_data_source(price_cache)

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        tickers = _load_watchlist_tickers()
        await market_source.start(tickers)
        snapshot_task = asyncio.create_task(snapshot_loop(price_cache))
        try:
            yield
        finally:
            snapshot_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await snapshot_task
            await market_source.stop()

    app = FastAPI(title="FinAlly", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(create_stream_router(price_cache))
    app.include_router(create_portfolio_router(price_cache))
    app.include_router(create_watchlist_router(price_cache))
    app.include_router(create_chat_router(price_cache))

    static_dir = _get_static_dir()
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    else:
        logger.warning("Static frontend directory not found at %s; frontend not served", static_dir)

    return app


app = create_app()
