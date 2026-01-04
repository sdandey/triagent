"""Security hooks for Triagent tool execution.

This module provides hooks for the Claude Agent SDK that implement
security controls and logging for tool execution.
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk.types import (
    HookContext,
    HookEvent,
    HookMatcher,
    PostToolUseHookInput,
    PreToolUseHookInput,
)
from rich.console import Console
from rich.panel import Panel

from triagent.session_logger import (
    post_tool_use_logger,
    pre_tool_use_logger,
    session_stop_logger,
    user_prompt_logger,
)

# Dangerous patterns to block in Bash commands
DANGEROUS_BASH_PATTERNS = [
    "rm -rf /",
    "DROP TABLE",
    "DELETE FROM",
    "> /dev/",
    "chmod 777",
    ":(){:|:&};:",  # Fork bomb
]

# MCP Azure DevOps write operations with descriptions
MCP_ADO_WRITE_OPS = {
    "create_work_item": "Create ADO work item",
    "update_work_item": "Update ADO work item",
    "create_pull_request": "Create pull request",
    "update_pull_request": "Update pull request",
    "create_pull_request_comment": "Add PR comment",
    "create_thread": "Create PR review thread",
    "reply_to_thread": "Reply to PR thread",
    "resolve_thread": "Resolve PR thread",
}

# Azure CLI write patterns requiring confirmation
AZURE_CLI_WRITE_PATTERNS = [
    # Pull Requests
    ("az repos pr create", "Create pull request"),
    ("az repos pr update", "Update pull request"),
    ("az repos pr set-vote", "Set PR vote/review"),
    ("az repos pr complete", "Complete/merge pull request"),
    ("az repos pr abandon", "Abandon pull request"),
    # Work Items
    ("az boards work-item create", "Create work item"),
    ("az boards work-item update", "Update work item"),
    ("az boards work-item delete", "Delete work item"),
    ("az boards work-item relation add", "Add work item link"),
    ("az boards work-item relation remove", "Remove work item link"),
    # Pipelines
    ("az pipelines run", "Trigger pipeline run"),
    ("az pipelines create", "Create pipeline"),
    ("az pipelines update", "Update pipeline"),
    ("az pipelines delete", "Delete pipeline"),
    ("az pipelines build queue", "Queue a build"),
    ("az pipelines release create", "Create release"),
    # Repositories
    ("az repos create", "Create repository"),
    ("az repos delete", "Delete repository"),
    ("az repos update", "Update repository"),
    ("az repos policy create", "Create branch policy"),
    ("az repos policy update", "Update branch policy"),
]

# Curl-based API patterns for Azure DevOps (method, description)
# These require both the method pattern AND dev.azure.com in the command
CURL_ADO_WRITE_PATTERNS = [
    ("-x delete", "DELETE API call to Azure DevOps"),
    ("-x post", "POST API call to Azure DevOps"),
    ("-x put", "PUT API call to Azure DevOps"),
    ("-x patch", "PATCH API call to Azure DevOps"),
]

# Git/GitHub write operations requiring confirmation
GIT_WRITE_PATTERNS = [
    # Git
    ("git commit", "Commit changes"),
    ("git push", "Push to remote"),
    ("git merge", "Merge branches"),
    # GitHub CLI
    ("gh pr create", "Create GitHub PR"),
    ("gh pr merge", "Merge GitHub PR"),
    ("gh pr close", "Close GitHub PR"),
    ("gh pr comment", "Add GitHub PR comment"),
]


def format_command_readable(command: str) -> str:
    """Format a command with line breaks for readability.

    Breaks at common argument patterns like -- flags to make
    long commands easier to read in confirmation panels.

    Args:
        command: The command string to format

    Returns:
        Formatted command with line breaks and indentation
    """
    parts = []
    current = ""
    tokens = command.split()

    for token in tokens:
        if token.startswith("--") and current:
            parts.append(current.strip())
            current = f"  {token} "
        else:
            current += f"{token} "

    if current.strip():
        parts.append(current.strip())

    return " \\\n".join(parts)


def format_field_value(value: str, max_length: int = 150) -> str:
    """Format any field value for human-readable display.

    Automatically detects HTML vs plain text and formats accordingly.
    Converts HTML list items to bullet points, strips tags, and truncates.

    Args:
        value: Field value (HTML or plain text)
        max_length: Maximum display length before truncation

    Returns:
        Clean, readable text
    """
    import re

    text = value

    # Auto-detect HTML and convert to plain text
    if "<" in text and ">" in text:
        # Convert list items to bullet points
        text = re.sub(r"<li[^>]*>", "• ", text)
        # Preserve strong/bold content
        text = re.sub(r"<strong>([^<]*)</strong>", r"\1", text)
        text = re.sub(r"<b>([^<]*)</b>", r"\1", text)
        # Remove all remaining HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

    # Clean up whitespace (works for both HTML and plain text)
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length].rstrip() + "..."

    return text


def format_field_name(field_name: str) -> str:
    """Format field name for human-readable display.

    Handles:
    - ADO field names: 'Microsoft.VSTS.Common.AcceptanceCriteria' → 'Acceptance Criteria'
    - CLI flags: 'work-item-type' → 'Work Item Type'

    Args:
        field_name: Raw field name

    Returns:
        Human-readable field name
    """
    import re

    name = field_name

    # Strip ADO prefixes
    ado_prefixes = [
        "Microsoft.VSTS.Common.",
        "Microsoft.VSTS.Scheduling.",
        "Microsoft.VSTS.",
        "System.",
    ]
    for prefix in ado_prefixes:
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break

    # Split CamelCase: 'AcceptanceCriteria' → 'Acceptance Criteria'
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    # Convert dashes/underscores to spaces
    name = name.replace("-", " ").replace("_", " ")

    return name.title()


def extract_command_fields(command: str) -> dict[str, str]:
    """Extract human-readable field values from a command.

    Parses --flag value and --flag="value" patterns to display
    field values in a user-friendly format. Handles both plain text
    and HTML content automatically.

    Args:
        command: The command string to parse

    Returns:
        Dict mapping field names to values (e.g., {"Title": "Test Task"})
    """
    import re

    fields: dict[str, str] = {}

    # Match --flag value or --flag="value" or --flag='value'
    # Handles: --title "value", --title="value", --title 'value', --title=value
    pattern = r'--([a-zA-Z][\w-]*)(?:=|\s+)(?:"([^"]+)"|\'([^\']+)\'|(\S+))'

    skip_flags = {"output", "query", "o", "debug", "verbose", "only-show-errors"}

    for match in re.finditer(pattern, command):
        flag = match.group(1)
        value = match.group(2) or match.group(3) or match.group(4)

        if not value or flag.lower() in skip_flags:
            continue

        # Handle --fields "FieldName=value" specially (ADO work item fields)
        if flag == "fields" and "=" in value:
            field_name, field_value = value.split("=", 1)
            display_name = format_field_name(field_name)
            display_value = format_field_value(field_value)
            fields[display_name] = display_value
        else:
            display_name = format_field_name(flag)
            display_value = format_field_value(value)
            fields[display_name] = display_value

    return fields


async def check_bash_command(
    input_data: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,  # noqa: ARG001
) -> dict[str, Any]:
    """PreToolUse hook to block dangerous Bash commands.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context with signal support

    Returns:
        Empty dict to allow, or dict with 'hookSpecificOutput' to deny
    """
    if input_data.get("tool_name") != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")

    for pattern in DANGEROUS_BASH_PATTERNS:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": input_data.get("hook_event_name", "PreToolUse"),
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked: contains dangerous pattern '{pattern}'",
                }
            }
    return {}


async def confirm_azure_write(
    input_data: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,  # noqa: ARG001
) -> dict[str, Any]:
    """PreToolUse hook to confirm MCP Azure DevOps write operations.

    Prompts user directly since SDK's 'ask' permissionDecision doesn't
    trigger interactive prompts.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Empty dict to allow, or deny decision to block
    """
    import asyncio
    import sys

    tool_name = input_data.get("tool_name", "")

    # Only check MCP Azure DevOps tools
    if not tool_name.startswith("mcp__azure-devops__"):
        return {}

    # Extract the operation name from tool name (e.g., mcp__azure-devops__create_work_item)
    operation = tool_name.replace("mcp__azure-devops__", "")

    # Check if this is a write operation
    if operation in MCP_ADO_WRITE_OPS:
        # Pause spinner and flush buffered text before prompting
        from triagent.cli import flush_buffer, pause_spinner

        pause_spinner()
        flush_buffer()

        description = MCP_ADO_WRITE_OPS[operation]
        tool_input = input_data.get("tool_input", {})

        # Build field lines for display
        field_lines = []
        if "title" in tool_input:
            title = tool_input["title"]
            if len(title) > 60:
                title = title[:57] + "..."
            field_lines.append(f"[cyan]Title:[/cyan] {title}")
        if "type" in tool_input:
            field_lines.append(f"[cyan]Type:[/cyan] {tool_input['type']}")
        if "work_item_id" in tool_input:
            field_lines.append(f"[cyan]Work Item:[/cyan] #{tool_input['work_item_id']}")
        if "pull_request_id" in tool_input:
            field_lines.append(f"[cyan]PR:[/cyan] #{tool_input['pull_request_id']}")
        if "state" in tool_input:
            field_lines.append(f"[cyan]State:[/cyan] {tool_input['state']}")
        if "assigned_to" in tool_input:
            field_lines.append(f"[cyan]Assigned To:[/cyan] {tool_input['assigned_to']}")

        # Create panel content
        if field_lines:
            content = f"[bold]{description}[/bold]\n\n" + "\n".join(field_lines)
        else:
            content = f"[bold]{description}[/bold]"

        # Display in a Claude Code-style panel
        console = Console()
        console.print()
        console.print(
            Panel(content, title="[yellow]Azure DevOps[/yellow]", border_style="yellow")
        )
        sys.stdout.flush()

        # Async-compatible input
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, input, "[y]es / [n]o: ")
        response = response.strip().lower()

        if response in ("y", "yes"):
            return {}  # Allow - empty dict means proceed
        else:
            return {
                "hookSpecificOutput": {
                    "hookEventName": input_data.get("hook_event_name", "PreToolUse"),
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "User denied operation",
                }
            }

    return {}


async def confirm_azure_cli_write(
    input_data: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,  # noqa: ARG001
) -> dict[str, Any]:
    """PreToolUse hook to confirm Azure CLI write operations.

    Prompts user directly since SDK's 'ask' permissionDecision doesn't
    trigger interactive prompts.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Empty dict to allow, or deny decision to block
    """
    import asyncio
    import sys

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    command_lower = command.lower()

    # Check for Azure CLI patterns
    matched_description = None
    for pattern, description in AZURE_CLI_WRITE_PATTERNS:
        if pattern in command_lower:
            matched_description = description
            break

    # Check for curl-based Azure DevOps API calls
    if not matched_description and "curl" in command_lower and "dev.azure.com" in command_lower:
        for pattern, description in CURL_ADO_WRITE_PATTERNS:
            if pattern in command_lower:
                matched_description = description
                break

    if matched_description:
        # Pause spinner and flush buffered text before prompting
        from triagent.cli import flush_buffer, pause_spinner

        pause_spinner()
        flush_buffer()

        # Extract human-readable fields from command
        fields = extract_command_fields(command)
        field_lines = "\n".join(
            f"[cyan]{k}:[/cyan] {v}" for k, v in fields.items()
        )

        # Format command for readability
        formatted_cmd = format_command_readable(command)

        # Create panel content with description, fields, and command
        if field_lines:
            content = (
                f"[bold]{matched_description}[/bold]\n\n"
                f"{field_lines}\n\n"
                f"[dim]Command:[/dim]\n[dim]{formatted_cmd}[/dim]"
            )
        else:
            content = f"[bold]{matched_description}[/bold]\n\n[dim]{formatted_cmd}[/dim]"

        # Display in a Claude Code-style panel
        console = Console()
        console.print()
        console.print(
            Panel(content, title="[yellow]Bash[/yellow]", border_style="yellow")
        )
        sys.stdout.flush()

        # Async-compatible input
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, input, "[y]es / [n]o: ")
        response = response.strip().lower()

        if response in ("y", "yes"):
            return {}  # Allow - empty dict means proceed
        else:
            return {
                "hookSpecificOutput": {
                    "hookEventName": input_data.get("hook_event_name", "PreToolUse"),
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "User denied operation",
                }
            }
    return {}


async def confirm_git_write(
    input_data: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,  # noqa: ARG001
) -> dict[str, Any]:
    """PreToolUse hook to confirm git and GitHub CLI write operations.

    Prompts user directly since SDK's 'ask' permissionDecision doesn't
    trigger interactive prompts.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Empty dict to allow, or deny decision to block
    """
    import asyncio
    import sys

    if input_data.get("tool_name") != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    command_lower = command.lower()

    for pattern, description in GIT_WRITE_PATTERNS:
        if pattern in command_lower:
            # Pause spinner and flush buffered text before prompting
            from triagent.cli import flush_buffer, pause_spinner

            pause_spinner()
            flush_buffer()

            # Extract human-readable fields from command
            fields = extract_command_fields(command)
            field_lines = "\n".join(
                f"[cyan]{k}:[/cyan] {v}" for k, v in fields.items()
            )

            # Format command for readability
            formatted_cmd = format_command_readable(command)

            # Create panel content with description, fields, and command
            if field_lines:
                content = (
                    f"[bold]{description}[/bold]\n\n"
                    f"{field_lines}\n\n"
                    f"[dim]Command:[/dim]\n[dim]{formatted_cmd}[/dim]"
                )
            else:
                content = f"[bold]{description}[/bold]\n\n[dim]{formatted_cmd}[/dim]"

            # Display in a Claude Code-style panel
            console = Console()
            console.print()
            console.print(
                Panel(content, title="[yellow]Bash[/yellow]", border_style="yellow")
            )
            sys.stdout.flush()

            # Async-compatible input
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, input, "[y]es / [n]o: ")
            response = response.strip().lower()

            if response in ("y", "yes"):
                return {}  # Allow - empty dict means proceed
            else:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": input_data.get("hook_event_name", "PreToolUse"),
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "User denied operation",
                    }
                }
    return {}


async def log_tool_result(
    input_data: PostToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,  # noqa: ARG001
) -> dict[str, Any]:
    """PostToolUse hook to log tool results for debugging.

    Args:
        input_data: Contains 'tool_name' and 'tool_response'
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Additional context for errors, empty dict otherwise
    """
    tool_response = input_data.get("tool_response", "")

    if "error" in str(tool_response).lower():
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Tool execution encountered an error.",
            }
        }
    return {}


def get_triagent_hooks(config: Any) -> dict[HookEvent, list[HookMatcher]]:
    """Get hooks configuration for Triagent.

    Args:
        config: Triagent configuration object

    Returns:
        Dict mapping HookEvent names to list of HookMatchers
    """
    hooks: dict[HookEvent, list[HookMatcher]] = {
        "PreToolUse": [
            # Security: block dangerous bash commands
            HookMatcher(matcher="Bash", hooks=[check_bash_command], timeout=120),  # type: ignore[list-item]
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[log_tool_result]),  # type: ignore[list-item]
        ],
    }

    # Add session logging hooks if enabled
    if getattr(config, "session_logging", True):
        # Add logging hooks for all tools
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[pre_tool_use_logger],  # type: ignore[list-item]
                timeout=5,  # Quick logging timeout
            )
        )
        hooks["PostToolUse"].append(
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[post_tool_use_logger],  # type: ignore[list-item]
                timeout=5,
            )
        )
        # User prompt logging
        hooks["UserPromptSubmit"] = [
            HookMatcher(
                matcher=None,
                hooks=[user_prompt_logger],  # type: ignore[list-item]
                timeout=5,
            )
        ]
        # Session stop logging
        hooks["Stop"] = [
            HookMatcher(
                matcher=None,
                hooks=[session_stop_logger],  # type: ignore[list-item]
                timeout=5,
            )
        ]

    # Add write confirmation hooks if not in auto-approve mode
    if not getattr(config, "auto_approve_writes", False):
        # MCP Azure DevOps write confirmation
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher="^mcp__azure-devops__",
                hooks=[confirm_azure_write],  # type: ignore[list-item]
                timeout=300,  # Allow time for user confirmation
            )
        )
        # Azure CLI write confirmation (via Bash tool)
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher="Bash",
                hooks=[confirm_azure_cli_write],  # type: ignore[list-item]
                timeout=300,
            )
        )
        # Git/GitHub write confirmation
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher="Bash",
                hooks=[confirm_git_write],  # type: ignore[list-item]
                timeout=300,
            )
        )

    return hooks
