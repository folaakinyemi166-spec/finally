"""User profile repository — single cash-balance row per user."""

from __future__ import annotations

from .connection import get_connection
from .models import UserProfile
from .schema import DEFAULT_USER_ID


def get_user_profile(user_id: str = DEFAULT_USER_ID) -> UserProfile | None:
    """Fetch the user's profile, or None if it doesn't exist.

    Shouldn't be None for DEFAULT_USER_ID in practice, since it's seeded on
    first lazy init.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users_profile WHERE id = ?", (user_id,)).fetchone()
    return UserProfile.from_row(row) if row else None


def get_cash_balance(user_id: str = DEFAULT_USER_ID) -> float:
    """Convenience accessor for just the cash balance.

    Raises ValueError if the user profile doesn't exist.
    """
    profile = get_user_profile(user_id)
    if profile is None:
        raise ValueError(f"No user profile for user_id={user_id!r}")
    return profile.cash_balance


def set_cash_balance(cash_balance: float, user_id: str = DEFAULT_USER_ID) -> None:
    """Overwrite the user's cash balance.

    Callers compute the new value (e.g. cash - quantity * price on a buy,
    cash + quantity * price on a sell) — this just persists it.
    """
    with get_connection() as conn:
        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?", (cash_balance, user_id)
        )
