"""Tests for Skill CLI argument parsing."""
import os
import sys
import tempfile
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# Load skill config directly to avoid import conflicts
config_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'config.py')
spec = importlib.util.spec_from_file_location("skill_config", config_path)
skill_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_config)

# Create mock config directory and file path
mock_config_dir = tempfile.mkdtemp()
mock_api_key_file = os.path.join(mock_config_dir, "api_key")

# Setup path and import scripts
scripts_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, scripts_path)
sys.modules['config'] = skill_config

from scripts import register, submit, query


class TestRegisterCLI:
    """Tests for register CLI."""

    @patch("requests.post")
    def test_register_main_success(self, mock_post):
        """Test register main normal call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_test123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            with patch.object(sys, 'argv', ['register']):
                try:
                    register.main()
                except SystemExit:
                    pass

        mock_post.assert_called_once()

    @patch("requests.post")
    def test_register_main_network_error(self, mock_post):
        """Test register main network error."""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")

        with patch.object(sys, 'argv', ['register']):
            try:
                register.main()
            except SystemExit as e:
                assert e.code == 1


class TestSubmitCLI:
    """Tests for submit CLI argument parsing."""

    def test_submit_missing_args(self):
        """Test submit missing arguments."""
        with patch.object(sys, 'argv', ['submit']):
            try:
                submit.main()
            except SystemExit:
                pass

    def test_submit_invalid_choice(self):
        """Test submit invalid choice."""
        with patch.object(sys, 'argv', ['submit', '--tool', 'test', '--accuracy', '6']):
            try:
                submit.main()
            except SystemExit:
                pass

    @patch("requests.post")
    def test_submit_main_success(self, mock_post):
        """Test submit main success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "uuid-123", "success": True}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            with patch.object(sys, 'argv', [
                'submit', '--tool', 'tavily',
                '--accuracy', '5', '--efficiency', '4',
                '--usability', '4', '--stability', '5',
                '--comment', '好'
            ]):
                try:
                    submit.main()
                except SystemExit:
                    pass

        mock_post.assert_called_once()

    def test_submit_file_not_found(self):
        """Test submit API Key file not found."""
        with patch.object(skill_config, 'API_KEY_FILE', "/nonexistent/path/api_key"):
            with patch.object(sys, 'argv', [
                'submit', '--tool', 'tavily',
                '--accuracy', '5', '--efficiency', '4',
                '--usability', '4', '--stability', '5'
            ]):
                try:
                    submit.main()
                except SystemExit as e:
                    assert e.code == 1


class TestQueryCLI:
    """Tests for query CLI argument parsing."""

    def test_query_missing_args(self):
        """Test query missing arguments."""
        with patch.object(sys, 'argv', ['query']):
            try:
                query.main()
            except SystemExit:
                pass

    @patch("requests.get")
    def test_query_main_success(self, mock_get):
        """Test query main success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tool_name": "tavily",
            "stats": {
                "total_ratings": 10,
                "avg_overall": 4.5,
                "avg_accuracy": 4.7,
                "avg_efficiency": 4.3,
                "avg_usability": 4.5,
                "avg_stability": 4.5,
                "last_updated": "2026-03-28T00:05:00"
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            with patch.object(sys, 'argv', ['query', '--tool', 'tavily']):
                try:
                    query.main()
                except SystemExit:
                    pass

        mock_get.assert_called_once()

    @patch("requests.get")
    def test_query_network_error(self, mock_get):
        """Test query network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch.object(skill_config, 'API_KEY_FILE', mock_api_key_file):
            with patch.object(sys, 'argv', ['query', '--tool', 'tavily']):
                try:
                    query.main()
                except SystemExit as e:
                    assert e.code == 1
