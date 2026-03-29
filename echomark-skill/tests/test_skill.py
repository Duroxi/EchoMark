"""Integration tests for EchoMark Skill."""
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# Mock config before import
mock_config_dir = tempfile.mkdtemp()
mock_api_key_file = os.path.join(mock_config_dir, "api_key")

with patch.dict(os.environ, {"ECHO_MARK_API_URL": "http://test.local"}):
    with patch("config.CONFIG_DIR", mock_config_dir):
        with patch("config.API_KEY_FILE", mock_api_key_file):
            from scripts import register, submit, query


class TestRegister:
    """Tests for register module."""

    @patch("scripts.register.requests.post")
    def test_register_success(self, mock_post):
        """Test successful agent registration."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_test123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = register.register()

        assert result["success"] is True
        assert result["api_key"] == "ek_test123"
        assert os.path.exists(mock_api_key_file)

    @patch("scripts.register.requests.post")
    def test_register_saves_api_key(self, mock_post):
        """Test that register saves API Key to file."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_saved_key"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        register.register()

        with open(mock_api_key_file, "r") as f:
            saved_key = f.read().strip()
        assert saved_key == "ek_saved_key"


class TestSubmit:
    """Tests for submit module."""

    def test_load_api_key_file_not_found(self):
        """Test error when API Key file doesn't exist."""
        # Use a non-existent path - must patch the module's local binding
        with patch("scripts.submit.API_KEY_FILE", "/nonexistent/path/api_key"):
            with pytest.raises(FileNotFoundError) as exc_info:
                submit.load_api_key()
            assert "Run 'python -m scripts.register' first" in str(exc_info.value)

    def test_load_api_key_success(self):
        """Test loading API Key from file."""
        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch("config.API_KEY_FILE", mock_api_key_file):
            key = submit.load_api_key()
            assert key == "ek_test_key"

    @patch("scripts.submit.requests.post")
    def test_submit_rating_success(self, mock_post):
        """Test successful rating submission."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "uuid-123", "success": True, "message": "Rating submitted"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch("config.API_KEY_FILE", mock_api_key_file):
            result = submit.submit_rating(
                tool_name="test_tool",
                accuracy=5,
                efficiency=4,
                usability=4,
                stability=5,
                comment="great",
            )

        assert result["success"] is True
        assert result["id"] == "uuid-123"


class TestQuery:
    """Tests for query module."""

    def test_load_api_key_file_not_found(self):
        """Test error when API Key file doesn't exist."""
        # Must patch the module's local binding, not config.API_KEY_FILE
        with patch("scripts.query.API_KEY_FILE", "/nonexistent/path/api_key"):
            with pytest.raises(FileNotFoundError) as exc_info:
                query.load_api_key()
            assert "Run 'python -m scripts.register' first" in str(exc_info.value)

    @patch("scripts.query.requests.get")
    def test_query_rating_success(self, mock_get):
        """Test successful rating query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tool_name": "test_tool",
            "stats": {
                "total_ratings": 10,
                "avg_overall": 4.5,
                "avg_accuracy": 4.7,
                "avg_efficiency": 4.3,
                "avg_usability": 4.5,
                "avg_stability": 4.5,
                "last_updated": "2026-03-28T00:05:00",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch("config.API_KEY_FILE", mock_api_key_file):
            result = query.query_rating("test_tool")

        assert result["tool_name"] == "test_tool"
        assert result["stats"]["total_ratings"] == 10
        assert result["stats"]["avg_overall"] == 4.5
