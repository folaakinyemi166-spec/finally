"""Tests for chat orchestration: context building, action execution, persistence."""

from app.ai.service import process_chat
from app.db.init import DEFAULT_CASH_BALANCE


class TestProcessChatNoActions:
    def test_plain_message_returns_message_with_no_actions(self, conn, price_cache):
        result = process_chat(conn, price_cache, "what's my P&L?")
        assert result.trades == []
        assert result.watchlist_changes == []
        assert result.message

    def test_persists_user_and_assistant_messages(self, conn, price_cache):
        process_chat(conn, price_cache, "hello")
        rows = conn.execute(
            "SELECT role, content FROM chat_messages ORDER BY created_at"
        ).fetchall()
        assert [r["role"] for r in rows] == ["user", "assistant"]
        assert rows[0]["content"] == "hello"


class TestProcessChatTrades:
    def test_valid_buy_trade_executes_and_debits_cash(self, conn, price_cache):
        result = process_chat(conn, price_cache, "buy 10 AAPL")
        assert len(result.trades) == 1
        trade = result.trades[0]
        assert trade.ticker == "AAPL"
        assert trade.side == "buy"
        assert trade.price == 100.0
        assert trade.error is None

        cash = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = 'default'"
        ).fetchone()["cash_balance"]
        assert cash == DEFAULT_CASH_BALANCE - 1000.0

    def test_insufficient_cash_surfaces_as_error_string_not_exception(self, conn, price_cache):
        result = process_chat(conn, price_cache, "buy 1000000 AAPL")
        assert len(result.trades) == 1
        assert result.trades[0].error is not None
        assert "Insufficient" in result.trades[0].error

        # No cash was actually debited.
        cash = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = 'default'"
        ).fetchone()["cash_balance"]
        assert cash == DEFAULT_CASH_BALANCE

    def test_unknown_ticker_surfaces_as_error_string(self, conn, price_cache):
        result = process_chat(conn, price_cache, "buy 1 ZZZZ")
        assert result.trades[0].error is not None

    def test_sell_without_position_surfaces_as_error_string(self, conn, price_cache):
        result = process_chat(conn, price_cache, "sell 1 AAPL")
        assert result.trades[0].error is not None


class TestProcessChatWatchlist:
    def test_add_ticker_persists_to_watchlist(self, conn, price_cache):
        result = process_chat(conn, price_cache, "add PYPL to my watchlist")
        assert result.watchlist_changes[0].ticker == "PYPL"
        assert result.watchlist_changes[0].error is None

        row = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = 'default' AND ticker = 'PYPL'"
        ).fetchone()
        assert row is not None

    def test_remove_ticker_deletes_from_watchlist(self, conn, price_cache):
        process_chat(conn, price_cache, "add PYPL to my watchlist")
        process_chat(conn, price_cache, "remove PYPL from my watchlist")

        row = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = 'default' AND ticker = 'PYPL'"
        ).fetchone()
        assert row is None


class TestChatHistoryContext:
    def test_second_call_includes_prior_exchange_in_history(self, conn, price_cache, monkeypatch):
        captured = {}
        from app.ai import service as service_module

        original = service_module.call_llm

        def _spy(messages, user_message):
            captured["messages"] = messages
            return original(messages, user_message)

        monkeypatch.setattr(service_module, "call_llm", _spy)

        process_chat(conn, price_cache, "hello")
        process_chat(conn, price_cache, "hello again")

        # The second call's message list should include the first turn's history.
        contents = [m["content"] for m in captured["messages"]]
        assert any("hello" == c for c in contents)
