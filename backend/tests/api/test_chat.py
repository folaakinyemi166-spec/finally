"""Tests for POST /api/chat (PLAN.md §8, §9). LLM_MOCK=true by default via the
`client` fixture, so these exercise the real endpoint/orchestration/db wiring
without a network call.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_chat_returns_message_with_no_actions(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "how is my portfolio doing?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert data["trades"] == []
    assert data["watchlist_changes"] == []


def test_chat_mock_trade_executes_and_updates_portfolio(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "buy 5 AAPL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["trades"]) == 1
    assert data["trades"][0]["success"] is True
    assert data["trades"][0]["ticker"] == "AAPL"

    portfolio = client.get("/api/portfolio").json()
    assert portfolio["positions"][0]["ticker"] == "AAPL"
    assert portfolio["positions"][0]["quantity"] == 5


def test_chat_mock_trade_insufficient_funds_reported_inline(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "buy 999999 AAPL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["trades"][0]["success"] is False
    assert "insufficient" in data["trades"][0]["error"].lower()

    # The failed action shouldn't have touched the portfolio.
    portfolio = client.get("/api/portfolio").json()
    assert portfolio["positions"] == []


def test_chat_blank_message_rejected(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 422


def test_chat_missing_message_rejected(client: TestClient) -> None:
    resp = client.post("/api/chat", json={})
    assert resp.status_code == 422


def test_chat_conversation_continues_across_turns(client: TestClient) -> None:
    first = client.post("/api/chat", json={"message": "hello"})
    assert first.status_code == 200
    second = client.post("/api/chat", json={"message": "hello again"})
    assert second.status_code == 200
