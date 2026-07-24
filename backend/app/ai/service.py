"""Chat orchestration: load context, call the LLM, execute actions, persist.

Operates on a plain `sqlite3.Connection` (row_factory = sqlite3.Row) and a
`PriceCache`, mirroring `app.portfolio.service` — callers own the connection
lifecycle.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime

from app.db.init import DEFAULT_USER_ID
from app.market.cache import PriceCache
from app.portfolio.errors import InsufficientCashError, InsufficientSharesError, UnknownTickerError
from app.portfolio.service import execute_trade, get_portfolio

from .llm import call_llm
from .schemas import (
    ChatResponseOut,
    ExecutedTradeOut,
    ExecutedWatchlistChangeOut,
    LLMChatResponse,
    TradeAction,
    WatchlistChangeAction,
)

_HISTORY_LIMIT = 20

_SYSTEM_PROMPT = (
    "You are FinAlly, an AI trading assistant for a simulated trading platform. "
    "Analyze the user's portfolio composition, risk concentration, and P&L. "
    "Suggest trades with reasoning, execute trades when the user asks or agrees, "
    "and manage the watchlist proactively. Be concise and data-driven.\n\n"
    "Always respond with JSON matching exactly this schema:\n"
    '{"message": "<your conversational reply>", '
    '"trades": [{"ticker": "<TICKER>", "side": "buy"|"sell", "quantity": <number>}], '
    '"watchlist_changes": [{"ticker": "<TICKER>", "action": "add"|"remove"}]}\n'
    "`trades` and `watchlist_changes` are optional and should be empty arrays when no "
    "action is needed."
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load_history(conn: sqlite3.Connection, user_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? "
        "ORDER BY created_at DESC LIMIT ?",
        (user_id, _HISTORY_LIMIT),
    ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def _watchlist_context(conn: sqlite3.Connection, price_cache: PriceCache, user_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at", (user_id,)
    ).fetchall()
    return [{"ticker": row["ticker"], "price": price_cache.get_price(row["ticker"])} for row in rows]


def _build_messages(
    conn: sqlite3.Connection, price_cache: PriceCache, user_id: str, user_message: str
) -> list[dict]:
    context = {
        "portfolio": get_portfolio(conn, price_cache, user_id),
        "watchlist": _watchlist_context(conn, price_cache, user_id),
    }
    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "system", "content": f"Current portfolio and watchlist: {json.dumps(context)}"},
    ]
    messages.extend(_load_history(conn, user_id))
    messages.append({"role": "user", "content": user_message})
    return messages


def _execute_trade_action(
    conn: sqlite3.Connection, price_cache: PriceCache, action: TradeAction, user_id: str
) -> ExecutedTradeOut:
    try:
        result = execute_trade(
            conn, price_cache, action.ticker, action.side, action.quantity, user_id
        )
        return ExecutedTradeOut(
            ticker=result["ticker"],
            side=result["side"],
            quantity=result["quantity"],
            price=result["price"],
        )
    except (UnknownTickerError, InsufficientCashError, InsufficientSharesError) as exc:
        return ExecutedTradeOut(
            ticker=action.ticker.strip().upper(),
            side=action.side,
            quantity=action.quantity,
            error=str(exc),
        )


def _execute_watchlist_action(
    conn: sqlite3.Connection, action: WatchlistChangeAction, user_id: str
) -> ExecutedWatchlistChangeOut:
    ticker = action.ticker.strip().upper()
    if not ticker:
        return ExecutedWatchlistChangeOut(
            ticker=action.ticker, action=action.action, error="ticker must not be empty"
        )

    if action.action == "add":
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, ticker, _now()),
        )
    else:
        conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        )
    conn.commit()
    return ExecutedWatchlistChangeOut(ticker=ticker, action=action.action)


def _persist_exchange(
    conn: sqlite3.Connection,
    user_id: str,
    user_message: str,
    llm_response: LLMChatResponse,
    executed_trades: list[ExecutedTradeOut],
    executed_watchlist_changes: list[ExecutedWatchlistChangeOut],
) -> None:
    conn.execute(
        "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
        "VALUES (?, ?, 'user', ?, NULL, ?)",
        (str(uuid.uuid4()), user_id, user_message, _now()),
    )
    actions_json = json.dumps(
        {
            "trades": [t.model_dump() for t in executed_trades],
            "watchlist_changes": [w.model_dump() for w in executed_watchlist_changes],
        }
    )
    conn.execute(
        "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
        "VALUES (?, ?, 'assistant', ?, ?, ?)",
        (str(uuid.uuid4()), user_id, llm_response.message, actions_json, _now()),
    )
    conn.commit()


def process_chat(
    conn: sqlite3.Connection,
    price_cache: PriceCache,
    user_message: str,
    user_id: str = DEFAULT_USER_ID,
) -> ChatResponseOut:
    """Handle one chat turn: context -> LLM -> auto-execute actions -> persist.

    Raises:
        LLMResponseError: propagated from `call_llm` when the call fails or
            the response isn't valid structured JSON. Callers (the router)
            should turn this into a non-500 HTTP response.
    """
    messages = _build_messages(conn, price_cache, user_id, user_message)
    llm_response = call_llm(messages, user_message)

    executed_trades = [
        _execute_trade_action(conn, price_cache, trade, user_id) for trade in llm_response.trades
    ]
    executed_watchlist_changes = [
        _execute_watchlist_action(conn, change, user_id)
        for change in llm_response.watchlist_changes
    ]

    _persist_exchange(
        conn, user_id, user_message, llm_response, executed_trades, executed_watchlist_changes
    )

    return ChatResponseOut(
        message=llm_response.message,
        trades=executed_trades,
        watchlist_changes=executed_watchlist_changes,
    )
