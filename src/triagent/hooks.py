"""Security hooks for Triagent tool execution.

This module provides hooks for the Claude Agent SDK that implement
security controls and logging for tool execution.
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk.types import HookContext, HookMatcher

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


async def check_bash_command(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext,
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
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked: contains dangerous pattern '{pattern}'",
                }
            }
    return {}


async def confirm_azure_write(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """PreToolUse hook to confirm MCP Azure DevOps write operations.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Empty dict for read operations, confirmation request for writes
    """
    tool_name = input_data.get("tool_name", "")

    # Only check MCP Azure DevOps tools
    if not tool_name.startswith("mcp__azure-devops__"):
        return {}

    # Extract the operation name from tool name (e.g., mcp__azure-devops__create_work_item)
    operation = tool_name.replace("mcp__azure-devops__", "")

    # Check if this is a write operation
    if operation in MCP_ADO_WRITE_OPS:
        description = MCP_ADO_WRITE_OPS[operation]
        tool_input = input_data.get("tool_input", {})
        # Build a summary of the operation
        summary_parts = [f"Operation: {description}"]
        if "title" in tool_input:
            summary_parts.append(f"Title: {tool_input['title'][:50]}")
        if "work_item_id" in tool_input:
            summary_parts.append(f"Work Item: #{tool_input['work_item_id']}")
        if "pull_request_id" in tool_input:
            summary_parts.append(f"PR: #{tool_input['pull_request_id']}")

        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "\n".join(summary_parts),
            }
        }

    return {}


async def confirm_azure_cli_write(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """PreToolUse hook to confirm Azure CLI write operations.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Empty dict for read operations, confirmation request for writes
    """
    tool_name = input_data.get("tool_name", "")
    if tool_name != "execute_azure_cli":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    command_lower = command.lower()

    for pattern, description in AZURE_CLI_WRITE_PATTERNS:
        if pattern in command_lower:
            # Truncate command for display
            display_cmd = command[:100] + "..." if len(command) > 100 else command
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"Confirm: {description}\nCommand: {display_cmd}",
                }
            }
    return {}


async def confirm_git_write(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """PreToolUse hook to confirm git and GitHub CLI write operations.

    Args:
        input_data: Contains 'tool_name' and 'tool_input' dict
        tool_use_id: Optional tool use identifier
        context: Hook context

    Returns:
        Empty dict for read operations, confirmation request for writes
    """
    if input_data.get("tool_name") != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    command_lower = command.lower()

    for pattern, description in GIT_WRITE_PATTERNS:
        if pattern in command_lower:
            # Truncate command for display
            display_cmd = command[:100] + "..." if len(command) > 100 else command
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"Confirm: {description}\nCommand: {display_cmd}",
                }
            }
    return {}


async def log_tool_result(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext,
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


def get_triagent_hooks(config: Any) -> dict[str, list[HookMatcher]]:
    """Get hooks configuration for Triagent.

    Args:
        config: Triagent configuration object

    Returns:
        Dict mapping HookEvent names to list of HookMatchers
    """
    hooks: dict[str, list[HookMatcher]] = {
        "PreToolUse": [
            # Security: block dangerous bash commands
            HookMatcher(matcher="Bash", hooks=[check_bash_command], timeout=120),
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[log_tool_result]),  # All tools
        ],
    }

    # Add write confirmation hooks if not in auto-approve mode
    if not getattr(config, "auto_approve_writes", False):
        # MCP Azure DevOps write confirmation
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher="^mcp__azure-devops__",
                hooks=[confirm_azure_write],
                timeout=300,  # Allow time for user confirmation
            )
        )
        # Azure CLI write confirmation
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher="execute_azure_cli",
                hooks=[confirm_azure_cli_write],
                timeout=300,
            )
        )
        # Git/GitHub write confirmation
        hooks["PreToolUse"].append(
            HookMatcher(
                matcher="Bash",
                hooks=[confirm_git_write],
                timeout=300,
            )
        )

    return hooks
