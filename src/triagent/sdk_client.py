"""Claude Agent SDK client configuration for Triagent CLI.

This module provides the TriagentSDKClient class which builds ClaudeAgentOptions
for use with the official Claude Agent SDK's ClaudeSDKClient.

The CLI uses ClaudeSDKClient directly with async patterns; this module
provides the configuration/options builder.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions
from rich.console import Console

from triagent.auth import get_foundry_env
from triagent.config import ConfigManager
from triagent.hooks import get_triagent_hooks
from triagent.mcp.tools import create_triagent_mcp_server
from triagent.permissions import TriagentPermissionHandler
from triagent.skills.loader import load_persona
from triagent.skills.system import get_system_prompt
from triagent.utils.windows import get_git_bash_env, is_windows
from triagent.versions import MCP_AZURE_DEVOPS_VERSION


@dataclass
class TriagentSDKClient:
    """Claude Agent SDK configuration builder for Triagent.

    Builds ClaudeAgentOptions with:
    - Security hooks (PreToolUse, PostToolUse)
    - Permission handler for write confirmations
    - In-process MCP tools (triagent-specific)
    - External MCP servers (Azure DevOps)
    - Azure Foundry authentication
    - Persona-based skills and subagents

    Usage:
        client = create_sdk_client(config_manager, console)
        options = client._build_options()
        async with ClaudeSDKClient(options=options) as sdk_client:
            await sdk_client.query(prompt)
            async for msg in sdk_client.receive_response():
                ...
    """

    config_manager: ConfigManager
    team: str
    persona: str
    console: Console
    working_dir: Path | None = None
    _permission_handler: TriagentPermissionHandler | None = field(
        default=None, repr=False, init=False
    )

    def __post_init__(self) -> None:
        """Initialize the client."""
        if self.working_dir is None:
            self.working_dir = Path.cwd()

        # Initialize permission handler
        config = self.config_manager.load_config()
        self._permission_handler = TriagentPermissionHandler(
            console=self.console,
            auto_approve=config.auto_approve_writes,
        )

    @property
    def system_prompt(self) -> str:
        """Get the system prompt for the current team and persona."""
        return get_system_prompt(self.team, self.persona)

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

        NOTE: We explicitly list MCP tools instead of using wildcards.
        Wildcards like 'mcp__azure-devops__*' bypass the can_use_tool callback,
        preventing our permission handler from prompting for write confirmations.

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
            "Task",  # Required for subagent invocation
            "WebFetch",
            "WebSearch",
            # In-process triagent MCP tools (read-only)
            "mcp__triagent__get_team_config",
            "mcp__triagent__generate_kusto_query",
            "mcp__triagent__list_telemetry_tables",
            # Azure DevOps MCP tools - read operations (auto-approved in permissions.py)
            "mcp__azure-devops__get_me",
            "mcp__azure-devops__list_organizations",
            "mcp__azure-devops__list_projects",
            "mcp__azure-devops__get_project",
            "mcp__azure-devops__get_project_details",
            "mcp__azure-devops__list_repositories",
            "mcp__azure-devops__get_repository",
            "mcp__azure-devops__get_repository_details",
            "mcp__azure-devops__get_file_content",
            "mcp__azure-devops__get_repository_tree",
            "mcp__azure-devops__get_work_item",
            "mcp__azure-devops__list_work_items",
            "mcp__azure-devops__search_code",
            "mcp__azure-devops__search_wiki",
            "mcp__azure-devops__search_work_items",
            "mcp__azure-devops__list_pipelines",
            "mcp__azure-devops__get_pipeline",
            "mcp__azure-devops__list_pipeline_runs",
            "mcp__azure-devops__get_pipeline_run",
            "mcp__azure-devops__download_pipeline_artifact",
            "mcp__azure-devops__pipeline_timeline",
            "mcp__azure-devops__get_pipeline_log",
            "mcp__azure-devops__get_wikis",
            "mcp__azure-devops__get_wiki_page",
            "mcp__azure-devops__list_pull_requests",
            "mcp__azure-devops__get_pull_request_comments",
            "mcp__azure-devops__get_pull_request_changes",
            "mcp__azure-devops__get_pull_request_checks",
            # Azure DevOps MCP tools - write operations (require confirmation via can_use_tool)
            "mcp__azure-devops__create_work_item",
            "mcp__azure-devops__update_work_item",
            "mcp__azure-devops__manage_work_item_link",
            "mcp__azure-devops__create_pull_request",
            "mcp__azure-devops__update_pull_request",
            "mcp__azure-devops__add_pull_request_comment",
            "mcp__azure-devops__create_branch",
            "mcp__azure-devops__create_commit",
            "mcp__azure-devops__trigger_pipeline",
        ]

    def _get_agent_definitions(self) -> dict[str, AgentDefinition]:
        """Load persona and build AgentDefinition objects for SDK.

        Subagents are generated dynamically from skill content - each skill's
        markdown content becomes the subagent's prompt, and the skill's
        description and tools are inherited.

        Returns:
            Dict mapping subagent names to AgentDefinition objects
        """
        persona = load_persona(self.team, self.persona)
        if not persona or not persona.subagents:
            return {}

        # Valid model values for AgentDefinition
        ModelType = Literal["sonnet", "opus", "haiku", "inherit"]
        valid_models = {"sonnet", "opus", "haiku", "inherit"}

        agents = {}
        for name, subagent in persona.subagents.items():
            # Validate and cast model to literal type
            model: ModelType | None = None
            if subagent.model in valid_models and subagent.model != "inherit":
                model = cast(ModelType, subagent.model)

            agents[name] = AgentDefinition(
                description=subagent.description,
                prompt=subagent.prompt,
                tools=subagent.tools if subagent.tools else None,  # None = inherit all
                model=model,
            )
        return agents

    def _build_options(self) -> ClaudeAgentOptions:
        """Build SDK options with Azure Foundry credentials and all features.

        Returns:
            ClaudeAgentOptions configured for triagent
        """
        config = self.config_manager.load_config()
        credentials = self.config_manager.load_credentials()

        # Start with Foundry auth environment
        env = get_foundry_env(self.config_manager)

        # On Windows, set CLAUDE_CODE_GIT_BASH_PATH for Claude Code CLI
        if is_windows():
            env.update(get_git_bash_env())

        # Get the model based on provider
        model = None
        if credentials.api_provider == "azure_foundry":
            model = credentials.anthropic_foundry_model

        # Add SSL handling for corporate environments
        if config.disable_ssl_verify:
            env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"

        if config.ssl_cert_file:
            env["NODE_EXTRA_CA_CERTS"] = config.ssl_cert_file

        return ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            # permission_mode is NOT set - let SDK handle with can_use_tool callback
            # When can_use_tool is set, SDK auto-configures permission_prompt_tool_name="stdio"
            can_use_tool=self._permission_handler.can_use_tool if self._permission_handler else None,
            cwd=str(self.working_dir) if self.working_dir else None,
            env=env,
            model=model,
            hooks=get_triagent_hooks(config),
            mcp_servers=self._get_mcp_config(),
            allowed_tools=self._get_allowed_tools(),
            agents=self._get_agent_definitions(),  # Subagents for Task tool
            stderr=self._stderr_handler if config.verbose else None,
        )


def create_sdk_client(
    config_manager: ConfigManager,
    console: Console,
) -> TriagentSDKClient:
    """Create a new SDK client configuration builder.

    Args:
        config_manager: Configuration manager instance
        console: Rich console for user interaction

    Returns:
        Configured TriagentSDKClient for building options
    """
    config = config_manager.load_config()

    return TriagentSDKClient(
        config_manager=config_manager,
        team=config.team,
        persona=config.persona,
        console=console,
        working_dir=Path.cwd(),
    )
