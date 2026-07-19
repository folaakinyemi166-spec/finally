"""Chat messages repository — conversation history with the LLM (PLAN.md §9)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from .connection import get_connection
from .models import ChatMessage
from .schema import DEFAULT_USER_ID
from .util import now_iso


def insert_message(
    role: str,
    content: str,
    actions: list[Any] | dict[str, Any] | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> ChatMessage:
    """Append a chat message.

    `role` is 'user' or 'assistant'. `actions` (trades/watchlist changes and
    their per-action success/failure outcomes) is JSON-encoded for storage and
    decoded back on read; pass None for messages with no side effects.
    """
    msg_id = str(uuid.uuid4())
    created_at = now_iso()
    actions_json = json.dumps(actions) if actions is not None else None
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (msg_id, user_id, role, content, actions_json, created_at),
        )
    return ChatMessage(
        id=msg_id,
        user_id=user_id,
        role=role,
        content=content,
        actions=actions,
        created_at=created_at,
    )


def list_recent_messages(user_id: str = DEFAULT_USER_ID, limit: int = 20) -> list[ChatMessage]:
    """Return the most recent `limit` messages, oldest first.

    Ready to feed directly into the LLM prompt as conversation history —
    PLAN.md §9 specifies a 20-message (10-turn) window.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [ChatMessage.from_row(r) for r in reversed(rows)]
