"""Pytest fixtures for Triagent Web API tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from triagent.web.app import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.ttl.return_value = 7200
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_session_proxy():
    """Mock Azure session pool proxy."""
    mock = AsyncMock()
    mock.execute_code.return_value = {
        "properties": {
            "status": "Success",
            "stdout": "initialized",
            "stderr": "",
        }
    }
    return mock


@pytest.fixture
def valid_api_key():
    """Valid API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_config(valid_api_key):
    """Mock WebConfig for testing."""
    with patch("triagent.web.config.WebConfig") as mock:
        config = MagicMock()
        config.triagent_api_key = valid_api_key
        config.redis_host = "localhost"
        config.redis_port = 6380
        config.redis_password = ""
        config.redis_ssl = False
        config.session_ttl = 7200
        config.session_pool_endpoint = "https://test.sessions.io"
        mock.return_value = config
        yield config
