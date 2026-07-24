"""Domain errors for chat/LLM processing."""

from __future__ import annotations


class LLMResponseError(Exception):
    """Raised when the LLM call fails or its response isn't valid structured JSON."""
