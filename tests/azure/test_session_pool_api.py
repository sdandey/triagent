"""Direct tests against Azure Container Apps Session Pool Management API.

Requires Azure CLI authentication: az login
"""

import pytest
import subprocess
import json
import os
import httpx


def get_azure_token() -> str:
    """Get Azure access token for dynamicsessions.io.

    Returns:
        Access token string.

    Raises:
        pytest.skip: If Azure CLI not authenticated.
    """
    result = subprocess.run(
        [
            "az", "account", "get-access-token",
            "--resource", "https://dynamicsessions.io",
            "--query", "accessToken", "-o", "tsv"
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("Azure CLI not authenticated")
    return result.stdout.strip()


@pytest.fixture
def session_pool_endpoint() -> str:
    """Get session pool management endpoint."""
    endpoint = os.environ.get("TRIAGENT_SESSION_POOL_ENDPOINT", "")
    if not endpoint:
        pytest.skip("TRIAGENT_SESSION_POOL_ENDPOINT not set")
    return endpoint


@pytest.fixture
async def session_pool_client(session_pool_endpoint):
    """HTTP client for session pool API.

    Args:
        session_pool_endpoint: Session pool management endpoint.

    Yields:
        AsyncClient configured for session pool testing.
    """
    token = get_azure_token()
    async with httpx.AsyncClient(
        base_url=session_pool_endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=60.0,
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_session_pool_execute_code(session_pool_client):
    """Test executing Python code in session pool."""
    test_session_id = f"test-{os.urandom(8).hex()}"

    response = await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": test_session_id},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "print('Hello from session pool!')",
            }
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Hello from session pool!" in data.get("properties", {}).get("stdout", "")


@pytest.mark.asyncio
async def test_session_pool_python_version(session_pool_client):
    """Test Python version in session pool."""
    test_session_id = f"test-pyver-{os.urandom(8).hex()}"

    response = await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": test_session_id},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "import sys; print(f'Python {sys.version}')",
            }
        },
    )

    assert response.status_code == 200
    data = response.json()
    stdout = data.get("properties", {}).get("stdout", "")
    assert "Python 3" in stdout


@pytest.mark.asyncio
async def test_session_pool_install_package(session_pool_client):
    """Test installing a package in session."""
    test_session_id = f"test-pkg-{os.urandom(8).hex()}"

    # Install a simple package
    response = await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": test_session_id},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": """
import subprocess
result = subprocess.run(['pip', 'install', 'cowsay', '-q'], capture_output=True)
import cowsay
cowsay.cow('Session pool works!')
""",
            }
        },
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_session_isolation(session_pool_client):
    """Test that sessions are isolated."""
    session_1 = f"test-iso1-{os.urandom(8).hex()}"
    session_2 = f"test-iso2-{os.urandom(8).hex()}"

    # Set variable in session 1
    await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": session_1},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "secret_value = 'session1_secret'",
            }
        },
    )

    # Try to access from session 2 (should fail)
    response = await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": session_2},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "print(secret_value)",
            }
        },
    )

    data = response.json()
    # Should get NameError since variable doesn't exist in session 2
    stderr = data.get("properties", {}).get("stderr", "")
    assert "NameError" in stderr or "not defined" in stderr


@pytest.mark.asyncio
async def test_session_persistence(session_pool_client):
    """Test that variables persist within same session."""
    test_session_id = f"test-persist-{os.urandom(8).hex()}"

    # Set variable
    await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": test_session_id},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "my_variable = 42",
            }
        },
    )

    # Read variable in same session
    response = await session_pool_client.post(
        "/code/execute",
        headers={"Identifier": test_session_id},
        json={
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": "print(my_variable)",
            }
        },
    )

    data = response.json()
    stdout = data.get("properties", {}).get("stdout", "")
    assert "42" in stdout
