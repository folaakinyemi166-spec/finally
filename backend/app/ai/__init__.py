"""AI chat subsystem: LLM-backed assistant that can trade and manage the watchlist.

Public API:
    create_chat_router - FastAPI router factory (POST /api/chat)
    process_chat        - Load context, call the LLM, auto-execute actions, persist
    call_llm             - LiteLLM/OpenRouter (Cerebras) call, or the LLM_MOCK stand-in
    LLMResponseError     - Raised on a failed/malformed LLM response
"""

from .errors import LLMResponseError
from .llm import call_llm
from .router import create_chat_router
from .schemas import (
    ChatRequest,
    ChatResponseOut,
    ExecutedTradeOut,
    ExecutedWatchlistChangeOut,
    LLMChatResponse,
    TradeAction,
    WatchlistChangeAction,
)
from .service import process_chat

__all__ = [
    "LLMResponseError",
    "create_chat_router",
    "call_llm",
    "process_chat",
    "ChatRequest",
    "ChatResponseOut",
    "ExecutedTradeOut",
    "ExecutedWatchlistChangeOut",
    "LLMChatResponse",
    "TradeAction",
    "WatchlistChangeAction",
]
