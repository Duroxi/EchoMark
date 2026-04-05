"""Tests for local_db module."""
import os
import sys
import sqlite3
import tempfile
import importlib.util
from unittest.mock import patch

import pytest

# Load skill config
config_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'config.py')
spec = importlib.util.spec_from_file_location("skill_config", config_path)
skill_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_config)

# Create temp dir and db
mock_config_dir = tempfile.mkdtemp()
mock_db_file = os.path.join(mock_config_dir, "local_ratings.db")

# Patch config and import local_db
with patch.object(skill_config, 'LOCAL_DB_FILE', mock_db_file):
    with patch.object(skill_config, 'CONFIG_DIR', mock_config_dir):
        scripts_path = os.path.join(os.path.dirname(__file__), '..')
        sys.path.insert(0, scripts_path)
        sys.modules['config'] = skill_config
        sys.modules.pop('scripts.local_db', None)
        from scripts import local_db


def _use_fresh_db(db_name):
    """Create a fresh db path and patch local_db to use it."""
    fresh_db = os.path.join(mock_config_dir, db_name)
    return patch.object(local_db, 'LOCAL_DB_FILE', fresh_db), fresh_db


class TestInitDB:
    """Tests for database initialization."""

    def test_init_db_creates_file(self):
        """Test init_db creates the database file."""
        patcher, fresh_db = _use_fresh_db("test_init.db")
        with patcher:
            with patch.object(local_db, 'CONFIG_DIR', mock_config_dir):
                local_db.init_db()
        assert os.path.exists(fresh_db)

    def test_init_db_idempotent(self):
        """Test init_db can be called multiple times safely."""
        local_db.init_db()
        local_db.init_db()


class TestSaveRating:
    """Tests for save_rating."""

    def test_save_and_query(self):
        """Test saving a rating and querying it back."""
        local_db.save_rating(
            tool_name="test_tool",
            accuracy=5, efficiency=4, usability=4, stability=5,
            overall=4.7, comment="great",
        )

        result = local_db.query_ratings("test_tool")
        assert result is not None
        assert result["tool_name"] == "test_tool"
        assert result["total_ratings"] == 1
        assert result["avg_accuracy"] == 5.0
        assert result["avg_overall"] == 4.7

    def test_save_multiple_ratings(self):
        """Test saving multiple ratings aggregates correctly."""
        for acc in [4, 5, 3]:
            local_db.save_rating(
                tool_name="multi_tool",
                accuracy=acc, efficiency=4, usability=4, stability=4,
                overall=round(acc * 0.4 + 4 * 0.3 + 4 * 0.2 + 4 * 0.1, 1),
            )

        result = local_db.query_ratings("multi_tool")
        assert result["total_ratings"] == 3
        assert result["avg_accuracy"] == 4.0


class TestQueryRatings:
    """Tests for query_ratings."""

    def test_query_nonexistent_tool(self):
        """Test querying a tool with no ratings returns None."""
        result = local_db.query_ratings("nonexistent_tool_xyz")
        assert result is None

    def test_query_returns_correct_fields(self):
        """Test query result has all expected fields."""
        local_db.save_rating(
            tool_name="fields_tool",
            accuracy=5, efficiency=4, usability=3, stability=4,
            overall=4.2, comment="ok",
        )

        result = local_db.query_ratings("fields_tool")
        expected_keys = {"tool_name", "total_ratings", "avg_accuracy",
                         "avg_efficiency", "avg_usability", "avg_stability",
                         "avg_overall", "last_updated"}
        assert expected_keys.issubset(set(result.keys()))


class TestListTools:
    """Tests for list_tools."""

    def test_list_tools_empty(self):
        """Test list_tools with empty db."""
        patcher, fresh_db = _use_fresh_db("empty_list.db")
        with patcher:
            with patch.object(local_db, 'CONFIG_DIR', mock_config_dir):
                local_db.init_db()
                tools = local_db.list_tools()
        assert tools == []

    def test_list_tools_returns_rated_tools(self):
        """Test list_tools returns tools with ratings."""
        local_db.save_rating("list_tool_a", 5, 4, 4, 5, 4.6)
        local_db.save_rating("list_tool_b", 3, 3, 3, 3, 3.0)

        tools = local_db.list_tools()
        tool_names = [t["tool_name"] for t in tools]
        assert "list_tool_a" in tool_names
        assert "list_tool_b" in tool_names


class TestGetRatingHistory:
    """Tests for get_rating_history."""

    def test_history_empty(self):
        """Test history for nonexistent tool."""
        history = local_db.get_rating_history("no_such_tool")
        assert history == []

    def test_history_returns_records(self):
        """Test history returns individual records in reverse order."""
        local_db.save_rating("hist_tool", 5, 4, 4, 5, 4.6, "first")
        local_db.save_rating("hist_tool", 3, 3, 3, 3, 3.0, "second")

        history = local_db.get_rating_history("hist_tool")
        assert len(history) == 2
        assert history[0]["comment"] == "second"  # Most recent first
        assert history[1]["comment"] == "first"
