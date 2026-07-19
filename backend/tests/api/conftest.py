"""Fixtures for API-layer tests: isolated DB + a fresh FastAPI app per test."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point FINALLY_DB_PATH at an isolated temp file for this test."""
    path = tmp_path / "finally_test.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    return path


@pytest.fixture
def client(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A TestClient wrapping a fresh app, isolated DB, and GBM simulator.

    Each test builds its own app via create_app() (fresh PriceCache /
    MarketDataSource) since MarketDataSource.start() may only be called once
    per instance — reusing a module-level app across tests would break on
    the second test's startup.
    """
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    # Deterministic, offline chat responses (PLAN.md §9) — API tests that care
    # about real LLM-call behavior monkeypatch app.ai directly instead.
    monkeypatch.setenv("LLM_MOCK", "true")
    with TestClient(create_app()) as test_client:
        yield test_client
