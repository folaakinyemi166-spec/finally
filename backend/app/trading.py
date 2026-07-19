"""Trade execution and portfolio valuation (PLAN.md §7, §8).

Sits between the API routes and the db/market layers: enforces business
rules (a cached price exists, sufficient cash/shares), applies
weighted-average-cost accounting for buys, and persists the trade,
position, and portfolio snapshot as one logical unit.
"""

from __future__ import annotations

from app.db import positions, snapshots, trades, users
from app.errors import InsufficientFundsError, InsufficientSharesError, NoPriceAvailableError
from app.market import PriceCache

# Below this remaining quantity, a sell is treated as fully closing the position
# (float weighted-average-cost math otherwise leaves dust like 1e-14 shares).
POSITION_EPSILON = 1e-9


def execute_trade(ticker: str, side: str, quantity: float, price_cache: PriceCache) -> dict:
    """Validate and execute a market order, persisting all side effects.

    Raises NoPriceAvailableError, InsufficientFundsError, or
    InsufficientSharesError on business-rule violations (all subclasses of
    app.errors.TradingError, handled by a single FastAPI exception handler).
    """
    price = price_cache.get_price(ticker)
    if price is None:
        raise NoPriceAvailableError(
            f"No live price available for {ticker!r} — it must be on the watchlist "
            "and have received at least one price tick before it can be traded"
        )

    cash = users.get_cash_balance()
    position = positions.get_position(ticker)

    if side == "buy":
        updated_position, new_cash = _apply_buy(ticker, quantity, price, cash, position)
    else:
        updated_position, new_cash = _apply_sell(ticker, quantity, price, cash, position)

    users.set_cash_balance(new_cash)
    trade = trades.insert_trade(ticker, side, quantity, price)

    total_value = compute_total_value(new_cash, price_cache)
    snapshots.insert_snapshot(total_value)

    return {
        "trade": trade.to_dict(),
        "position": updated_position.to_dict() if updated_position else None,
        "cash_balance": new_cash,
        "total_value": total_value,
    }


def _apply_buy(ticker, quantity, price, cash, position):
    cost = quantity * price
    if cost > cash + POSITION_EPSILON:
        raise InsufficientFundsError(f"Insufficient cash: need {cost:.2f}, have {cash:.2f}")

    if position is None:
        new_quantity = quantity
        new_avg_cost = price
    else:
        new_quantity = position.quantity + quantity
        new_avg_cost = (position.quantity * position.avg_cost + cost) / new_quantity

    updated_position = positions.upsert_position(ticker, new_quantity, new_avg_cost)
    return updated_position, cash - cost


def _apply_sell(ticker, quantity, price, cash, position):
    held = position.quantity if position else 0.0
    if quantity > held + POSITION_EPSILON:
        raise InsufficientSharesError(f"Insufficient shares: trying to sell {quantity}, hold {held}")

    proceeds = quantity * price
    new_quantity = held - quantity

    if new_quantity <= POSITION_EPSILON:
        positions.delete_position(ticker)
        updated_position = None
    else:
        updated_position = positions.upsert_position(ticker, new_quantity, position.avg_cost)

    return updated_position, cash + proceeds


def compute_total_value(cash: float, price_cache: PriceCache) -> float:
    """Cash plus the market value of every open position.

    Falls back to a position's average cost when no live price is cached
    (e.g. it was removed from the watchlist after being bought) so
    valuation never breaks on a missing tick.
    """
    total = cash
    for position in positions.list_positions():
        price = price_cache.get_price(position.ticker)
        total += position.quantity * (price if price is not None else position.avg_cost)
    return round(total, 2)


def get_portfolio_summary(price_cache: PriceCache) -> dict:
    """Current positions, cash, total value, and unrealized P&L (PLAN.md §8)."""
    cash = users.get_cash_balance()
    total_value = cash
    total_unrealized_pl = 0.0
    position_dicts = []

    for position in positions.list_positions():
        price = price_cache.get_price(position.ticker)
        effective_price = price if price is not None else position.avg_cost
        market_value = position.quantity * effective_price
        unrealized_pl = position.quantity * (effective_price - position.avg_cost)
        unrealized_pl_percent = (
            (effective_price - position.avg_cost) / position.avg_cost * 100
            if position.avg_cost
            else 0.0
        )

        total_value += market_value
        total_unrealized_pl += unrealized_pl
        position_dicts.append(
            {
                **position.to_dict(),
                "current_price": price,
                "market_value": round(market_value, 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_pl_percent": round(unrealized_pl_percent, 4),
            }
        )

    return {
        "cash_balance": cash,
        "positions": position_dicts,
        "total_value": round(total_value, 2),
        "total_unrealized_pl": round(total_unrealized_pl, 2),
    }
