"""Tests for app/ai.py — LLM_MOCK stand-in and the real-call parsing/error path."""

from __future__ import annotations

import pytest

from app import ai
from app.errors import LLMError


def test_mock_response_with_no_trade_phrase_is_static(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MOCK", "true")
    result = ai.generate_response("hello there", {}, [], [])
    assert result.trades == []
    assert result.watchlist_changes == []
    assert "mock" in result.message.lower()


@pytest.mark.parametrize(
    ("phrase", "side", "quantity", "ticker"),
    [
        ("buy 5 AAPL", "buy", 5.0, "AAPL"),
        ("Sell 10.5 shares of tsla", "sell", 10.5, "TSLA"),
        ("please buy 1 msft for me", "buy", 1.0, "MSFT"),
    ],
)
def test_mock_response_parses_trade_phrases(
    monkeypatch: pytest.MonkeyPatch, phrase: str, side: str, quantity: float, ticker: str
) -> None:
    monkeypatch.setenv("LLM_MOCK", "true")
    result = ai.generate_response(phrase, {}, [], [])
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.side == side
    assert trade.quantity == quantity
    assert trade.ticker == ticker


def test_mock_mode_is_case_insensitive_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MOCK", "True")
    result = ai.generate_response("buy 1 AAPL", {}, [], [])
    assert result.trades[0].ticker == "AAPL"


def test_generate_response_calls_real_llm_when_not_mocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_MOCK", raising=False)
    captured = {}

    class _FakeMessage:
        content = '{"message": "Looks balanced.", "trades": [], "watchlist_changes": []}'

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    monkeypatch.setattr(ai, "completion", fake_completion)

    result = ai.generate_response("how am I doing?", {"cash_balance": 10000.0}, [], [])

    assert result.message == "Looks balanced."
    assert captured["model"] == ai.MODEL
    assert captured["response_format"] is ai.LLMChatResponse
    assert captured["messages"][-1] == {"role": "user", "content": "how am I doing?"}


def test_generate_response_wraps_llm_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_MOCK", raising=False)

    def raising_completion(**kwargs):
        raise RuntimeError("network exploded")

    monkeypatch.setattr(ai, "completion", raising_completion)

    with pytest.raises(LLMError):
        ai.generate_response("hi", {}, [], [])


def test_generate_response_wraps_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_MOCK", raising=False)

    class _FakeMessage:
        content = "not valid json"

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    monkeypatch.setattr(ai, "completion", lambda **kwargs: _FakeResponse())

    with pytest.raises(LLMError):
        ai.generate_response("hi", {}, [], [])
