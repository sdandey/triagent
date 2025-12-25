"""Init command (setup wizard) for Triagent CLI."""

from __future__ import annotations

import getpass
import platform
import webbrowser

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from triagent.config import ConfigManager, TriagentConfig, TriagentCredentials
from triagent.mcp.setup import (
    REQUIRED_AZURE_EXTENSIONS,
    check_azure_cli_installed,
    check_azure_extension,
    check_claude_code_installed,
    check_nodejs_installed,
    check_npm_installed,
    get_azure_account,
    install_azure_cli,
    install_azure_extension,
    install_claude_code,
    install_nodejs,
    run_azure_login,
    setup_mcp_servers,
)
from triagent.teams.config import TEAM_CONFIG, get_team_config

AZURE_CLI_INSTALL_URL = "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"

# API Provider options
API_PROVIDERS = [
    ("databricks", "Databricks (recommended)"),
    ("azure_foundry", "Azure AI Foundry"),
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
    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to Triagent CLI Setup[/bold cyan]\n\n"
            "This wizard will help you configure Triagent for Azure DevOps automation.",
            border_style="cyan",
        )
    )
    console.print()

    # Step 1: Azure CLI
    if not _step_azure_cli(console):
        return False

    # Step 2: Azure Authentication
    if not _step_azure_auth(console, config_manager):
        return False

    # Step 3: API Provider Selection
    credentials = _step_api_provider(console, config_manager)

    # Step 4: Team Selection
    config = _step_team_selection(console, config_manager)
    if config is None:
        return False

    # Step 5: MCP Server Setup
    _step_mcp_setup(console, config_manager, config)

    # Step 6: Claude Code CLI
    _step_claude_code(console)

    # Save configuration
    config_manager.save_config(config)
    if credentials:
        config_manager.save_credentials(credentials)

    # Show completion summary
    _show_completion(console, config_manager, config)

    return True


def _step_azure_cli(console: Console) -> bool:
    """Step 1: Check and auto-install Azure CLI and extensions."""
    console.print("[bold]Step 1/6: Azure CLI Installation[/bold]")
    console.print("-" * 40)

    installed, version = check_azure_cli_installed()

    if installed:
        console.print(f"[green]✓[/green] Azure CLI is installed: {version}")
    else:
        console.print("[yellow]Azure CLI not detected. Installing...[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Installing Azure CLI (this may take a few minutes)...")
            success, message = install_azure_cli()

        if success:
            console.print(f"[green]✓[/green] Azure CLI installed: {message}")
            # Verify installation
            installed, version = check_azure_cli_installed()
            if installed:
                console.print(f"[green]✓[/green] Verified: {version}")
            else:
                console.print("[yellow]Note: You may need to restart your terminal[/yellow]")
        else:
            console.print(f"[red]✗[/red] Auto-install failed: {message}")
            console.print("[yellow]Please install manually:[/yellow]")
            console.print(f"  {AZURE_CLI_INSTALL_URL}")

            if confirm_prompt("Open installation guide in browser?", default=True):
                webbrowser.open(AZURE_CLI_INSTALL_URL)

            return False

    # Install all required Azure CLI extensions
    console.print()
    console.print("[dim]Checking Azure CLI extensions...[/dim]")

    for ext_name in REQUIRED_AZURE_EXTENSIONS:
        if check_azure_extension(ext_name):
            console.print(f"[green]✓[/green] {ext_name} extension installed")
        else:
            console.print(f"[yellow]Installing {ext_name} extension...[/yellow]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Installing {ext_name}...")
                if install_azure_extension(ext_name):
                    console.print(f"[green]✓[/green] {ext_name} extension installed")
                else:
                    console.print(f"[red]✗[/red] Failed to install {ext_name} extension")
                    console.print(f"Try manually: az extension add --name {ext_name}")
                    # Don't fail for optional extensions (only azure-devops is critical)
                    if ext_name == "azure-devops":
                        return False

    console.print()
    return True


def _step_azure_auth(console: Console, config_manager: ConfigManager) -> bool:
    """Step 2: Azure Authentication."""
    console.print("[bold]Step 2/6: Azure Authentication[/bold]")
    console.print("-" * 40)

    # Check if already logged in
    account = get_azure_account()
    if account:
        user = account.get("user", {}).get("name", "Unknown")
        console.print(f"[green]✓[/green] Already authenticated as: {user}")

        if not confirm_prompt("Use this account?", default=True):
            account = None

    if not account:
        console.print("[yellow]Opening browser for Azure authentication...[/yellow]")
        if run_azure_login():
            account = get_azure_account()
            if account:
                user = account.get("user", {}).get("name", "Unknown")
                console.print(f"[green]✓[/green] Authenticated as: {user}")
            else:
                console.print("[red]✗[/red] Authentication failed")
                return False
        else:
            console.print("[red]✗[/red] Azure login failed")
            return False

    # Update config
    config = config_manager.load_config()
    config.azure_cli_authenticated = True
    config_manager.save_config(config)

    console.print()
    return True


