"""Tests for the watchlist CRUD API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.watchlist import create_watchlist_router
from app.db import DEFAULT_WATCHLIST_TICKERS
from app.market import PriceCache


@pytest.fixture
def price_cache() -> PriceCache:
    return PriceCache()


@pytest.fixture
def client(tmp_path, price_cache) -> TestClient:
    db_path = tmp_path / "finally.db"
    app = FastAPI()
    app.include_router(create_watchlist_router(price_cache, db_path=db_path))
    return TestClient(app)


class TestListWatchlist:
    def test_lists_seeded_default_tickers(self, client):
        response = client.get("/api/watchlist")
        assert response.status_code == 200
        body = response.json()
        assert {entry["ticker"] for entry in body} == set(DEFAULT_WATCHLIST_TICKERS)
        assert len(body) == 10

    def test_entry_has_null_price_fields_when_uncached(self, client):
        response = client.get("/api/watchlist")
        entry = response.json()[0]
        assert entry["price"] is None
        assert entry["previous_price"] is None
        assert entry["direction"] is None

    def test_entry_reflects_cached_price(self, client, price_cache):
        price_cache.update("AAPL", 190.5)
        response = client.get("/api/watchlist")
        entries = {entry["ticker"]: entry for entry in response.json()}
        assert entries["AAPL"]["price"] == 190.5
        assert entries["AAPL"]["direction"] == "flat"


class TestAddTicker:
    def test_adds_new_ticker(self, client):
        response = client.post("/api/watchlist", json={"ticker": "pypl"})
        assert response.status_code == 201
        assert response.json()["ticker"] == "PYPL"

        listed = {e["ticker"] for e in client.get("/api/watchlist").json()}
        assert "PYPL" in listed
        assert len(listed) == 11

    def test_duplicate_add_is_idempotent(self, client):
        first = client.post("/api/watchlist", json={"ticker": "PYPL"})
        assert first.status_code == 201

        second = client.post("/api/watchlist", json={"ticker": "PYPL"})
        assert second.status_code == 200

        listed = [e["ticker"] for e in client.get("/api/watchlist").json()]
        assert listed.count("PYPL") == 1

    def test_re_adding_existing_seeded_ticker_is_idempotent(self, client):
        response = client.post("/api/watchlist", json={"ticker": "AAPL"})
        assert response.status_code == 200

        listed = [e["ticker"] for e in client.get("/api/watchlist").json()]
        assert listed.count("AAPL") == 1
        assert len(listed) == 10

    def test_rejects_empty_ticker(self, client):
        response = client.post("/api/watchlist", json={"ticker": "   "})
        assert response.status_code == 422

    def test_rejects_missing_ticker_field(self, client):
        response = client.post("/api/watchlist", json={})
        assert response.status_code == 422


class TestRemoveTicker:
    def test_removes_existing_ticker(self, client):
        response = client.delete("/api/watchlist/AAPL")
        assert response.status_code == 204

        listed = {e["ticker"] for e in client.get("/api/watchlist").json()}
        assert "AAPL" not in listed
        assert len(listed) == 9

    def test_remove_is_case_insensitive(self, client):
        response = client.delete("/api/watchlist/aapl")
        assert response.status_code == 204

        listed = {e["ticker"] for e in client.get("/api/watchlist").json()}
        assert "AAPL" not in listed

    def test_removing_nonexistent_ticker_is_idempotent(self, client):
        response = client.delete("/api/watchlist/ZZZZ")
        assert response.status_code == 204

        listed = {e["ticker"] for e in client.get("/api/watchlist").json()}
        assert len(listed) == 10

    def test_remove_twice_is_idempotent(self, client):
        first = client.delete("/api/watchlist/AAPL")
        second = client.delete("/api/watchlist/AAPL")
        assert first.status_code == 204
        assert second.status_code == 204
