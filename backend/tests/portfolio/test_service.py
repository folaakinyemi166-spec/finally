"""Tests for portfolio valuation, trade execution, and snapshots."""

import pytest

from app.db.init import DEFAULT_CASH_BALANCE
from app.portfolio.errors import InsufficientCashError, InsufficientSharesError, UnknownTickerError
from app.portfolio.service import execute_trade, get_history, get_portfolio, record_snapshot


class TestGetPortfolio:
    def test_fresh_portfolio_has_no_positions(self, conn, price_cache):
        portfolio = get_portfolio(conn, price_cache)
        assert portfolio["cash_balance"] == DEFAULT_CASH_BALANCE
        assert portfolio["positions"] == []
        assert portfolio["total_value"] == DEFAULT_CASH_BALANCE
        assert portfolio["total_unrealized_pnl"] == 0.0

    def test_position_pnl_reflects_live_price(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)
        price_cache.update("AAPL", 120.0)

        portfolio = get_portfolio(conn, price_cache)
        position = portfolio["positions"][0]
        assert position["ticker"] == "AAPL"
        assert position["quantity"] == 10
        assert position["avg_cost"] == 100.0
        assert position["current_price"] == 120.0
        assert position["market_value"] == 1200.0
        assert position["unrealized_pnl"] == 200.0
        assert position["unrealized_pnl_percent"] == pytest.approx(20.0)

    def test_position_falls_back_to_avg_cost_when_price_unknown(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)
        price_cache.remove("AAPL")

        portfolio = get_portfolio(conn, price_cache)
        position = portfolio["positions"][0]
        assert position["current_price"] == position["avg_cost"]
        assert position["unrealized_pnl"] == 0.0


class TestExecuteTradeBuy:
    def test_buy_creates_new_position_and_debits_cash(self, conn, price_cache):
        result = execute_trade(conn, price_cache, "AAPL", "buy", 10)
        assert result["ticker"] == "AAPL"
        assert result["price"] == 100.0

        portfolio = result["portfolio"]
        assert portfolio["cash_balance"] == DEFAULT_CASH_BALANCE - 1000.0
        assert len(portfolio["positions"]) == 1
        assert portfolio["positions"][0]["quantity"] == 10
        assert portfolio["positions"][0]["avg_cost"] == 100.0

    def test_buy_averages_cost_across_fills(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)  # 10 @ 100
        price_cache.update("AAPL", 200.0)
        execute_trade(conn, price_cache, "AAPL", "buy", 10)  # 10 @ 200

        portfolio = get_portfolio(conn, price_cache)
        position = portfolio["positions"][0]
        assert position["quantity"] == 20
        assert position["avg_cost"] == pytest.approx(150.0)

    def test_buy_supports_fractional_shares(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 0.5)
        portfolio = get_portfolio(conn, price_cache)
        assert portfolio["positions"][0]["quantity"] == 0.5
        assert portfolio["cash_balance"] == DEFAULT_CASH_BALANCE - 50.0

    def test_buy_insufficient_cash_raises_and_makes_no_changes(self, conn, price_cache):
        with pytest.raises(InsufficientCashError):
            execute_trade(conn, price_cache, "AAPL", "buy", 1_000_000)

        portfolio = get_portfolio(conn, price_cache)
        assert portfolio["cash_balance"] == DEFAULT_CASH_BALANCE
        assert portfolio["positions"] == []

    def test_buy_unknown_ticker_raises(self, conn, price_cache):
        with pytest.raises(UnknownTickerError):
            execute_trade(conn, price_cache, "ZZZZ", "buy", 1)

    def test_buy_exact_cash_balance_succeeds(self, conn, price_cache):
        # 100 shares @ 100 == exactly the full 10,000 cash balance.
        result = execute_trade(conn, price_cache, "AAPL", "buy", 100)
        assert result["portfolio"]["cash_balance"] == pytest.approx(0.0)


class TestExecuteTradeSell:
    def test_sell_reduces_position_and_credits_cash(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)
        result = execute_trade(conn, price_cache, "AAPL", "sell", 4)

        portfolio = result["portfolio"]
        assert portfolio["positions"][0]["quantity"] == 6
        assert portfolio["cash_balance"] == DEFAULT_CASH_BALANCE - 1000.0 + 400.0

    def test_sell_full_position_removes_row(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)
        result = execute_trade(conn, price_cache, "AAPL", "sell", 10)
        assert result["portfolio"]["positions"] == []

    def test_sell_more_than_owned_raises_and_makes_no_changes(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 5)
        with pytest.raises(InsufficientSharesError):
            execute_trade(conn, price_cache, "AAPL", "sell", 10)

        portfolio = get_portfolio(conn, price_cache)
        assert portfolio["positions"][0]["quantity"] == 5

    def test_sell_without_a_position_raises(self, conn, price_cache):
        with pytest.raises(InsufficientSharesError):
            execute_trade(conn, price_cache, "AAPL", "sell", 1)

    def test_sell_at_a_loss_still_executes(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)  # 10 @ 100 == 1000
        price_cache.update("AAPL", 50.0)
        result = execute_trade(conn, price_cache, "AAPL", "sell", 10)

        assert result["price"] == 50.0
        # Cash: 10000 - 1000 (buy) + 500 (sell at a loss) == 9500
        assert result["portfolio"]["cash_balance"] == DEFAULT_CASH_BALANCE - 1000.0 + 500.0
        assert result["portfolio"]["positions"] == []

    def test_sell_fractional_shares(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 1.5)
        result = execute_trade(conn, price_cache, "AAPL", "sell", 0.5)
        assert result["portfolio"]["positions"][0]["quantity"] == pytest.approx(1.0)


class TestSnapshotsAndHistory:
    def test_execute_trade_records_a_snapshot(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 10)
        history = get_history(conn)
        assert len(history) == 1
        assert history[0]["total_value"] == pytest.approx(DEFAULT_CASH_BALANCE)

    def test_record_snapshot_appends(self, conn, price_cache):
        record_snapshot(conn, price_cache)
        record_snapshot(conn, price_cache)
        history = get_history(conn)
        assert len(history) == 2

    def test_history_is_ordered_oldest_first(self, conn, price_cache):
        execute_trade(conn, price_cache, "AAPL", "buy", 1)
        execute_trade(conn, price_cache, "AAPL", "buy", 1)
        history = get_history(conn)
        recorded_ats = [point["recorded_at"] for point in history]
        assert recorded_ats == sorted(recorded_ats)
