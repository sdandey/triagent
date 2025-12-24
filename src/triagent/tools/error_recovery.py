"""Error recovery and intelligent retry logic for Triagent tool execution."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


class ErrorType(Enum):
    """Classification of API errors."""

    CONTEXT_TOO_LARGE = "context_too_large"
    RATE_LIMIT = "rate_limit"
    SYNTAX_ERROR = "syntax_error"
    AUTH_ERROR = "auth_error"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    enable_help_lookup: bool = True
    aggressive_truncation_threshold: int = 2000


@dataclass
class ErrorContext:
    """Context for error recovery."""

    status_code: int
    error_message: str
    error_type: ErrorType
    original_command: str | None = None
    attempt_number: int = 1
    previous_output: str | None = None


def classify_http_error(status_code: int, error_text: str) -> ErrorType:
    """Classify an HTTP error based on status code and message.

    Args:
        status_code: HTTP status code
        error_text: Error response text

    Returns:
        Classified error type
    """
    if status_code == 400:
        # Check for context/token limit indicators
        context_indicators = [
            "context length",
            "token limit",
            "too large",
            "max_tokens",
            "input too long",
            "context window",
            "exceeds maximum",
        ]
        error_lower = error_text.lower()
        if any(indicator in error_lower for indicator in context_indicators):
            return ErrorType.CONTEXT_TOO_LARGE
        # Default 400 to context too large as most common cause
        return ErrorType.CONTEXT_TOO_LARGE
    elif status_code == 429:
        return ErrorType.RATE_LIMIT
    elif status_code in (401, 403):
        return ErrorType.AUTH_ERROR
    return ErrorType.UNKNOWN


@lru_cache(maxsize=50)
def get_cli_help(command_base: str) -> str | None:
    """Get Azure CLI help for a command (cached).

    Args:
        command_base: The base command (e.g., "az repos pr list")

    Returns:
        Help text or None if failed
    """
    try:
        help_cmd = f"{command_base} -h"
        result = subprocess.run(
            shlex.split(help_cmd),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception:
        return None


def extract_command_base(full_command: str) -> str:
    """Extract the base command for help lookup.

    Args:
        full_command: Full az command string

    Returns:
        Base command (e.g., "az repos pr list")
    """
    parts = full_command.split()
    base_parts = []
    for part in parts:
        if part.startswith("-"):
            break
        base_parts.append(part)
    return " ".join(base_parts)


def generate_recovery_instruction(
    ctx: ErrorContext,
    help_text: str | None = None,
) -> str:
    """Generate an instruction for Claude to self-correct.

    Args:
        ctx: Context about the error
        help_text: Optional CLI help text

    Returns:
        Recovery instruction message
    """
    instruction_parts = [
        f"## Error Recovery - Attempt {ctx.attempt_number}",
        "",
        "The previous API call failed due to response/context size.",
        "You MUST retry with a command that produces LESS output.",
        "",
        "### Required Recovery Actions:",
        "1. Use `--top 5` (or smaller value)",
        "2. Use `--query` to select ONLY essential fields like:",
        '   `--query "[].{id:pullRequestId,title:title,status:status}"`',
        "3. Add more specific filters (--status, --repository, --target-branch)",
        "",
    ]

    if ctx.original_command:
        instruction_parts.extend([
            "### Previous Command (caused error):",
            f"`{ctx.original_command}`",
            "",
        ])

    if help_text:
        # Extract relevant filtering options from help
        relevant_lines = []
        for line in help_text.split("\n"):
            line_lower = line.lower()
            if any(kw in line_lower for kw in ["--top", "--query", "--status", "--repository"]):
                stripped = line.strip()
                if stripped and len(stripped) < 100:
                    relevant_lines.append(stripped)

        if relevant_lines:
            instruction_parts.extend([
                "### Available Filtering Options (from --help):",
                *[f"  {line}" for line in relevant_lines[:8]],
                "",
            ])

    instruction_parts.extend([
        "### Example Corrected Command:",
        '`az repos pr list --org URL --project NAME --top 5 --query "[].{id:pullRequestId,title:title,status:status}" --output json`',
        "",
        "Generate a corrected command with better filtering NOW.",
    ])

    return "\n".join(instruction_parts)


def truncate_aggressively(content: str, max_length: int = 2000) -> str:
    """Aggressively truncate content for retry scenarios.

    Args:
        content: Content to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated content with summary
    """
    if len(content) <= max_length:
        return content

    # Keep first portion and a small end portion
    first_portion = max_length * 3 // 4
    last_portion = max_length // 8

    truncated = (
        content[:first_portion]
        + f"\n\n... [{len(content) - first_portion - last_portion} chars truncated] ...\n\n"
        + content[-last_portion:]
    )
    return truncated
