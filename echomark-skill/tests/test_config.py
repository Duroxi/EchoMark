"""Tests for EchoMark Skill config."""
import importlib.util
import os
import sys

# Load config directly from the scripts directory
config_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'config.py')
spec = importlib.util.spec_from_file_location("skill_config", config_path)
skill_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_config)

ECHO_MARK_API_URL = skill_config.ECHO_MARK_API_URL
API_TIMEOUT = skill_config.API_TIMEOUT
CONFIG_DIR = skill_config.CONFIG_DIR
API_KEY_FILE = skill_config.API_KEY_FILE


def test_api_url_default():
    """测试默认 API URL"""
    assert ECHO_MARK_API_URL == "http://47.109.154.82:9527"


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
