"""Tests for /api/watchlist* endpoints (PLAN.md §7 cap, §8 contract)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_watchlist_has_default_tickers_with_prices(client: TestClient) -> None:
    resp = client.get("/api/watchlist")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10
    tickers = {entry["ticker"] for entry in data}
    assert "AAPL" in tickers
    for entry in data:
        assert entry["price"] is not None


def test_add_ticker_normalizes_and_seeds_price(client: TestClient) -> None:
    resp = client.post("/api/watchlist", json={"ticker": "pypl"})
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "PYPL"

    watchlist = client.get("/api/watchlist").json()
    entry = next(e for e in watchlist if e["ticker"] == "PYPL")
    assert entry["price"] is not None


def test_add_duplicate_ticker_rejected(client: TestClient) -> None:
    resp = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert resp.status_code == 400


def test_add_invalid_ticker_rejected(client: TestClient) -> None:
    resp = client.post("/api/watchlist", json={"ticker": "not valid!"})
    assert resp.status_code == 422


def test_remove_ticker(client: TestClient) -> None:
    resp = client.delete("/api/watchlist/AAPL")
    assert resp.status_code == 200
    tickers = {e["ticker"] for e in client.get("/api/watchlist").json()}
    assert "AAPL" not in tickers


def test_remove_unknown_ticker_404(client: TestClient) -> None:
    resp = client.delete("/api/watchlist/ZZZZ")
    assert resp.status_code == 404


def test_watchlist_cap_enforced(client: TestClient) -> None:
    # 10 default tickers already seeded; adding 20 more hits the 30 cap exactly.
    for i in range(20):
        resp = client.post("/api/watchlist", json={"ticker": f"T{i}"})
        assert resp.status_code == 200

    resp = client.post("/api/watchlist", json={"ticker": "OVER"})
    assert resp.status_code == 400
    assert "limit" in resp.json()["detail"].lower()
