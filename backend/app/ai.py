"""LLM chat integration — LiteLLM via OpenRouter with Cerebras inference (PLAN.md §9).

Structured Outputs only guarantee the JSON *shape* returned by the model
matches LLMChatResponse below; they say nothing about whether a suggested
ticker exists or a quantity is affordable. app/chat.py re-validates and
executes each trade/watchlist action through the exact same business logic
as a manual trade — this module's only job is producing that shape, from
either the real model or the deterministic LLM_MOCK stand-in.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Literal

from litellm import completion
from pydantic import BaseModel, Field

from app.db.models import ChatMessage
from app.errors import LLMError

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

SYSTEM_PROMPT = """You are FinAlly, an AI trading assistant for a simulated portfolio.
Analyze the user's portfolio composition, risk concentration, and P&L using the
context provided in the following system message. Suggest trades with clear
reasoning, execute trades when the user asks for one or agrees to one, and
proactively help manage their watchlist. Be concise and data-driven. Always
respond with valid JSON matching the required schema."""


class LLMTradeAction(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float


class LLMWatchlistAction(BaseModel):
    ticker: str
    action: Literal["add", "remove"]


class LLMChatResponse(BaseModel):
    message: str
    trades: list[LLMTradeAction] = Field(default_factory=list)
    watchlist_changes: list[LLMWatchlistAction] = Field(default_factory=list)


# Recognizes "buy/sell <quantity> [shares of] <ticker>" so LLM_MOCK=true can
# deterministically exercise the trade-execution path for E2E tests (PLAN.md
# §12: "AI chat (mocked): ... trade execution appears inline") without a
# network call or API key.
_MOCK_TRADE_PATTERN = re.compile(
    r"\b(buy|sell)\s+(\d+(?:\.\d+)?)\s+(?:shares?\s+of\s+)?([a-zA-Z.]{1,10})\b",
    re.IGNORECASE,
)


def generate_response(
    user_message: str,
    portfolio_context: dict,
    watchlist_context: list[dict],
    history: list[ChatMessage],
) -> LLMChatResponse:
    """Produce a structured chat response for `user_message`.

    Uses the deterministic LLM_MOCK stand-in when LLM_MOCK=true (PLAN.md §9,
    for fast/free/reproducible tests without a network call), otherwise
    calls the real model via LiteLLM/OpenRouter/Cerebras.
    """
    if os.environ.get("LLM_MOCK", "").strip().lower() == "true":
        return _mock_response(user_message)
    return _call_llm(user_message, portfolio_context, watchlist_context, history)


def _call_llm(
    user_message: str,
    portfolio_context: dict,
    watchlist_context: list[dict],
    history: list[ChatMessage],
) -> LLMChatResponse:
    context_message = (
        f"Current portfolio (JSON): {json.dumps(portfolio_context)}\n"
        f"Current watchlist (JSON): {json.dumps(watchlist_context)}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_message},
        *({"role": entry.role, "content": entry.content} for entry in history),
        {"role": "user", "content": user_message},
    ]

    try:
        response = completion(
            model=MODEL,
            messages=messages,
            response_format=LLMChatResponse,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
        )
        raw = response.choices[0].message.content
        return LLMChatResponse.model_validate_json(raw)
    except Exception as exc:
        logger.exception("LLM call failed")
        raise LLMError(f"AI assistant is unavailable: {exc}") from exc


def _mock_response(user_message: str) -> LLMChatResponse:
    match = _MOCK_TRADE_PATTERN.search(user_message)
    if match:
        side, quantity, ticker = match.groups()
        return LLMChatResponse(
            message=f"Executing a {side.lower()} order for {quantity} shares of {ticker.upper()}.",
            trades=[
                LLMTradeAction(ticker=ticker.upper(), side=side.lower(), quantity=float(quantity))
            ],
        )
    return LLMChatResponse(
        message=(
            "This is a mock AI response (LLM_MOCK=true). "
            'Try "buy 5 AAPL" to see a mocked trade execution.'
        )
    )
