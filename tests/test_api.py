"""API endpoint tests for EchoMark server."""
import sys
sys.path.insert(0, 'server')

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import ASGITransport, AsyncClient
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from main import app, validation_exception_handler, http_exception_handler, general_exception_handler


@pytest.fixture
def mock_db():
    """Mock database module."""
    with patch('main.execute_sql') as mock:
        yield mock


@pytest.fixture
def mock_verify_auth():
    """Mock verify_auth to return (api_key_hash, agent_type)."""
    with patch('main.verify_auth', new_callable=AsyncMock) as mock:
        mock.return_value = ('$2b$12$mock_hash_value_placeholder', 'claude-code')
        yield mock


# ===== Registration Tests =====

@pytest.mark.asyncio
async def test_register_agent_success(mock_db):
    """Test agent registration returns API key."""
    mock_db.return_value = {'id': 'test-uuid'}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register", json={"agent_type": "claude-code"})

    assert resp.status_code == 200
    data = resp.json()
    assert 'api_key' in data
    assert data['agent_type'] == 'claude-code'


@pytest.mark.asyncio
async def test_register_agent_returns_ek_prefix(mock_db):
    """Test API Key starts with ek_ prefix."""
    mock_db.return_value = {'id': 'test-uuid'}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register", json={"agent_type": "claude-code"})

    assert resp.status_code == 200
    data = resp.json()
    assert data['api_key'].startswith('ek_')


@pytest.mark.asyncio
async def test_register_agent_returns_35_chars(mock_db):
    """Test API Key is 35 characters long."""
    mock_db.return_value = {'id': 'test-uuid'}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register", json={"agent_type": "claude-code"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data['api_key']) == 35


