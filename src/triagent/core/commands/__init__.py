"""Command registry for unified slash commands.

This module provides a unified command system that works across CLI and Web interfaces.
Commands are registered here and can be executed through either interface using the
same business logic with different UI adapters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from triagent.core.commands.base import (
    Command,
    CommandContext,
    CommandResult,
    OutputContext,
    PromptContext,
)

if TYPE_CHECKING:
    pass

# Command registry - maps command names to command classes
_COMMANDS: dict[str, type[Command]] = {}


def register_command(cmd_class: type[Command]) -> type[Command]:
    """Decorator to register a command class.

    Args:
        cmd_class: The command class to register.

    Returns:
        The same command class (for decorator chaining).
    """
    _COMMANDS[cmd_class.name] = cmd_class
    for alias in cmd_class.aliases:
        _COMMANDS[alias] = cmd_class
    return cmd_class


def get_command(name: str) -> type[Command] | None:
    """Get a command class by name.

    Args:
        name: Command name (without leading slash).

    Returns:
        Command class if found, None otherwise.
    """
    return _COMMANDS.get(name.lower())


def get_all_commands() -> dict[str, type[Command]]:
    """Get all registered commands (excluding aliases).

    Returns:
        Dictionary mapping command names to command classes.
    """
    seen = set()
    result = {}
    for name, cmd_class in _COMMANDS.items():
        if cmd_class not in seen:
            result[cmd_class.name] = cmd_class
            seen.add(cmd_class)
    return result


async def execute_command(name: str, ctx: CommandContext) -> CommandResult:
    """Execute a command by name.

    Args:
        name: Command name (without leading slash).
        ctx: Command execution context.

    Returns:
        Result of command execution.
    """
    cmd_class = get_command(name)
    if cmd_class is None:
        return CommandResult(
            success=False,
            message=f"Unknown command: /{name}. Use /help to see available commands.",
        )

    cmd = cmd_class()
    return await cmd.execute(ctx)


# Import commands to trigger registration
# These imports must be at the end to avoid circular imports
from triagent.core.commands.help import HelpCommand  # noqa: E402, F401
from triagent.core.commands.init import InitCommand  # noqa: E402, F401
from triagent.core.commands.team import TeamCommand  # noqa: E402, F401
from triagent.core.commands.persona import PersonaCommand  # noqa: E402, F401
from triagent.core.commands.config import ConfigCommand  # noqa: E402, F401
from triagent.core.commands.confirm import ConfirmCommand  # noqa: E402, F401
from triagent.core.commands.versions import VersionsCommand  # noqa: E402, F401
from triagent.core.commands.clear import ClearCommand  # noqa: E402, F401

__all__ = [
    "Command",
    "CommandContext",
    "CommandResult",
    "OutputContext",
    "PromptContext",
    "register_command",
    "get_command",
    "get_all_commands",
    "execute_command",
]
