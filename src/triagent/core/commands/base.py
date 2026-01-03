"""Base classes and protocols for unified commands.

This module defines the core abstractions that enable commands to work
across both CLI and Web interfaces:

- PromptContext: Protocol for user input (selection, text, confirmation)
- OutputContext: Protocol for user output (text, tables, panels)
- CommandContext: Bundles prompt, output, and config for command execution
- CommandResult: Standardized command execution result
- Command: Abstract base class for all commands
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from triagent.config import ConfigManager


@runtime_checkable
class PromptContext(Protocol):
    """Protocol for UI-agnostic user prompting.

    This protocol defines the interface for collecting user input.
    Implementations exist for both CLI (Rich-based) and Web (Chainlit-based).
    """

    async def ask_selection(
        self,
        prompt: str,
        options: list[tuple[str, str]],
        default: int = 0,
    ) -> str | None:
        """Ask user to select from a list of options.

        Args:
            prompt: The question to display.
            options: List of (value, display_label) tuples.
            default: Index of default option (0-based).

        Returns:
            Selected value, or None if cancelled.
        """
        ...

    async def ask_text(
        self,
        prompt: str,
        secret: bool = False,
        default: str | None = None,
    ) -> str | None:
        """Ask user for text input.

        Args:
            prompt: The question to display.
            secret: If True, hide input (for passwords/tokens).
            default: Default value if user provides empty input.

        Returns:
            User input, or None if cancelled.
        """
        ...

    async def ask_confirmation(
        self,
        message: str,
        default: bool = True,
    ) -> bool:
        """Ask user for yes/no confirmation.

        Args:
            message: The confirmation message.
            default: Default response if user just presses Enter.

        Returns:
            True if confirmed, False otherwise.
        """
        ...

    async def display_message(
        self,
        message: str,
        style: str = "info",
    ) -> None:
        """Display a styled message to the user.

        Args:
            message: The message to display.
            style: One of "info", "success", "warning", "error".
        """
        ...

    async def display_progress(
        self,
        message: str,
    ) -> None:
        """Display a progress/loading message.

        Args:
            message: The progress message (e.g., "Loading...").
        """
        ...


@runtime_checkable
class OutputContext(Protocol):
    """Protocol for UI-agnostic output rendering.

    This protocol defines the interface for displaying output to users.
    Implementations exist for both CLI (Rich-based) and Web (Chainlit-based).
    """

    async def write_text(self, text: str) -> None:
        """Write plain text output.

        Args:
            text: The text to display.
        """
        ...

    async def write_markdown(self, markdown: str) -> None:
        """Write markdown-formatted output.

        Args:
            markdown: Markdown content to render.
        """
        ...

    async def show_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        title: str | None = None,
    ) -> None:
        """Display a table.

        Args:
            headers: Column headers.
            rows: Table rows (list of lists).
            title: Optional table title.
        """
        ...

    async def show_panel(
        self,
        content: str,
        title: str | None = None,
        style: str = "info",
    ) -> None:
        """Display a panel/card with content.

        Args:
            content: Panel content (can be markdown).
            title: Optional panel title.
            style: One of "info", "success", "warning", "error".
        """
        ...

    async def show_key_value(
        self,
        items: list[tuple[str, str]],
        title: str | None = None,
    ) -> None:
        """Display key-value pairs.

        Args:
            items: List of (key, value) tuples.
            title: Optional section title.
        """
        ...


@dataclass
class CommandResult:
    """Result of executing a command.

    Attributes:
        success: Whether the command completed successfully.
        message: Optional message to display to user.
        data: Optional structured data from command execution.
        requires_restart: If True, SDK client needs to be restarted.
        should_exit: If True, the application should exit.
        should_clear: If True, conversation history should be cleared.
    """

    success: bool
    message: str | None = None
    data: dict[str, Any] | None = None
    requires_restart: bool = False
    should_exit: bool = False
    should_clear: bool = False


@dataclass
class CommandContext:
    """Context passed to command handlers.

    This bundles all dependencies needed for command execution,
    allowing commands to work with either CLI or Web adapters.

    Attributes:
        config_manager: Access to triagent configuration.
        prompt: Interface for user prompts.
        output: Interface for displaying output.
        args: Command arguments (words after the command name).
        environment: Either "cli" or "web".
        session_data: Optional session-specific data.
    """

    config_manager: ConfigManager
    prompt: PromptContext
    output: OutputContext
    args: list[str] = field(default_factory=list)
    environment: str = "cli"
    session_data: dict[str, Any] = field(default_factory=dict)


class Command(ABC):
    """Abstract base class for all commands.

    Subclasses must implement the execute() method and set class attributes
    for name, description, and optionally aliases.

    Example:
        @register_command
        class MyCommand(Command):
            name = "mycommand"
            description = "Does something useful"
            aliases = ["mc", "my"]

            async def execute(self, ctx: CommandContext) -> CommandResult:
                await ctx.output.write_text("Hello!")
                return CommandResult(success=True)
    """

    # Command name (without leading slash)
    name: str = ""

    # Short description for help text
    description: str = ""

    # Alternative names for the command
    aliases: list[str] = []

    # Whether this command is visible in help
    hidden: bool = False

    @abstractmethod
    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute the command.

        Args:
            ctx: Command execution context with prompt, output, and config.

        Returns:
            CommandResult indicating success/failure and any side effects.
        """
        ...

    def get_usage(self) -> str:
        """Get usage string for help text.

        Returns:
            Usage string like "/command [args]".
        """
        return f"/{self.name}"

    def get_help(self) -> str:
        """Get detailed help text for the command.

        Returns:
            Multi-line help string.
        """
        lines = [f"**/{self.name}** - {self.description}"]
        if self.aliases:
            lines.append(f"Aliases: {', '.join('/' + a for a in self.aliases)}")
        return "\n".join(lines)
