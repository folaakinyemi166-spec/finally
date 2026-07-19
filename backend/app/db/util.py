"""Small shared helpers for the db package."""

from __future__ import annotations

from datetime import UTC, datetime


def now_iso() -> str:
    """Current UTC time as an ISO-8601 string, used for all timestamp columns."""
    return datetime.now(UTC).isoformat()
