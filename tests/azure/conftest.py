"""Pytest fixtures for Azure sandbox integration tests."""

import os
import pytest
import httpx

# Azure sandbox environment
SANDBOX_URL = os.environ.get(
    "TRIAGENT_SANDBOX_URL",
    "https://triagent-sandbox-app.azurewebsites.net"
)
SANDBOX_API_KEY = os.environ.get("TRIAGENT_SANDBOX_API_KEY", "")


@pytest.fixture
def sandbox_url() -> str:
    """Get sandbox App Service URL."""
    return SANDBOX_URL


@pytest.fixture
def sandbox_api_key() -> str:
    """Get sandbox API key."""
    if not SANDBOX_API_KEY:
        pytest.skip("TRIAGENT_SANDBOX_API_KEY not set")
    return SANDBOX_API_KEY


@pytest.fixture
async def sandbox_client(sandbox_url, sandbox_api_key):
    """HTTP client for sandbox testing.

    Args:
        sandbox_url: Sandbox App Service URL.
        sandbox_api_key: API key for authentication.

    Yields:
        AsyncClient configured for sandbox testing.
    """
    async with httpx.AsyncClient(
        base_url=sandbox_url,
        headers={"X-API-Key": sandbox_api_key},
        timeout=30.0,
    ) as client:
        yield client
