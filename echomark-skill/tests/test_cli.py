"""Tests for Skill CLI argument parsing."""
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Setup mock config before import
mock_config_dir = tempfile.mkdtemp()
mock_api_key_file = os.path.join(mock_config_dir, "api_key")

with patch.dict(os.environ, {"ECHO_MARK_API_URL": "http://test.local"}):
    with patch("config.CONFIG_DIR", mock_config_dir):
        with patch("config.API_KEY_FILE", mock_api_key_file):
            from scripts import register, submit, query


class TestRegisterCLI:
    """Tests for register CLI."""

    @patch("scripts.register.requests.post")
    def test_register_main_success(self, mock_post, capsys=None):
        """测试 register main 正常调用"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_key": "ek_test123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Simulate calling main (no args needed)
        with patch.object(sys, 'argv', ['register']):
            try:
                register.main()
            except SystemExit:
                pass

        # Verify API was called
        mock_post.assert_called_once()

    @patch("scripts.register.requests.post")
    def test_register_main_network_error(self, mock_post, capsys):
        """测试 register main 网络错误"""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")

        with patch.object(sys, 'argv', ['register']):
            try:
                register.main()
            except SystemExit as e:
                assert e.code == 1

        captured = capsys.readouterr()
        assert "Registration failed" in captured.err


class TestSubmitCLI:
    """Tests for submit CLI argument parsing."""

    def test_submit_missing_args(self, capsys=None):
        """测试 submit 缺少参数"""
        with patch.object(sys, 'argv', ['submit']):
            try:
                submit.main()
            except SystemExit:
                pass

        # argparse 会打印用法信息

    def test_submit_invalid_choice(self, capsys=None):
        """测试 submit 无效选项"""
        with patch.object(sys, 'argv', ['submit', '--tool', 'test', '--accuracy', '6']):
            try:
                submit.main()
            except SystemExit:
                pass

    @patch("scripts.submit.requests.post")
    def test_submit_main_success(self, mock_post, capsys=None):
        """测试 submit main 成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "uuid-123", "success": True}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Create a mock API key file
        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

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

    @patch("scripts.submit.requests.post")
    def test_submit_file_not_found(self, mock_post, capsys):
        """测试 submit API Key 文件不存在"""
        # Remove API key file to simulate not registered
        if os.path.exists(mock_api_key_file):
            os.remove(mock_api_key_file)

        with patch.object(sys, 'argv', [
            'submit', '--tool', 'tavily',
            '--accuracy', '5', '--efficiency', '4',
            '--usability', '4', '--stability', '5'
        ]):
            try:
                submit.main()
            except SystemExit as e:
                assert e.code == 1

        captured = capsys.readouterr()
        assert "Run 'python -m scripts.register' first" in captured.err


class TestQueryCLI:
    """Tests for query CLI argument parsing."""

    def test_query_missing_args(self, capsys=None):
        """测试 query 缺少参数"""
        with patch.object(sys, 'argv', ['query']):
            try:
                query.main()
            except SystemExit:
                pass

    @patch("scripts.query.requests.get")
    def test_query_main_success(self, mock_get, capsys=None):
        """测试 query main 成功"""
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

        # Create a mock API key file
        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch.object(sys, 'argv', ['query', '--tool', 'tavily']):
            try:
                query.main()
            except SystemExit:
                pass

        mock_get.assert_called_once()

    @patch("scripts.query.requests.get")
    def test_query_network_error(self, mock_get, capsys=None):
        """测试 query 网络错误"""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        with open(mock_api_key_file, "w") as f:
            f.write("ek_test_key")

        with patch.object(sys, 'argv', ['query', '--tool', 'tavily']):
            try:
                query.main()
            except SystemExit as e:
                assert e.code == 1
