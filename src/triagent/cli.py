"""Main CLI for Triagent - Interactive chat interface with async SDK."""

from __future__ import annotations

import asyncio
import random
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from time import time
from typing import Any

import typer
from claude_agent_sdk import ClaudeSDKClient, CLINotFoundError, ProcessError
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from triagent import __version__
from triagent.commands.config import config_command
from triagent.commands.help import help_command
from triagent.commands.init import init_command
from triagent.commands.persona import persona_command
from triagent.commands.team import team_command
from triagent.commands.team_report import team_report_command
from triagent.config import ConfigManager, get_config_manager
from triagent.sdk_client import create_sdk_client
from triagent.session_logger import (
    create_session_logger,
    log_session_end,
    log_session_start,
)
from triagent.skills import get_available_personas
from triagent.teams.config import get_team_config
from triagent.utils.windows import find_git_bash, is_windows
from triagent.versions import (
    AZURE_EXTENSION_VERSIONS,
    CLAUDE_CODE_VERSION,
    MCP_AZURE_DEVOPS_VERSION,
)
from triagent.visibility.subagent_visibility import (
    show_subagent_complete,
    show_subagent_start,
)

# Classic braille spinner (rotates like a wheel)
BRAILLE_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Global spinner control for hooks to pause spinner during prompts
_current_activity_tracker: ActivityTracker | None = None


def set_activity_tracker(tracker: ActivityTracker | None) -> None:
    """Set the current activity tracker for global access.

    Args:
        tracker: The activity tracker instance or None to clear
    """
    global _current_activity_tracker
    _current_activity_tracker = tracker


def pause_spinner() -> None:
    """Pause the current spinner (called by hooks before prompting).

    This allows hooks to display confirmation prompts without being
    overwritten by the spinner's continuous refresh.
    """
    if _current_activity_tracker:
        _current_activity_tracker.stop()


def flush_buffer() -> None:
    """Flush any buffered text output before displaying prompts.

    This ensures all accumulated text (when markdown mode is enabled)
    is displayed before showing confirmation prompts or questions.
    """
    if _current_activity_tracker:
        _current_activity_tracker.flush_remaining()

# Whimsical status messages (Claude Code style)
THINKING_MESSAGES = ["Thinking", "Mulling", "Pondering", "Contemplating"]
TOOL_MESSAGES = ["Executing", "Running", "Processing"]


class SpinnerStatus:
    """Animated spinner status indicator using Rich's renderable protocol."""

    def __init__(self, message: str, color: str = "yellow"):
        self.message = message
        self.color = color
        self._idx = 0

    def __rich__(self) -> str:
        """Render with rotating spinner character."""
        spinner = BRAILLE_SPINNER[self._idx % len(BRAILLE_SPINNER)]
        self._idx += 1
        return f"[{self.color}]{spinner} {self.message}...[/{self.color}]"


