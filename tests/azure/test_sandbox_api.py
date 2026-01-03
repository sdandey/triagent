"""Azure sandbox API integration tests."""

import pytest
import uuid


@pytest.mark.asyncio
async def test_sandbox_health(sandbox_client):
    """Test sandbox health endpoint."""
    response = await sandbox_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_sandbox_health_format(sandbox_client):
    """Test sandbox health response format."""
    response = await sandbox_client.get("/health")
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_sandbox_session_create(sandbox_client, sandbox_api_key):
    """Test session creation in sandbox."""
    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

    response = await sandbox_client.post(
        "/api/session",
        json={
            "email": unique_email,
            "api_key": sandbox_api_key,
            "team": "omnia-data",
            "api_provider": "anthropic",
            "api_token": "sk-ant-test",
        },
    )

    # Session should be created successfully
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "session_id" in data
    assert "expires_at" in data  # Proves Redis TTL is working


@pytest.mark.asyncio
async def test_sandbox_session_duplicate(sandbox_client, sandbox_api_key):
    """Test duplicate session creation returns 409."""
    unique_email = f"dup-{uuid.uuid4().hex[:8]}@example.com"

    # Create first session
    response1 = await sandbox_client.post(
        "/api/session",
        json={
            "email": unique_email,
            "api_key": sandbox_api_key,
            "team": "omnia-data",
            "api_provider": "anthropic",
            "api_token": "sk-ant-test",
        },
    )
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await sandbox_client.post(
        "/api/session",
        json={
            "email": unique_email,
            "api_key": sandbox_api_key,
            "team": "omnia-data",
            "api_provider": "anthropic",
            "api_token": "sk-ant-test",
        },
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_sandbox_invalid_api_key(sandbox_client):
    """Test invalid API key returns 401."""
    response = await sandbox_client.post(
        "/api/session",
        json={
            "email": "test@example.com",
            "api_key": "wrong-key",
            "team": "omnia-data",
            "api_provider": "anthropic",
            "api_token": "sk-ant-test",
        },
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sandbox_unknown_endpoint(sandbox_client):
    """Test unknown endpoint returns 404."""
    response = await sandbox_client.get("/api/unknown")
    assert response.status_code == 404
