"""Pinned versions for external dependencies.

This module centralizes all version constants for external tools
installed during `/init` command. Update versions here to change
what gets installed across all environments.
"""

from __future__ import annotations

# Triagent version (should match pyproject.toml)
__version__ = "0.1.0"

# Claude Code CLI version
# https://www.npmjs.com/package/@anthropic-ai/claude-code
CLAUDE_CODE_VERSION = "1.0.30"

# MCP Azure DevOps Server version
# https://www.npmjs.com/package/@anthropic-ai/mcp-server-azure-devops
MCP_AZURE_DEVOPS_VERSION = "0.1.1"

# Azure CLI Extensions
# https://learn.microsoft.com/en-us/cli/azure/azure-cli-extensions-list
# Note: application-insights and log-analytics are preview extensions
AZURE_EXTENSION_VERSIONS: dict[str, str] = {
    "azure-devops": "1.0.2",
    "application-insights": "2.0.0b1",
    "log-analytics": "1.0.0b1",
}

# Minimum Node.js version required
MIN_NODEJS_VERSION = "18.0.0"

# Windows Installer Versions
# Used by install.ps1 for consistent cross-environment installations
PYTHON_VERSION = "3.12.8"
AZURE_CLI_VERSION = "2.67.0"
GIT_FOR_WINDOWS_VERSION = "2.47.1"
