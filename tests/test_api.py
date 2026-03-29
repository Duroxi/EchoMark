import sys
sys.path.insert(0, 'server')

import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_full_flow():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register
        resp = await client.post("/api/v1/agents/register")
        assert resp.status_code == 200
        api_key = resp.json()["api_key"]

        # Submit rating
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "test-tool",
                "accuracy": 5,
                "efficiency": 4,
                "usability": 4,
                "stability": 5,
                "comment": "好用"
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp.status_code == 200

        # Query (will be empty since no nightly update yet)
        resp = await client.get(
            "/api/v1/ratings/test-tool",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert resp.status_code == 404  # No stats yet
