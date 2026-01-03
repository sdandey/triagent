"""Azure CLI tool for Triagent.

Provides a single flexible tool that can execute any Azure CLI command,
with automatic consent for read operations and confirmation for write operations.

Supports both:
- Legacy format (AZURE_CLI_TOOL dict) for custom client implementations
- SDK format (@tool decorator) for Claude Agent SDK
"""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from typing import Any

from claude_agent_sdk import tool

# Tool definition for OpenAI/Anthropic function calling format (legacy)
AZURE_CLI_TOOL = {
    "name": "execute_azure_cli",
    "description": """Execute an Azure CLI command to interact with Azure DevOps.

IMPORTANT: Always use --top AND --query to limit results and avoid large responses:
- For PR lists, use --top 10-20 and select specific fields with --query
- For repo lists, use --top 50 max
- Always use --query to select only needed fields (reduces response size)

ORGANIZATION URL FORMAT: https://dev.azure.com/ORGANIZATION_NAME

## REPOSITORY COMMANDS (az repos)

List repositories:
  az repos list --org URL --project NAME --output json

Filter active repos only (exclude disabled):
  az repos list --org URL --project NAME --query "[?isDisabled==`false`]" --output json

Filter by name pattern:
  az repos list --org URL --project NAME --query "[?contains(name, 'cortex')]" --output json

## PULL REQUEST COMMANDS (az repos pr)

IMPORTANT: Always use --top AND --query to select only needed fields!

List PRs with essential fields only (RECOMMENDED):
  az repos pr list --org URL --project NAME --top 15 --query "[].{id:pullRequestId,title:title,status:status,createdBy:createdBy.displayName,createdDate:creationDate}" --output json

Filter by target branch:
  az repos pr list --org URL --project NAME --target-branch develop --top 15 --query "[].{id:pullRequestId,title:title,status:status,createdBy:createdBy.displayName}" --output json

Filter by status:
  az repos pr list --org URL --project NAME --status completed --top 15 --query "[].{id:pullRequestId,title:title,closedDate:closedDate,createdBy:createdBy.displayName}" --output json

Filter by repository:
  az repos pr list --org URL --project NAME --repository REPO_NAME --top 15 --query "[].{id:pullRequestId,title:title,status:status}" --output json

Combined filters:
  az repos pr list --org URL --project NAME --target-branch develop --status completed --top 15 --query "[].{id:pullRequestId,title:title,closedDate:closedDate}" --output json

## WORK ITEM COMMANDS (az boards)

Query work items (WIQL):
  az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] = 'Active'" --org URL --project NAME --output json

Get work item details:
  az boards work-item show --id ID --org URL --output json

## PIPELINE COMMANDS (az pipelines)

List pipelines:
  az pipelines list --org URL --project NAME --output json

List recent runs:
  az pipelines runs list --pipeline-id ID --org URL --project NAME --top 10 --output json

## JMESPath FILTERING (--query)

Filter by field value:
  --query "[?fieldName==`value`]"

Filter by contains:
  --query "[?contains(name, 'pattern')]"

Select specific fields:
  --query "[].{name: name, id: id, status: status}"

Combine filters:
  --query "[?isDisabled==`false` && contains(name, 'cortex')]"

NOTE: Date filtering is not directly available in CLI. To find recent activity:
1. Use --status completed for recent completed PRs
2. Check pipeline runs for recent builds
3. Query work items by date fields using WIQL""",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The full Azure CLI command. ALWAYS include --top for list commands to limit results.",
            }
        },
        "required": ["command"],
    },
}

# Commands that require user confirmation before execution
WRITE_OPERATIONS = ["create", "update", "delete", "run", "set-vote"]


def is_write_operation(command: str) -> bool:
    """Check if the command modifies state and requires confirmation.

    Args:
        command: The Azure CLI command string

    Returns:
        True if this is a write operation that needs confirmation
    """
    command_lower = command.lower()
    return any(op in command_lower for op in WRITE_OPERATIONS)


def execute_azure_cli(
    command: str,
    confirm_callback: Callable[[str], bool] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Execute an Azure CLI command.

    Args:
        command: Full az command string
        confirm_callback: Function to ask user for confirmation on write operations.
                         Takes the command string, returns True to proceed.
        timeout: Command timeout in seconds

    Returns:
        Dictionary with keys:
        - success: bool indicating if command succeeded
        - output: stdout from the command (on success)
        - error: error message (on failure)
    """
    # Security: only allow az commands
    command = command.strip()
    if not command.startswith("az "):
        return {"success": False, "output": "", "error": "Only 'az' commands are allowed"}

    # Check for confirmation on write operations
    if is_write_operation(command):
        if confirm_callback is not None and not confirm_callback(command):
            return {"success": False, "output": "", "error": "Operation cancelled by user"}

    try:
        # Parse the command safely
        args = shlex.split(command)

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout, "error": ""}
        else:
            return {"success": False, "output": "", "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Command timed out after {timeout} seconds"}
    except ValueError as e:
        return {"success": False, "output": "", "error": f"Invalid command format: {e}"}
    except FileNotFoundError:
        return {"success": False, "output": "", "error": "Azure CLI (az) not found. Please install it first."}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}


# SDK-compatible tool using @tool decorator
@tool(
    name="execute_azure_cli",
    description="""Execute an Azure CLI command to interact with Azure DevOps.

IMPORTANT: Always use --top AND --query to limit results and avoid large responses.

Common commands:
- az repos list --org URL --project NAME --top 10 --output json
- az repos pr list --org URL --project NAME --top 15 --query "[].{id:pullRequestId,title:title}" --output json
- az boards work-item show --id ID --org URL --output json
- az pipelines runs list --pipeline-id ID --org URL --project NAME --top 10 --output json

Only 'az' commands are allowed for security.""",
    input_schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The full Azure CLI command starting with 'az'",
            }
        },
        "required": ["command"],
    },
)
async def execute_azure_cli_sdk(args: dict[str, Any]) -> dict[str, Any]:
    """SDK-compatible Azure CLI tool execution.

    Args:
        args: Dictionary containing 'command' key with the az command

    Returns:
        SDK-format response with content array
    """
    command = args.get("command", "").strip()

    # Security: only allow az commands
    if not command.startswith("az "):
        return {
            "content": [{"type": "text", "text": "Error: Only 'az' commands are allowed"}],
            "is_error": True,
        }

    try:
        # Parse and execute the command
        cmd_args = shlex.split(command)
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return {
                "content": [{"type": "text", "text": result.stdout}],
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Error: {result.stderr}"}],
                "is_error": True,
            }

    except subprocess.TimeoutExpired:
        return {
            "content": [{"type": "text", "text": "Error: Command timed out after 60 seconds"}],
            "is_error": True,
        }
    except ValueError as e:
        return {
            "content": [{"type": "text", "text": f"Error: Invalid command format: {e}"}],
            "is_error": True,
        }
    except FileNotFoundError:
        return {
            "content": [{"type": "text", "text": "Error: Azure CLI (az) not found. Please install it."}],
            "is_error": True,
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {e}"}],
            "is_error": True,
        }
