"""Help command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def help_command(
    console: Console,
    sdk_commands: list[str] | None = None,
) -> None:
    """Display help information with triagent and SDK commands.

    Args:
        console: Rich console for output
        sdk_commands: Available SDK slash commands (from get_server_info)
    """
    # Section 1: Triagent CLI Commands
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
        ("/persona", "Show current persona and available options"),
        ("/persona <name>", "Switch persona (developer/support)"),
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
    console.print(
        Panel(table, title="[bold cyan]Triagent Commands[/bold cyan]", border_style="cyan")
    )

    # Section 2: Claude Code SDK Commands
    if sdk_commands:
        sdk_table = Table(show_header=True, header_style="bold magenta")
        sdk_table.add_column("Command", style="magenta")
        sdk_table.add_column("Description")

        for cmd in sdk_commands:
            # Handle both dict and string formats
            if isinstance(cmd, dict):
                # SDK returns commands as dicts with name/description
                cmd_name = cmd.get("name", cmd.get("command", str(cmd)))
                cmd_desc = cmd.get("description", "Claude Code SDK command")
            else:
                cmd_name = str(cmd)
                cmd_desc = "Claude Code SDK command"

            # Ensure command has leading /
            if not cmd_name.startswith("/"):
                cmd_name = f"/{cmd_name}"

            sdk_table.add_row(cmd_name, cmd_desc)

        console.print()
        console.print(
            Panel(
                sdk_table,
                title="[bold magenta]Claude Code Commands[/bold magenta]",
                border_style="magenta",
            )
        )
    else:
        console.print()
        console.print("[dim]SDK commands will be shown after connection.[/dim]")

    console.print()
