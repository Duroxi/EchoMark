"""Configuration for EchoMark Skill."""
import os

ECHO_MARK_API_URL = os.environ.get("ECHO_MARK_API_URL", "https://api.echomark.dev")
API_TIMEOUT = 30  # seconds

# API Key storage path
CONFIG_DIR = os.path.expanduser("~/.echomark")
API_KEY_FILE = os.path.join(CONFIG_DIR, "api_key")
