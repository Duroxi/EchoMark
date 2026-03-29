#!/usr/bin/env python3
"""Query tool ratings from EchoMark."""
import sys
import os

# Add current directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from config import ECHO_MARK_API_URL, API_TIMEOUT, API_KEY_FILE


def load_api_key():
    """Load API Key from config file."""
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError(
            f"API Key not found at {API_KEY_FILE}. "
            "Run './register.py' or 'python register.py' first."
        )
    with open(API_KEY_FILE, "r") as f:
        return f.read().strip()


def query_rating(tool_name):
    """Query ratings for a specific tool."""
    api_key = load_api_key()
    url = f"{ECHO_MARK_API_URL}/api/v1/ratings/{tool_name}"

    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
    response.raise_for_status()

    return response.json()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Query tool ratings from EchoMark")
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
