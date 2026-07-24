"""Pydantic models for the chat API and the LLM's structured output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Body for POST /api/chat."""

    message: str = Field(min_length=1)


class TradeAction(BaseModel):
    """A trade the LLM wants to execute, before validation/execution."""

    ticker: str
    side: Literal["buy", "sell"]
    quantity: float


class WatchlistChangeAction(BaseModel):
    """A watchlist change the LLM wants to make, before execution."""

    ticker: str
    action: Literal["add", "remove"]


class LLMChatResponse(BaseModel):
    """Structured output schema requested from the LLM (PLAN.md section 9)."""

    message: str
    trades: list[TradeAction] = Field(default_factory=list)
    watchlist_changes: list[WatchlistChangeAction] = Field(default_factory=list)


class ExecutedTradeOut(BaseModel):
    """Result of attempting to execute a single LLM-proposed trade."""

    ticker: str
    side: Literal["buy", "sell"]
    quantity: float
    price: float | None = None
    error: str | None = None


class ExecutedWatchlistChangeOut(BaseModel):
    """Result of attempting to apply a single LLM-proposed watchlist change."""

    ticker: str
    action: Literal["add", "remove"]
    error: str | None = None


class ChatResponseOut(BaseModel):
    """Response body for POST /api/chat."""

    message: str
    trades: list[ExecutedTradeOut]
    watchlist_changes: list[ExecutedWatchlistChangeOut]