@dataclass
class ActivityTracker:
    """Tracks tool execution activity with Claude Code style spinner and optional markdown."""

    console: Console
    verbose: bool = False
    markdown_enabled: bool = False  # If True, buffer for markdown; False streams plain text
    use_nerd_fonts: bool = True  # If True, use Nerd Font icons for subagents
    _live: Live | None = field(default=None, repr=False)
    _spinner_idx: int = field(default=0, repr=False)
    _tool_start_time: float = field(default=0.0, repr=False)
    _current_tool: str = field(default="", repr=False)
    _text_buffer: str = field(default="", repr=False)
    _current_subagent: str = field(default="", repr=False)  # Track active subagent type
    _current_tool_id: str = field(default="", repr=False)  # Track tool_use_id for matching

    def _get_spinner_char(self) -> str:
        """Get next spinner character."""
        char = BRAILLE_SPINNER[self._spinner_idx % len(BRAILLE_SPINNER)]
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

        # Start rotating spinner
        message = random.choice(TOOL_MESSAGES)
        status = SpinnerStatus(message, color="cyan")
        self._live = Live(
            status,
            console=self.console,
            refresh_per_second=10,  # 10Hz for smooth spinner rotation
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

        # Start rotating spinner for thinking
        message = random.choice(THINKING_MESSAGES)
        status = SpinnerStatus(message, color="yellow")
        self._live = Live(
            status,
            console=self.console,
            refresh_per_second=10,  # 10Hz for smooth spinner rotation
            transient=True,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop any active spinner."""
        if self._live:
            self._live.stop()
            self._live = None

    def buffer_text(self, text: str) -> None:
        """Buffer text for markdown or stream plain text immediately."""
        if self.markdown_enabled:
            # Buffer for markdown rendering
            self._text_buffer += text
            self._flush_paragraphs()
        else:
            # Stream plain text immediately
            self.console.print(text, end="")

    def _flush_paragraphs(self) -> None:
        """Render complete paragraphs as markdown."""
        # Look for paragraph breaks (double newline)
        while "\n\n" in self._text_buffer:
            paragraph, self._text_buffer = self._text_buffer.split("\n\n", 1)
            if paragraph.strip():
                md = Markdown(paragraph)
                self.console.print(md)

    def flush_remaining(self) -> None:
        """Flush any remaining buffered text as markdown."""
        if self.markdown_enabled and self._text_buffer.strip():
            md = Markdown(self._text_buffer)
            self.console.print(md)
        self._text_buffer = ""


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

    # Get persona display name
    personas = get_available_personas(config.team)
    persona_display = config.persona.title()
    for p in personas:
        if p.name == config.persona:
            persona_display = p.display_name
            break

    return f"[bold cyan]Triagent CLI v{__version__}[/bold cyan] | Team: {team_name} | Persona: {persona_display} | Project: {config.ado_project}"


def versions_command(console: Console) -> None:
    """Display installed and pinned tool versions."""
    from triagent.mcp.setup import (
        check_azure_cli_installed,
        check_claude_code_installed,
        check_nodejs_installed,
    )

    console.print()
    console.print("[bold cyan]Triagent Tool Versions[/bold cyan]")
    console.print()

    # Triagent version
    console.print(f"  [bold]Triagent CLI:[/bold]         v{__version__}")
    console.print()

    # Detected installed versions
    console.print("[bold]Installed Tools:[/bold]")
    az_installed, az_version = check_azure_cli_installed()
    node_installed, node_version = check_nodejs_installed()
    claude_installed, claude_version = check_claude_code_installed()

    az_display = az_version if az_installed else "[red]Not installed[/red]"
    node_display = node_version if node_installed else "[red]Not installed[/red]"
    claude_display = claude_version if claude_installed else "[red]Not installed[/red]"

    console.print(f"  Azure CLI:             {az_display}")
    console.print(f"  Node.js:               {node_display}")
    console.print(f"  Claude Code CLI:       {claude_display}")
    console.print()

    # Pinned versions (used by /init)
    console.print("[bold]Pinned Versions (used by /init):[/bold]")
    console.print(f"  Claude Code:           v{CLAUDE_CODE_VERSION}")
    console.print(f"  MCP Azure DevOps:      v{MCP_AZURE_DEVOPS_VERSION}")
    for ext_name, ext_version in AZURE_EXTENSION_VERSIONS.items():
        console.print(f"  az ext {ext_name}:  v{ext_version}")
    console.print()


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
    sdk_commands: list[str] | None = None,
) -> bool | str:
    """Handle a slash command synchronously.

    Args:
        command: Command name (without /)
        args: Command arguments
        console: Rich console
        config_manager: Config manager
        sdk_commands: Available SDK commands (for /help display)

    Returns:
        True to continue, False to exit, "sdk" to forward to SDK,
        "restart" to restart session
    """
    if command in ("exit", "quit", "q"):
        console.print("[dim]Goodbye![/dim]")
        log_session_end()  # Guard prevents duplicate logging
        return False

    if command == "help":
        help_command(console, sdk_commands=sdk_commands)
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

    if command == "persona":
        persona_name = args[0] if args else None
        changed = persona_command(console, config_manager, persona_name)
        # Return "restart" to signal SDK restart needed (special return value)
        if changed:
            return "restart"  # type: ignore
        return True

    if command == "clear":
        console.print("[dim]Conversation cleared (new session on next message)[/dim]")
        return True

    if command == "versions":
        versions_command(console)
        return True

    if command == "team-report":
        team_report_command(console, config_manager, args)
        return True

    if command == "confirm":
        # Toggle write operation confirmations
        config = config_manager.load_config()
        arg = args[0].lower() if args else ""

        if arg == "off":
            config.auto_approve_writes = True
            config_manager.save_config(config)
            console.print("[green]✓ Write confirmations DISABLED[/green]")
            console.print("[dim]  ADO/Git write operations will auto-approve[/dim]")
        elif arg == "on":
            config.auto_approve_writes = False
            config_manager.save_config(config)
            console.print("[green]✓ Write confirmations ENABLED[/green]")
            console.print("[dim]  You'll be asked to confirm write operations[/dim]")
        else:
            status = "[red]OFF[/red] (auto-approve)" if config.auto_approve_writes else "[green]ON[/green] (confirm)"
            console.print(f"[bold]Write confirmations:[/bold] {status}")
            console.print()
            console.print("[dim]Usage: /confirm on|off[/dim]")
            console.print("[dim]  on  - Ask for confirmation before write operations[/dim]")
            console.print("[dim]  off - Auto-approve write operations[/dim]")
        return True

    # Unknown CLI command - forward to SDK
    return "sdk"


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
                # Stop any spinner before buffering text
                tracker.stop()
                # Buffer text for markdown rendering
                tracker.buffer_text(block.text)

            elif block_type == "ToolUseBlock":
                # Start spinner for tool execution
                tool_input = getattr(block, "input", None)
                tool_id = getattr(block, "id", "")
                tracker._current_tool_id = tool_id

                # Check if this is a Task (subagent) invocation
                if block.name == "Task" and tool_input:
                    subagent_type = tool_input.get("subagent_type", "")
                    description = tool_input.get("description", "")
                    if subagent_type:
                        tracker._current_subagent = subagent_type
                        # Stop any existing spinner before showing subagent indicator
                        tracker.stop()
                        # Show subagent start indicator and log it
                        show_subagent_start(
                            console=tracker.console,
                            subagent_type=subagent_type,
                            use_nerd_fonts=tracker.use_nerd_fonts,
                            trigger=description,
                            context={"prompt": tool_input.get("prompt", "")[:200]},
                        )

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

                # Check if this was a subagent task completion
                if tracker._current_subagent and tracker._current_tool == "Task":
                    # Create brief result summary (first 100 chars)
                    result_summary = content[:100] if content else "completed"
                    if len(content) > 100:
                        result_summary += "..."
                    # Show subagent completion indicator and log it
                    show_subagent_complete(
                        console=tracker.console,
                        subagent_type=tracker._current_subagent,
                        result_summary=result_summary,
                        use_nerd_fonts=tracker.use_nerd_fonts,
                        is_error=is_error,
                    )
                    tracker._current_subagent = ""  # Clear subagent tracking

                tracker.tool_completed(
                    tracker._current_tool or "tool",
                    not is_error,
                    content,
                )

    elif msg_type == "SystemMessage":
        # Handle system messages (including SDK slash command responses)
        tracker.stop()
        subtype = getattr(msg, "subtype", "")
        data = getattr(msg, "data", {})

        if subtype == "command_result":
            # SDK slash command output
            output = data.get("output", data.get("result", ""))
            if output:
                console.print(output)
        elif data:
            # Other system messages - show relevant data
            if "message" in data:
                console.print(f"[dim]{data['message']}[/dim]")
            elif "output" in data:
                console.print(data["output"])

    elif msg_type == "UserMessage":
        # Handle SDK slash command output (e.g., /release-notes)
        # Note: content can be a string (slash commands) or list (regular messages)
        content = getattr(msg, "content", "")
        if content and isinstance(content, str):
            # Only stop spinner and display for actual SDK slash command output
            tracker.stop()
            # Strip the <local-command-stdout> wrapper if present
            cleaned = re.sub(r"<local-command-stdout>\s*", "", content)
            cleaned = re.sub(r"\s*</local-command-stdout>", "", cleaned)
            if cleaned.strip():
                console.print(cleaned.strip())
        # List content (echoed user input) - don't stop spinner, let it continue

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

    else:
        # Log unknown message types for debugging
        if tracker.verbose:
            console.print(f"\n[dim]Unknown message type: {msg_type}[/dim]")
            console.print(f"[dim]Message: {msg}[/dim]")


async def _stream_prompt(prompt: str) -> AsyncIterator[dict[str, Any]]:
    """Convert string prompt to async iterable for streaming mode.

    The Claude Agent SDK's control protocol requires an AsyncIterable prompt
    to enable the can_use_tool callback for runtime permission decisions.
    Without streaming mode, the callback is registered but never invoked.

    Args:
        prompt: The user's input string

    Yields:
        Message dict in the format expected by the SDK control protocol
    """
    yield {
        "type": "user",
        "message": {"role": "user", "content": prompt},
        "session_id": "default",
    }


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

    # Initialize session logging
    config = config_manager.load_config()
    session_logger = create_session_logger(
        session_id=None,  # Auto-generate
        log_level=config.session_log_level,
        enabled=config.session_logging,
    )
    if session_logger:
        log_session_start()

    # Check if setup is needed
    if not config_manager.config_exists():
        console.print(
            "[yellow]No configuration found. Running setup wizard...[/yellow]"
        )
        console.print()
        if not init_command(console, config_manager):
            console.print("[red]Setup failed. Exiting.[/red]")
            return

    # Windows: Early check for Git Bash before attempting to start Claude Code
    if is_windows() and not find_git_bash():
        console.print(
            "[red]Error: Git Bash is required on Windows but was not found.[/red]"
        )
        console.print()
        console.print("[yellow]To fix this:[/yellow]")
        console.print(
            "  1. Install Git for Windows from: https://git-scm.com/downloads/win"
        )
        console.print("  2. OR set CLAUDE_CODE_GIT_BASH_PATH to your bash.exe location:")
        console.print("     [cyan]Common locations:[/cyan]")
        console.print("       C:\\Program Files\\Git\\bin\\bash.exe")
        console.print("       C:\\Program Files (x86)\\Git\\bin\\bash.exe")
        console.print()
        console.print("[dim]After installing Git, restart your terminal and try again.[/dim]")
        return

    # Outer loop allows restarting SDK client after /init changes credentials
    restart_session = True
    while restart_session:
        restart_session = False

        # Build SDK options (inside loop to pick up new credentials after /init)
        client_factory = create_sdk_client(config_manager, console)
        options = client_factory._build_options()

        # Create activity tracker for visual feedback
        config = config_manager.load_config()
        tracker = ActivityTracker(
            console=console,
            verbose=config.verbose,
            markdown_enabled=config.markdown_format,
        )
        # Make tracker globally accessible for hooks to pause spinner
        set_activity_tracker(tracker)

        # Use SDK context manager for session lifecycle
        try:
            async with ClaudeSDKClient(options=options) as client:
                # Discover available SDK commands from server info
                sdk_commands: list[str] = []
                try:
                    server_info = await client.get_server_info()
                    if server_info:
                        sdk_commands = server_info.get("commands", [])
                except Exception:
                    pass  # Fallback: no SDK commands shown in help

                console.print("[dim]Connected to Claude. Type /help for commands[/dim]")
                console.print()

                while True:
                    try:
                        # Get user input (sync input() is OK inside async)
                        user_input = input("You: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        console.print()
                        console.print("[dim]Goodbye![/dim]")
                        log_session_end()  # Guard prevents duplicate logging
                        break

                    if not user_input:
                        continue

                    # Handle slash commands
                    if user_input.startswith("/"):
                        command, args = parse_slash_command(user_input)
                        result = handle_slash_command(
                            command, args, console, config_manager, sdk_commands
                        )

                        if result == "sdk":
                            # Unknown CLI command - forward to SDK as prompt
                            pass  # Fall through to send to SDK
                        elif command == "init" or result == "restart":
                            # Restart SDK client after /init or /persona
                            restart_session = True
                            break
                        elif not result:
                            break
                        else:
                            continue  # CLI handled it, get next input

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

                    await client.query(prompt=_stream_prompt(user_input))

                    # Stream response
                    async for msg in client.receive_response():
                        process_sdk_message(msg, console, tracker)

                    # Ensure spinner is stopped and flush remaining markdown
                    tracker.stop()
                    tracker.flush_remaining()
                    console.print()

        except CLINotFoundError:
            console.print("[red]Error: Claude CLI not installed[/red]")
            console.print(
                "[dim]Install with: npm install -g @anthropic-ai/claude-code[/dim]"
            )
            set_activity_tracker(None)
        except ProcessError as e:
            console.print(f"[red]Process error: {e}[/red]")
            set_activity_tracker(None)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            set_activity_tracker(None)


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


@app.command()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Enable verbose output"
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

    try:
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