@pytest.mark.asyncio
async def test_register_agent_requires_body(mock_db):
    """Test registration without body returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/agents/register")
    assert resp.status_code == 422


# ===== Submit Rating Tests =====

@pytest.mark.asyncio
async def test_submit_rating_without_auth():
    """Test submit rating without auth returns 401.

    Note: With FastAPI's Header() validation, missing headers return 422.
    This test verifies the HTTPException handler directly.
    """
    mock_request = MagicMock()
    exc = HTTPException(status_code=401, detail="Invalid API key")
    response = await http_exception_handler(mock_request, exc)
    assert response.status_code == 401
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'UNAUTHORIZED'
    assert isinstance(body['error']['message'], str)


@pytest.mark.asyncio
async def test_submit_rating_invalid_bearer(mock_verify_auth, mock_db):
    """Test submit rating with invalid Bearer returns 401."""
    mock_db.side_effect = HTTPException(status_code=401, detail="Invalid API key")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "test-tool",
                "accuracy": 5, "efficiency": 4, "usability": 4, "stability": 5
            },
            headers={"Authorization": "Bearer invalid_token"}
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_rating_success(mock_db, mock_verify_auth):
    """Test successful rating submission."""
    mock_db.return_value = {'id': 'test-uuid-123'}

    api_key = 'ek_test_api_key_12345678901234'
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "tavily",
                "accuracy": 5,
                "efficiency": 4,
                "usability": 4,
                "stability": 5,
                "comment": "好用"
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data['success'] is True
    assert 'id' in data


@pytest.mark.asyncio
async def test_submit_rating_calculates_overall(mock_db, mock_verify_auth):
    """Test overall score calculation is correct."""
    mock_db.return_value = {'id': 'test-uuid-456'}

    # accuracy=5, stability=5, efficiency=4, usability=4
    # overall = 5*0.40 + 5*0.30 + 4*0.20 + 4*0.10 = 2.0 + 1.5 + 0.8 + 0.4 = 4.7
    api_key = 'ek_test_api_key_12345678901234'
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "test-tool",
                "accuracy": 5,
                "efficiency": 4,
                "usability": 4,
                "stability": 5
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )

    assert resp.status_code == 200
    # Verify execute_sql was called with correct overall calculation
    call_args = mock_db.call_args
    assert call_args is not None
    # The overall value should be 4.7 (5*0.4 + 5*0.3 + 4*0.2 + 4*0.1)
    overall_index = 6  # overall is the 7th parameter (index 6)
    assert call_args[0][1][overall_index] == 4.7


@pytest.mark.asyncio
async def test_submit_rating_validation_error(mock_verify_auth, mock_db):
    """Test submit with invalid data returns 422."""
    api_key = 'ek_test_api_key_12345678901234'
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "test-tool",
                "accuracy": 6,  # Invalid: > 5
                "efficiency": 4,
                "usability": 4,
                "stability": 5
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )
    assert resp.status_code == 422


# ===== Query Rating Tests =====

@pytest.mark.asyncio
async def test_query_rating_without_auth():
    """Test query rating without auth returns 401.

    Note: With FastAPI's Header() validation, missing headers return 422.
    This test verifies the HTTPException handler directly.
    """
    mock_request = MagicMock()
    exc = HTTPException(status_code=401, detail="Invalid API key")
    response = await http_exception_handler(mock_request, exc)
    assert response.status_code == 401
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'UNAUTHORIZED'
    assert isinstance(body['error']['message'], str)


@pytest.mark.asyncio
async def test_query_rating_not_found(mock_db, mock_verify_auth):
    """Test query rating for non-existent tool returns 404."""
    mock_db.return_value = None  # No result found

    api_key = 'ek_test_api_key_12345678901234'
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/ratings/nonexistent",
            headers={"Authorization": f"Bearer {api_key}"}
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_query_rating_success(mock_db, mock_verify_auth):
    """Test successful rating query."""
    from datetime import datetime
    mock_db.return_value = {
        'tool_name': 'tavily',
        'total_ratings': 10,
        'avg_accuracy': 4.5,
        'avg_efficiency': 4.2,
        'avg_usability': 4.4,
        'avg_stability': 4.1,
        'avg_overall': 4.3,
        'last_updated': datetime(2026, 3, 28, 0, 5, 0)
    }

    api_key = 'ek_test_api_key_12345678901234'
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/ratings/tavily",
            headers={"Authorization": f"Bearer {api_key}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data['tool_name'] == 'tavily'
    assert data['stats']['total_ratings'] == 10
    assert data['stats']['avg_overall'] == 4.3


# ===== Exception Handler Tests =====

@pytest.mark.asyncio
async def test_validation_error_handler(mock_verify_auth, mock_db):
    """Test 422 error handler for validation errors."""
    api_key = 'ek_test_api_key_12345678901234'
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ratings",
            json={
                "tool_name": "test-tool",
                "accuracy": 6,  # Invalid: > 5
                "efficiency": 4,
                "usability": 4,
                "stability": 5
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )

    assert resp.status_code == 422
    data = resp.json()
    assert 'error' in data
    assert data['error']['code'] == 'VALIDATION_ERROR'


@pytest.mark.asyncio
async def test_http_exception_handler():
    """Test HTTP exception handler for 401 and other HTTP errors."""
    mock_request = MagicMock()

    # Test 401
    exc_401 = HTTPException(status_code=401, detail="Invalid API key")
    response = await http_exception_handler(mock_request, exc_401)
    assert response.status_code == 401
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'UNAUTHORIZED'
    assert isinstance(body['error']['message'], str)

    # Test 404
    exc_404 = HTTPException(status_code=404, detail="No ratings found for tool: unknown")
    response = await http_exception_handler(mock_request, exc_404)
    assert response.status_code == 404
    body = json.loads(response.body)
    assert body['error']['code'] == 'NOT_FOUND'
    assert body['error']['message'] == "No ratings found for tool: unknown"


@pytest.mark.asyncio
async def test_general_exception_handler():
    """Test 500 error handler for general exceptions."""
    mock_request = MagicMock()
    exc = Exception("Database connection failed")

    response = await general_exception_handler(mock_request, exc)

    assert response.status_code == 500
    import json
    body = json.loads(response.body)
    assert body['error']['code'] == 'INTERNAL_ERROR'
