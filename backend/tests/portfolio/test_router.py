"""Tests for the portfolio FastAPI router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.init import DEFAULT_CASH_BALANCE, create_schema, seed_default_data
from app.market.cache import PriceCache
from app.portfolio.router import create_portfolio_router


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"

    import sqlite3

    seed_conn = sqlite3.connect(db_path)
    create_schema(seed_conn)
    seed_default_data(seed_conn)
    seed_conn.close()

    price_cache = PriceCache()
    price_cache.update("AAPL", 100.0)

    app = FastAPI()
    app.include_router(create_portfolio_router(price_cache, db_path=db_path))
    return TestClient(app)


class TestGetPortfolioEndpoint:
    def test_returns_seeded_cash_balance(self, client):
        response = client.get("/api/portfolio")
        assert response.status_code == 200
        body = response.json()
        assert body["cash_balance"] == DEFAULT_CASH_BALANCE
        assert body["positions"] == []


class TestTradeEndpoint:
    def test_buy_returns_updated_portfolio(self, client):
        response = client.post(
            "/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 10}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["ticker"] == "AAPL"
        assert body["price"] == 100.0
        assert body["portfolio"]["cash_balance"] == DEFAULT_CASH_BALANCE - 1000.0

    def test_insufficient_cash_returns_400(self, client):
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "side": "buy", "quantity": 1_000_000},
        )
        assert response.status_code == 400

    def test_unknown_ticker_returns_400(self, client):
        response = client.post(
            "/api/portfolio/trade", json={"ticker": "ZZZZ", "side": "buy", "quantity": 1}
        )
        assert response.status_code == 400

    def test_sell_without_position_returns_400(self, client):
        response = client.post(
            "/api/portfolio/trade", json={"ticker": "AAPL", "side": "sell", "quantity": 1}
        )
        assert response.status_code == 400

    def test_negative_quantity_is_rejected_by_validation(self, client):
        response = client.post(
            "/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": -5}
        )
        assert response.status_code == 422

    def test_invalid_side_is_rejected_by_validation(self, client):
        response = client.post(
            "/api/portfolio/trade", json={"ticker": "AAPL", "side": "hold", "quantity": 1}
        )
        assert response.status_code == 422


class TestHistoryEndpoint:
    def test_empty_history_initially(self, client):
        response = client.get("/api/portfolio/history")
        assert response.status_code == 200
        assert response.json() == {"history": []}

    def test_history_grows_after_trade(self, client):
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 1})
        response = client.get("/api/portfolio/history")
        assert len(response.json()["history"]) == 1
