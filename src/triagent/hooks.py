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
    """PreToolUse hook to confirm Azure DevOps write operations.

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

    # Allow read operations automatically
    read_patterns = ["list_", "get_", "search_", "show_"]
    if any(op in tool_name for op in read_patterns):
        return {}

    # Require confirmation for write operations
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"Confirm write operation: {tool_name}",
        }
    }


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
            HookMatcher(matcher="Bash", hooks=[check_bash_command], timeout=120),
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[log_tool_result]),  # All tools
        ],
    }

    # Add Azure DevOps write confirmation if not in auto mode
    if not getattr(config, "auto_approve_writes", False):
        hooks["PreToolUse"].append(
            HookMatcher(matcher=None, hooks=[confirm_azure_write])
        )

    return hooks
