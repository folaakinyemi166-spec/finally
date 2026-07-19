"""Tests for the users repository."""

import pytest

from app.db import users


class TestUsers:
    def test_get_user_profile_seeded(self, db_path):
        profile = users.get_user_profile()
        assert profile is not None
        assert profile.id == "default"
        assert profile.cash_balance == 10000.0

    def test_get_user_profile_missing_user(self, db_path):
        assert users.get_user_profile(user_id="nobody") is None

    def test_get_cash_balance(self, db_path):
        assert users.get_cash_balance() == 10000.0

    def test_get_cash_balance_missing_user_raises(self, db_path):
        with pytest.raises(ValueError):
            users.get_cash_balance(user_id="nobody")

    def test_set_cash_balance(self, db_path):
        users.set_cash_balance(4321.50)
        assert users.get_cash_balance() == 4321.50
        # Persisted, not just returned in-memory
        profile = users.get_user_profile()
        assert profile.cash_balance == 4321.50
