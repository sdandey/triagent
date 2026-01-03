"""Container internal API for Triagent sessions."""

import json
import re
import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

container_app = FastAPI(title="Triagent Container API")


class InitRequest(BaseModel):
    """Session initialization request."""

    api_provider: str
    api_base_url: str | None = None
    api_token: str
    team: str


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str


@container_app.post("/init")
async def initialize_session(request: InitRequest) -> dict:
    """Initialize triagent with provided config.

    Args:
        request: Initialization parameters.

    Returns:
        Status dict with initialization result.
    """
    from triagent.config import ConfigManager, TriagentConfig, TriagentCredentials

    manager = ConfigManager()
    manager.ensure_dirs()

    # Save credentials
    credentials = TriagentCredentials(
        api_provider=request.api_provider,
        anthropic_foundry_api_key=request.api_token,
        anthropic_foundry_base_url=request.api_base_url or "",
    )
    manager.save_credentials(credentials)

    # Save config
    config = TriagentConfig(team=request.team)
    manager.save_config(config)

    return {
        "status": "initialized",
        "team": request.team,
        "api_provider": request.api_provider,
    }


@container_app.post("/auth/azure")
async def start_azure_auth() -> dict:
    """Start device code flow.

    Returns:
        Device code info for authentication.

    Raises:
        HTTPException: If device code flow fails.
    """
    result = subprocess.run(
        ["az", "login", "--use-device-code"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Parse device code from stderr
    match = re.search(r"code ([A-Z0-9-]+)", result.stderr)
    if match:
        return {
            "device_code": match.group(1),
            "verification_url": "https://microsoft.com/devicelogin",
            "message": "Open the URL and enter the code to authenticate",
        }

    raise HTTPException(status_code=500, detail="Failed to get device code")


@container_app.get("/auth/azure/status")
async def check_azure_status() -> dict:
    """Check if Azure authenticated.

    Returns:
        Authentication status with user details if authenticated.
    """
    result = subprocess.run(
        ["az", "account", "show", "--output", "json"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return {
                "authenticated": True,
                "user": data.get("user", {}).get("name", ""),
                "subscription": data.get("name", ""),
                "tenant": data.get("tenantId", ""),
            }
        except json.JSONDecodeError:
            return {"authenticated": True, "user": "Unknown"}

    return {"authenticated": False, "message": "Not authenticated"}


@container_app.get("/config")
async def get_config() -> dict:
    """Get current config.

    Returns:
        Current team and API provider configuration.
    """
    from triagent.config import ConfigManager

    manager = ConfigManager()
    config = manager.load_config()
    creds = manager.load_credentials()

    return {
        "team": config.team,
        "api_provider": creds.api_provider,
    }


@container_app.get("/health")
async def health() -> dict:
    """Container health check.

    Returns:
        Health status.
    """
    return {"status": "healthy"}
