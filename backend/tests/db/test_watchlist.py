"""Tests for the watchlist repository."""

import pytest

from app.db import watchlist
from app.db.errors import DuplicateTickerError


class TestWatchlist:
    def test_list_watchlist_seeded(self, db_path):
        entries = watchlist.list_watchlist()
        assert len(entries) == 10
        tickers = {e.ticker for e in entries}
        assert "AAPL" in tickers
        assert "NFLX" in tickers

    def test_count_tickers_seeded(self, db_path):
        assert watchlist.count_tickers() == 10

    def test_add_ticker(self, db_path):
        entry = watchlist.add_ticker("PYPL")
        assert entry.ticker == "PYPL"
        assert entry.user_id == "default"
        assert watchlist.count_tickers() == 11
        tickers = {e.ticker for e in watchlist.list_watchlist()}
        assert "PYPL" in tickers

    def test_add_duplicate_ticker_raises(self, db_path):
        with pytest.raises(DuplicateTickerError):
            watchlist.add_ticker("AAPL")  # already seeded
        # Should not have inserted a second row
        assert watchlist.count_tickers() == 10

    def test_add_same_ticker_different_user_allowed(self, db_path):
        # UNIQUE is (user_id, ticker), so another user can watch the same ticker
        entry = watchlist.add_ticker("AAPL", user_id="other")
        assert entry.ticker == "AAPL"
        assert entry.user_id == "other"

    def test_remove_ticker(self, db_path):
        removed = watchlist.remove_ticker("AAPL")
        assert removed is True
        assert watchlist.count_tickers() == 9
        tickers = {e.ticker for e in watchlist.list_watchlist()}
        assert "AAPL" not in tickers

    def test_remove_nonexistent_ticker(self, db_path):
        removed = watchlist.remove_ticker("DOES_NOT_EXIST")
        assert removed is False
        assert watchlist.count_tickers() == 10
