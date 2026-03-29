"""Tests for EchoMark Skill config."""
import os
import sys
sys.path.insert(0, '.')
from config import ECHO_MARK_API_URL, API_TIMEOUT, CONFIG_DIR, API_KEY_FILE

def test_api_url_default():
    """测试默认 API URL"""
    assert ECHO_MARK_API_URL == "https://api.echomark.dev"

def test_api_timeout():
    """测试超时配置"""
    assert API_TIMEOUT == 30

def test_config_dir():
    """测试配置目录"""
    assert CONFIG_DIR == os.path.expanduser("~/.echomark")

def test_api_key_file():
    """测试 API Key 文件路径"""
    expected = os.path.join(os.path.expanduser("~/.echomark"), "api_key")
    assert API_KEY_FILE == expected
