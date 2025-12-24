"""Config command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from triagent.config import ConfigManager


def config_command(
    console: Console,
    config_manager: ConfigManager,
    args: list[str] | None = None,
) -> None:
    """Show or modify configuration.

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        args: Command arguments (None, ["show"], or ["set", key, value])
    """
    if args is None or len(args) == 0 or args[0] == "show":
        _show_config(console, config_manager)
        return

    if args[0] == "set" and len(args) >= 3:
        key = args[1]
        value = " ".join(args[2:])
        _set_config(console, config_manager, key, value)
        return

    console.print("[red]Error:[/red] Invalid config command")
    console.print("Usage:")
    console.print("  /config         - Show current configuration")
    console.print("  /config show    - Show current configuration")
    console.print("  /config set <key> <value> - Set a config value")


def _show_config(console: Console, config_manager: ConfigManager) -> None:
    """Display current configuration."""
    config = config_manager.load_config()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="green")
    table.add_column("Value")

    for key, value in config.to_dict().items():
        display_value = str(value)
        if isinstance(value, bool):
            display_value = "[green]Yes[/green]" if value else "[red]No[/red]"
        elif not value:
            display_value = "[dim]Not set[/dim]"
        table.add_row(key, display_value)

    console.print()
    console.print(Panel(table, title="[bold]Configuration[/bold]", border_style="blue"))
    console.print()
    console.print(f"[dim]Config file: {config_manager.config_file}[/dim]")
    console.print()


def _set_config(
    console: Console,
    config_manager: ConfigManager,
    key: str,
    value: str,
) -> None:
    """Set a config value."""
    config = config_manager.load_config()

    if not hasattr(config, key):
        console.print(f"[red]Error:[/red] Unknown config key '{key}'")
        console.print("[bold]Available keys:[/bold]")
        for k in config.to_dict():
            console.print(f"  - {k}")
        return

    # Handle type conversion
    current_value = getattr(config, key)
    try:
        if isinstance(current_value, bool):
            parsed_value = value.lower() in ("true", "yes", "1", "on")
        elif isinstance(current_value, int):
            parsed_value = int(value)
        else:
            parsed_value = value

        setattr(config, key, parsed_value)
        config_manager.save_config(config)

        console.print(f"[green]Updated:[/green] {key} = {parsed_value}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] Invalid value for '{key}': {e}")
