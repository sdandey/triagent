"""Main CLI for Triagent - Interactive chat interface."""

from __future__ import annotations

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel

from triagent import __version__
from triagent.agent import AgentSession, create_agent_session
from triagent.commands.config import config_command
from triagent.commands.help import help_command
from triagent.commands.init import confirm_prompt, init_command
from triagent.commands.team import team_command
from triagent.config import ConfigManager, get_config_manager
from triagent.teams.config import get_team_config

app = typer.Typer(
    name="triagent",
    help="Claude-powered CLI for Azure DevOps automation",
    add_completion=False,
)


def create_header(config_manager: ConfigManager) -> str:
    """Create the header panel content."""
    config = config_manager.load_config()
    team_config = get_team_config(config.team)
    team_name = team_config.display_name if team_config else config.team

    return f"[bold cyan]Triagent CLI v{__version__}[/bold cyan] | Team: {team_name} | Project: {config.ado_project}"


def parse_slash_command(user_input: str) -> tuple[str, list[str]]:
    """Parse a slash command from user input.

    Args:
        user_input: Raw user input

    Returns:
        Tuple of (command_name, args)
    """
    parts = user_input.strip().split()
    if not parts or not parts[0].startswith("/"):
        return "", []

    command = parts[0][1:].lower()  # Remove leading /
    args = parts[1:] if len(parts) > 1 else []

    return command, args


def handle_slash_command(
    command: str,
    args: list[str],
    console: Console,
    config_manager: ConfigManager,
    agent: AgentSession | None,
) -> tuple[bool, AgentSession | None]:
    """Handle a slash command.

    Args:
        command: Command name (without /)
        args: Command arguments
        console: Rich console
        config_manager: Config manager
        agent: Current agent session

    Returns:
        Tuple of (should_continue, updated_agent)
    """
    if command in ("exit", "quit", "q"):
        console.print("[dim]Goodbye![/dim]")
        return False, agent

    if command == "help":
        help_command(console)
        return True, agent

    if command == "init":
        if init_command(console, config_manager):
            # Recreate agent with new config
            agent = create_agent_session(config_manager)
        return True, agent

    if command == "config":
        config_command(console, config_manager, args if args else None)
        return True, agent

    if command == "team":
        team_name = args[0] if args else None
        team_command(console, config_manager, team_name)
        if team_name:
            # Recreate agent with new team
            agent = create_agent_session(config_manager)
        return True, agent

    if command == "clear":
        if agent:
            agent.clear_history()
        console.print("[dim]Conversation cleared[/dim]")
        return True, agent

    # Unknown command
    console.print(f"[red]Unknown command: /{command}[/red]")
    console.print("[dim]Type /help for available commands[/dim]")
    return True, agent


def interactive_loop(
    console: Console,
    config_manager: ConfigManager,
) -> None:
    """Run the interactive chat loop.

    Args:
        console: Rich console
        config_manager: Config manager
    """
    # Show header
    console.print()
    console.print(Panel(create_header(config_manager), border_style="cyan"))
    console.print()

    # Check if setup is needed
    if not config_manager.config_exists():
        console.print("[yellow]No configuration found. Running setup wizard...[/yellow]")
        console.print()
        if not init_command(console, config_manager):
            console.print("[red]Setup failed. Exiting.[/red]")
            return

    # Create agent session
    agent = create_agent_session(config_manager)

    # Set up prompt session with history
    history_file = config_manager.history_dir / "prompt_history"
    config_manager.ensure_dirs()
    session: PromptSession[str] = PromptSession(history=FileHistory(str(history_file)))

    console.print("[dim]Type your message or use /help for commands[/dim]")
    console.print()

    while True:
        try:
            # Get user input
            user_input = session.prompt("You: ").strip()

            if not user_input:
                continue

            # Check for slash command
            if user_input.startswith("/"):
                command, args = parse_slash_command(user_input)
                should_continue, agent = handle_slash_command(
                    command, args, console, config_manager, agent
                )
                if not should_continue:
                    break
                continue

            # Send message to agent with tool support
            console.print()

            def on_tool_start(tool_name: str, command: str) -> None:
                """Show tool execution starting."""
                console.print(f"[dim]→ Executing: {command}[/dim]")

            def on_tool_end(tool_name: str, success: bool) -> None:
                """Show tool execution result."""
                if success:
                    console.print("[green]✓[/green] Command completed")
                else:
                    console.print("[red]✗[/red] Command failed")

            def confirm_write(command: str) -> bool:
                """Ask user to confirm write operations."""
                console.print(f"[yellow]→ Write operation: {command}[/yellow]")
                return confirm_prompt("Proceed?", default=True)

            console.print("[bold cyan]Triagent:[/bold cyan]", end=" ")

            # Use tool-enabled message sending
            response_text = ""
            try:
                for chunk in agent.send_message_with_tools(
                    user_input,
                    confirm_callback=confirm_write,
                    on_tool_start=on_tool_start,
                    on_tool_end=on_tool_end,
                ):
                    console.print(chunk, end="")
                    response_text += chunk
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
                continue

            console.print()  # New line after response
            console.print()

        except KeyboardInterrupt:
            console.print()
            console.print("[dim]Use /exit to quit[/dim]")
        except EOFError:
            console.print()
            console.print("[dim]Goodbye![/dim]")
            break


@app.command()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Enable verbose output"
    ),
) -> None:
    """Triagent - Claude-powered CLI for Azure DevOps automation.

    Start an interactive chat session or run with slash commands.
    """
    console = Console()

    if version:
        console.print(f"Triagent CLI v{__version__}")
        raise typer.Exit()

    config_manager = get_config_manager()

    if verbose:
        config = config_manager.load_config()
        config.verbose = True
        config_manager.save_config(config)

    try:
        interactive_loop(console, config_manager)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
