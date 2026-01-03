"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from triagent.web.models import (
    SessionCreateRequest,
    SessionResponse,
    ChatRequest,
    AzureAuthResponse,
    AzureAuthStatusResponse,
    ErrorResponse,
)


class TestSessionCreateRequest:
    """Tests for SessionCreateRequest model."""

    def test_valid_anthropic_request(self):
        """Test valid request with Anthropic provider."""
        req = SessionCreateRequest(
            email="test@example.com",
            api_key="test-key",
            team="omnia-data",
            api_provider="anthropic",
            api_token="sk-ant-xxx",
        )
        assert req.email == "test@example.com"
        assert req.api_provider == "anthropic"
        assert req.api_base_url is None

    def test_valid_azure_foundry_request(self):
        """Test valid request with Azure Foundry provider."""
        req = SessionCreateRequest(
            email="test@example.com",
            api_key="test-key",
            team="omnia-data",
            api_provider="azure_foundry",
            api_base_url="https://foundry.azure.com/endpoint",
            api_token="test-token",
        )
        assert req.api_provider == "azure_foundry"
        assert req.api_base_url == "https://foundry.azure.com/endpoint"

    def test_azure_foundry_requires_base_url(self):
        """Test that Azure Foundry provider requires base URL."""
        with pytest.raises(ValidationError) as exc_info:
            SessionCreateRequest(
                email="test@example.com",
                api_key="test-key",
                team="omnia-data",
                api_provider="azure_foundry",
                api_token="test-token",
                # Missing api_base_url
            )
        assert "api_base_url required" in str(exc_info.value)

    def test_invalid_provider(self):
        """Test that invalid provider fails validation."""
        with pytest.raises(ValidationError):
            SessionCreateRequest(
                email="test@example.com",
                api_key="test-key",
                team="omnia-data",
                api_provider="databricks",  # Invalid - removed in PR #19
                api_token="test-token",
            )

    def test_default_values(self):
        """Test default values are applied correctly."""
        req = SessionCreateRequest(
            email="test@example.com",
            api_key="test-key",
            api_token="test-token",
            api_base_url="https://example.com",  # Required for default azure_foundry
        )
        assert req.team == "omnia-data"
        assert req.api_provider == "azure_foundry"


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_valid_request(self):
        """Test valid chat request."""
        req = ChatRequest(message="Hello, Claude!")
        assert req.message == "Hello, Claude!"

    def test_empty_message(self):
        """Test empty message is allowed."""
        req = ChatRequest(message="")
        assert req.message == ""


class TestAzureAuthResponse:
    """Tests for AzureAuthResponse model."""

    def test_valid_response(self):
        """Test valid Azure auth response."""
        resp = AzureAuthResponse(
            device_code="ABC123",
            verification_url="https://microsoft.com/devicelogin",
            message="Enter the code to authenticate",
        )
        assert resp.device_code == "ABC123"
        assert resp.verification_url == "https://microsoft.com/devicelogin"


class TestAzureAuthStatusResponse:
    """Tests for AzureAuthStatusResponse model."""

    def test_authenticated_response(self):
        """Test authenticated status response."""
        resp = AzureAuthStatusResponse(
            authenticated=True,
            user="user@example.com",
            subscription="My Subscription",
            tenant="tenant-id",
        )
        assert resp.authenticated is True
        assert resp.user == "user@example.com"

    def test_unauthenticated_response(self):
        """Test unauthenticated status response."""
        resp = AzureAuthStatusResponse(
            authenticated=False,
            message="Not authenticated",
        )
        assert resp.authenticated is False
        assert resp.message == "Not authenticated"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response(self):
        """Test error response model."""
        resp = ErrorResponse(
            code="SESSION_NOT_FOUND",
            message="Session not found",
            details={"session_id": "test-123"},
        )
        assert resp.code == "SESSION_NOT_FOUND"
        assert resp.details == {"session_id": "test-123"}

    def test_error_response_without_details(self):
        """Test error response without details."""
        resp = ErrorResponse(
            code="UNAUTHORIZED",
            message="Invalid API key",
        )
        assert resp.details is None
