"""FastAPI application entrypoint (PLAN.md §3, §11).

Serves the REST/SSE API under /api/* and, once the frontend is built, the
static Next.js export from app/static/ at "/" (single-origin, single-port —
PLAN.md §3). create_app() is a factory rather than a module-level singleton
so tests can spin up isolated PriceCache/MarketDataSource instances per test
(MarketDataSource.start() may only be called once per instance).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.chat import create_chat_router
from app.api.health import router as health_router
from app.api.portfolio import create_portfolio_router
from app.api.watchlist import create_watchlist_router
from app.db import init_db, watchlist
from app.db.errors import DuplicateTickerError
from app.errors import AppError
from app.market import PriceCache, create_market_data_source, create_stream_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    price_cache = PriceCache()
    market_source = create_market_data_source(price_cache)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db()
        tickers = [entry.ticker for entry in watchlist.list_watchlist()]
        await market_source.start(tickers)
        logger.info("Market data source started for %d tickers", len(tickers))
        yield
        await market_source.stop()

    app = FastAPI(title="FinAlly API", lifespan=lifespan)

    # Only needed for `next dev` on :3000 talking to the backend on :8000;
    # the production single-container deploy is same-origin (PLAN.md §11).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.exception_handler(DuplicateTickerError)
    async def _duplicate_ticker_handler(request: Request, exc: DuplicateTickerError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(health_router)
    app.include_router(create_stream_router(price_cache))
    app.include_router(create_portfolio_router(price_cache))
    app.include_router(create_watchlist_router(price_cache, market_source))
    app.include_router(create_chat_router(price_cache, market_source))

    # Registered last: API routes above always match first, so this only
    # catches paths that aren't /api/* (PLAN.md §3).
    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app


app = create_app()
