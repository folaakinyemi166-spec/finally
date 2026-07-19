"""Pydantic request models for the REST API (PLAN.md §8).

Response bodies are plain dicts built from the db/market dataclasses'
to_dict() methods (see app/trading.py, app/api/*) rather than dedicated
response models — this project's dataclasses already own serialization, so
mirroring that shape here would just be duplicated schema maintenance.
"""

from __future__ import annotations

import math
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_TICKER_PATTERN = re.compile(r"^[A-Z0-9.]{1,10}$")

# Minimum tradable increment (PLAN.md §8) and a ceiling generous enough for
# any realistic simulated trade while still rejecting hallucinated LLM
# quantities like 1e30.
MIN_TRADE_QUANTITY = 0.0001
MAX_TRADE_QUANTITY = 1_000_000_000


def _validate_ticker(value: str) -> str:
    value = value.strip().upper()
    if not _TICKER_PATTERN.match(value):
        raise ValueError("ticker must be 1-10 characters: letters, digits, or '.'")
    return value


def _validate_quantity(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("quantity must be a finite number")
    if value < MIN_TRADE_QUANTITY or value > MAX_TRADE_QUANTITY:
        raise ValueError(
            f"quantity must be between {MIN_TRADE_QUANTITY} and {MAX_TRADE_QUANTITY}"
        )
    steps = round(value / MIN_TRADE_QUANTITY)
    if abs(value - steps * MIN_TRADE_QUANTITY) > 1e-9:
        raise ValueError(f"quantity must be in increments of {MIN_TRADE_QUANTITY}")
    return value


class TradeRequest(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float

    @field_validator("ticker")
    @classmethod
    def _validate_ticker_field(cls, v: str) -> str:
        return _validate_ticker(v)

    @field_validator("quantity")
    @classmethod
    def _validate_quantity_field(cls, v: float) -> float:
        return _validate_quantity(v)


class WatchlistAddRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def _validate_ticker_field(cls, v: str) -> str:
        return _validate_ticker(v)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def _strip_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be blank")
        return v
