"""LLM call wrapper: LiteLLM via OpenRouter, Cerebras inference provider.

Real calls request structured output matching `LLMChatResponse`. When
`LLM_MOCK=true`, no network call is made — a small deterministic rule-based
parser stands in for the LLM so E2E/CI tests are fast, free, and reproducible.

Mock phrasing convention (case-insensitive):
    "buy <qty> <TICKER>" / "sell <qty> <TICKER>" -> a trade action
    "add <TICKER> to [my/the] watchlist"          -> a watchlist add
    "remove <TICKER> from [my/the] watchlist"     -> a watchlist remove
Any other message produces a canned acknowledgement with no actions.
"""

from __future__ import annotations

import os
import re

from litellm import completion

from .errors import LLMResponseError
from .schemas import LLMChatResponse, TradeAction, WatchlistChangeAction

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

_TRADE_RE = re.compile(
    r"\b(buy|sell)\s+(\d+(?:\.\d+)?)\s+(?:shares?\s+of\s+)?([a-zA-Z]{1,5})\b", re.IGNORECASE
)
_ADD_RE = re.compile(
    r"\badd\s+([a-zA-Z]{1,5})\s+to\s+(?:my\s+|the\s+)?watchlist\b", re.IGNORECASE
)
_REMOVE_RE = re.compile(
    r"\bremove\s+([a-zA-Z]{1,5})\s+from\s+(?:my\s+|the\s+)?watchlist\b", re.IGNORECASE
)


def _mock_mode() -> bool:
    return os.environ.get("LLM_MOCK", "").strip().lower() == "true"


def _mock_response(user_message: str) -> LLMChatResponse:
    trades = [
        TradeAction(ticker=m.group(3).upper(), side=m.group(1).lower(), quantity=float(m.group(2)))
        for m in _TRADE_RE.finditer(user_message)
    ]
    watchlist_changes = [
        WatchlistChangeAction(ticker=m.group(1).upper(), action="add")
        for m in _ADD_RE.finditer(user_message)
    ] + [
        WatchlistChangeAction(ticker=m.group(1).upper(), action="remove")
        for m in _REMOVE_RE.finditer(user_message)
    ]
    if trades or watchlist_changes:
        message = "Mock response: executing the requested action(s)."
    else:
        message = f"Mock response: received '{user_message}'."
    return LLMChatResponse(message=message, trades=trades, watchlist_changes=watchlist_changes)


def call_llm(messages: list[dict], user_message: str) -> LLMChatResponse:
    """Call the LLM (or the mock) and return its parsed structured response.

    Raises:
        LLMResponseError: the underlying call failed, or the response body
            isn't valid JSON matching `LLMChatResponse`. Callers should treat
            this as a graceful failure (e.g. HTTP 502), never a crash.
    """
    if _mock_mode():
        return _mock_response(user_message)

    try:
        response = completion(
            model=MODEL,
            messages=messages,
            response_format=LLMChatResponse,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise LLMResponseError(f"LLM call failed: {exc}") from exc

    if not content:
        raise LLMResponseError("LLM returned an empty response")

    try:
        return LLMChatResponse.model_validate_json(content)
    except (ValueError, TypeError) as exc:
        raise LLMResponseError(f"LLM returned invalid structured JSON: {exc}") from exc
