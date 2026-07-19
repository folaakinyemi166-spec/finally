"""Tests for the trades repository."""

from app.db import trades


class TestTrades:
    def test_insert_trade(self, db_path):
        trade = trades.insert_trade("AAPL", "buy", quantity=10, price=190.0)
        assert trade.ticker == "AAPL"
        assert trade.side == "buy"
        assert trade.quantity == 10
        assert trade.price == 190.0
        assert trade.id
        assert trade.executed_at

    def test_list_trades_most_recent_first(self, db_path):
        trades.insert_trade("AAPL", "buy", quantity=10, price=190.0)
        trades.insert_trade("AAPL", "sell", quantity=5, price=195.0)
        result = trades.list_trades()
        assert len(result) == 2
        assert result[0].side == "sell"  # most recent inserted last, listed first
        assert result[1].side == "buy"

    def test_list_trades_limit(self, db_path):
        for i in range(5):
            trades.insert_trade("AAPL", "buy", quantity=1, price=100.0 + i)
        result = trades.list_trades(limit=2)
        assert len(result) == 2

    def test_trades_scoped_per_user(self, db_path):
        trades.insert_trade("AAPL", "buy", quantity=10, price=190.0, user_id="default")
        trades.insert_trade("AAPL", "buy", quantity=3, price=190.0, user_id="other")
        assert len(trades.list_trades(user_id="default")) == 1
        assert len(trades.list_trades(user_id="other")) == 1

    def test_trades_are_append_only(self, db_path):
        trades.insert_trade("AAPL", "buy", quantity=10, price=190.0)
        trades.insert_trade("AAPL", "buy", quantity=10, price=191.0)
        assert len(trades.list_trades()) == 2
