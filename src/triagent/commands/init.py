"""Init command (setup wizard) for Triagent CLI."""

from __future__ import annotations

import getpass
import platform
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from triagent.config import ConfigManager, TriagentConfig, TriagentCredentials
from triagent.mcp.setup import (
    REQUIRED_AZURE_EXTENSIONS,
    check_azure_cli_installed,
    check_azure_extension,
    check_nodejs_installed,
    get_azure_account,
    run_azure_login,
    setup_mcp_servers,
)
from triagent.skills import get_available_personas
from triagent.teams.config import TEAM_CONFIG, get_team_config
from triagent.utils.environment import get_environment_type
from triagent.utils.windows import find_git_bash, is_windows

AZURE_CLI_INSTALL_URL = "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"


@dataclass
class InitFailure:
    """Represents a failure during initialization."""

    step: str
    component: str
    error: str
    manual_fix: str


@dataclass
class InitReport:
    """Tracks initialization results for reporting."""

    failures: list[InitFailure] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    successes: list[str] = field(default_factory=list)

    def add_failure(
        self, step: str, component: str, error: str, manual_fix: str
    ) -> None:
        """Add a failure to the report."""
        self.failures.append(InitFailure(step, component, error, manual_fix))

    def add_warning(self, message: str) -> None:
        """Add a warning to the report."""
        self.warnings.append(message)

    def add_success(self, message: str) -> None:
        """Add a success to the report."""
        self.successes.append(message)

    def has_failures(self) -> bool:
        """Check if there are any failures."""
        return len(self.failures) > 0

    def write_log(self, config_dir: Path) -> Path:
        """Write failures to a log file.

        Args:
            config_dir: Directory to write the log file to

        Returns:
            Path to the written log file
        """
        log_file = config_dir / f"init-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        with open(log_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("TRIAGENT INIT REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            if self.successes:
                f.write("SUCCESSES:\n")
                for s in self.successes:
                    f.write(f"  [OK] {s}\n")
                f.write("\n")

            if self.warnings:
                f.write("WARNINGS:\n")
                for w in self.warnings:
                    f.write(f"  [!] {w}\n")
                f.write("\n")

            if self.failures:
                f.write("FAILURES (with manual fix instructions):\n")
                f.write("-" * 60 + "\n")
                for fail in self.failures:
                    f.write(f"\nStep: {fail.step}\n")
                    f.write(f"Component: {fail.component}\n")
                    f.write(f"Error: {fail.error}\n")
                    f.write(f"Manual Fix:\n  {fail.manual_fix}\n")
                    f.write("-" * 60 + "\n")

        return log_file

# API Provider options
API_PROVIDERS = [
    ("azure_foundry", "Azure AI Foundry (recommended)"),
    ("anthropic", "Direct Anthropic API"),
]


