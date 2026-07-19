"""Tests for request validation in app/schemas.py (PLAN.md §8, §9)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import TradeRequest, WatchlistAddRequest


def test_ticker_normalized_to_uppercase() -> None:
    req = TradeRequest(ticker="aapl", side="buy", quantity=1)
    assert req.ticker == "AAPL"


@pytest.mark.parametrize("ticker", ["", "toolongticker123", "bad ticker", "bad!"])
def test_invalid_ticker_rejected(ticker: str) -> None:
    with pytest.raises(ValidationError):
        TradeRequest(ticker=ticker, side="buy", quantity=1)


def test_dotted_ticker_allowed() -> None:
    req = TradeRequest(ticker="brk.b", side="buy", quantity=1)
    assert req.ticker == "BRK.B"


@pytest.mark.parametrize(
    "quantity",
    [0, -1, 1e30, float("inf"), float("nan"), 1.00005],
)
def test_invalid_quantity_rejected(quantity: float) -> None:
    with pytest.raises(ValidationError):
        TradeRequest(ticker="AAPL", side="buy", quantity=quantity)


@pytest.mark.parametrize("quantity", [0.0001, 1, 0.5, 100.25])
def test_valid_quantity_accepted(quantity: float) -> None:
    req = TradeRequest(ticker="AAPL", side="buy", quantity=quantity)
    assert req.quantity == quantity


def test_invalid_side_rejected() -> None:
    with pytest.raises(ValidationError):
        TradeRequest(ticker="AAPL", side="hold", quantity=1)


def test_watchlist_add_request_normalizes_ticker() -> None:
    req = WatchlistAddRequest(ticker="tsla")
    assert req.ticker == "TSLA"
