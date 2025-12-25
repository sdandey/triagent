"""Help command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def help_command(console: Console) -> None:
    """Display help information.

    Args:
        console: Rich console for output
    """
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Command", style="green")
    table.add_column("Description")

    commands = [
        ("/init", "Run initial setup wizard"),
        ("/help", "Show this help message"),
        ("/config", "View current configuration"),
        ("/config show", "Display all config values"),
        ("/config set <key> <value>", "Set a config value"),
        ("/team", "Show current team"),
        ("/team <name>", "Switch team (levvia/omnia/omnia-data)"),
        ("/team-report <team>", "Generate team iteration status report"),
        ("/team-report <team> --save", "Generate and save report to docs/"),
        ("/confirm", "Show write confirmation status"),
        ("/confirm on", "Enable confirmations for ADO/Git writes"),
        ("/confirm off", "Disable confirmations (auto-approve)"),
        ("/versions", "Show installed and pinned tool versions"),
        ("/clear", "Clear conversation history"),
        ("/exit, /quit", "Exit Triagent"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print()
    console.print(Panel(table, title="[bold]Available Commands[/bold]", border_style="blue"))
    console.print()
