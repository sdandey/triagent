"""CLI output adapter using Rich for terminal rendering.

This adapter implements the OutputContext protocol for CLI environments,
using Rich for styled panels, tables, and markdown rendering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from rich.console import Console


class CLIOutputAdapter:
    """Rich console output implementation for CLI.

    Implements the OutputContext protocol for terminal-based output rendering.
    """

    def __init__(self, console: Console, markdown_enabled: bool = True):
        """Initialize the CLI output adapter.

        Args:
            console: Rich Console instance for output.
            markdown_enabled: If True, render markdown content.
        """
        self.console = console
        self.markdown_enabled = markdown_enabled

    async def write_text(self, text: str) -> None:
        """Write plain text output.

        Args:
            text: The text to display.
        """
        if self.markdown_enabled and any(
            marker in text for marker in ["**", "*", "`", "#", "-", "["]
        ):
            # Contains markdown-like formatting, render as markdown
            self.console.print(Markdown(text))
        else:
            self.console.print(text)

    async def write_markdown(self, markdown: str) -> None:
        """Write markdown-formatted output.

        Args:
            markdown: Markdown content to render.
        """
        self.console.print(Markdown(markdown))

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
        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
        )

        for header in headers:
            table.add_column(header)

        for row in rows:
            # Convert all values to strings and handle styling
            styled_row = []
            for cell in row:
                if cell in ("OK", "✓"):
                    styled_row.append(f"[green]{cell}[/green]")
                elif cell in ("Not found", "Missing", "✗"):
                    styled_row.append(f"[yellow]{cell}[/yellow]")
                elif cell in ("Error", "Failed"):
                    styled_row.append(f"[red]{cell}[/red]")
                else:
                    styled_row.append(str(cell))
            table.add_row(*styled_row)

        self.console.print()
        self.console.print(table)
        self.console.print()

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
        style_map = {
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        border_style = style_map.get(style, "white")

        # Render markdown content
        if self.markdown_enabled:
            rendered_content = Markdown(content)
        else:
            rendered_content = content

        self.console.print()
        self.console.print(
            Panel(
                rendered_content,
                title=title,
                border_style=border_style,
                padding=(1, 2),
            )
        )
        self.console.print()

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
        if title:
            self.console.print()
            self.console.print(f"[bold]{title}[/bold]")
            self.console.print("-" * 40)

        for key, value in items:
            # Style certain values
            if value in ("enabled", "true", "yes"):
                styled_value = f"[green]{value}[/green]"
            elif value in ("disabled", "false", "no", "not set"):
                styled_value = f"[dim]{value}[/dim]"
            elif value.startswith("***"):
                styled_value = f"[dim]{value}[/dim]"
            else:
                styled_value = value

            self.console.print(f"  [cyan]{key}:[/cyan] {styled_value}")

        self.console.print()
