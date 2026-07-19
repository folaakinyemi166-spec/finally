"""SQLite persistence layer for FinAlly.

Lazily initialized: the first call to init_db() (or any repository function,
which calls it internally) creates the schema and seeds default data if the
DB file is missing or empty. See connection.py for path resolution and the
thread-safety approach (short-lived connection per call).

Public API:
    init_db, get_connection, get_db_path
                        - lifecycle / low-level access (connection.py)
    DuplicateTickerError
                        - raised by watchlist.add_ticker() on duplicates
    UserProfile, WatchlistEntry, Position, Trade, PortfolioSnapshot,
    ChatMessage         - row dataclasses, each with from_row()/to_dict()
    DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, DEFAULT_WATCHLIST_TICKERS
                        - seed constants

Repository submodules (import the submodule, or the functions directly):
    users:      get_user_profile, get_cash_balance, set_cash_balance
    watchlist:  list_watchlist, add_ticker, remove_ticker, count_tickers
    positions:  get_position, list_positions, upsert_position, delete_position
    trades:     insert_trade, list_trades
    snapshots:  insert_snapshot, list_snapshots
    chat:       insert_message, list_recent_messages

Example:
    from app.db import watchlist
    watchlist.list_watchlist()

    from app.db.positions import upsert_position
    upsert_position("AAPL", quantity=10, avg_cost=190.0)
"""

from . import chat, positions, snapshots, trades, users, watchlist
from .connection import get_connection, get_db_path, init_db
from .errors import DuplicateTickerError
from .models import ChatMessage, PortfolioSnapshot, Position, Trade, UserProfile, WatchlistEntry
from .schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS

__all__ = [
    "init_db",
    "get_connection",
    "get_db_path",
    "DuplicateTickerError",
    "UserProfile",
    "WatchlistEntry",
    "Position",
    "Trade",
    "PortfolioSnapshot",
    "ChatMessage",
    "DEFAULT_USER_ID",
    "DEFAULT_CASH_BALANCE",
    "DEFAULT_WATCHLIST_TICKERS",
    "users",
    "watchlist",
    "positions",
    "trades",
    "snapshots",
    "chat",
]
