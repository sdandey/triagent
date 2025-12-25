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
AZURE_EXTENSION_VERSIONS: dict[str, str] = {
    "azure-devops": "1.0.1",
    "application-insights": "1.2.1",
    "log-analytics": "0.2.3",
}

# Minimum Node.js version required
MIN_NODEJS_VERSION = "18.0.0"
