"""Persona command for Triagent CLI.

This command allows users to view and switch personas at runtime.
Personas determine which skills and subagents are loaded for the session.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from triagent.config import ConfigManager
from triagent.skills import get_available_personas


def persona_command(
    console: Console,
    config_manager: ConfigManager,
    persona_name: str | None = None,
) -> bool:
    """Show current persona or switch to a different one.

    Usage:
        /persona           - Show current persona and available options
        /persona developer - Switch to developer persona
        /persona support   - Switch to support persona

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        persona_name: Optional persona name to switch to

    Returns:
        True if persona was changed (SDK restart needed), False otherwise
    """
    config = config_manager.load_config()
    personas = get_available_personas(config.team)

    if not personas:
        console.print("[dim]No personas defined for this team.[/dim]")
        return False

    # Get current persona display name
    current_display = config.persona.title()
    for p in personas:
        if p.name == config.persona:
            current_display = p.display_name
            break

    if persona_name is None:
        # Show current persona and available options
        console.print()
        console.print(f"[bold]Current Persona:[/bold] {current_display}")
        console.print()
        console.print("[bold]Available Personas:[/bold]")
        console.print()

        for persona in personas:
            current = " [green](current)[/green]" if persona.name == config.persona else ""
            console.print(f"  • {persona.display_name} - {persona.description}{current}")

        console.print()
        console.print("[dim]Usage: /persona <name> to switch (e.g., /persona developer)[/dim]")
        console.print()
        return False

    # Switch to specified persona
    persona_name_lower = persona_name.lower().strip()

    # Find matching persona
    matched_persona = None
    for persona in personas:
        if persona.name.lower() == persona_name_lower or persona.display_name.lower() == persona_name_lower:
            matched_persona = persona
            break

    if not matched_persona:
        console.print(f"[red]Unknown persona: {persona_name}[/red]")
        console.print()
        console.print("[bold]Available personas:[/bold]")
        for persona in personas:
            console.print(f"  • {persona.name} - {persona.display_name}")
        console.print()
        return False

    # Check if already using this persona
    if matched_persona.name == config.persona:
        console.print(f"[dim]Already using {matched_persona.display_name} persona.[/dim]")
        return False

    # Switch persona
    old_persona = config.persona
    config.persona = matched_persona.name
    config_manager.save_config(config)

    console.print()
    console.print(
        Panel(
            f"[bold green]Persona Changed[/bold green]\n\n"
            f"[bold]From:[/bold] {old_persona.title()}\n"
            f"[bold]To:[/bold] {matched_persona.display_name}\n\n"
            f"[dim]{matched_persona.description}[/dim]\n\n"
            "[yellow]Reloading skills and subagents...[/yellow]",
            border_style="green",
        )
    )
    console.print()

    return True  # Signal that SDK needs to be restarted
