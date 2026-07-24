"""Portfolio subsystem: positions, trade execution, P&L, and snapshots.

Public API:
    create_portfolio_router - FastAPI router factory (GET/POST /api/portfolio/*)
    snapshot_loop           - Background task recording snapshots every 30s
    get_portfolio           - Cash + positions + live P&L
    execute_trade           - Market order: validate, fill, persist, snapshot
    record_snapshot         - Insert a single portfolio_snapshots row
    get_history             - Snapshot history for the P&L chart
"""

from .background import snapshot_loop
from .errors import (
    InsufficientCashError,
    InsufficientSharesError,
    PortfolioError,
    UnknownTickerError,
)
from .router import create_portfolio_router
from .schemas import (
    HistoryOut,
    HistoryPointOut,
    PortfolioOut,
    PositionOut,
    TradeOut,
    TradeRequest,
)
from .service import execute_trade, get_history, get_portfolio, record_snapshot

__all__ = [
    "PortfolioError",
    "UnknownTickerError",
    "InsufficientCashError",
    "InsufficientSharesError",
    "create_portfolio_router",
    "snapshot_loop",
    "get_portfolio",
    "execute_trade",
    "record_snapshot",
    "get_history",
    "HistoryOut",
    "HistoryPointOut",
    "PortfolioOut",
    "PositionOut",
    "TradeOut",
    "TradeRequest",
]
