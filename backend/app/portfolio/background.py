"""Background task: periodic portfolio snapshots for the P&L chart."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.db.connection import get_connection
from app.db.init import DEFAULT_USER_ID
from app.market.cache import PriceCache

from .service import record_snapshot

logger = logging.getLogger(__name__)

DEFAULT_SNAPSHOT_INTERVAL = 30.0


async def snapshot_loop(
    price_cache: PriceCache,
    db_path: str | Path | None = None,
    user_id: str = DEFAULT_USER_ID,
    interval: float = DEFAULT_SNAPSHOT_INTERVAL,
) -> None:
    """Record a portfolio snapshot every `interval` seconds until cancelled.

    Intended to be run as an asyncio background task from the app lifespan:

        task = asyncio.create_task(snapshot_loop(price_cache))
        ...  # app shutdown
        task.cancel()
        await task

    Opens a fresh connection per tick rather than holding one open for the
    life of the task.
    """
    try:
        while True:
            await asyncio.sleep(interval)
            conn = get_connection(db_path)
            try:
                record_snapshot(conn, price_cache, user_id)
            except Exception:
                logger.exception("Portfolio snapshot tick failed")
            finally:
                conn.close()
    except asyncio.CancelledError:
        raise
