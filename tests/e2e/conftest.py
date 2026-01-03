"""Pytest fixtures for E2E tests."""

import os
import pytest
from playwright.sync_api import Page


@pytest.fixture
def base_url() -> str:
    """Get base URL from environment or default."""
    return os.environ.get("TRIAGENT_TEST_URL", "http://localhost:8080")


@pytest.fixture
def api_url() -> str:
    """Get API URL from environment or default."""
    return os.environ.get("TRIAGENT_API_URL", "http://localhost:8000")


@pytest.fixture
def api_key() -> str:
    """Get API key from environment."""
    return os.environ.get("TRIAGENT_API_KEY", "test-key")


@pytest.fixture
def api_token() -> str:
    """Get API token from environment."""
    return os.environ.get("TRIAGENT_API_TOKEN", "test-token")


@pytest.fixture
def authenticated_page(page: Page, base_url: str) -> Page:
    """Fixture for authenticated session.

    Args:
        page: Playwright page.
        base_url: Base URL for the application.

    Returns:
        Page ready for testing.
    """
    page.goto(base_url)

    # Wait for page to load
    page.wait_for_load_state("networkidle")

    # Wait for chat to be ready
    # Chainlit typically shows a textarea for input
    page.wait_for_selector("textarea", timeout=30000)
    return page
