"""CLI prompt adapter using Rich for terminal prompts.

This adapter implements the PromptContext protocol for CLI environments,
using Rich for styled prompts and async input handling.
"""

from __future__ import annotations

import asyncio
import getpass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


class CLIPromptAdapter:
    """Rich console prompt implementation for CLI.

    Implements the PromptContext protocol for terminal-based user interaction.
    """

    def __init__(self, console: Console):
        """Initialize the CLI prompt adapter.

        Args:
            console: Rich Console instance for output.
        """
        self.console = console

    async def _async_input(self, prompt: str = "") -> str:
        """Non-blocking input using executor.

        Args:
            prompt: Prompt string to display.

        Returns:
            User input string.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)

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
        self.console.print()
        self.console.print(prompt)
        self.console.print()

        for i, (value, display) in enumerate(options, 1):
            marker = "[cyan]>[/cyan]" if i - 1 == default else " "
            self.console.print(f"  {marker} {i}. {display}")

        self.console.print()

        while True:
            try:
                choice = await self._async_input(f"Enter number (1-{len(options)}): ")
                choice = choice.strip()

                # Handle empty input (use default)
                if not choice:
                    return options[default][0]

                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx][0]

                self.console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")
            except (KeyboardInterrupt, EOFError):
                return None

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
        try:
            if default:
                display_prompt = f"{prompt} [{default}]: "
            else:
                display_prompt = f"{prompt}: "

            if secret:
                # getpass doesn't work well with asyncio, use sync
                loop = asyncio.get_event_loop()
                value = await loop.run_in_executor(
                    None, getpass.getpass, display_prompt
                )
            else:
                value = await self._async_input(display_prompt)

            value = value.strip()
            return value if value else default

        except (KeyboardInterrupt, EOFError):
            return None

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
        try:
            suffix = " [Y/n]: " if default else " [y/N]: "
            response = await self._async_input(message + suffix)
            response = response.strip().lower()

            if not response:
                return default

            return response in ("y", "yes", "true", "1")

        except (KeyboardInterrupt, EOFError):
            return False

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
        style_map = {
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        color = style_map.get(style, "white")

        prefix_map = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
        }
        prefix = prefix_map.get(style, "•")

        self.console.print(f"[{color}]{prefix}[/{color}] {message}")

    async def display_progress(
        self,
        message: str,
    ) -> None:
        """Display a progress/loading message.

        Args:
            message: The progress message (e.g., "Loading...").
        """
        self.console.print(f"[dim]{message}...[/dim]")