def _step_api_provider(
    console: Console,
    config_manager: ConfigManager,
) -> TriagentCredentials | None:
    """Step 3: API Provider selection and configuration."""
    console.print("[bold]Step 3/6: Claude API Provider[/bold]")
    console.print("-" * 40)

    credentials = config_manager.load_credentials()

    # Check if already configured
    current_provider = credentials.api_provider
    has_token = (
        (current_provider == "databricks" and credentials.databricks_auth_token)
        or (current_provider == "azure_foundry" and credentials.anthropic_foundry_api_key)
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
            choice = input("Enter provider number (1-3): ").strip()
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
    if provider_key == "databricks":
        credentials = _configure_databricks(console, credentials)
    elif provider_key == "azure_foundry":
        credentials = _configure_azure_foundry(console, credentials)
    else:
        console.print("[dim]Using direct Anthropic API (requires ANTHROPIC_API_KEY env var)[/dim]")
        console.print("[green]✓[/green] API provider configured")

    console.print()
    return credentials


def _test_databricks_connection(
    console: Console,
    credentials: TriagentCredentials,
) -> bool:
    """Test Databricks API connection.

    Args:
        console: Rich console for output
        credentials: Credentials to test

    Returns:
        True if connection successful, False otherwise
    """
    from triagent.agent import DatabricksClient

    try:
        client = DatabricksClient(credentials)
        # Simple test call with minimal tokens
        client.send_message(
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10,
        )
        return True
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        return False


def _configure_databricks(
    console: Console,
    credentials: TriagentCredentials,
) -> TriagentCredentials:
    """Configure Databricks API settings."""
    while True:
        console.print("[dim]Configure Databricks API settings:[/dim]")
        console.print("[dim]Press Enter to accept default values shown in brackets[/dim]")
        console.print()

        # Prompt for ANTHROPIC_BASE_URL
        base_url = input(
            f"ANTHROPIC_BASE_URL [{credentials.databricks_base_url}]: "
        ).strip()
        if base_url:
            credentials.databricks_base_url = base_url

        # Prompt for ANTHROPIC_MODEL
        model = input(
            f"ANTHROPIC_MODEL [{credentials.databricks_model}]: "
        ).strip()
        if model:
            credentials.databricks_model = model

        # Prompt for ANTHROPIC_AUTH_TOKEN (required)
        token = getpass.getpass("ANTHROPIC_AUTH_TOKEN: ").strip()
        if not token:
            console.print()
            console.print("[yellow]Warning: No token provided. You'll need to configure it later.[/yellow]")
            return credentials

        credentials.databricks_auth_token = token
        console.print()

        # Test the connection
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Testing connection...")
            success = _test_databricks_connection(console, credentials)

        if success:
            console.print("[green]✓[/green] Connection successful!")
            console.print("[green]✓[/green] Databricks credentials configured")
            return credentials

        # Connection failed - offer retry
        console.print()
        if not confirm_prompt("Retry configuration?", default=True):
            console.print("[yellow]Skipping connection test. You may need to reconfigure later.[/yellow]")
            return credentials

        console.print()  # Add spacing before retry


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
    """Step 4: Team Selection."""
    console.print("[bold]Step 4/6: Team Selection[/bold]")
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


def _step_mcp_setup(
    console: Console,
    config_manager: ConfigManager,
    config: TriagentConfig,
) -> None:
    """Step 5: MCP Server Setup."""
    console.print("[bold]Step 5/6: Azure DevOps MCP Server[/bold]")
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


def _show_manual_install_instructions(console: Console, system: str) -> None:
    """Show manual installation instructions when auto-install fails.

    Args:
        console: Rich console for output
        system: OS type (darwin, windows, linux)
    """
    console.print()
    console.print("[bold yellow]Manual Installation Required[/bold yellow]")
    console.print()

    if system == "darwin":
        console.print("Install Node.js on macOS:")
        console.print("  1. Install Homebrew: https://brew.sh")
        console.print("  2. Run: brew install node")
        console.print()
        console.print("Or download from: https://nodejs.org")

    elif system == "windows":
        console.print("Install Node.js on Windows:")
        console.print("  Option 1 - winget (recommended):")
        console.print("    winget install -e --id OpenJS.NodeJS.LTS")
        console.print()
        console.print("  Option 2 - Download installer:")
        console.print("    1. Go to https://nodejs.org")
        console.print("    2. Download Windows Installer (.msi)")
        console.print("    3. Run installer and follow prompts")
        console.print()
        console.print("  Option 3 - Chocolatey:")
        console.print("    choco install nodejs-lts")

    elif system == "linux":
        console.print("Install Node.js on Linux (Ubuntu/Debian):")
        console.print("  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -")
        console.print("  sudo apt-get install -y nodejs")
        console.print()
        console.print("For other distributions: https://nodejs.org/en/download")

    else:
        console.print(f"Install Node.js for your OS ({system}):")
        console.print("  https://nodejs.org/en/download")

    console.print()
    console.print("After installing Node.js, run:")
    console.print("  npm install -g @anthropic-ai/claude-code")
    console.print()
    console.print("[dim]Or use legacy mode: triagent --legacy[/dim]")


def _step_claude_code(console: Console) -> bool:
    """Step 6: Claude Code CLI Installation.

    This step checks for Node.js and claude-code CLI.
    If not installed, attempts auto-install. If that fails,
    shows manual installation instructions.

    Returns:
        True if claude-code is available or user accepted fallback to legacy
    """
    console.print("[bold]Step 6/6: Claude Code CLI[/bold]")
    console.print("-" * 40)

    system = platform.system().lower()

    # Step 1: Check/Install Node.js
    nodejs_installed, nodejs_version = check_nodejs_installed()

    if nodejs_installed:
        console.print(f"[green]✓[/green] Node.js is installed: {nodejs_version}")
    else:
        console.print("[yellow]Node.js not detected. Installing...[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Installing Node.js (this may take a few minutes)...")
            success, message = install_nodejs()

        if success:
            console.print(f"[green]✓[/green] Node.js installed: {message}")
            # Verify npm is now available
            if not check_npm_installed():
                console.print("[yellow]Note: You may need to restart your terminal for npm to be available[/yellow]")
        else:
            console.print(f"[red]✗[/red] Auto-install failed: {message}")
            _show_manual_install_instructions(console, system)
            console.print()
            return True  # Don't fail setup

    # Step 2: Check/Install claude-code CLI
    installed, version = check_claude_code_installed()

    if installed:
        console.print(f"[green]✓[/green] Claude Code CLI is installed: {version}")
        console.print()
        return True

    # Not installed - offer to install
    console.print("[yellow]Claude Code CLI not detected.[/yellow]")
    console.print()
    console.print("[dim]Claude Code CLI is required for the SDK mode (default).[/dim]")
    console.print("[dim]Without it, use: triagent --legacy[/dim]")
    console.print()

    if confirm_prompt("Install Claude Code CLI now?", default=True):
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Installing @anthropic-ai/claude-code (this may take a few minutes)...")
            success, message = install_claude_code()

        if success:
            console.print(f"[green]✓[/green] Claude Code CLI installed: {message}")
            console.print()
            return True
        else:
            console.print(f"[red]✗[/red] Installation failed: {message}")
            console.print()
            console.print("[yellow]You can install manually:[/yellow]")
            console.print("  npm install -g @anthropic-ai/claude-code")
            console.print()
            console.print("[dim]Or use legacy mode: triagent --legacy[/dim]")
            console.print()
            return True  # Don't fail setup
    else:
        console.print()
        console.print("[dim]Skipped. To use triagent without Claude Code CLI:[/dim]")
        console.print("[dim]  triagent --legacy[/dim]")
        console.print()
        return True  # Don't fail setup


def _show_completion(
    console: Console,
    config_manager: ConfigManager,
    config: TriagentConfig,
) -> None:
    """Show setup completion summary."""
    team_config = get_team_config(config.team)
    team_name = team_config.display_name if team_config else config.team

    # Get API provider name
    credentials = config_manager.load_credentials()
    provider_name = dict(API_PROVIDERS).get(credentials.api_provider, credentials.api_provider)

    console.print(
        Panel(
            f"[bold green]Setup Complete![/bold green]\n\n"
            f"[bold]Config saved to:[/bold] {config_manager.config_file}\n"
            f"[bold]Team:[/bold] {team_name}\n"
            f"[bold]ADO Project:[/bold] {config.ado_project}\n"
            f"[bold]API Provider:[/bold] {provider_name}\n"
            f"[bold]MCP Servers:[/bold] Azure DevOps\n\n"
            "[dim]Type your message or use /help for commands[/dim]",
            border_style="green",
        )
    )
    console.print()
