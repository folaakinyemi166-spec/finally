"""Tests for database path resolution."""

from pathlib import Path

from app.db.connection import DB_PATH_ENV_VAR, get_db_path


class TestGetDbPath:
    def test_default_path_ends_with_db_finally_db(self, monkeypatch):
        monkeypatch.delenv(DB_PATH_ENV_VAR, raising=False)
        path = get_db_path()
        assert path.parts[-2:] == ("db", "finally.db")

    def test_env_var_override(self, monkeypatch, tmp_path):
        override = tmp_path / "custom" / "somewhere.db"
        monkeypatch.setenv(DB_PATH_ENV_VAR, str(override))
        assert get_db_path() == Path(override)
