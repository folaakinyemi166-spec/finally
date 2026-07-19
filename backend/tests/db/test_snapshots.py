"""Tests for the portfolio_snapshots repository."""

from app.db import snapshots


class TestSnapshots:
    def test_insert_snapshot(self, db_path):
        snap = snapshots.insert_snapshot(total_value=10500.0)
        assert snap.total_value == 10500.0
        assert snap.user_id == "default"
        assert snap.id

    def test_list_snapshots_chronological(self, db_path):
        snapshots.insert_snapshot(total_value=10000.0)
        snapshots.insert_snapshot(total_value=10500.0)
        snapshots.insert_snapshot(total_value=10250.0)
        result = snapshots.list_snapshots()
        assert [s.total_value for s in result] == [10000.0, 10500.0, 10250.0]

    def test_snapshots_scoped_per_user(self, db_path):
        snapshots.insert_snapshot(total_value=10000.0, user_id="default")
        snapshots.insert_snapshot(total_value=5000.0, user_id="other")
        assert len(snapshots.list_snapshots(user_id="default")) == 1
        assert len(snapshots.list_snapshots(user_id="other")) == 1

    def test_list_snapshots_empty(self, db_path):
        assert snapshots.list_snapshots() == []
