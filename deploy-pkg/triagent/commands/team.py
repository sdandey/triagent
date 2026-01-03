"""Team command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from triagent.config import ConfigManager
from triagent.teams.config import TEAM_CONFIG, get_team_config


def team_command(
    console: Console,
    config_manager: ConfigManager,
    team_name: str | None = None,
) -> None:
    """Show or switch team.

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        team_name: Team to switch to (None to show current)
    """
    config = config_manager.load_config()

    if team_name is None:
        # Show current team
        team_config = get_team_config(config.team)
        if team_config:
            console.print()
            console.print(
                Panel(
                    f"[bold]Team:[/bold] {team_config.display_name}\n"
                    f"[bold]ADO Project:[/bold] {team_config.ado_project}\n"
                    f"[bold]ADO Organization:[/bold] {team_config.ado_organization}",
                    title="[bold cyan]Current Team[/bold cyan]",
                    border_style="cyan",
                )
            )
        else:
            console.print(f"[yellow]Current team '{config.team}' not found in config[/yellow]")

        # Show available teams
        console.print()
        console.print("[bold]Available teams:[/bold]")
        for name, tc in TEAM_CONFIG.items():
            marker = " [green](current)[/green]" if name == config.team else ""
            console.print(f"  - {name}: {tc.display_name}{marker}")
        console.print()
        return

    # Switch team
    team_name = team_name.lower().strip()
    new_team = get_team_config(team_name)

    if new_team is None:
        console.print(f"[red]Error:[/red] Unknown team '{team_name}'")
        console.print("[bold]Available teams:[/bold]")
        for name in TEAM_CONFIG:
            console.print(f"  - {name}")
        return

    # Update config
    config.team = team_name
    config.ado_project = new_team.ado_project
    config.ado_organization = new_team.ado_organization
    config_manager.save_config(config)

    console.print()
    console.print(
        Panel(
            f"[bold green]Switched to team: {new_team.display_name}[/bold green]\n"
            f"ADO Project: {new_team.ado_project}",
            border_style="green",
        )
    )
    console.print()
