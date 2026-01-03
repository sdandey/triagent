"""Tool execution handlers for Chainlit container."""

import json
import subprocess


async def show_setup_status() -> str:
    """Display session status.

    Returns:
        Formatted status string with team, provider, and Azure auth status.
    """
    from triagent.config import ConfigManager

    manager = ConfigManager()
    config = manager.load_config()
    creds = manager.load_credentials()

    status = f"""
**Session Status**
- Team: {config.team}
- API Provider: {creds.api_provider}
- Azure Authenticated: Checking...
"""

    # Check Azure CLI status
    result = subprocess.run(
        ["az", "account", "show", "--output", "json"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            user = data.get("user", {}).get("name", "Unknown")
            status = status.replace("Checking...", f"Yes ({user})")
        except json.JSONDecodeError:
            status = status.replace("Checking...", "Yes")
    else:
        status = status.replace("Checking...", "No")

    return status


async def start_azure_auth() -> subprocess.CompletedProcess:
    """Start Azure device code authentication.

    Returns:
        CompletedProcess with auth result.
    """
    result = subprocess.run(
        ["az", "login", "--use-device-code", "--output", "json"],
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout for auth
    )
    return result


async def check_azure_auth() -> bool:
    """Check if Azure CLI is authenticated.

    Returns:
        True if authenticated, False otherwise.
    """
    result = subprocess.run(
        ["az", "account", "show", "--output", "json"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
