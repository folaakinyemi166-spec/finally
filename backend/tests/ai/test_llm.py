"""Tests for the LLM call wrapper: mock mode parsing and real-call error handling."""

import pytest

from app.ai.errors import LLMResponseError
from app.ai.llm import call_llm
from app.ai.schemas import LLMChatResponse


class TestMockMode:
    def test_no_action_message_returns_canned_reply(self):
        response = call_llm([], "What's my portfolio doing?")
        assert isinstance(response, LLMChatResponse)
        assert response.trades == []
        assert response.watchlist_changes == []
        assert "What's my portfolio doing?" in response.message

    def test_parses_buy_trade(self):
        response = call_llm([], "buy 10 AAPL")
        assert len(response.trades) == 1
        trade = response.trades[0]
        assert trade.ticker == "AAPL"
        assert trade.side == "buy"
        assert trade.quantity == 10.0

    def test_parses_sell_with_fractional_quantity_and_shares_wording(self):
        response = call_llm([], "please sell 2.5 shares of TSLA now")
        assert len(response.trades) == 1
        trade = response.trades[0]
        assert trade.ticker == "TSLA"
        assert trade.side == "sell"
        assert trade.quantity == 2.5

    def test_parses_multiple_trades(self):
        response = call_llm([], "buy 5 AAPL and sell 3 GOOGL")
        tickers = {t.ticker for t in response.trades}
        assert tickers == {"AAPL", "GOOGL"}

    def test_parses_watchlist_add(self):
        response = call_llm([], "add PYPL to my watchlist")
        assert len(response.watchlist_changes) == 1
        assert response.watchlist_changes[0].ticker == "PYPL"
        assert response.watchlist_changes[0].action == "add"

    def test_parses_watchlist_remove(self):
        response = call_llm([], "remove NFLX from the watchlist")
        assert len(response.watchlist_changes) == 1
        assert response.watchlist_changes[0].ticker == "NFLX"
        assert response.watchlist_changes[0].action == "remove"

    def test_is_case_insensitive(self):
        response = call_llm([], "BUY 1 aapl")
        assert response.trades[0].ticker == "AAPL"
        assert response.trades[0].side == "buy"

    def test_mock_mode_makes_no_network_call(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise AssertionError("real LLM should not be called in mock mode")

        monkeypatch.setattr("app.ai.llm.completion", _boom)
        # Does not raise -- proves the mock path short-circuits before completion().
        call_llm([{"role": "user", "content": "buy 1 AAPL"}], "buy 1 AAPL")


class TestRealCallErrorHandling:
    def test_provider_exception_raises_llm_response_error(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        def _boom(*args, **kwargs):
            raise RuntimeError("network exploded")

        monkeypatch.setattr("app.ai.llm.completion", _boom)

        with pytest.raises(LLMResponseError):
            call_llm([{"role": "user", "content": "hi"}], "hi")

    def test_malformed_json_raises_llm_response_error(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        class _Choice:
            class message:  # noqa: N801 - mimics litellm's response shape
                content = "not valid json{{{"

        class _Response:
            choices = [_Choice()]

        monkeypatch.setattr("app.ai.llm.completion", lambda *a, **k: _Response())

        with pytest.raises(LLMResponseError):
            call_llm([{"role": "user", "content": "hi"}], "hi")

    def test_empty_content_raises_llm_response_error(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        class _Choice:
            class message:  # noqa: N801
                content = None

        class _Response:
            choices = [_Choice()]

        monkeypatch.setattr("app.ai.llm.completion", lambda *a, **k: _Response())

        with pytest.raises(LLMResponseError):
            call_llm([{"role": "user", "content": "hi"}], "hi")

    def test_valid_structured_json_parses(self, monkeypatch):
        monkeypatch.delenv("LLM_MOCK", raising=False)

        class _Choice:
            class message:  # noqa: N801
                content = '{"message": "hi there", "trades": [], "watchlist_changes": []}'

        class _Response:
            choices = [_Choice()]

        monkeypatch.setattr("app.ai.llm.completion", lambda *a, **k: _Response())

        response = call_llm([{"role": "user", "content": "hi"}], "hi")
        assert response.message == "hi there"
