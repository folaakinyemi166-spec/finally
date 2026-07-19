"""Chat orchestration: builds LLM context, executes returned actions, and
persists the conversation turn (PLAN.md §9).

Sits between app/api/chat.py (thin router) and app.ai (LLM call) /
app.trading / app.watchlist_service (persistence and business validation).
Trades and watchlist changes the LLM proposes are re-validated through the
exact same pydantic schemas and business logic a manual trade or watchlist
edit would use, since Structured Outputs only guarantee the JSON *shape* is
correct, not that a ticker exists or a quantity is affordable (PLAN.md §9
points 5-6). A failed action is reported inline rather than raised, so one
bad suggestion doesn't fail the whole chat turn.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.ai import LLMTradeAction, LLMWatchlistAction, generate_response
from app.db import chat as chat_db
from app.db.errors import DuplicateTickerError
from app.errors import TradingError
from app.market import MarketDataSource, PriceCache
from app.schemas import TradeRequest, WatchlistAddRequest
from app.trading import execute_trade, get_portfolio_summary
from app.watchlist_service import add_to_watchlist, build_watchlist_view, remove_from_watchlist

CHAT_HISTORY_WINDOW = 20  # PLAN.md §9: last 20 messages (10 user/assistant turns)


async def handle_chat_message(
    user_message: str,
    price_cache: PriceCache,
    market_source: MarketDataSource,
) -> dict:
    """Process one chat turn end-to-end: context -> LLM -> actions -> persistence."""
    history = chat_db.list_recent_messages(limit=CHAT_HISTORY_WINDOW)
    portfolio_context = get_portfolio_summary(price_cache)
    watchlist_context = build_watchlist_view(price_cache)

    llm_response = generate_response(user_message, portfolio_context, watchlist_context, history)

    trade_results = [_execute_trade_action(action, price_cache) for action in llm_response.trades]
    watchlist_results = [
        await _execute_watchlist_action(action, market_source)
        for action in llm_response.watchlist_changes
    ]

    chat_db.insert_message("user", user_message)
    chat_db.insert_message(
        "assistant",
        llm_response.message,
        actions={"trades": trade_results, "watchlist_changes": watchlist_results},
    )

    return {
        "message": llm_response.message,
        "trades": trade_results,
        "watchlist_changes": watchlist_results,
    }


def _execute_trade_action(action: LLMTradeAction, price_cache: PriceCache) -> dict:
    try:
        validated = TradeRequest(ticker=action.ticker, side=action.side, quantity=action.quantity)
    except ValidationError as exc:
        return _trade_result(action.ticker, action.side, action.quantity, success=False, error=str(exc))

    try:
        result = execute_trade(validated.ticker, validated.side, validated.quantity, price_cache)
    except TradingError as exc:
        return _trade_result(
            validated.ticker, validated.side, validated.quantity, success=False, error=str(exc)
        )

    return _trade_result(
        validated.ticker, validated.side, validated.quantity, success=True, error=None, **result
    )


def _trade_result(ticker, side, quantity, *, success, error, **extra) -> dict:
    return {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "success": success,
        "error": error,
        **extra,
    }


async def _execute_watchlist_action(
    action: LLMWatchlistAction, market_source: MarketDataSource
) -> dict:
    try:
        ticker = WatchlistAddRequest(ticker=action.ticker).ticker
    except ValidationError as exc:
        return {"ticker": action.ticker, "action": action.action, "success": False, "error": str(exc)}

    try:
        if action.action == "add":
            await add_to_watchlist(ticker, market_source)
        else:
            removed = await remove_from_watchlist(ticker, market_source)
            if not removed:
                return {
                    "ticker": ticker,
                    "action": "remove",
                    "success": False,
                    "error": f"{ticker!r} is not on the watchlist",
                }
    except (TradingError, DuplicateTickerError) as exc:
        # Covers WatchlistCapExceededError (TradingError) and a duplicate-add —
        # both are per-action failures here, not turn-ending errors.
        return {"ticker": ticker, "action": action.action, "success": False, "error": str(exc)}

    return {"ticker": ticker, "action": action.action, "success": True, "error": None}
