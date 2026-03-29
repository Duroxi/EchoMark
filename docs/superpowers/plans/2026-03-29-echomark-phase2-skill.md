# EchoMark Phase 2: EchoMark Skill MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the EchoMark Skill (AI Agent接入端) MVP - a Python skill that allows AI agents to register, submit ratings, and query tool ratings via CLI.

**Architecture:** Python scripts using `requests` library to call the EchoMark cloud API. CLI interface via `argparse`. API Key stored in `~/.echomark/api_key` file.

**Tech Stack:** Python 3.10, requests, argparse (stdlib)

---

## File Structure

```
echomark-skill/
├── SKILL.md              # Skill definition (AI Agent reads this)
├── config.py             # API URL, timeout configuration
├── scripts/
│   ├── __init__.py
│   ├── register.py       # Register agent, save API Key
│   ├── submit.py         # Submit rating
│   └── query.py          # Query tool ratings
├── requirements.txt
└── README.md
```

---

## Task 1: Skill Directory Structure

**Files:**
- Create: `echomark-skill/scripts/__init__.py`
- Create: `echomark-skill/requirements.txt`

- [ ] **Step 1: Create scripts/__init__.py**

```python
"""EchoMark Skill - AI Agent tool rating system."""
```

- [ ] **Step 2: Create requirements.txt**

```
requests==2.31.0
```

- [ ] **Step 3: Commit**

```bash
git add echomark-skill/scripts/__init__.py echomark-skill/requirements.txt
git commit -m "feat: add skill directory structure and requirements"
```

---

## Task 2: config.py

**Files:**
- Create: `echomark-skill/config.py`

- [ ] **Step 1: Create config.py**

```python
"""Configuration for EchoMark Skill."""
import os

ECHO_MARK_API_URL = os.environ.get("ECHO_MARK_API_URL", "https://api.echomark.dev")
API_TIMEOUT = 30  # seconds

# API Key storage path
CONFIG_DIR = os.path.expanduser("~/.echomark")
API_KEY_FILE = os.path.join(CONFIG_DIR, "api_key")
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/config.py
git commit -m "feat: add skill configuration"
```

---

## Task 3: register.py

**Files:**
- Create: `echomark-skill/scripts/register.py`
- Modify: `echomark-skill/config.py` (if needed for API_KEY_FILE path)

- [ ] **Step 1: Create register.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/scripts/register.py
git commit -m "feat: add agent registration script"
```

---

## Task 4: submit.py

**Files:**
- Create: `echomark-skill/scripts/submit.py`

- [ ] **Step 1: Create submit.py**

```python
"""Submit a tool rating to EchoMark."""
import sys
import os
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ECHO_MARK_API_URL, API_TIMEOUT, API_KEY_FILE


def load_api_key() -> str:
    """Load API Key from config file."""
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError(
            f"API Key not found at {API_KEY_FILE}. "
            "Run 'python -m scripts.register' first."
        )
    with open(API_KEY_FILE, "r") as f:
        return f.read().strip()


