"""Tests for the AI chat FastAPI router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.router import create_chat_router
from app.db.init import create_schema, seed_default_data
from app.market.cache import PriceCache


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
    app.include_router(create_chat_router(price_cache, db_path=db_path))
    return TestClient(app)


class TestChatEndpoint:
    def test_plain_message_returns_200_with_message(self, client):
        response = client.post("/api/chat", json={"message": "how am I doing?"})
        assert response.status_code == 200
        body = response.json()
        assert body["message"]
        assert body["trades"] == []
        assert body["watchlist_changes"] == []

    def test_trade_message_executes_and_returns_result(self, client):
        response = client.post("/api/chat", json={"message": "buy 5 AAPL"})
        assert response.status_code == 200
        body = response.json()
        assert body["trades"][0]["ticker"] == "AAPL"
        assert body["trades"][0]["price"] == 100.0

    def test_empty_message_rejected_by_validation(self, client):
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422

    def test_missing_message_field_rejected_by_validation(self, client):
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_malformed_llm_json_returns_502_not_500(self, client, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        class _Choice:
            class message:  # noqa: N801 - mimics litellm's response shape
                content = "not valid json{{{"

        class _Response:
            choices = [_Choice()]

        monkeypatch.setattr("app.ai.llm.completion", lambda *a, **k: _Response())

        response = client.post("/api/chat", json={"message": "hi"})
        assert response.status_code == 502

    def test_llm_call_exception_returns_502_not_500(self, client, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        def _boom(*args, **kwargs):
            raise RuntimeError("provider down")

        monkeypatch.setattr("app.ai.llm.completion", _boom)

        response = client.post("/api/chat", json={"message": "hi"})
        assert response.status_code == 502
