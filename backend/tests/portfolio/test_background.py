"""Tests for the periodic portfolio snapshot background task."""

import asyncio
import sqlite3

import pytest

from app.db.connection import get_connection
from app.db.init import create_schema, seed_default_data
from app.market.cache import PriceCache
from app.portfolio.background import snapshot_loop
from app.portfolio.service import get_history


@pytest.mark.asyncio
async def test_snapshot_loop_records_ticks_until_cancelled(tmp_path):
    db_path = tmp_path / "test.db"
    seed_conn = sqlite3.connect(db_path)
    create_schema(seed_conn)
    seed_default_data(seed_conn)
    seed_conn.close()

    price_cache = PriceCache()
    price_cache.update("AAPL", 100.0)

    task = asyncio.create_task(snapshot_loop(price_cache, db_path=db_path, interval=0.01))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    conn = get_connection(db_path)
    history = get_history(conn)
    conn.close()
    assert len(history) >= 1
