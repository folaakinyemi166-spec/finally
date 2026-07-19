"""Portfolio snapshots repository — total portfolio value recorded over time.

Written immediately after each trade execution, plus opportunistically every
60s from the market-data background loop (PLAN.md §7) — both call sites live
in the API layer; this module only persists/reads.
"""

from __future__ import annotations

import uuid

from .connection import get_connection
from .models import PortfolioSnapshot
from .schema import DEFAULT_USER_ID
from .util import now_iso


def insert_snapshot(total_value: float, user_id: str = DEFAULT_USER_ID) -> PortfolioSnapshot:
    """Record a portfolio value snapshot."""
    snapshot_id = str(uuid.uuid4())
    recorded_at = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (snapshot_id, user_id, total_value, recorded_at),
        )
    return PortfolioSnapshot(
        id=snapshot_id, user_id=user_id, total_value=total_value, recorded_at=recorded_at
    )


def list_snapshots(user_id: str = DEFAULT_USER_ID) -> list[PortfolioSnapshot]:
    """All snapshots for a user, chronological (oldest first) — for the P&L chart."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM portfolio_snapshots WHERE user_id = ? ORDER BY recorded_at",
            (user_id,),
        ).fetchall()
    return [PortfolioSnapshot.from_row(r) for r in rows]
