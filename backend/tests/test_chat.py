"""Tests for app/chat.py orchestration logic (PLAN.md §9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import chat as chat_module
from app.ai import LLMChatResponse, LLMTradeAction, LLMWatchlistAction
from app.db import chat as chat_db
from app.market import PriceCache


class _FakeMarketSource:
    def __init__(self) -> None:
        self.added: list[str] = []
        self.removed: list[str] = []

    async def add_ticker(self, ticker: str) -> None:
        self.added.append(ticker)

    async def remove_ticker(self, ticker: str) -> None:
        self.removed.append(ticker)


@pytest.fixture
def price_cache() -> PriceCache:
    cache = PriceCache()
    cache.update("AAPL", 100.0)
    return cache


@pytest.mark.asyncio
async def test_successful_trade_action_executes_and_persists(
    db_path: Path, price_cache: PriceCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        chat_module,
        "generate_response",
        lambda *a, **k: LLMChatResponse(
            message="Buying some AAPL.",
            trades=[LLMTradeAction(ticker="AAPL", side="buy", quantity=5)],
        ),
    )

    result = await chat_module.handle_chat_message("buy 5 AAPL", price_cache, _FakeMarketSource())

    assert result["message"] == "Buying some AAPL."
    assert result["trades"][0]["success"] is True
    assert result["trades"][0]["position"]["quantity"] == 5

    history = chat_db.list_recent_messages()
    assert [m.role for m in history] == ["user", "assistant"]
    assert history[0].content == "buy 5 AAPL"
    assert history[1].actions["trades"][0]["success"] is True


@pytest.mark.asyncio
async def test_trade_action_failure_does_not_crash_turn(
    db_path: Path, price_cache: PriceCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        chat_module,
        "generate_response",
        lambda *a, **k: LLMChatResponse(
            message="Selling AAPL you don't own.",
            trades=[LLMTradeAction(ticker="AAPL", side="sell", quantity=5)],
        ),
    )

    result = await chat_module.handle_chat_message(
        "sell 5 AAPL", price_cache, _FakeMarketSource()
    )

    assert result["trades"][0]["success"] is False
    assert "insufficient" in result["trades"][0]["error"].lower()


@pytest.mark.asyncio
async def test_invalid_llm_ticker_reported_as_failed_action_not_raised(
    db_path: Path, price_cache: PriceCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        chat_module,
        "generate_response",
        lambda *a, **k: LLMChatResponse(
            message="Buying a hallucinated ticker.",
            trades=[LLMTradeAction(ticker="not a real ticker", side="buy", quantity=1)],
        ),
    )

    result = await chat_module.handle_chat_message(
        "buy something weird", price_cache, _FakeMarketSource()
    )

    assert result["trades"][0]["success"] is False
    assert result["trades"][0]["error"]


@pytest.mark.asyncio
async def test_hallucinated_quantity_reported_as_failed_action(
    db_path: Path, price_cache: PriceCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        chat_module,
        "generate_response",
        lambda *a, **k: LLMChatResponse(
            message="Buying an absurd amount.",
            trades=[LLMTradeAction(ticker="AAPL", side="buy", quantity=1e30)],
        ),
    )

    result = await chat_module.handle_chat_message("buy a lot", price_cache, _FakeMarketSource())

    assert result["trades"][0]["success"] is False


@pytest.mark.asyncio
async def test_watchlist_add_and_remove_actions(
    db_path: Path, price_cache: PriceCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        chat_module,
        "generate_response",
        lambda *a, **k: LLMChatResponse(
            message="Managing your watchlist.",
            watchlist_changes=[
                LLMWatchlistAction(ticker="PYPL", action="add"),
                LLMWatchlistAction(ticker="ZZZZ", action="remove"),
            ],
        ),
    )
    market_source = _FakeMarketSource()

    result = await chat_module.handle_chat_message("watchlist stuff", price_cache, market_source)

    assert result["watchlist_changes"][0]["success"] is True
    assert "PYPL" in market_source.added
    # ZZZZ was never on the default seeded watchlist -> not-found failure
    assert result["watchlist_changes"][1]["success"] is False


@pytest.mark.asyncio
async def test_chat_history_and_context_passed_to_llm(
    db_path: Path, price_cache: PriceCache, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_generate(user_message, portfolio_context, watchlist_context, history):
        captured["history"] = history
        captured["portfolio_context"] = portfolio_context
        return LLMChatResponse(message="ok")

    monkeypatch.setattr(chat_module, "generate_response", fake_generate)

    await chat_module.handle_chat_message("first", price_cache, _FakeMarketSource())
    await chat_module.handle_chat_message("second", price_cache, _FakeMarketSource())

    # Second call's history includes both messages persisted by the first turn.
    assert len(captured["history"]) == 2
    assert captured["portfolio_context"]["cash_balance"] == 10000.0
