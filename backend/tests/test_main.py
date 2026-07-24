"""Tests for the FastAPI app wiring: health check, routers, and static serving."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    monkeypatch.setenv("FINALLY_DB_PATH", str(tmp_path / "finally.db"))


@pytest.fixture
def no_static_env(tmp_path, db_env, monkeypatch):
    monkeypatch.setenv("FINALLY_STATIC_DIR", str(tmp_path / "does-not-exist"))


@pytest.fixture
def static_env(tmp_path, db_env, monkeypatch):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>FinAlly</body></html>")
    monkeypatch.setenv("FINALLY_STATIC_DIR", str(static_dir))
    return static_dir


def test_health_check_returns_ok(no_static_env):
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_all_routers_mounted(no_static_env):
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/api/watchlist").status_code == 200
        assert client.get("/api/portfolio").status_code == 200
        assert client.get("/api/portfolio/history").status_code == 200


def test_static_frontend_not_mounted_when_directory_absent(no_static_env):
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 404


def test_static_frontend_served_when_directory_present(static_env):
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "FinAlly" in response.text
