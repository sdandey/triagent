"""Session logging for Triagent using SDK hooks.

This module provides session logging functionality that captures all tool calls,
user prompts, and session lifecycle events. Logs are written to platform-specific
directories in standard text format for later LLM triage analysis.

Logging is automatically disabled in Docker environments.
"""

from __future__ import annotations

import logging
import os
import platform
import re
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# Global session logger instance
_session_logger: logging.Logger | None = None
_session_id: str | None = None
_session_start_time: datetime | None = None
_session_ended: bool = False  # Guard against duplicate SESSION_END logs


def get_log_directory() -> Path:
    """Get platform-specific log directory.

    Returns:
        Path to the log directory based on the current platform:
        - macOS: ~/Library/Logs/triagent/sessions/
        - Windows: %LOCALAPPDATA%/triagent/logs/sessions/
        - Linux: ~/.local/share/triagent/logs/sessions/
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Logs" / "triagent"
    elif system == "Windows":
        # Use LOCALAPPDATA on Windows
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            base = Path(local_app_data) / "triagent" / "logs"
        else:
            base = Path.home() / "AppData" / "Local" / "triagent" / "logs"
    else:  # Linux and others
        base = Path.home() / ".local" / "share" / "triagent" / "logs"

    return base / "sessions"


def is_docker_environment() -> bool:
    """Detect if running inside a Docker container.

    Returns:
        True if running in Docker, False otherwise
    """
    # Check for .dockerenv file
    if Path("/.dockerenv").exists():
        return True

    # Check for Docker-related environment variables
    if os.environ.get("DOCKER_CONTAINER"):
        return True

    # Check cgroup for docker
    try:
        with open("/proc/1/cgroup") as f:
            return "docker" in f.read()
    except (FileNotFoundError, PermissionError):
        pass

    return False


def redact_sensitive_data(data: Any) -> Any:
    """Redact sensitive data from logs.

    Applies regex patterns to redact:
    - API keys
    - Tokens
    - Passwords
    - Bearer tokens
    - Connection strings
    - Azure secrets
    - Private keys
    - PAT tokens

    Args:
        data: Data to redact (string, dict, or any other type)

    Returns:
        Redacted data with sensitive information replaced
    """
    if data is None:
        return None

    # Convert to string for pattern matching
    if isinstance(data, dict):
        # Recursively redact dict values
        return {k: redact_sensitive_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif not isinstance(data, str):
        text = str(data)
    else:
        text = data

    # Define redaction patterns
    patterns = [
        # API keys
        (r'api[_-]?key["\s:=]+[A-Za-z0-9_-]{20,}', "[REDACTED_API_KEY]"),
        # Tokens
        (r'token["\s:=]+[A-Za-z0-9_.-]{20,}', "[REDACTED_TOKEN]"),
        # Passwords
        (r'password["\s:=]+.{1,50}(?=[\s,}"\']|$)', "[REDACTED_PASSWORD]"),
        # Bearer tokens
        (r"Bearer [A-Za-z0-9_.-]+", "Bearer [REDACTED]"),
        # Connection strings
        (r"(Server|Data Source)=.+?(;|$)", "[REDACTED_CONN_STRING]"),
        # Azure secrets
        (r'(client_secret|azure_secret)["\s:=]+[^\s,}"\']+', "[REDACTED_AZURE_SECRET]"),
        # Private keys
        (r"-----BEGIN .* PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
        # ADO PAT tokens (52 lowercase alphanumeric)
        (r"\b[a-z0-9]{52}\b", "[REDACTED_PAT]"),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def is_write_operation(tool_name: str) -> bool:
    """Check if a tool is a write operation.

    Args:
        tool_name: Name of the tool

    Returns:
        True if this is a write operation, False otherwise
    """
    # MCP Azure DevOps write operations
    mcp_write_ops = [
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

    if tool_name.startswith("mcp__azure-devops__"):
        operation = tool_name.replace("mcp__azure-devops__", "")
        return operation in mcp_write_ops

    # Built-in write tools
    if tool_name in ["Write", "Edit", "Bash"]:
        return True

    return False


def create_session_logger(
    session_id: str | None = None,
    log_level: str = "INFO",
    enabled: bool = True,
) -> logging.Logger | None:
    """Create and configure a session logger.

    Args:
        session_id: Unique session identifier (auto-generated if None)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enabled: Whether logging is enabled

    Returns:
        Configured logger instance, or None if disabled
    """
    global _session_logger, _session_id, _session_start_time, _session_ended

    # Check if logging should be disabled
    if not enabled or is_docker_environment():
        _session_logger = None
        return None

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    _session_id = session_id
    _session_start_time = datetime.now()
    _session_ended = False  # Reset guard for new session

    # Create log directory
    log_dir = get_log_directory()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    timestamp = _session_start_time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"session_{timestamp}.log"

    # Create logger
    logger = logging.getLogger(f"triagent.session.{session_id}")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB per file
        backupCount=0,  # Keep all files (no auto-delete)
        encoding="utf-8",
    )

    # Standard text formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create symlink to latest log
    latest_link = log_dir / "latest.log"
    try:
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(log_file)
    except OSError:
        pass  # Symlinks may not be supported on all platforms

    _session_logger = logger
    return logger


def get_session_logger() -> logging.Logger | None:
    """Get the current session logger.

    Returns:
        Current session logger, or None if not initialized
    """
    return _session_logger


def log_session_start(cwd: str | None = None) -> None:
    """Log session start event."""
    if _session_logger and _session_id:
        cwd = cwd or os.getcwd()
        _session_logger.info(f"SESSION_START session_id={_session_id} cwd={cwd}")


def log_session_end() -> None:
    """Log session end event with duration.

    Uses a guard to prevent duplicate SESSION_END logs when called
    from both manual code and SDK Stop hook.
    """
    global _session_ended
    if _session_logger and _session_id and _session_start_time and not _session_ended:
        _session_ended = True
        duration_ms = int((datetime.now() - _session_start_time).total_seconds() * 1000)
        _session_logger.info(
            f"SESSION_END session_id={_session_id} duration_ms={duration_ms}"
        )


# SDK Hook Callbacks


async def pre_tool_use_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Log tool call before execution.

    This is an SDK hook callback that logs tool invocations.

    Args:
        input_data: Hook input data containing tool_name, tool_input, etc.
        tool_use_id: Unique identifier for this tool use
        context: Hook context (currently unused)

    Returns:
        Empty dict to allow the operation (just logging, no blocking)
    """
    if _session_logger:
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = redact_sensitive_data(input_data.get("tool_input", {}))
        is_write = is_write_operation(tool_name)

        _session_logger.info(
            f"PRE_TOOL_USE tool={tool_name} tool_use_id={tool_use_id} "
            f"is_write={is_write} input={tool_input}"
        )

    return {}  # Don't block, just log


