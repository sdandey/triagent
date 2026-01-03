"""Pytest fixtures for integration tests using testcontainers."""

import os
import pytest
from testcontainers.redis import RedisContainer
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container for entire test session.

    Yields:
        RedisContainer with environment configured.
    """
    with RedisContainer("redis:7-alpine") as redis:
        # Set environment variables for app
        os.environ["TRIAGENT_REDIS_HOST"] = redis.get_container_host_ip()
        os.environ["TRIAGENT_REDIS_PORT"] = str(redis.get_exposed_port(6379))
        os.environ["TRIAGENT_REDIS_PASSWORD"] = ""
        os.environ["TRIAGENT_REDIS_SSL"] = "false"
        yield redis


@pytest.fixture
async def async_client(redis_container):
    """Async HTTP client for FastAPI app.

    Args:
        redis_container: Redis container fixture.

    Yields:
        AsyncClient configured for testing.
    """
    from triagent.web.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_api_key():
    """Set test API key.

    Returns:
        Test API key string.
    """
    os.environ["TRIAGENT_TRIAGENT_API_KEY"] = "test-integration-key"
    return "test-integration-key"
