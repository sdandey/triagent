"""Tool definitions and executors for Triagent CLI."""

from triagent.tools.azure_cli import (
    AZURE_CLI_TOOL,
    execute_azure_cli,
    is_write_operation,
)
from triagent.tools.error_recovery import (
    ErrorContext,
    ErrorType,
    RetryConfig,
    classify_http_error,
    extract_command_base,
    generate_recovery_instruction,
    get_cli_help,
    truncate_aggressively,
)

__all__ = [
    # Azure CLI tool
    "AZURE_CLI_TOOL",
    "execute_azure_cli",
    "is_write_operation",
    # Error recovery
    "ErrorContext",
    "ErrorType",
    "RetryConfig",
    "classify_http_error",
    "extract_command_base",
    "generate_recovery_instruction",
    "get_cli_help",
    "truncate_aggressively",
]
