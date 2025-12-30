"""Permission handler for Triagent tool execution.

This module provides user confirmation for write operations and handles
the AskUserQuestion tool for clarifying questions.

The permission handler integrates with the Claude Agent SDK's canUseTool
callback to intercept tool calls and request user approval for write
operations.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from claude_agent_sdk.types import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from triagent.session_logger import log_permission_decision

# Tools that are always auto-approved (read-only)
READ_ONLY_TOOLS = [
    # Built-in Claude Code tools (read-only)
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "LS",
    "Task",
    "TodoRead",
    # Triagent MCP tools (read-only)
    "mcp__triagent__get_team_config",
    "mcp__triagent__generate_kusto_query",
    "mcp__triagent__list_telemetry_tables",
    # Azure DevOps MCP tools (read-only)
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
]

# MCP ADO write operations (operation names extracted from tool name)
MCP_ADO_WRITE_OPS = [
    "create_work_item",
    "update_work_item",
    "manage_work_item_link",
    "create_pull_request",
    "update_pull_request",
    "add_pull_request_comment",
    "create_branch",
    "create_commit",
    "trigger_pipeline",
]

# Complex MCP operations that show rich panel
COMPLEX_MCP_OPS = [
    "create_work_item",
    "update_work_item",
    "create_pull_request",
    "update_pull_request",
    "create_commit",
    "trigger_pipeline",
]

# Azure CLI write patterns with descriptions
AZURE_CLI_WRITE_PATTERNS = [
    # Pull Requests
    ("az repos pr create", "Create pull request"),
    ("az repos pr update", "Update pull request"),
    ("az repos pr set-vote", "Set PR vote"),
    ("az repos pr complete", "Complete/merge PR"),
    ("az repos pr abandon", "Abandon pull request"),
    # Work Items
    ("az boards work-item create", "Create work item"),
    ("az boards work-item update", "Update work item"),
    ("az boards work-item delete", "Delete work item"),
    ("az boards work-item relation add", "Add work item link"),
    ("az boards work-item relation remove", "Remove work item link"),
    # Pipelines
    ("az pipelines run", "Trigger pipeline"),
    ("az pipelines create", "Create pipeline"),
    ("az pipelines update", "Update pipeline"),
    ("az pipelines delete", "Delete pipeline"),
    ("az pipelines build queue", "Queue build"),
    ("az pipelines release create", "Create release"),
    # Repositories
    ("az repos create", "Create repository"),
    ("az repos delete", "Delete repository"),
    ("az repos update", "Update repository"),
    ("az repos policy create", "Create branch policy"),
    ("az repos policy update", "Update branch policy"),
    # Direct API call
    ("az devops invoke", "Azure DevOps API call"),
]

# Complex AZ CLI operations that show rich panel
COMPLEX_AZ_CLI_PATTERNS = [
    "az repos pr complete",
    "az boards work-item create",
    "az boards work-item update",
    "az boards work-item delete",
    "az pipelines run",
    "az pipelines create",
    "az pipelines delete",
    "az pipelines release create",
    "az repos create",
    "az repos delete",
    "az devops invoke",
]

# Git/GitHub write patterns
GIT_WRITE_PATTERNS = [
    ("git commit", "Commit changes"),
    ("git push", "Push to remote"),
    ("git merge", "Merge branches"),
    ("gh pr create", "Create GitHub PR"),
    ("gh pr merge", "Merge GitHub PR"),
    ("gh pr close", "Close GitHub PR"),
    ("gh pr comment", "Add PR comment"),
]


class TriagentPermissionHandler:
    """Handles tool permission requests with user confirmation.

    This class implements the canUseTool callback for the Claude Agent SDK,
    providing interactive confirmation for write operations and handling
    the AskUserQuestion tool for clarifying questions.
    """

    def __init__(self, console: Console, auto_approve: bool = False):
        """Initialize the permission handler.

        Args:
            console: Rich console for user interaction
            auto_approve: If True, skip confirmation prompts for write operations
        """
        self.console = console
        self.auto_approve = auto_approve

    async def _async_input(self, prompt: str = "") -> str:
        """Non-blocking input that works with asyncio event loop."""
        # Flush stdout to ensure prompt is visible before input
        sys.stdout.flush()
        return await asyncio.get_event_loop().run_in_executor(None, input, prompt)

    async def can_use_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        context: ToolPermissionContext,  # noqa: ARG002
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Main callback for SDK permission requests.

        This method is called by the Claude Agent SDK when it needs to check
        whether a tool can be used.

        Args:
            tool_name: Name of the tool being called
            input_data: Input parameters for the tool
            context: Permission context from the SDK (not currently used)

        Returns:
            PermissionResultAllow or PermissionResultDeny with appropriate details
        """
        # Auto-approve read-only tools
        if tool_name in READ_ONLY_TOOLS:
            return PermissionResultAllow(updated_input=input_data)

        # Handle AskUserQuestion specially - always allow and process
        if tool_name == "AskUserQuestion":
            return await self._handle_ask_question(input_data)

        # Auto-approve if configured (e.g., /confirm off)
        if self.auto_approve:
            return PermissionResultAllow(updated_input=input_data)

        # Check if this is a write operation that needs confirmation
        if self._is_write_operation(tool_name, input_data):
            return await self._prompt_for_approval(tool_name, input_data)

        # Default: allow the operation
        return PermissionResultAllow(updated_input=input_data)

    def _is_write_operation(self, tool_name: str, input_data: dict[str, Any]) -> bool:
        """Check if the tool call is a write operation.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            True if this is a write operation requiring confirmation
        """
        # Check MCP Azure DevOps write operations
        if tool_name.startswith("mcp__azure-devops__"):
            operation = tool_name.replace("mcp__azure-devops__", "")
            if operation in MCP_ADO_WRITE_OPS:
                return True

        # Check Bash commands for Azure CLI, Git, and GitHub patterns
        if tool_name == "Bash":
            command = input_data.get("command", "")
            command_lower = command.lower()

            # Check Azure CLI patterns
            for pattern, _ in AZURE_CLI_WRITE_PATTERNS:
                if pattern in command_lower:
                    return True

            # Check Git/GitHub patterns
            for pattern, _ in GIT_WRITE_PATTERNS:
                if pattern in command_lower:
                    return True

        return False

    def _is_complex_operation(self, tool_name: str, input_data: dict[str, Any]) -> bool:
        """Check if the operation should show a rich panel.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            True if this operation should show a rich panel confirmation
        """
        # Check MCP Azure DevOps complex operations
        if tool_name.startswith("mcp__azure-devops__"):
            operation = tool_name.replace("mcp__azure-devops__", "")
            if operation in COMPLEX_MCP_OPS:
                return True

        # Check Bash commands for complex patterns
        if tool_name == "Bash":
            command = input_data.get("command", "").lower()
            for pattern in COMPLEX_AZ_CLI_PATTERNS:
                if pattern in command:
                    return True
            # gh pr merge is also complex
            if "gh pr merge" in command:
                return True

        return False

    async def _prompt_for_approval(
        self, tool_name: str, input_data: dict[str, Any]
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Prompt user for write operation approval.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        if self._is_complex_operation(tool_name, input_data):
            return await self._rich_panel_confirm(tool_name, input_data)
        else:
            return await self._simple_confirm(tool_name, input_data)

    async def _simple_confirm(
        self, tool_name: str, input_data: dict[str, Any]
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Simple y/n confirmation prompt.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        # Build description
        description = self._get_operation_description(tool_name, input_data)

        self.console.print()
        self.console.print(f"[yellow]Confirm:[/yellow] {description}")

        while True:
            response = (await self._async_input("[y]es / [n]o: ")).strip().lower()
            if response in ("y", "yes"):
                log_permission_decision(tool_name, "allow", "User approved")
                return PermissionResultAllow(updated_input=input_data)
            elif response in ("n", "no"):
                log_permission_decision(tool_name, "deny", "User denied")
                return PermissionResultDeny(message="Operation cancelled by user")
            else:
                self.console.print("[dim]Please enter 'y' or 'n'[/dim]")

    async def _rich_panel_confirm(
        self, tool_name: str, input_data: dict[str, Any]
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Rich panel confirmation for complex operations.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        # Build description and details
        description = self._get_operation_description(tool_name, input_data)
        details = self._get_operation_details(tool_name, input_data)

        # Create table for details
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        for key, value in details.items():
            # Truncate long values
            display_value = str(value)
            if len(display_value) > 60:
                display_value = display_value[:57] + "..."
            table.add_row(key, display_value)

        # Show panel
        self.console.print()
        self.console.print(
            Panel(
                table,
                title=f"[bold yellow]Confirm: {description}[/bold yellow]",
                border_style="yellow",
            )
        )

        while True:
            response = (await self._async_input("[a]pprove / [d]eny / [v]iew full details: ")).strip().lower()
            if response in ("a", "approve"):
                log_permission_decision(tool_name, "allow", "User approved")
                return PermissionResultAllow(updated_input=input_data)
            elif response in ("d", "deny"):
                log_permission_decision(tool_name, "deny", "User denied")
                return PermissionResultDeny(message="Operation cancelled by user")
            elif response in ("v", "view"):
                # Show full JSON
                self.console.print()
                self.console.print("[dim]Full input data:[/dim]")
                self.console.print(json.dumps(input_data, indent=2))
                self.console.print()
            else:
                self.console.print("[dim]Please enter 'a', 'd', or 'v'[/dim]")

    def _get_operation_description(
        self, tool_name: str, input_data: dict[str, Any]
    ) -> str:
        """Get a human-readable description of the operation.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            Human-readable description
        """
        # MCP Azure DevOps operations
        if tool_name.startswith("mcp__azure-devops__"):
            operation = tool_name.replace("mcp__azure-devops__", "")
            op_descriptions = {
                "create_work_item": "Create work item",
                "update_work_item": "Update work item",
                "manage_work_item_link": "Manage work item link",
                "create_pull_request": "Create pull request",
                "update_pull_request": "Update pull request",
                "add_pull_request_comment": "Add PR comment",
                "create_branch": "Create branch",
                "create_commit": "Create commit",
                "trigger_pipeline": "Trigger pipeline",
            }
            return op_descriptions.get(operation, f"Execute {operation}")

        # Bash commands
        if tool_name == "Bash":
            command = input_data.get("command", "")
            command_lower = command.lower()

            # Check Azure CLI patterns
            for pattern, description in AZURE_CLI_WRITE_PATTERNS:
                if pattern in command_lower:
                    return description

            # Check Git/GitHub patterns
            for pattern, description in GIT_WRITE_PATTERNS:
                if pattern in command_lower:
                    return description

            # Fallback
            return f"Execute: {command[:50]}..." if len(command) > 50 else f"Execute: {command}"

        return f"Execute {tool_name}"

    def _get_operation_details(
        self, tool_name: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Get operation details for rich panel display.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters

        Returns:
            Dict of field names to values
        """
        details: dict[str, Any] = {}

        # MCP Azure DevOps operations
        if tool_name.startswith("mcp__azure-devops__"):
            operation = tool_name.replace("mcp__azure-devops__", "")

            if operation == "create_work_item":
                if "type" in input_data:
                    details["Type"] = input_data["type"]
                if "title" in input_data:
                    details["Title"] = input_data["title"]
                if "description" in input_data:
                    details["Description"] = input_data["description"][:100]
                if "parent_id" in input_data:
                    details["Parent"] = f"#{input_data['parent_id']}"

            elif operation == "update_work_item":
                if "id" in input_data:
                    details["Work Item"] = f"#{input_data['id']}"
                # Include any fields being updated
                for key in ["title", "state", "assigned_to", "description"]:
                    if key in input_data:
                        details[key.replace("_", " ").title()] = input_data[key]

            elif operation == "create_pull_request":
                if "title" in input_data:
                    details["Title"] = input_data["title"]
                if "source_branch" in input_data:
                    details["Source"] = input_data["source_branch"]
                if "target_branch" in input_data:
                    details["Target"] = input_data["target_branch"]

            elif operation == "add_pull_request_comment":
                if "pull_request_id" in input_data:
                    details["PR"] = f"#{input_data['pull_request_id']}"
                if "content" in input_data:
                    details["Comment"] = input_data["content"][:100]

            elif operation == "trigger_pipeline":
                if "pipeline_id" in input_data:
                    details["Pipeline"] = input_data["pipeline_id"]
                if "branch" in input_data:
                    details["Branch"] = input_data["branch"]

        # Bash commands
        elif tool_name == "Bash":
            command = input_data.get("command", "")
            # Show truncated command
            if len(command) > 100:
                details["Command"] = command[:100] + "..."
            else:
                details["Command"] = command

        return details if details else {"Input": str(input_data)[:200]}

    async def _handle_ask_question(
        self, input_data: dict[str, Any]
    ) -> PermissionResultAllow:
        """Handle AskUserQuestion tool - display questions and collect answers.

        Args:
            input_data: Tool input containing questions

        Returns:
            PermissionResultAllow with answers in updated_input
        """
        # Pause spinner and flush buffered text before showing questions
        from triagent.cli import flush_buffer, pause_spinner

        pause_spinner()
        flush_buffer()

        questions = input_data.get("questions", [])
        answers: dict[str, str] = {}

        self.console.print()

        for q in questions:
            header = q.get("header", "Question")
            question_text = q.get("question", "")
            options = q.get("options", [])
            multi_select = q.get("multiSelect", False)

            # Display question
            self.console.print(f"[bold cyan]{header}:[/bold cyan] {question_text}")

            # Display options
            for i, opt in enumerate(options, 1):
                label = opt.get("label", f"Option {i}")
                description = opt.get("description", "")
                if description:
                    self.console.print(f"  {i}. {label} - [dim]{description}[/dim]")
                else:
                    self.console.print(f"  {i}. {label}")

            # Get user selection
            if multi_select:
                self.console.print("[dim]Enter numbers separated by commas (e.g., 1,3)[/dim]")
                while True:
                    choice = (await self._async_input("Select: ")).strip()
                    try:
                        selections = [int(x.strip()) for x in choice.split(",")]
                        if all(1 <= s <= len(options) for s in selections):
                            selected_labels = [options[s - 1]["label"] for s in selections]
                            answers[question_text] = ", ".join(selected_labels)
                            break
                        else:
                            self.console.print(f"[red]Please enter numbers between 1 and {len(options)}[/red]")
                    except ValueError:
                        self.console.print("[red]Please enter valid numbers separated by commas[/red]")
            else:
                while True:
                    choice = (await self._async_input("Select (number): ")).strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(options):
                        answers[question_text] = options[int(choice) - 1]["label"]
                        break
                    else:
                        self.console.print(f"[red]Please enter a number between 1 and {len(options)}[/red]")

            self.console.print()

        return PermissionResultAllow(
            updated_input={"questions": questions, "answers": answers}
        )
