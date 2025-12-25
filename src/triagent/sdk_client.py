"""Claude Agent SDK client configuration for Triagent CLI.

This module provides the TriagentSDKClient class which builds ClaudeAgentOptions
for use with the official Claude Agent SDK's ClaudeSDKClient.

The CLI uses ClaudeSDKClient directly with async patterns; this module
provides the configuration/options builder.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions

from triagent.auth import get_foundry_env
from triagent.config import ConfigManager
from triagent.hooks import get_triagent_hooks
from triagent.mcp.tools import create_triagent_mcp_server
from triagent.prompts.system import get_system_prompt
from triagent.versions import MCP_AZURE_DEVOPS_VERSION


@dataclass
class TriagentSDKClient:
    """Claude Agent SDK configuration builder for Triagent.

    Builds ClaudeAgentOptions with:
    - Security hooks (PreToolUse, PostToolUse)
    - In-process MCP tools (triagent-specific)
    - External MCP servers (Azure DevOps)
    - Azure Foundry authentication

    Usage:
        client = create_sdk_client(config_manager)
        options = client._build_options()
        async with ClaudeSDKClient(options=options) as sdk_client:
            await sdk_client.query(prompt)
            async for msg in sdk_client.receive_response():
                ...
    """

    config_manager: ConfigManager
    team: str
    working_dir: Path | None = None

    def __post_init__(self) -> None:
        """Initialize the client."""
        if self.working_dir is None:
            self.working_dir = Path.cwd()

    @property
    def system_prompt(self) -> str:
        """Get the system prompt for the current team."""
        return get_system_prompt(self.team)

    def _stderr_handler(self, msg: str) -> None:
        """Handle stderr output from Claude CLI."""
        config = self.config_manager.load_config()
        if config.verbose:
            print(f"[Claude CLI] {msg}", file=sys.stderr)

    def _get_mcp_config(self) -> dict[str, Any]:
        """Get combined MCP configuration (in-process + external).

        Returns:
            Dict mapping server names to their configurations
        """
        config = self.config_manager.load_config()

        # Pin MCP server version
        mcp_package = f"@anthropic-ai/mcp-server-azure-devops@{MCP_AZURE_DEVOPS_VERSION}"

        return {
            # In-process triagent tools
            "triagent": create_triagent_mcp_server(),
            # External Azure DevOps MCP server (pinned version)
            "azure-devops": {
                "command": "npx",
                "args": ["-y", mcp_package],
                "env": {
                    "AZURE_DEVOPS_ORG": config.ado_organization,
                    "AZURE_DEVOPS_PROJECT": config.ado_project,
                },
            },
        }

    def _get_allowed_tools(self) -> list[str]:
        """Get list of allowed tools including MCP tools.

        Returns:
            List of tool names allowed for this session
        """
        return [
            # Built-in Claude Code tools
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Glob",
            "Grep",
            "WebFetch",
            "WebSearch",
            # In-process triagent MCP tools
            "mcp__triagent__get_team_config",
            "mcp__triagent__generate_kusto_query",
            "mcp__triagent__list_telemetry_tables",
            # Azure DevOps MCP tools - allow all
            "mcp__azure-devops__*",
        ]

    def _build_options(self) -> ClaudeAgentOptions:
        """Build SDK options with Azure Foundry credentials and all features.

        Returns:
            ClaudeAgentOptions configured for triagent
        """
        config = self.config_manager.load_config()
        credentials = self.config_manager.load_credentials()

        # Start with Foundry auth environment
        env = get_foundry_env(self.config_manager)

        # Get the model based on provider
        model = None
        if credentials.api_provider == "azure_foundry":
            model = credentials.anthropic_foundry_model
        elif credentials.api_provider == "databricks":
            model = credentials.databricks_model

        # Add SSL handling for corporate environments
        if config.disable_ssl_verify:
            env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

        if config.ssl_cert_file:
            env["NODE_EXTRA_CA_CERTS"] = config.ssl_cert_file

        return ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            permission_mode="bypassPermissions",
            cwd=str(self.working_dir) if self.working_dir else None,
            env=env,
            model=model,
            hooks=get_triagent_hooks(config),
            mcp_servers=self._get_mcp_config(),
            allowed_tools=self._get_allowed_tools(),
            stderr=self._stderr_handler if config.verbose else None,
        )


def create_sdk_client(config_manager: ConfigManager) -> TriagentSDKClient:
    """Create a new SDK client configuration builder.

    Args:
        config_manager: Configuration manager instance

    Returns:
        Configured TriagentSDKClient for building options
    """
    config = config_manager.load_config()

    return TriagentSDKClient(
        config_manager=config_manager,
        team=config.team,
        working_dir=Path.cwd(),
    )
