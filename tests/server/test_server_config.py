"""Tests for server config."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
from config import DATABASE_URL, LAST_UPDATE_FILE, API_KEY_LENGTH, API_KEY_PREFIX

def test_database_url_default():
    """测试默认数据库 URL"""
    assert DATABASE_URL == "postgresql://user:password@localhost:5432/echomark"

def test_last_update_file_default():
    """测试默认 last_update 文件路径"""
    assert LAST_UPDATE_FILE == "/opt/echomark/last_update"

def test_api_key_length():
    """测试 API Key 长度"""
    assert API_KEY_LENGTH == 32

def test_api_key_prefix():
    """测试 API Key 前缀"""
    assert API_KEY_PREFIX == "ek_"
