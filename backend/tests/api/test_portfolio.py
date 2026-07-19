"""Tests for /api/portfolio* endpoints (PLAN.md §8)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_portfolio_starts_empty_with_seed_cash(client: TestClient) -> None:
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cash_balance"] == 10000.0
    assert data["positions"] == []
    assert data["total_value"] == 10000.0
    assert data["total_unrealized_pl"] == 0.0


def test_buy_trade_success(client: TestClient) -> None:
    resp = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["position"]["ticker"] == "AAPL"
    assert data["position"]["quantity"] == 10
    assert data["cash_balance"] < 10000.0

    portfolio = client.get("/api/portfolio").json()
    assert len(portfolio["positions"]) == 1
    assert portfolio["positions"][0]["ticker"] == "AAPL"
    assert portfolio["positions"][0]["current_price"] is not None


def test_buy_averages_cost_across_two_purchases(client: TestClient) -> None:
    first = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 10})
    price1 = first.json()["trade"]["price"]
    second = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 10})
    price2 = second.json()["trade"]["price"]

    expected_avg = (10 * price1 + 10 * price2) / 20
    position = second.json()["position"]
    assert position["quantity"] == 20
    assert position["avg_cost"] == expected_avg


def test_buy_insufficient_funds(client: TestClient) -> None:
    resp = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 1_000_000}
    )
    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()


def test_sell_insufficient_shares(client: TestClient) -> None:
    resp = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "sell", "quantity": 1})
    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()


def test_trade_unknown_ticker_has_no_price(client: TestClient) -> None:
    resp = client.post("/api/portfolio/trade", json={"ticker": "ZZZZ", "side": "buy", "quantity": 1})
    assert resp.status_code == 400
    assert "no live price" in resp.json()["detail"].lower()


def test_sell_full_position_closes_it(client: TestClient) -> None:
    buy = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 5})
    assert buy.status_code == 200
    sell = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "sell", "quantity": 5})
    assert sell.status_code == 200
    assert sell.json()["position"] is None

    portfolio = client.get("/api/portfolio").json()
    assert portfolio["positions"] == []


def test_trade_records_snapshot(client: TestClient) -> None:
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 1})
    history = client.get("/api/portfolio/history").json()
    assert len(history) == 1
    assert history[0]["total_value"] > 0


def test_trade_validation_rejects_bad_quantities(client: TestClient) -> None:
    huge = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 1e30})
    assert huge.status_code == 422

    zero = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 0})
    assert zero.status_code == 422

    off_increment = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "side": "buy", "quantity": 1.00005}
    )
    assert off_increment.status_code == 422


def test_trade_validation_rejects_bad_ticker(client: TestClient) -> None:
    resp = client.post(
        "/api/portfolio/trade", json={"ticker": "not-a-ticker!!", "side": "buy", "quantity": 1}
    )
    assert resp.status_code == 422
