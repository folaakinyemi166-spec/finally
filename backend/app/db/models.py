"""Dataclasses representing rows from each table.

Each has a ``from_row`` classmethod (accepts a ``sqlite3.Row``) and a
``to_dict`` method for JSON serialization, matching the style of
``PriceUpdate`` in app/market/models.py.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UserProfile:
    id: str
    cash_balance: float
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> UserProfile:
        return cls(id=row["id"], cash_balance=row["cash_balance"], created_at=row["created_at"])

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "cash_balance": self.cash_balance, "created_at": self.created_at}


@dataclass(frozen=True)
class WatchlistEntry:
    id: str
    user_id: str
    ticker: str
    added_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> WatchlistEntry:
        return cls(
            id=row["id"], user_id=row["user_id"], ticker=row["ticker"], added_at=row["added_at"]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "added_at": self.added_at,
        }


@dataclass(frozen=True)
class Position:
    id: str
    user_id: str
    ticker: str
    quantity: float
    avg_cost: float
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Position:
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            ticker=row["ticker"],
            quantity=row["quantity"],
            avg_cost=row["avg_cost"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Trade:
    id: str
    user_id: str
    ticker: str
    side: str
    quantity: float
    price: float
    executed_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Trade:
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            ticker=row["ticker"],
            side=row["side"],
            quantity=row["quantity"],
            price=row["price"],
            executed_at=row["executed_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "executed_at": self.executed_at,
        }


@dataclass(frozen=True)
class PortfolioSnapshot:
    id: str
    user_id: str
    total_value: float
    recorded_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> PortfolioSnapshot:
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            total_value=row["total_value"],
            recorded_at=row["recorded_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_value": self.total_value,
            "recorded_at": self.recorded_at,
        }


@dataclass(frozen=True)
class ChatMessage:
    id: str
    user_id: str
    role: str
    content: str
    actions: list[Any] | dict[str, Any] | None
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ChatMessage:
        raw_actions = row["actions"]
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            role=row["role"],
            content=row["content"],
            actions=json.loads(raw_actions) if raw_actions is not None else None,
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "actions": self.actions,
            "created_at": self.created_at,
        }
