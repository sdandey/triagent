"""Azure Foundry authentication setup for Claude Agent SDK.

This module configures environment variables required by the Claude Agent SDK
to authenticate with Azure AI Foundry.
"""

from __future__ import annotations

import os
import re

from triagent.config import ConfigManager


def _extract_foundry_resource(url: str) -> str:
    """Extract Azure Foundry resource name from URL.

    Claude CLI expects ANTHROPIC_FOUNDRY_RESOURCE (the Azure resource name)
    rather than the full base URL.

    Args:
        url: The full API URL (e.g., https://resource.services.ai.azure.com/...)

    Returns:
        Resource name extracted from URL
    """
    # Extract resource name from URL pattern: https://{resource}.services.ai.azure.com
    match = re.search(r"https://([^.]+)\.services\.ai\.azure\.com", url)
    if match:
        return match.group(1)

    # Fallback: return the URL stripped of common suffixes
    suffixes_to_strip = [
        "/anthropic/v1/messages",
        "/anthropic/v1",
        "/v1/messages",
    ]
    for suffix in suffixes_to_strip:
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url


def setup_sdk_environment(config_manager: ConfigManager) -> None:
    """Configure environment variables for Claude Agent SDK.

    Sets up the required environment variables based on the configured
    API provider (Azure Foundry or direct Anthropic).

    Args:
        config_manager: Configuration manager instance
    """
    credentials = config_manager.load_credentials()

    if credentials.api_provider == "azure_foundry":
        # Azure AI Foundry configuration
        # Claude CLI expects ANTHROPIC_FOUNDRY_RESOURCE (not BASE_URL)
        resource = _extract_foundry_resource(credentials.anthropic_foundry_base_url)
        os.environ["CLAUDE_CODE_USE_FOUNDRY"] = "1"
        os.environ["ANTHROPIC_FOUNDRY_API_KEY"] = credentials.anthropic_foundry_api_key
        os.environ["ANTHROPIC_FOUNDRY_RESOURCE"] = resource
        os.environ["ANTHROPIC_DEFAULT_OPUS_MODEL"] = credentials.anthropic_foundry_model

        # Clear any conflicting env vars
        for key in ["ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_FOUNDRY_BASE_URL"]:
            if key in os.environ:
                del os.environ[key]

    # For direct Anthropic API, no special setup needed
    # SDK will use ANTHROPIC_API_KEY from environment


def get_sdk_model() -> str:
    """Get the model name for SDK configuration.

    Returns:
        The configured model name
    """
    return os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL", "claude-sonnet-4-20250514")


def get_foundry_env(config_manager: ConfigManager) -> dict[str, str]:
    """Get Azure Foundry environment variables for SDK subprocess.

    The Claude Agent SDK spawns Claude CLI as a subprocess. This function
    returns the environment variables that need to be passed explicitly
    via ClaudeAgentOptions.env for reliable subprocess inheritance.

    Args:
        config_manager: Configuration manager instance

    Returns:
        Dictionary of environment variables to pass to ClaudeAgentOptions.env
    """
    credentials = config_manager.load_credentials()

    if credentials.api_provider == "azure_foundry":
        # Claude CLI expects ANTHROPIC_FOUNDRY_RESOURCE (just the resource name)
        resource = _extract_foundry_resource(credentials.anthropic_foundry_base_url)
        return {
            "CLAUDE_CODE_USE_FOUNDRY": "1",
            "ANTHROPIC_FOUNDRY_API_KEY": credentials.anthropic_foundry_api_key,
            "ANTHROPIC_FOUNDRY_RESOURCE": resource,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": credentials.anthropic_foundry_model,
        }
    # For direct Anthropic API, no special env vars needed
    return {}