async def post_tool_use_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Log tool result after execution.

    This is an SDK hook callback that logs tool results.

    Args:
        input_data: Hook input data containing tool_name, tool_response, etc.
        tool_use_id: Unique identifier for this tool use
        context: Hook context (currently unused)

    Returns:
        Empty dict to allow the operation (just logging, no blocking)
    """
    if _session_logger:
        tool_name = input_data.get("tool_name", "unknown")
        tool_response = input_data.get("tool_response", "")

        # Truncate long responses
        response_str = str(tool_response)
        if len(response_str) > 500:
            response_str = response_str[:500] + "...[truncated]"

        response = redact_sensitive_data(response_str)

        _session_logger.info(
            f"POST_TOOL_USE tool={tool_name} tool_use_id={tool_use_id} "
            f"response={response}"
        )

    return {}


async def user_prompt_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Log user prompt.

    This is an SDK hook callback that logs user prompts.

    Args:
        input_data: Hook input data containing prompt
        tool_use_id: Unique identifier (usually None for prompts)
        context: Hook context (currently unused)

    Returns:
        Empty dict to allow the operation (just logging, no blocking)
    """
    if _session_logger:
        prompt = input_data.get("prompt", "")
        prompt = redact_sensitive_data(prompt)

        # Truncate long prompts
        if len(prompt) > 200:
            prompt = prompt[:200] + "...[truncated]"

        _session_logger.info(f'USER_PROMPT prompt="{prompt}"')

    return {}


async def session_stop_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Log session stop event.

    This is an SDK hook callback that logs session end.

    Args:
        input_data: Hook input data
        tool_use_id: Unique identifier (usually None for stop)
        context: Hook context (currently unused)

    Returns:
        Empty dict to allow the operation (just logging, no blocking)
    """
    log_session_end()
    return {}


def log_permission_decision(
    tool_name: str,
    decision: str,
    reason: str | None = None,
) -> None:
    """Log a permission decision.

    Args:
        tool_name: Name of the tool
        decision: Decision made (allow/deny)
        reason: Optional reason for the decision
    """
    if _session_logger:
        msg = f"PERMISSION_DECISION tool={tool_name} decision={decision}"
        if reason:
            msg += f' reason="{reason}"'
        _session_logger.info(msg)


# Subagent Logging Functions


def log_subagent_start(
    subagent_name: str,
    description: str,
    trigger: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Log when a subagent is invoked.

    Args:
        subagent_name: The subagent identifier (e.g., "csharp-code-reviewer")
        description: Human-readable description (e.g., "C# Code Reviewer")
        trigger: What triggered the selection (e.g., "PR #123 file extensions")
        context: Additional context (files analyzed, etc.)
    """
    if _session_logger:
        ctx_str = ""
        if context:
            ctx_str = " " + " ".join(f"{k}={v}" for k, v in context.items())
        _session_logger.info(
            f'SUBAGENT_START subagent={subagent_name} '
            f'description="{description}" trigger="{trigger}"{ctx_str}'
        )


def log_subagent_complete(
    subagent_name: str,
    duration_ms: int,
    result_summary: str,
) -> None:
    """Log when a subagent completes.

    Args:
        subagent_name: The subagent identifier
        duration_ms: Duration of the subagent execution in milliseconds
        result_summary: Brief summary of the result
    """
    if _session_logger:
        _session_logger.info(
            f'SUBAGENT_COMPLETE subagent={subagent_name} '
            f'duration_ms={duration_ms} result="{result_summary}"'
        )


def log_subagent_error(
    subagent_name: str,
    error: str,
) -> None:
    """Log when a subagent encounters an error.

    Args:
        subagent_name: The subagent identifier
        error: Error message
    """
    if _session_logger:
        _session_logger.error(
            f'SUBAGENT_ERROR subagent={subagent_name} error="{error}"'
        )


def log_subagent_detected(
    extensions: list[str],
    matched_subagent: str,
    confidence: str = "high",
) -> None:
    """Log language/type detection for auto-routing.

    Args:
        extensions: File extensions that were analyzed
        matched_subagent: The subagent selected based on detection
        confidence: Detection confidence level
    """
    if _session_logger:
        _session_logger.debug(
            f'SUBAGENT_DETECTED extensions={extensions} '
            f'matched_subagent={matched_subagent} confidence={confidence}'
        )
