"""Tests for app/trading.py trade execution and portfolio valuation logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db import positions, snapshots, users
from app.errors import InsufficientFundsError, InsufficientSharesError, NoPriceAvailableError
from app.market import PriceCache
from app.trading import compute_total_value, execute_trade, get_portfolio_summary


@pytest.fixture
def price_cache() -> PriceCache:
    cache = PriceCache()
    cache.update("AAPL", 100.0)
    return cache


def test_buy_creates_new_position(db_path: Path, price_cache: PriceCache) -> None:
    result = execute_trade("AAPL", "buy", 10, price_cache)

    assert result["position"]["quantity"] == 10
    assert result["position"]["avg_cost"] == 100.0
    assert result["cash_balance"] == 10000.0 - 1000.0
    assert users.get_cash_balance() == 10000.0 - 1000.0

    position = positions.get_position("AAPL")
    assert position is not None
    assert position.quantity == 10


def test_buy_averages_cost(db_path: Path, price_cache: PriceCache) -> None:
    execute_trade("AAPL", "buy", 10, price_cache)
    price_cache.update("AAPL", 200.0)
    result = execute_trade("AAPL", "buy", 10, price_cache)

    # (10 * 100 + 10 * 200) / 20 = 150
    assert result["position"]["avg_cost"] == 150.0
    assert result["position"]["quantity"] == 20


def test_buy_insufficient_funds_raises(db_path: Path, price_cache: PriceCache) -> None:
    with pytest.raises(InsufficientFundsError):
        execute_trade("AAPL", "buy", 1000, price_cache)
    # No partial side effects on failure
    assert users.get_cash_balance() == 10000.0
    assert positions.get_position("AAPL") is None


def test_sell_reduces_position_and_keeps_avg_cost(db_path: Path, price_cache: PriceCache) -> None:
    execute_trade("AAPL", "buy", 10, price_cache)
    price_cache.update("AAPL", 150.0)
    result = execute_trade("AAPL", "sell", 4, price_cache)

    assert result["position"]["quantity"] == 6
    assert result["position"]["avg_cost"] == 100.0  # avg cost unchanged on sell
    assert result["cash_balance"] == 10000.0 - 1000.0 + 4 * 150.0


def test_sell_full_position_deletes_it(db_path: Path, price_cache: PriceCache) -> None:
    execute_trade("AAPL", "buy", 10, price_cache)
    result = execute_trade("AAPL", "sell", 10, price_cache)

    assert result["position"] is None
    assert positions.get_position("AAPL") is None


def test_sell_more_than_held_raises(db_path: Path, price_cache: PriceCache) -> None:
    execute_trade("AAPL", "buy", 5, price_cache)
    with pytest.raises(InsufficientSharesError):
        execute_trade("AAPL", "sell", 6, price_cache)


def test_sell_with_no_position_raises(db_path: Path, price_cache: PriceCache) -> None:
    with pytest.raises(InsufficientSharesError):
        execute_trade("AAPL", "sell", 1, price_cache)


def test_trade_with_no_cached_price_raises(db_path: Path, price_cache: PriceCache) -> None:
    with pytest.raises(NoPriceAvailableError):
        execute_trade("ZZZZ", "buy", 1, price_cache)


def test_trade_inserts_snapshot(db_path: Path, price_cache: PriceCache) -> None:
    execute_trade("AAPL", "buy", 10, price_cache)
    history = snapshots.list_snapshots()
    assert len(history) == 1
    assert history[0].total_value == 10000.0  # cash converted to equal-value stock


def test_compute_total_value_falls_back_to_avg_cost_without_price(
    db_path: Path, price_cache: PriceCache
) -> None:
    execute_trade("AAPL", "buy", 10, price_cache)
    empty_cache = PriceCache()  # ticker not tracked here
    total = compute_total_value(users.get_cash_balance(), empty_cache)
    # 10 shares valued at their avg_cost (100.0) since no live price exists
    assert total == users.get_cash_balance() + 10 * 100.0


def test_get_portfolio_summary_computes_unrealized_pl(db_path: Path, price_cache: PriceCache) -> None:
    execute_trade("AAPL", "buy", 10, price_cache)
    price_cache.update("AAPL", 150.0)

    summary = get_portfolio_summary(price_cache)
    position = summary["positions"][0]
    assert position["current_price"] == 150.0
    assert position["market_value"] == 1500.0
    assert position["unrealized_pl"] == 500.0
    assert position["unrealized_pl_percent"] == 50.0
    assert summary["total_unrealized_pl"] == 500.0