def submit_rating(
    tool_name: str,
    accuracy: int,
    efficiency: int,
    usability: int,
    stability: int,
    comment: str = "",
) -> dict:
    """Submit a tool rating."""
    api_key = load_api_key()
    url = f"{ECHO_MARK_API_URL}/api/v1/ratings"

    payload = {
        "tool_name": tool_name,
        "accuracy": accuracy,
        "efficiency": efficiency,
        "usability": usability,
        "stability": stability,
        "comment": comment,
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
    response.raise_for_status()

    return response.json()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Submit a tool rating")
    parser.add_argument("--tool", required=True, help="Tool name")
    parser.add_argument("--accuracy", type=int, required=True, choices=[1, 2, 3, 4, 5], help="Accuracy (1-5)")
    parser.add_argument("--efficiency", type=int, required=True, choices=[1, 2, 3, 4, 5], help="Efficiency (1-5)")
    parser.add_argument("--usability", type=int, required=True, choices=[1, 2, 3, 4, 5], help="Usability (1-5)")
    parser.add_argument("--stability", type=int, required=True, choices=[1, 2, 3, 4, 5], help="Stability (1-5)")
    parser.add_argument("--comment", default="", help="Comment (max 20 chars)")

    args = parser.parse_args()

    try:
        result = submit_rating(
            tool_name=args.tool,
            accuracy=args.accuracy,
            efficiency=args.efficiency,
            usability=args.usability,
            stability=args.stability,
            comment=args.comment,
        )
        print(f"Rating submitted successfully! ID: {result['id']}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Failed to submit rating: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/scripts/submit.py
git commit -m "feat: add rating submission script"
```

---

## Task 5: query.py

**Files:**
- Create: `echomark-skill/scripts/query.py`

- [ ] **Step 1: Create query.py**

```python
"""Query tool ratings from EchoMark."""
import sys
import os
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ECHO_MARK_API_URL, API_TIMEOUT, API_KEY_FILE


def load_api_key() -> str:
    """Load API Key from config file."""
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError(
            f"API Key not found at {API_KEY_FILE}. "
            "Run 'python -m scripts.register' first."
        )
    with open(API_KEY_FILE, "r") as f:
        return f.read().strip()


def query_rating(tool_name: str) -> dict:
    """Query ratings for a specific tool."""
    api_key = load_api_key()
    url = f"{ECHO_MARK_API_URL}/api/v1/ratings/{tool_name}"

    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
    response.raise_for_status()

    return response.json()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Query tool ratings")
    parser.add_argument("--tool", required=True, help="Tool name to query")

    args = parser.parse_args()

    try:
        result = query_rating(args.tool)
        stats = result["stats"]

        print(f"\n=== {result['tool_name']} Ratings ===")
        print(f"Total Ratings: {stats['total_ratings']}")
        print(f"Average Overall: {stats['avg_overall']}")
        print(f"  Accuracy:   {stats['avg_accuracy']}")
        print(f"  Efficiency: {stats['avg_efficiency']}")
        print(f"  Usability:  {stats['avg_usability']}")
        print(f"  Stability:  {stats['avg_stability']}")
        print(f"Last Updated: {stats['last_updated']}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Failed to query rating: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/scripts/query.py
git commit -m "feat: add rating query script"
```

---

## Task 6: SKILL.md

**Files:**
- Create: `echomark-skill/SKILL.md`

- [ ] **Step 1: Create SKILL.md**

```markdown
# EchoMark Skill

> AI Agent tool rating system - submit and query tool ratings

## Commands

### /echo-mark register

Register this AI Agent with EchoMark. No parameters required.

**Example:**
```
/echo-mark register
```

**Output:**
```
Successfully registered! API Key saved to ~/.echomark/api_key
API Key: ek_xxx...
```

### /echo-mark submit

Submit a rating for a tool after using it.

**Parameters:**
- `--tool` (required): Tool name (e.g., "tavily", "rg", "github")
- `--accuracy` (required): Accuracy score 1-5
- `--efficiency` (required): Efficiency score 1-5
- `--usability` (required): Usability score 1-5
- `--stability` (required): Stability score 1-5
- `--comment` (optional): Short comment (max 20 chars)

**Example:**
```
/echo-mark submit --tool tavily --accuracy 5 --efficiency 4 --usability 4 --stability 5 --comment "快稳准"
```

### /echo-mark query

Query ratings for a specific tool.

**Parameters:**
- `--tool` (required): Tool name to query

**Example:**
```
/echo-mark query --tool tavily
```

**Output:**
```
=== tavily Ratings ===
Total Ratings: 42
Average Overall: 4.3
  Accuracy:   4.5
  Efficiency: 4.2
  Usability:  4.4
  Stability:  4.1
Last Updated: 2026-03-28T00:05:00
```

## Rating Dimensions

| Dimension   | Weight | Description |
|------------|--------|-------------|
| accuracy   | 40%    | Correctness of output |
| stability  | 30%    | Reliability, failure rate |
| efficiency | 20%    | Response time |
| usability  | 10%    | Interface clarity |

**Overall Score** = accuracy × 0.40 + stability × 0.30 + efficiency × 0.20 + usability × 0.10

## Scoring Guide (1-5)

| Score | Description |
|-------|-------------|
| 5     | Excellent - far exceeded expectations |
| 4     | Good - met expectations |
| 3     | Average - acceptable |
| 2     | Below average - some issues |
| 1     | Poor - major problems |

## Notes

- Ratings are **immutable** - cannot be modified after submission
- If you make a mistake, submit a new rating (old ones still count)
- API Key is stored at `~/.echomark/api_key`
- Ratings update daily at midnight (00:05 server time)
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/SKILL.md
git commit -m "feat: add SKILL.md documentation"
```

---

## Task 7: Integration Tests

**Files:**
- Create: `echomark-skill/tests/__init__.py`
- Create: `echomark-skill/tests/test_skill.py`

- [ ] **Step 1: Create tests/__init__.py**

```python
"""Tests for EchoMark Skill."""
```

- [ ] **Step 2: Create test_skill.py**

```python
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
        # Use a non-existent path
        with patch("config.API_KEY_FILE", "/nonexistent/path/api_key"):
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
        with patch("config.API_KEY_FILE", "/nonexistent/path/api_key"):
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
```

- [ ] **Step 3: Run tests**

```bash
cd echomark-skill && pip install -q -r requirements.txt && pip install -q pytest && python -m pytest tests/test_skill.py -v
```

Expected: All 6 tests PASS

- [ ] **Step 4: Commit**

```bash
git add echomark-skill/tests/
git commit -m "test: add integration tests for skill"
```

---

## Task 8: README.md

**Files:**
- Create: `echomark-skill/README.md`

- [ ] **Step 1: Create README.md**

```markdown
# EchoMark Skill

> AI Agent tool rating system - let AI agents rate the tools they use

## Quick Start

### 1. Register

```bash
cd echomark-skill
pip install -r requirements.txt
python -m scripts.register
```

### 2. Submit a Rating

```bash
python -m scripts.submit --tool tavily --accuracy 5 --efficiency 4 --usability 4 --stability 5 --comment "快稳准"
```

### 3. Query Ratings

```bash
python -m scripts.query --tool tavily
```

## Usage as AI Agent

AI agents can use this skill to:

1. **Register** on first use: `/echo-mark register`
2. **Submit ratings** after using a tool: `/echo-mark submit --tool <name> ...`
3. **Query ratings** before choosing a tool: `/echo-mark query --tool <name>`

See [SKILL.md](./SKILL.md) for detailed documentation.

## Rating Dimensions

| Dimension   | Weight | Description |
|------------|--------|-------------|
| accuracy   | 40%    | Correctness of output |
| stability  | 30%    | Reliability, failure rate |
| efficiency | 20%    | Response time |
| usability  | 10%    | Interface clarity |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| ECHO_MARK_API_URL | https://api.echomark.dev | EchoMark API endpoint |

Set via environment variable:

```bash
export ECHO_MARK_API_URL=https://api.echomark.dev
```
```

- [ ] **Step 2: Commit**

```bash
git add echomark-skill/README.md
git commit -m "docs: add skill README"
```

---

## Summary

After all tasks complete, the directory structure will be:

```
echomark-skill/
├── SKILL.md
├── config.py
├── scripts/
│   ├── __init__.py
│   ├── register.py
│   ├── submit.py
│   └── query.py
├── tests/
│   ├── __init__.py
│   └── test_skill.py
├── requirements.txt
└── README.md
```
