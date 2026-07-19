"""Tests for the positions repository."""

from app.db import positions


class TestPositions:
    def test_get_position_missing(self, db_path):
        assert positions.get_position("AAPL") is None

    def test_upsert_creates_position(self, db_path):
        pos = positions.upsert_position("AAPL", quantity=10, avg_cost=190.0)
        assert pos.ticker == "AAPL"
        assert pos.quantity == 10
        assert pos.avg_cost == 190.0

        fetched = positions.get_position("AAPL")
        assert fetched is not None
        assert fetched.quantity == 10
        assert fetched.avg_cost == 190.0

    def test_upsert_updates_existing_position(self, db_path):
        first = positions.upsert_position("AAPL", quantity=10, avg_cost=190.0)
        second = positions.upsert_position("AAPL", quantity=15, avg_cost=195.0)

        # Same underlying row (id preserved), values updated
        assert second.id == first.id
        fetched = positions.get_position("AAPL")
        assert fetched.quantity == 15
        assert fetched.avg_cost == 195.0

        # UNIQUE(user_id, ticker) means only one row exists, not two
        all_positions = positions.list_positions()
        assert len(all_positions) == 1

    def test_list_positions_ordered_by_ticker(self, db_path):
        positions.upsert_position("TSLA", quantity=1, avg_cost=250.0)
        positions.upsert_position("AAPL", quantity=2, avg_cost=190.0)
        result = [p.ticker for p in positions.list_positions()]
        assert result == ["AAPL", "TSLA"]

    def test_delete_position(self, db_path):
        positions.upsert_position("AAPL", quantity=10, avg_cost=190.0)
        positions.delete_position("AAPL")
        assert positions.get_position("AAPL") is None
        assert positions.list_positions() == []

    def test_delete_nonexistent_position_does_not_raise(self, db_path):
        positions.delete_position("AAPL")  # should not raise

    def test_positions_scoped_per_user(self, db_path):
        positions.upsert_position("AAPL", quantity=10, avg_cost=190.0, user_id="default")
        positions.upsert_position("AAPL", quantity=5, avg_cost=200.0, user_id="other")
        assert positions.get_position("AAPL", user_id="default").quantity == 10
        assert positions.get_position("AAPL", user_id="other").quantity == 5
