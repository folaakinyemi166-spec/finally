"""Pydantic request/response models for the portfolio API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TradeRequest(BaseModel):
    """Body for POST /api/portfolio/trade."""

    ticker: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("ticker must not be empty")
        return normalized


class PositionOut(BaseModel):
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


class PortfolioOut(BaseModel):
    cash_balance: float
    positions: list[PositionOut]
    total_value: float
    total_unrealized_pnl: float


class TradeOut(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float
    price: float
    executed_at: str
    portfolio: PortfolioOut


class HistoryPointOut(BaseModel):
    total_value: float
    recorded_at: str


class HistoryOut(BaseModel):
    history: list[HistoryPointOut]
