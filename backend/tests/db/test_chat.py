"""Tests for the chat_messages repository."""

from app.db import chat


class TestChat:
    def test_insert_user_message_no_actions(self, db_path):
        msg = chat.insert_message("user", "What's my portfolio worth?")
        assert msg.role == "user"
        assert msg.content == "What's my portfolio worth?"
        assert msg.actions is None

    def test_insert_assistant_message_with_actions(self, db_path):
        actions = [{"type": "trade", "ticker": "AAPL", "side": "buy", "status": "ok"}]
        msg = chat.insert_message("assistant", "Bought 10 AAPL.", actions=actions)
        assert msg.actions == actions

    def test_actions_json_round_trips_through_storage(self, db_path):
        actions = {"trades": [{"ticker": "AAPL"}], "watchlist_changes": []}
        chat.insert_message("assistant", "done", actions=actions)
        messages = chat.list_recent_messages()
        assert messages[-1].actions == actions

    def test_list_recent_messages_chronological_oldest_first(self, db_path):
        chat.insert_message("user", "first")
        chat.insert_message("assistant", "second")
        chat.insert_message("user", "third")
        result = chat.list_recent_messages()
        assert [m.content for m in result] == ["first", "second", "third"]

    def test_list_recent_messages_respects_limit_window(self, db_path):
        for i in range(25):
            chat.insert_message("user", f"message {i}")
        result = chat.list_recent_messages(limit=20)
        assert len(result) == 20
        # Should be the most recent 20, still oldest-first within that window
        assert result[0].content == "message 5"
        assert result[-1].content == "message 24"

    def test_chat_scoped_per_user(self, db_path):
        chat.insert_message("user", "hi", user_id="default")
        chat.insert_message("user", "hola", user_id="other")
        assert len(chat.list_recent_messages(user_id="default")) == 1
        assert len(chat.list_recent_messages(user_id="other")) == 1
