"""Main CLI for Triagent - Interactive chat interface with async SDK."""

from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass, field
from time import time
from typing import Any

import typer
from claude_agent_sdk import ClaudeSDKClient, CLINotFoundError, ProcessError
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from triagent import __version__

# Claude Code spinner characters
CLAUDE_SPINNER = ["·", "✻", "✽", "✶", "✳", "✢"]

# Whimsical status messages (Claude Code style)
THINKING_MESSAGES = ["Thinking", "Mulling", "Pondering", "Contemplating"]
TOOL_MESSAGES = ["Executing", "Running", "Processing"]


@dataclass
class ActivityTracker:
    """Tracks tool execution activity with Claude Code style spinner."""

    console: Console
    verbose: bool = False
    _live: Live | None = field(default=None, repr=False)
    _spinner_idx: int = field(default=0, repr=False)
    _tool_start_time: float = field(default=0.0, repr=False)
    _current_tool: str = field(default="", repr=False)

    def _get_spinner_char(self) -> str:
        """Get next spinner character."""
        char = CLAUDE_SPINNER[self._spinner_idx % len(CLAUDE_SPINNER)]
        self._spinner_idx += 1
        return char

    def tool_starting(self, tool_name: str, tool_input: dict | None = None) -> None:
        """Called when a tool starts executing."""
        self._tool_start_time = time()
        self._current_tool = tool_name

        # Stop any existing spinner
        if self._live:
            self._live.stop()

        # Show tool info in verbose mode
        if self.verbose and tool_input:
            self.console.print(f"\n[dim]Tool: {tool_name}[/dim]")
            input_str = str(tool_input)[:200]
            if len(str(tool_input)) > 200:
                input_str += "..."
            self.console.print(f"[dim]  Input: {input_str}[/dim]")

        # Start Claude-style spinner
        message = random.choice(TOOL_MESSAGES)
        self._live = Live(
            f"[cyan]{self._get_spinner_char()} {message}...[/cyan]",
            console=self.console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.start()

    def tool_completed(self, tool_name: str, success: bool, result: str = "") -> None:
        """Called when a tool completes."""
        if self._live:
            self._live.stop()
            self._live = None

        duration = time() - self._tool_start_time
        icon = "[green]✓[/green]" if success else "[red]✗[/red]"

        self.console.print(f"{icon} {tool_name} ({duration:.1f}s)")

        if self.verbose and result:
            result_preview = result[:300].replace("\n", " ")
            if len(result) > 300:
                result_preview += "..."
            self.console.print(f"[dim]  Result: {result_preview}[/dim]")

    def thinking(self) -> None:
        """Called when Claude is thinking."""
        if self._live:
            self._live.stop()

        message = random.choice(THINKING_MESSAGES)
        self._live = Live(
            f"[yellow]{self._get_spinner_char()} {message}...[/yellow]",
            console=self.console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop any active spinner."""
        if self._live:
            self._live.stop()
            self._live = None


from triagent.commands.config import config_command
from triagent.commands.help import help_command
from triagent.commands.init import init_command
from triagent.commands.team import team_command
from triagent.config import ConfigManager, get_config_manager
from triagent.sdk_client import create_sdk_client
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


def detect_investigation_request(user_input: str) -> tuple[str, int] | None:
    """Detect if user wants to investigate a defect/incident.

    Args:
        user_input: Raw user input

    Returns:
        Tuple of (work_item_type, work_item_id) or None if not an investigation request
    """
    patterns = [
        r"investigate\s+(defect|incident|bug)\s*#?(\d+)",
        r"look\s+into\s+(defect|incident|bug)\s*#?(\d+)",
        r"analyze\s+(defect|incident|bug)\s*#?(\d+)",
        r"check\s+(defect|incident|bug)\s*#?(\d+)",
        r"debug\s+(defect|incident|bug)\s*#?(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            return (match.group(1), int(match.group(2)))
    return None


def enhance_investigation_prompt(
    user_input: str,
    work_item_type: str,
    work_item_id: int,
) -> str:
    """Enhance the user's investigation request with detailed instructions.

    Args:
        user_input: Original user input
        work_item_type: Type of work item (defect, incident, bug)
        work_item_id: Work item ID

    Returns:
        Enhanced prompt with investigation instructions
    """
    return f"""{user_input}

## Investigation Instructions

You are investigating {work_item_type.capitalize()} #{work_item_id}. Please follow this workflow:

1. **Fetch Work Item Details**: Use the Azure DevOps MCP tools to get the work item:
   - Use `mcp__azure-devops__wit_get_work_item` with id={work_item_id}
   - Get the title, description, state, priority, and assigned to
   - Also fetch comments using `mcp__azure-devops__wit_list_work_item_comments`

2. **Identify Scope**: Ask me to specify:
   - Which microservice or component is affected?
   - What environment should I investigate (DEV, QAS, STG, PRD)?
   - What is the timeframe of the issue?

3. **Read Telemetry Config**: Read the team memory file at:
   `src/triagent/prompts/claude_md/omnia_data.md`
   - Get the Log Analytics Workspace for the environment
   - Find the CloudRoleName for the affected service

4. **Generate Kusto Queries**: Based on the defect details, generate queries for:
   - AppExceptions - search for error patterns
   - AppRequests - look for failed requests
   - AppDependencies - check for dependency failures
   - AppTraces - search for related log messages

5. **Present Findings**: Provide:
   - Summary of the defect
   - Suggested Kusto queries to run
   - Azure Portal link for the Log Analytics workspace
   - Recommended next steps
"""


def handle_slash_command(
    command: str,
    args: list[str],
    console: Console,
    config_manager: ConfigManager,
) -> bool:
    """Handle a slash command synchronously.

    Args:
        command: Command name (without /)
        args: Command arguments
        console: Rich console
        config_manager: Config manager

    Returns:
        True to continue, False to exit
    """
    if command in ("exit", "quit", "q"):
        console.print("[dim]Goodbye![/dim]")
        return False

    if command == "help":
        help_command(console)
        return True

    if command == "init":
        init_command(console, config_manager)
        return True

    if command == "config":
        config_command(console, config_manager, args if args else None)
        return True

    if command == "team":
        team_name = args[0] if args else None
        team_command(console, config_manager, team_name)
        return True

    if command == "clear":
        console.print("[dim]Conversation cleared (new session on next message)[/dim]")
        return True

    # Unknown command
    console.print(f"[red]Unknown command: /{command}[/red]")
    console.print("[dim]Type /help for available commands[/dim]")
    return True


def process_sdk_message(
    msg: Any,
    console: Console,
    tracker: ActivityTracker,
) -> None:
    """Process SDK message with activity tracking.

    Args:
        msg: SDK message (AssistantMessage, ResultMessage, etc.)
        console: Rich console for output
        tracker: Activity tracker for spinner/verbose output
    """
    msg_type = type(msg).__name__

    if msg_type == "AssistantMessage":
        for block in msg.content:
            block_type = type(block).__name__

            if block_type == "TextBlock":
                # Stop any spinner before printing text
                tracker.stop()
                console.print(block.text, end="")

            elif block_type == "ToolUseBlock":
                # Start spinner for tool execution
                tool_input = getattr(block, "input", None)
                tracker.tool_starting(block.name, tool_input)

            elif block_type == "ThinkingBlock":
                # Show thinking spinner
                tracker.thinking()
                if tracker.verbose:
                    thinking_text = getattr(block, "thinking", "")[:100]
                    if len(getattr(block, "thinking", "")) > 100:
                        thinking_text += "..."
                    console.print(f"\n[dim]{thinking_text}[/dim]")

            elif block_type == "ToolResultBlock":
                # Tool completed
                is_error = getattr(block, "is_error", False)
                content = (
                    str(getattr(block, "content", ""))
                    if hasattr(block, "content")
                    else ""
                )
                tracker.tool_completed(
                    tracker._current_tool or "tool",
                    not is_error,
                    content,
                )

    elif msg_type == "ResultMessage":
        # Stop any active spinner
        tracker.stop()

        # Show stats
        if tracker.verbose:
            num_turns = getattr(msg, "num_turns", 0)
            duration_ms = getattr(msg, "duration_ms", 0)
            console.print(
                f"\n[dim]Turns: {num_turns} | Duration: {duration_ms}ms[/dim]", end=""
            )

        if hasattr(msg, "total_cost_usd") and msg.total_cost_usd:
            console.print(f"\n[dim]Cost: ${msg.total_cost_usd:.4f}[/dim]", end="")


async def interactive_loop_async(
    console: Console,
    config_manager: ConfigManager,
) -> None:
    """Run the async interactive chat loop.

    Following the research-agent demo pattern:
    - Uses async with ClaudeSDKClient for session lifecycle
    - Streams responses with async for
    - Keeps entire conversation in one event loop

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
        console.print(
            "[yellow]No configuration found. Running setup wizard...[/yellow]"
        )
        console.print()
        if not init_command(console, config_manager):
            console.print("[red]Setup failed. Exiting.[/red]")
            return

    # Build SDK options
    client_factory = create_sdk_client(config_manager)
    options = client_factory._build_options()

    # Create activity tracker for visual feedback
    config = config_manager.load_config()
    tracker = ActivityTracker(console=console, verbose=config.verbose)

    # Use SDK context manager for session lifecycle
    try:
        async with ClaudeSDKClient(options=options) as client:
            console.print("[dim]Connected to Claude. Type /help for commands[/dim]")
            console.print()

            while True:
                try:
                    # Get user input (sync input() is OK inside async)
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    console.print("[dim]Goodbye![/dim]")
                    break

                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    command, args = parse_slash_command(user_input)
                    should_continue = handle_slash_command(
                        command, args, console, config_manager
                    )
                    if not should_continue:
                        break
                    continue

                # Check for investigation request
                investigation = detect_investigation_request(user_input)
                if investigation:
                    work_item_type, work_item_id = investigation
                    console.print(
                        f"[cyan]Detected investigation request for "
                        f"{work_item_type.capitalize()} #{work_item_id}[/cyan]"
                    )
                    user_input = enhance_investigation_prompt(
                        user_input, work_item_type, work_item_id
                    )

                # Send to Claude
                console.print()
                console.print("[bold cyan]Triagent:[/bold cyan] ", end="")

                await client.query(prompt=user_input)

                # Stream response
                async for msg in client.receive_response():
                    process_sdk_message(msg, console, tracker)

                # Ensure spinner is stopped
                tracker.stop()
                console.print()
                console.print()

    except CLINotFoundError:
        console.print("[red]Error: Claude CLI not installed[/red]")
        console.print(
            "[dim]Install with: npm install -g @anthropic-ai/claude-code[/dim]"
        )
    except ProcessError as e:
        console.print(f"[red]Process error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def async_main(config_manager: ConfigManager) -> None:
    """Async main entry point.

    Args:
        config_manager: Configuration manager
    """
    console = Console()

    try:
        await interactive_loop_async(console, config_manager)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


def interactive_loop_legacy(
    console: Console,
    config_manager: ConfigManager,
) -> None:
    """Legacy sync interactive loop using AgentSession.

    Args:
        console: Rich console
        config_manager: Config manager
    """
    from triagent.agent import create_agent_session

    # Show header with yellow border for legacy mode
    console.print()
    console.print(Panel(create_header(config_manager), border_style="yellow"))
    console.print("[yellow]Running in legacy mode[/yellow]")
    console.print()

    # Check if setup is needed
    if not config_manager.config_exists():
        console.print(
            "[yellow]No configuration found. Running setup wizard...[/yellow]"
        )
        console.print()
        if not init_command(console, config_manager):
            console.print("[red]Setup failed. Exiting.[/red]")
            return

    try:
        agent = create_agent_session(config_manager)
        console.print("[dim]Connected (legacy). Type /help for commands[/dim]")
        console.print()

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                console.print("[dim]Goodbye![/dim]")
                break

            if not user_input:
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                command, args = parse_slash_command(user_input)
                should_continue = handle_slash_command(
                    command, args, console, config_manager
                )
                if not should_continue:
                    break
                continue

            # Check for investigation request
            investigation = detect_investigation_request(user_input)
            if investigation:
                work_item_type, work_item_id = investigation
                console.print(
                    f"[cyan]Detected investigation request for "
                    f"{work_item_type.capitalize()} #{work_item_id}[/cyan]"
                )
                user_input = enhance_investigation_prompt(
                    user_input, work_item_type, work_item_id
                )

            console.print()
            console.print("[bold yellow]Triagent (legacy):[/bold yellow] ", end="")

            # Create activity tracker for visual feedback
            config = config_manager.load_config()
            tracker = ActivityTracker(console=console, verbose=config.verbose)

            # Define callbacks that use the tracker
            def on_tool_start(tool_name: str, command: str) -> None:
                tool_input = {"command": command} if command else None
                tracker.tool_starting(tool_name, tool_input)

            def on_tool_end(tool_name: str, success: bool) -> None:
                tracker.tool_completed(tool_name, success)

            try:
                # Use send_message_with_tools for Azure CLI execution
                for chunk in agent.send_message_with_tools(
                    user_input,
                    on_tool_start=on_tool_start,
                    on_tool_end=on_tool_end,
                ):
                    tracker.stop()  # Stop spinner before printing text
                    console.print(chunk, end="")
            except Exception as e:
                tracker.stop()
                console.print(f"[red]Error: {e}[/red]")

            tracker.stop()
            console.print()

    except Exception as e:
        console.print(f"[red]Error initializing legacy agent: {e}[/red]")


@app.command()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Enable verbose output"
    ),
    legacy: bool = typer.Option(
        False, "--legacy", help="Use legacy sync client instead of Claude Agent SDK"
    ),
    enable_ssl_verify: bool = typer.Option(
        False,
        "--enable-ssl-verify",
        help="Enable SSL certificate verification (disabled by default for corporate proxies)",
    ),
) -> None:
    """Triagent - Claude-powered CLI for Azure DevOps automation.

    Start an interactive chat session using the Claude Agent SDK.
    """
    console = Console()

    if version:
        console.print(f"Triagent CLI v{__version__}")
        raise typer.Exit()

    config_manager = get_config_manager()

    # Apply runtime options to config
    config = config_manager.load_config()
    if verbose:
        config.verbose = True
    if enable_ssl_verify:
        config.disable_ssl_verify = False  # Re-enable SSL verification
    config_manager.save_config(config)

    # Run in legacy or async mode
    try:
        if legacy:
            interactive_loop_legacy(console, config_manager)
        else:
            asyncio.run(async_main(config_manager))
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
