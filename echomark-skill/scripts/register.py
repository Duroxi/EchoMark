"""Register an AI Agent and obtain API Key."""
import sys
import json
import os
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ECHO_MARK_API_URL, API_TIMEOUT, CONFIG_DIR, API_KEY_FILE


def register() -> dict:
    """Register agent with EchoMark cloud service."""
    url = f"{ECHO_MARK_API_URL}/api/v1/agents/register"

    response = requests.post(url, timeout=API_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    api_key = data["api_key"]

    # Save API Key to config file
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(API_KEY_FILE, "w") as f:
        f.write(api_key)

    # Set file permissions to user-only (Unix)
    os.chmod(API_KEY_FILE, 0o600)

    return {"success": True, "api_key": api_key}


def main():
    try:
        result = register()
        print(f"Successfully registered! API Key saved to {API_KEY_FILE}")
        print(f"API Key: {result['api_key']}")
    except requests.RequestException as e:
        print(f"Registration failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
