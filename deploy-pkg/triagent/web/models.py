"""Pydantic models for Triagent Web API requests and responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator


class SessionCreateRequest(BaseModel):
    """Request to create a new triagent session."""

    email: str
    api_key: str  # Triagent API key (shared secret)
    team: str = "omnia-data"
    # Only azure_foundry and anthropic supported (no databricks)
    api_provider: Literal["azure_foundry", "anthropic"] = "azure_foundry"
    # Azure Foundry specific
    api_base_url: str | None = None  # Required for azure_foundry
    api_token: str  # LLM provider token

    @model_validator(mode="after")
    def validate_base_url(self) -> "SessionCreateRequest":
        """Validate that azure_foundry provider has base URL."""
        if self.api_provider == "azure_foundry" and not self.api_base_url:
            raise ValueError("api_base_url required for azure_foundry provider")
        return self


class SessionResponse(BaseModel):
    """Response for session creation/retrieval."""

    session_id: str
    email: str
    team: str
    api_provider: str
    created_at: datetime
    expires_at: datetime


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str


class AzureAuthResponse(BaseModel):
    """Response for Azure CLI device code authentication."""

    device_code: str
    verification_url: str
    message: str


class AzureAuthStatusResponse(BaseModel):
    """Response for Azure CLI authentication status check."""

    authenticated: bool
    user: str | None = None
    subscription: str | None = None
    tenant: str | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """Error response model."""

    code: str
    message: str
    details: dict | None = None
