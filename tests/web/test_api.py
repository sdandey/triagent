"""Tests for API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from triagent.web.app import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_healthy(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestSessionEndpoint:
    """Tests for session management endpoints."""

    def test_create_session_missing_api_key(self, client):
        """Test session creation without API key header."""
        response = client.post(
            "/api/session",
            json={
                "email": "test@example.com",
                "api_key": "test-key",
                "team": "omnia-data",
                "api_provider": "anthropic",
                "api_token": "test-token",
            },
        )
        # Missing X-API-Key header
        assert response.status_code == 422

    @patch("triagent.web.config.WebConfig")
    def test_create_session_invalid_api_key(self, mock_config_cls, client):
        """Test session creation with invalid API key."""
        mock_config = MagicMock()
        mock_config.triagent_api_key = "correct-key"
        mock_config_cls.return_value = mock_config

        response = client.post(
            "/api/session",
            json={
                "email": "test@example.com",
                "api_key": "wrong-key",
                "team": "omnia-data",
                "api_provider": "anthropic",
                "api_token": "test-token",
            },
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    @patch("triagent.web.routers.session.SessionStore")
    @patch("triagent.web.routers.session.SessionProxy")
    @patch("triagent.web.config.WebConfig")
    def test_create_session_success(
        self, mock_config_cls, mock_proxy_cls, mock_store_cls, client
    ):
        """Test successful session creation."""
        valid_api_key = "test-api-key"

        # Setup config mock
        mock_config = MagicMock()
        mock_config.triagent_api_key = valid_api_key
        mock_config_cls.return_value = mock_config

        # Setup store mock
        mock_store = AsyncMock()
        mock_store.get_session.return_value = None
        mock_store.create_session.return_value = {
            "session_id": "triagent-abc123def456",
            "email": "test@example.com",
            "team": "omnia-data",
            "api_provider": "anthropic",
            "created_at": "2025-01-01T00:00:00+00:00",
            "expires_at": "2025-01-01T02:00:00+00:00",
        }
        mock_store_cls.return_value = mock_store

        # Setup proxy mock
        mock_proxy = AsyncMock()
        mock_proxy.execute_code.return_value = {
            "properties": {"stdout": "initialized"}
        }
        mock_proxy_cls.return_value = mock_proxy

        response = client.post(
            "/api/session",
            json={
                "email": "test@example.com",
                "api_key": valid_api_key,
                "team": "omnia-data",
                "api_provider": "anthropic",
                "api_token": "sk-ant-xxx",
            },
            headers={"X-API-Key": valid_api_key},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "triagent-abc123def456"
        assert data["team"] == "omnia-data"
        assert data["api_provider"] == "anthropic"

    @patch("triagent.web.routers.session.SessionStore")
    @patch("triagent.web.config.WebConfig")
    def test_create_session_already_exists(
        self, mock_config_cls, mock_store_cls, client
    ):
        """Test session creation when session already exists."""
        valid_api_key = "test-api-key"

        mock_config = MagicMock()
        mock_config.triagent_api_key = valid_api_key
        mock_config_cls.return_value = mock_config

        mock_store = AsyncMock()
        mock_store.get_session.return_value = {
            "session_id": "existing-session",
            "email": "test@example.com",
        }
        mock_store_cls.return_value = mock_store

        response = client.post(
            "/api/session",
            json={
                "email": "test@example.com",
                "api_key": valid_api_key,
                "team": "omnia-data",
                "api_provider": "anthropic",
                "api_token": "sk-ant-xxx",
            },
            headers={"X-API-Key": valid_api_key},
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_get_session_missing_header(self, client):
        """Test get session without X-Session-ID header."""
        response = client.get("/api/session")
        # Missing X-Session-ID header
        assert response.status_code == 422

    @patch("triagent.web.routers.session.SessionStore")
    def test_get_session_not_found(self, mock_store_cls, client):
        """Test get session when session doesn't exist."""
        mock_store = AsyncMock()
        mock_store.get_session_by_id.return_value = None
        mock_store_cls.return_value = mock_store

        response = client.get(
            "/api/session",
            headers={"X-Session-ID": "nonexistent-session-id"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("triagent.web.routers.session.SessionStore")
    def test_get_session_success(self, mock_store_cls, client):
        """Test successful session retrieval."""
        mock_store = AsyncMock()
        mock_store.get_session_by_id.return_value = {
            "session_id": "triagent-abc123def456",
            "email": "test@example.com",
            "team": "omnia-data",
            "api_provider": "anthropic",
            "created_at": "2025-01-01T00:00:00+00:00",
            "expires_at": "2025-01-01T02:00:00+00:00",
        }
        mock_store_cls.return_value = mock_store

        response = client.get(
            "/api/session",
            headers={"X-Session-ID": "triagent-abc123def456"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "triagent-abc123def456"
        assert data["email"] == "test@example.com"
        assert data["team"] == "omnia-data"


class TestChatEndpoint:
    """Tests for chat streaming endpoint."""

    def test_chat_missing_session_id(self, client):
        """Test chat without session ID header."""
        response = client.post(
            "/api/chat/stream",
            json={"message": "Hello"},
        )
        # Missing X-Session-ID header
        assert response.status_code == 422


class TestAuthEndpoint:
    """Tests for Azure authentication endpoints."""

    def test_azure_auth_missing_session_id(self, client):
        """Test Azure auth without session ID header."""
        response = client.post("/api/auth/azure")
        # Missing X-Session-ID header
        assert response.status_code == 422

    def test_azure_auth_status_missing_session_id(self, client):
        """Test Azure auth status without session ID header."""
        response = client.get("/api/auth/azure/status")
        # Missing X-Session-ID header
        assert response.status_code == 422
