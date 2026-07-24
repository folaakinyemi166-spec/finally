"""Watchlist CRUD API: list/add/remove tickers, enriched with live prices."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, field_validator

from app.db import DEFAULT_USER_ID, ensure_db
from app.market import PriceCache


class WatchlistAddRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("ticker must not be empty")
        return normalized


def _entry(ticker: str, price_cache: PriceCache) -> dict:
    """Build a watchlist entry, enriched with the latest cached price if known."""
    update = price_cache.get(ticker)
    if update is not None:
        return update.to_dict()
    return {
        "ticker": ticker,
        "price": None,
        "previous_price": None,
        "timestamp": None,
        "change": None,
        "change_percent": None,
        "direction": None,
    }


def create_watchlist_router(
    price_cache: PriceCache, db_path: str | Path | None = None
) -> APIRouter:
    """Create the watchlist CRUD router.

    Factory pattern injects the PriceCache and db_path without globals,
    matching the SSE stream router (see app/market/stream.py).
    """
    router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

    def _conn() -> sqlite3.Connection:
        return ensure_db(db_path)

    @router.get("")
    def list_watchlist() -> list[dict]:
        conn = _conn()
        try:
            rows = conn.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at",
                (DEFAULT_USER_ID,),
            ).fetchall()
        finally:
            conn.close()
        return [_entry(row["ticker"], price_cache) for row in rows]

    @router.post("", status_code=201)
    def add_ticker(payload: WatchlistAddRequest, response: Response) -> dict:
        ticker = payload.ticker
        conn = _conn()
        try:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) "
                "VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), DEFAULT_USER_ID, ticker, datetime.now(UTC).isoformat()),
            )
            conn.commit()
            if cursor.rowcount == 0:
                # Already on the watchlist — idempotent no-op, not a new resource.
                response.status_code = 200
        finally:
            conn.close()
        return _entry(ticker, price_cache)

    @router.delete("/{ticker}", status_code=204)
    def remove_ticker(ticker: str) -> Response:
        normalized = ticker.strip().upper()
        if not normalized:
            raise HTTPException(status_code=422, detail="ticker must not be empty")
        conn = _conn()
        try:
            conn.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                (DEFAULT_USER_ID, normalized),
            )
            conn.commit()
        finally:
            conn.close()
        return Response(status_code=204)

    return router
