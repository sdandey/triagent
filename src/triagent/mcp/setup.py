"""MCP Server setup for Triagent CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from triagent.config import ConfigManager

MCP_SERVERS_CONFIG = {
    "azure-devops": {
        "command": "npx",
        "args": ["-y", "@anthropic-ai/mcp-server-azure-devops"],
        "env": {
            "AZURE_DEVOPS_ORG": "",
            "AZURE_DEVOPS_PROJECT": "",
        },
    }
}


def check_npm_installed() -> bool:
    """Check if npm/npx is installed."""
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_azure_cli_installed() -> tuple[bool, str]:
    """Check if Azure CLI is installed.

    Returns:
        Tuple of (is_installed, version_string)
    """
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split("\n")[0]
            return True, first_line
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_azure_devops_extension() -> bool:
    """Check if Azure DevOps CLI extension is installed."""
    try:
        result = subprocess.run(
            ["az", "extension", "show", "--name", "azure-devops"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_azure_devops_extension() -> bool:
    """Install Azure DevOps CLI extension.

    Returns:
        True if installation succeeded
    """
    try:
        result = subprocess.run(
            ["az", "extension", "add", "--name", "azure-devops", "-y"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_azure_login() -> bool:
    """Run Azure CLI login via browser.

    Returns:
        True if login succeeded
    """
    try:
        result = subprocess.run(
            ["az", "login"],
            capture_output=False,  # Let user see the browser prompt
            timeout=300,  # 5 minute timeout for login
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_azure_account() -> dict[str, Any] | None:
    """Get current Azure account info.

    Returns:
        Account info dict or None if not logged in
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def setup_mcp_servers(
    config_manager: ConfigManager,
    ado_org: str,
    ado_project: str,
) -> bool:
    """Set up MCP servers configuration.

    Args:
        config_manager: Config manager instance
        ado_org: Azure DevOps organization
        ado_project: Azure DevOps project

    Returns:
        True if setup succeeded
    """
    mcp_config = MCP_SERVERS_CONFIG.copy()

    # Update Azure DevOps server config
    mcp_config["azure-devops"]["env"]["AZURE_DEVOPS_ORG"] = ado_org
    mcp_config["azure-devops"]["env"]["AZURE_DEVOPS_PROJECT"] = ado_project

    config_manager.ensure_dirs()

    with open(config_manager.mcp_servers_file, "w") as f:
        json.dump({"mcpServers": mcp_config}, f, indent=2)

    return True


def check_databricks_cli_installed() -> tuple[bool, str]:
    """Check if Databricks CLI is installed.

    Returns:
        Tuple of (is_installed, version_string)
    """
    try:
        result = subprocess.run(
            ["databricks", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def get_databricks_token_from_cli() -> str | None:
    """Get Databricks token from CLI authentication.

    Returns:
        Token string or None if not available
    """
    try:
        result = subprocess.run(
            ["databricks", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_databricks_token_from_config() -> str | None:
    """Get Databricks token from ~/.databrickscfg file.

    Returns:
        Token string or None if not found
    """
    config_file = Path.home() / ".databrickscfg"
    if not config_file.exists():
        return None

    try:
        import configparser

        config = configparser.ConfigParser()
        config.read(config_file)

        # Check DEFAULT section first, then any other section
        for section in ["DEFAULT"] + config.sections():
            if config.has_option(section, "token"):
                return config.get(section, "token")

        return None
    except Exception:
        return None


def get_databricks_token() -> str | None:
    """Get Databricks token from CLI or config file.

    Returns:
        Token string or None if not available
    """
    # Try CLI first (more reliable for current auth)
    token = get_databricks_token_from_cli()
    if token:
        return token

    # Fall back to config file
    return get_databricks_token_from_config()