def confirm_prompt(message: str, default: bool = True) -> bool:
    """Simple confirmation prompt.

    Args:
        message: The question to ask
        default: Default value if user just presses Enter

    Returns:
        True for yes, False for no
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    result = input(message + suffix).strip().lower()
    if not result:
        return default
    return result in ("y", "yes")


def init_command(console: Console, config_manager: ConfigManager) -> bool:
    """Run the setup wizard.

    Args:
        console: Rich console for output
        config_manager: Config manager instance

    Returns:
        True if setup completed successfully
    """
    # Initialize the report to track successes, warnings, and failures
    report = InitReport()
    env_type = get_environment_type()

    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to Triagent CLI Setup[/bold cyan]\n\n"
            "This wizard will help you configure Triagent for Azure DevOps automation.\n"
            f"[dim]Environment: {env_type}[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # Step 1: API Provider Selection (moved first)
    credentials = _step_api_provider(console, config_manager)

    # Step 2: Team Selection
    config = _step_team_selection(console, config_manager)
    if config is None:
        return False

    # Step 3: Persona Selection
    config = _step_persona_selection(console, config_manager, config)

    # Step 4: MCP Server Setup
    _step_mcp_setup(console, config_manager, config)

    # Step 5: Azure Authentication (fail gracefully if az not found)
    _step_azure_auth(console, config_manager, report)

    # Step 6: Prerequisites Check (display-only)
    _step_prerequisites(console, report)

    # Save configuration
    config_manager.save_config(config)
    if credentials:
        config_manager.save_credentials(credentials)

    # Show completion summary (includes failure report if any)
    _show_completion(console, config_manager, config, report)

    return True


def _step_azure_auth(
    console: Console, config_manager: ConfigManager, report: InitReport
) -> bool:
    """Step 5: Azure Authentication.

    This step is non-blocking - failures are logged to report but setup continues.
    If Azure CLI is not detected, shows manual installation instructions.

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        report: InitReport to track successes and failures

    Returns:
        True (always continues to next step)
    """
    console.print("[bold]Step 5/6: Azure Authentication[/bold]")
    console.print("-" * 40)
    console.print()

    # Check if Azure CLI is installed first
    az_installed, _ = check_azure_cli_installed()
    if not az_installed:
        console.print("[yellow]Azure CLI not detected.[/yellow]")
        console.print()
        console.print("[bold]Please install Azure CLI and authenticate manually:[/bold]")
        console.print()
        console.print("1. Install Azure CLI:")
        system = platform.system().lower()
        if system == "windows":
            console.print("   Download from: https://aka.ms/installazurecliwindows")
        elif system == "darwin":
            console.print("   brew install azure-cli")
        else:
            console.print("   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        console.print()
        console.print("2. Install required extensions:")
        console.print("   az extension add --name azure-devops --version 1.0.1")
        console.print("   az extension add --name application-insights --version 1.2.1")
        console.print("   az extension add --name log-analytics --version 0.2.3")
        console.print()
        console.print("3. Authenticate:")
        console.print("   az login")
        console.print()
        report.add_warning("Azure CLI not installed - manual authentication required")
        return True

    # Check if already logged in
    account = get_azure_account()
    if account:
        user = account.get("user", {}).get("name", "Unknown")
        console.print(f"[green]✓[/green] Already authenticated as: {user}")
        report.add_success(f"Azure authenticated: {user}")

        if not confirm_prompt("Use this account?", default=True):
            account = None

    if not account:
        console.print("[yellow]Opening browser for Azure authentication...[/yellow]")
        if run_azure_login():
            account = get_azure_account()
            if account:
                user = account.get("user", {}).get("name", "Unknown")
                console.print(f"[green]✓[/green] Authenticated as: {user}")
                report.add_success(f"Azure authenticated: {user}")
            else:
                console.print("[yellow]⚠[/yellow] Authentication failed (will continue)")
                report.add_failure(
                    step="Step 5/6",
                    component="Azure Authentication",
                    error="Failed to get account info after login",
                    manual_fix="az login",
                )
        else:
            console.print("[yellow]⚠[/yellow] Azure login failed (will continue)")
            report.add_failure(
                step="Step 5/6",
                component="Azure Authentication",
                error="Azure login command failed",
                manual_fix="az login",
            )
            report.add_warning("Azure authentication failed - some features may not work")

    # Update config if authenticated
    if account:
        config = config_manager.load_config()
        config.azure_cli_authenticated = True
        config_manager.save_config(config)

    console.print()
    return True  # Always continue


def _step_api_provider(
    console: Console,
    config_manager: ConfigManager,
) -> TriagentCredentials | None:
    """Step 1: API Provider selection and configuration."""
    console.print("[bold]Step 1/6: Claude API Provider[/bold]")
    console.print("-" * 40)

    credentials = config_manager.load_credentials()

    # Check if already configured
    current_provider = credentials.api_provider
    has_token = (
        (current_provider == "azure_foundry" and credentials.anthropic_foundry_api_key)
        or current_provider == "anthropic"
    )

    if has_token:
        provider_name = dict(API_PROVIDERS).get(current_provider, current_provider)
        console.print(f"[green]✓[/green] API provider configured: {provider_name}")
        if not confirm_prompt("Reconfigure API provider?", default=False):
            console.print()
            return None

    console.print("Select your Claude API provider:")
    console.print()

    for i, (_, display_name) in enumerate(API_PROVIDERS, 1):
        console.print(f"  {i}. {display_name}")

    console.print()

    while True:
        try:
            choice = input("Enter provider number (1-2): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(API_PROVIDERS):
                break
            console.print("[red]Invalid selection[/red]")
        except ValueError:
            console.print("[red]Please enter a number[/red]")

    provider_key, provider_name = API_PROVIDERS[idx]
    credentials.api_provider = provider_key

    console.print()
    console.print(f"Selected: {provider_name}")
    console.print()

    # Configure based on provider
    if provider_key == "azure_foundry":
        credentials = _configure_azure_foundry(console, credentials)
    else:
        console.print("[dim]Using direct Anthropic API (requires ANTHROPIC_API_KEY env var)[/dim]")
        console.print("[green]✓[/green] API provider configured")

    console.print()
    return credentials


def _test_azure_foundry_connection(
    console: Console,
    credentials: TriagentCredentials,
) -> bool:
    """Test Azure AI Foundry API connection.

    Args:
        console: Rich console for output
        credentials: Credentials to test

    Returns:
        True if connection successful, False otherwise
    """
    import httpx

    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": credentials.anthropic_foundry_api_key,
            "anthropic-version": "2023-06-01",
        }

        body = {
            "model": credentials.anthropic_foundry_model,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say hi in 5 words"}],
        }

        response = httpx.post(
            credentials.anthropic_foundry_base_url,
            headers=headers,
            json=body,
            timeout=60,
        )

        if response.status_code == 200:
            return True
        else:
            error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            console.print(f"[red]✗ Connection failed: {error_msg}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        return False


def _configure_azure_foundry(
    console: Console,
    credentials: TriagentCredentials,
) -> TriagentCredentials:
    """Configure Azure AI Foundry API settings."""
    while True:
        console.print("[dim]Configure Azure AI Foundry API settings:[/dim]")
        console.print("[dim]Press Enter to accept default values shown in brackets[/dim]")
        console.print()

        # Prompt for Base URL (required)
        default_url = credentials.anthropic_foundry_base_url or "https://your-resource.services.ai.azure.com/anthropic/v1/messages"
        base_url = input(f"Target URI [{default_url}]: ").strip()
        if base_url:
            credentials.anthropic_foundry_base_url = base_url
        elif not credentials.anthropic_foundry_base_url:
            console.print("[red]Target URI is required[/red]")
            continue

        # Prompt for API Key (required)
        api_key = getpass.getpass("API Key: ").strip()
        if not api_key:
            console.print()
            console.print("[yellow]Warning: No API key provided. You'll need to configure it later.[/yellow]")
            return credentials
        credentials.anthropic_foundry_api_key = api_key

        # Prompt for Model/Deployment name
        default_model = credentials.anthropic_foundry_model or "claude-opus-4-5"
        model = input(f"Deployment Name [{default_model}]: ").strip()
        if model:
            credentials.anthropic_foundry_model = model

        console.print()

        # Test the connection
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Testing connection...")
            success = _test_azure_foundry_connection(console, credentials)

        if success:
            console.print("[green]✓[/green] Connection successful!")
            console.print("[green]✓[/green] Azure Foundry credentials configured")
            return credentials

        # Connection failed - offer retry
        console.print()
        if not confirm_prompt("Retry configuration?", default=True):
            console.print("[yellow]Skipping connection test. You may need to reconfigure later.[/yellow]")
            return credentials

        console.print()  # Add spacing before retry


def _step_team_selection(
    console: Console,
    config_manager: ConfigManager,
) -> TriagentConfig | None:
    """Step 2: Team Selection."""
    console.print("[bold]Step 2/6: Team Selection[/bold]")
    console.print("-" * 40)

    config = config_manager.load_config()

    console.print("Select your team:")
    console.print()

    team_list = list(TEAM_CONFIG.items())
    for i, (name, tc) in enumerate(team_list, 1):
        current = " [green](current)[/green]" if name == config.team else ""
        console.print(f"  {i}. {tc.display_name}{current}")

    console.print()

    while True:
        try:
            choice = input("Enter team number (1-3): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(team_list):
                break
            console.print("[red]Invalid selection[/red]")
        except ValueError:
            console.print("[red]Please enter a number[/red]")

    team_name, team_config = team_list[idx]

    config.team = team_name
    config.ado_project = team_config.ado_project
    config.ado_organization = team_config.ado_organization

    console.print()
    console.print(f"[green]✓[/green] Selected team: {team_config.display_name}")
    console.print(f"    ADO Organization: {team_config.ado_organization}")
    console.print(f"    ADO Project: {team_config.ado_project}")
    console.print()

    return config


def _step_persona_selection(
    console: Console,
    config_manager: ConfigManager,
    config: TriagentConfig,
) -> TriagentConfig:
    """Step 3: Persona Selection.

    Allows users to select their persona (Developer or Support) which
    determines the skills and subagents loaded for their session.

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        config: Current configuration

    Returns:
        Updated configuration with persona set
    """
    console.print("[bold]Step 3/6: Persona Selection[/bold]")
    console.print("-" * 40)

    # Get available personas for the selected team
    personas = get_available_personas(config.team)

    if not personas:
        # No personas defined for this team, use default
        console.print("[dim]No personas defined for this team. Using default.[/dim]")
        console.print()
        return config

    console.print("Select your persona:")
    console.print()

    for i, persona in enumerate(personas, 1):
        current = " [green](current)[/green]" if persona.name == config.persona else ""
        console.print(f"  {i}. {persona.display_name} - {persona.description}{current}")

    console.print()

    while True:
        try:
            choice = input(f"Enter persona number (1-{len(personas)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(personas):
                break
            console.print("[red]Invalid selection[/red]")
        except ValueError:
            console.print("[red]Please enter a number[/red]")

    selected_persona = personas[idx]
    config.persona = selected_persona.name

    console.print()
    console.print(f"[green]✓[/green] Selected persona: {selected_persona.display_name}")
    console.print(f"    {selected_persona.description}")
    console.print()

    return config


def _step_mcp_setup(
    console: Console,
    config_manager: ConfigManager,
    config: TriagentConfig,
) -> None:
    """Step 4: MCP Server Setup."""
    console.print("[bold]Step 4/6: Azure DevOps MCP Server[/bold]")
    console.print("-" * 40)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Configuring MCP servers...")
        setup_mcp_servers(
            config_manager,
            config.ado_organization,
            config.ado_project,
        )

    console.print(f"[green]✓[/green] MCP server configured at {config_manager.mcp_servers_file}")
    console.print()


def _step_prerequisites(
    console: Console,
    report: InitReport,
) -> None:
    """Step 6: Prerequisites Check (display-only, no auto-install).

    This step checks for required prerequisites and displays manual
    installation instructions if any are missing. No auto-installation.

    Note: Claude Code CLI check is removed because the claude_agent_sdk
    package bundles its own CLI binary - npm installation is not required.

    Args:
        console: Rich console for output
        report: InitReport to track status
    """
    import os

    console.print("[bold]Step 6/6: Prerequisites Check[/bold]")
    console.print("-" * 40)
    console.print()

    system = platform.system().lower()
    missing_prereqs: list[str] = []

    # Check Azure CLI
    az_installed, az_version = check_azure_cli_installed()
    if az_installed:
        console.print(f"[green]✓[/green] Azure CLI: {az_version}")
        report.add_success(f"Azure CLI: {az_version}")

        # Check Azure extensions
        for ext_name in REQUIRED_AZURE_EXTENSIONS:
            if check_azure_extension(ext_name):
                console.print(f"[green]✓[/green] Extension: {ext_name}")
            else:
                console.print(f"[yellow]○[/yellow] Extension missing: {ext_name}")
                missing_prereqs.append(f"az extension add --name {ext_name}")
    else:
        console.print("[red]✗[/red] Azure CLI not found")
        missing_prereqs.append("Azure CLI installation required")
        report.add_warning("Azure CLI not installed")

    console.print()

    # Check Node.js
    node_installed, node_version = check_nodejs_installed()
    if node_installed:
        console.print(f"[green]✓[/green] Node.js: {node_version}")
        report.add_success(f"Node.js: {node_version}")
    else:
        console.print("[yellow]○[/yellow] Node.js not found (needed for MCP servers)")
        missing_prereqs.append("Node.js installation required")
        report.add_warning("Node.js not installed - MCP servers may not work")

    # Check Git Bash on Windows
    if is_windows():
        bash_path = find_git_bash()
        if bash_path:
            os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = bash_path
            console.print(f"[green]✓[/green] Git Bash: {bash_path}")
            report.add_success(f"Git Bash: {bash_path}")
        else:
            console.print("[yellow]○[/yellow] Git Bash not found (recommended for Windows)")
            missing_prereqs.append("Git for Windows installation required")
            report.add_warning("Git Bash not found - some features may not work on Windows")

    # Note: Claude Code CLI check removed - SDK bundles its own CLI binary

    console.print()

    # Display manual installation instructions if needed
    if missing_prereqs:
        _show_prerequisites_instructions(console, missing_prereqs, system)


def _show_prerequisites_instructions(
    console: Console,
    missing: list[str],
    system: str,
) -> None:
    """Display manual installation instructions for missing prerequisites.

    Args:
        console: Rich console for output
        missing: List of missing prerequisites/commands
        system: OS type (darwin, windows, linux)
    """
    console.print("[bold yellow]Missing Prerequisites[/bold yellow]")
    console.print()

    # Azure CLI instructions
    if any("Azure CLI" in m for m in missing):
        console.print("[bold]Azure CLI Installation:[/bold]")
        if system == "darwin":
            console.print("  brew install azure-cli")
        elif system == "windows":
            console.print("  Download from: https://aka.ms/installazurecliwindows")
        else:
            console.print("  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        console.print()

    # Azure extensions
    ext_missing = [m for m in missing if m.startswith("az extension")]
    if ext_missing:
        console.print("[bold]Azure CLI Extensions:[/bold]")
        for cmd in ext_missing:
            console.print(f"  {cmd}")
        console.print()

    # Node.js instructions
    if any("Node.js" in m for m in missing):
        console.print("[bold]Node.js Installation:[/bold]")
        if system == "darwin":
            console.print("  brew install node")
        elif system == "windows":
            console.print("  Download from: https://nodejs.org")
        else:
            console.print("  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -")
            console.print("  sudo apt-get install -y nodejs")
        console.print()

    # Git for Windows instructions
    if any("Git for Windows" in m for m in missing):
        console.print("[bold]Git for Windows Installation:[/bold]")
        console.print("  Download from: https://git-scm.com/download/win")
        console.print()


def _show_completion(
    console: Console,
    config_manager: ConfigManager,
    config: TriagentConfig,
    report: InitReport,
) -> None:
    """Show setup completion summary with failure report if any.

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        config: Configuration object
        report: InitReport with successes, warnings, and failures
    """
    team_config = get_team_config(config.team)
    team_name = team_config.display_name if team_config else config.team

    # Get API provider name
    credentials = config_manager.load_credentials()
    provider_name = dict(API_PROVIDERS).get(credentials.api_provider, credentials.api_provider)

    # Get persona display name
    personas = get_available_personas(config.team)
    persona_display = config.persona.title()
    for p in personas:
        if p.name == config.persona:
            persona_display = p.display_name
            break

    console.print(
        Panel(
            f"[bold green]Setup Complete![/bold green]\n\n"
            f"[bold]Config saved to:[/bold] {config_manager.config_file}\n"
            f"[bold]Team:[/bold] {team_name}\n"
            f"[bold]Persona:[/bold] {persona_display}\n"
            f"[bold]ADO Project:[/bold] {config.ado_project}\n"
            f"[bold]API Provider:[/bold] {provider_name}\n"
            f"[bold]MCP Servers:[/bold] Azure DevOps\n\n"
            "[dim]Type your message or use /help for commands[/dim]",
            border_style="green",
        )
    )
    console.print()

    # Show failure report if there were any issues
    if report.has_failures():
        # Write log file
        config_manager.ensure_dirs()
        log_file = report.write_log(config_manager.config_dir)

        # Build failure list
        failure_list = "\n".join([f"  • {f.component}" for f in report.failures])

        console.print(
            Panel(
                f"[bold yellow]Some components failed to install[/bold yellow]\n\n"
                f"The following issues need manual attention:\n"
                f"{failure_list}\n\n"
                f"[dim]Full details and fix instructions saved to:[/dim]\n"
                f"  {log_file}",
                border_style="yellow",
            )
        )
        console.print()
    elif report.warnings:
        # Show warnings even if no failures
        warning_list = "\n".join([f"  • {w}" for w in report.warnings])
        console.print(
            Panel(
                f"[bold yellow]Warnings[/bold yellow]\n\n{warning_list}",
                border_style="yellow",
            )
        )
        console.print()
