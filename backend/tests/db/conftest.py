"""Fixtures for db package tests.

Every test gets its own temp-file SQLite DB (never the real db/finally.db)
by pointing FINALLY_DB_PATH at a path inside pytest's tmp_path. This is a
real file rather than ':memory:' because app.db.connection opens a fresh
connection per call — ':memory:' would give each call its own empty DB.
"""

from pathlib import Path

import pytest


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point FINALLY_DB_PATH at an isolated temp file for this test."""
    path = tmp_path / "finally_test.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    return path
