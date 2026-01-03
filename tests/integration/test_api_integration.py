"""Integration tests for API endpoints with real Redis."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """Test health endpoint returns healthy status."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint_format(async_client):
    """Test health endpoint response format."""
    response = await async_client.get("/health")
    data = response.json()

    # Verify required fields
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data

    # Verify types
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["version"], str)


@pytest.mark.asyncio
async def test_session_endpoint_missing_header(async_client, test_api_key):
    """Test session endpoint requires X-API-Key header."""
    response = await async_client.post(
        "/api/session",
        json={
            "email": "test@example.com",
            "api_key": test_api_key,
            "team": "omnia-data",
            "api_provider": "anthropic",
            "api_token": "test-token",
        },
    )
    # Missing X-API-Key header should return 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_endpoint_missing_session(async_client):
    """Test chat endpoint requires X-Session-ID header."""
    response = await async_client.post(
        "/api/chat/stream",
        json={"message": "Hello"},
    )
    # Missing X-Session-ID header should return 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_azure_missing_session(async_client):
    """Test Azure auth endpoint requires X-Session-ID header."""
    response = await async_client.post("/api/auth/azure")
    # Missing X-Session-ID header should return 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_azure_status_missing_session(async_client):
    """Test Azure auth status endpoint requires X-Session-ID header."""
    response = await async_client.get("/api/auth/azure/status")
    # Missing X-Session-ID header should return 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unknown_endpoint_returns_404(async_client):
    """Test unknown endpoint returns 404."""
    response = await async_client.get("/api/unknown-endpoint")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers(async_client):
    """Test CORS headers are present."""
    response = await async_client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI with CORS middleware should allow the request
    assert response.status_code in [200, 204]
