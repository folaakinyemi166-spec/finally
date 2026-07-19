"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def event_loop_policy():
    """Use the default event loop policy for all async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point FINALLY_DB_PATH at an isolated temp file for this test."""
    path = tmp_path / "finally_test.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    return path
