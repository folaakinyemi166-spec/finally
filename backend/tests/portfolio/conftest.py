"""Shared fixtures for portfolio tests: a seeded in-memory DB and price cache."""

import sqlite3

import pytest

from app.db.init import create_schema, seed_default_data
from app.market.cache import PriceCache


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_schema(connection)
    seed_default_data(connection)
    yield connection
    connection.close()


@pytest.fixture
def price_cache():
    cache = PriceCache()
    cache.update("AAPL", 100.0)
    cache.update("GOOGL", 50.0)
    return cache
