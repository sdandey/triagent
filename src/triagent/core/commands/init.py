"""Init command - unified setup wizard for CLI and Web.

This command provides a multi-step setup wizard that works across both
CLI and Web interfaces. Some steps (MCP setup, Azure auth, prerequisites)
are CLI-only and are skipped in the Web environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from triagent.core.commands.base import Command, CommandContext, CommandResult

if TYPE_CHECKING:
    from triagent.config import TriagentConfig, TriagentCredentials

# API Provider options
API_PROVIDERS = [
    ("azure_foundry", "Azure AI Foundry (recommended)"),
    ("anthropic", "Direct Anthropic API"),
]


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
        """Write failures to a log file."""
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


class InitCommand(Command):
    """Run the setup wizard to configure Triagent."""

    name = "init"
    description = "Run setup wizard"
    aliases = ["setup"]

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute the setup wizard.

        Steps:
        1. API Provider selection (CLI + Web)
        2. Team selection (CLI + Web)
        3. Persona selection (CLI + Web)
        4. MCP server setup (CLI only)
        5. Azure authentication (CLI only)
        6. Prerequisites check (CLI only)
        """
        from triagent.utils.environment import get_environment_type

        report = InitReport()
        env_type = get_environment_type()
        is_web = ctx.environment == "web"

        # Determine number of steps based on environment
        total_steps = 3 if is_web else 6

        # Welcome message
        await ctx.output.show_panel(
            f"**Welcome to Triagent Setup**\n\n"
            f"This wizard will configure Triagent for Azure DevOps automation.\n"
            f"*Environment: {env_type}*",
            title="Setup Wizard",
            style="info",
        )

        # Step 1: API Provider
        credentials = await self._step_api_provider(ctx, 1, total_steps)
        if credentials is None:
            # Check if user cancelled or just kept existing config
            existing_creds = ctx.config_manager.load_credentials()
            if not existing_creds.api_provider:
                return CommandResult(success=False, message="Setup cancelled")
            # User kept existing config, continue
            credentials = existing_creds

        # Step 2: Team Selection
        config = await self._step_team_selection(ctx, 2, total_steps)
        if config is None:
            return CommandResult(success=False, message="Setup cancelled")

        # Step 3: Persona Selection
        config = await self._step_persona_selection(ctx, config, 3, total_steps)

        # CLI-only steps
        if not is_web:
            # Step 4: MCP Server Setup
            await self._step_mcp_setup(ctx, config, 4, total_steps)

            # Step 5: Azure Authentication
            await self._step_azure_auth(ctx, report, 5, total_steps)

            # Step 6: Prerequisites Check
            await self._step_prerequisites(ctx, report, 6, total_steps)

        # Save configuration
        ctx.config_manager.save_config(config)
        if credentials:
            ctx.config_manager.save_credentials(credentials)

        # Show completion summary
        await self._show_completion(ctx, config, credentials, report)

        return CommandResult(
            success=True,
            requires_restart=True,
            data={
                "team": config.team,
                "persona": config.persona,
                "api_provider": credentials.api_provider if credentials else None,
            },
        )

    async def _step_api_provider(
        self,
        ctx: CommandContext,
        step: int,
        total: int,
    ) -> TriagentCredentials | None:
        """Step 1: API Provider selection and configuration."""
        from triagent.config import TriagentCredentials

        await ctx.output.write_text(f"**Step {step}/{total}: Claude API Provider**")

        credentials = ctx.config_manager.load_credentials()

        # Check if already configured
        current_provider = credentials.api_provider
        has_token = (
            (current_provider == "azure_foundry" and credentials.anthropic_foundry_api_key)
            or current_provider == "anthropic"
        )

        if has_token:
            provider_name = dict(API_PROVIDERS).get(current_provider, current_provider)
            await ctx.prompt.display_message(
                f"API provider configured: {provider_name}",
                style="success",
            )

            reconfigure = await ctx.prompt.ask_confirmation(
                "Reconfigure API provider?",
                default=False,
            )
            if not reconfigure:
                return None  # Keep existing config

        # Show provider options
        options = [(key, name) for key, name in API_PROVIDERS]
        provider_key = await ctx.prompt.ask_selection(
            "Select your Claude API provider:",
            options,
        )

        if provider_key is None:
            return None

        credentials.api_provider = provider_key

        # Configure based on provider
        if provider_key == "azure_foundry":
            credentials = await self._configure_azure_foundry(ctx, credentials)
        else:
            await ctx.prompt.display_message(
                "Using direct Anthropic API (requires ANTHROPIC_API_KEY env var)",
                style="info",
            )

        return credentials

    async def _configure_azure_foundry(
        self,
        ctx: CommandContext,
        credentials: TriagentCredentials,
    ) -> TriagentCredentials:
        """Configure Azure AI Foundry API settings."""
        await ctx.prompt.display_message(
            "Configure Azure AI Foundry settings:",
            style="info",
        )

        # Get Base URL
        default_url = credentials.anthropic_foundry_base_url or ""
        base_url = await ctx.prompt.ask_text(
            "Target URI (Azure Foundry endpoint):",
            default=default_url if default_url else None,
        )
        if base_url:
            credentials.anthropic_foundry_base_url = base_url

        # Get API Key
        api_key = await ctx.prompt.ask_text(
            "API Key:",
            secret=True,
        )
        if api_key:
            credentials.anthropic_foundry_api_key = api_key

        # Get Model/Deployment name
        default_model = credentials.anthropic_foundry_model or "claude-opus-4-5"
        model = await ctx.prompt.ask_text(
            "Deployment Name:",
            default=default_model,
        )
        if model:
            credentials.anthropic_foundry_model = model

        # Test connection (CLI only - Web doesn't have httpx readily available)
        if ctx.environment == "cli" and credentials.anthropic_foundry_api_key:
            await ctx.prompt.display_progress("Testing connection...")
            success = await self._test_azure_foundry_connection(ctx, credentials)
            if success:
                await ctx.prompt.display_message("Connection successful!", style="success")
            else:
                await ctx.prompt.display_message(
                    "Connection test failed. Please verify your credentials.",
                    style="warning",
                )

        return credentials

    async def _test_azure_foundry_connection(
        self,
        ctx: CommandContext,
        credentials: TriagentCredentials,
    ) -> bool:
        """Test Azure AI Foundry API connection."""
        try:
            import httpx

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

            return response.status_code == 200
        except Exception:
            return False

    async def _step_team_selection(
        self,
        ctx: CommandContext,
        step: int,
        total: int,
    ) -> TriagentConfig | None:
        """Step 2: Team Selection."""
        from triagent.teams.config import TEAM_CONFIG

        await ctx.output.write_text(f"**Step {step}/{total}: Team Selection**")

        config = ctx.config_manager.load_config()

        # Build options
        options = [
            (name, f"{tc.display_name} ({tc.ado_project})")
            for name, tc in TEAM_CONFIG.items()
        ]

        team_name = await ctx.prompt.ask_selection(
            "Select your team:",
            options,
        )

        if team_name is None:
            return None

        team_config = TEAM_CONFIG[team_name]
        config.team = team_name
        config.ado_project = team_config.ado_project
        config.ado_organization = team_config.ado_organization

        await ctx.prompt.display_message(
            f"Selected: {team_config.display_name}",
            style="success",
        )

        return config

    async def _step_persona_selection(
        self,
        ctx: CommandContext,
        config: TriagentConfig,
        step: int,
        total: int,
    ) -> TriagentConfig:
        """Step 3: Persona Selection."""
        from triagent.skills import get_available_personas

        await ctx.output.write_text(f"**Step {step}/{total}: Persona Selection**")

        personas = get_available_personas(config.team)

        if not personas:
            await ctx.prompt.display_message(
                "No personas defined for this team. Using default.",
                style="info",
            )
            config.persona = "developer"
            return config

        # Build options
        options = [
            (p.name, f"{p.display_name} - {p.description}")
            for p in personas
        ]

        persona_name = await ctx.prompt.ask_selection(
            "Select your persona:",
            options,
        )

        if persona_name:
            config.persona = persona_name
            selected = next((p for p in personas if p.name == persona_name), None)
            if selected:
                await ctx.prompt.display_message(
                    f"Selected: {selected.display_name}",
                    style="success",
                )
        else:
            config.persona = "developer"

        return config

    async def _step_mcp_setup(
        self,
        ctx: CommandContext,
        config: TriagentConfig,
        step: int,
        total: int,
    ) -> None:
        """Step 4: MCP Server Setup (CLI only)."""
        from triagent.mcp.setup import setup_mcp_servers

        await ctx.output.write_text(f"**Step {step}/{total}: Azure DevOps MCP Server**")

        await ctx.prompt.display_progress("Configuring MCP servers...")

        setup_mcp_servers(
            ctx.config_manager,
            config.ado_organization,
            config.ado_project,
        )

        await ctx.prompt.display_message(
            f"MCP server configured at {ctx.config_manager.mcp_servers_file}",
            style="success",
        )

    async def _step_azure_auth(
        self,
        ctx: CommandContext,
        report: InitReport,
        step: int,
        total: int,
    ) -> None:
        """Step 5: Azure Authentication (CLI only)."""
        import platform

        from triagent.mcp.setup import (
            check_azure_cli_installed,
            get_azure_account,
            run_azure_login,
        )

        await ctx.output.write_text(f"**Step {step}/{total}: Azure Authentication**")

        # Check if Azure CLI is installed
        az_installed, _ = check_azure_cli_installed()
        if not az_installed:
            system = platform.system().lower()
            install_cmd = {
                "darwin": "brew install azure-cli",
                "windows": "Download from: https://aka.ms/installazurecliwindows",
            }.get(system, "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")

            await ctx.prompt.display_message(
                f"Azure CLI not detected. Install with:\n  {install_cmd}",
                style="warning",
            )
            report.add_warning("Azure CLI not installed - manual authentication required")
            return

        # Check if already logged in
        account = get_azure_account()
        if account:
            user = account.get("user", {}).get("name", "Unknown")
            await ctx.prompt.display_message(
                f"Already authenticated as: {user}",
                style="success",
            )
            report.add_success(f"Azure authenticated: {user}")

            use_existing = await ctx.prompt.ask_confirmation(
                "Use this account?",
                default=True,
            )
            if use_existing:
                config = ctx.config_manager.load_config()
                config.azure_cli_authenticated = True
                ctx.config_manager.save_config(config)
                return

        # Need to authenticate
        await ctx.prompt.display_message(
            "Opening browser for Azure authentication...",
            style="info",
        )

        if run_azure_login():
            account = get_azure_account()
            if account:
                user = account.get("user", {}).get("name", "Unknown")
                await ctx.prompt.display_message(
                    f"Authenticated as: {user}",
                    style="success",
                )
                report.add_success(f"Azure authenticated: {user}")

                config = ctx.config_manager.load_config()
                config.azure_cli_authenticated = True
                ctx.config_manager.save_config(config)
            else:
                await ctx.prompt.display_message(
                    "Authentication status unknown (will continue)",
                    style="warning",
                )
                report.add_warning("Azure authentication status unknown")
        else:
            await ctx.prompt.display_message(
                "Azure login failed (will continue)",
                style="warning",
            )
            report.add_failure(
                step=f"Step {step}/{total}",
                component="Azure Authentication",
                error="Azure login command failed",
                manual_fix="az login",
            )

    async def _step_prerequisites(
        self,
        ctx: CommandContext,
        report: InitReport,
        step: int,
        total: int,
    ) -> None:
        """Step 6: Prerequisites Check (CLI only)."""
        import platform

        from triagent.mcp.setup import (
            REQUIRED_AZURE_EXTENSIONS,
            check_azure_cli_installed,
            check_azure_extension,
            check_claude_code_installed,
            check_nodejs_installed,
        )
        from triagent.utils.environment import is_docker
        from triagent.utils.windows import find_git_bash, is_windows

        await ctx.output.write_text(f"**Step {step}/{total}: Prerequisites Check**")

        system = platform.system().lower()
        rows = []

        # Check Azure CLI
        az_installed, az_version = check_azure_cli_installed()
        if az_installed:
            rows.append(["Azure CLI", az_version, "OK"])
            report.add_success(f"Azure CLI: {az_version}")

            # Check extensions
            for ext_name in REQUIRED_AZURE_EXTENSIONS:
                if check_azure_extension(ext_name):
                    rows.append([f"Extension: {ext_name}", "", "OK"])
                else:
                    rows.append([f"Extension: {ext_name}", "", "Missing"])
        else:
            rows.append(["Azure CLI", "", "Not found"])
            report.add_warning("Azure CLI not installed")

        # Check Node.js
        node_installed, node_version = check_nodejs_installed()
        if node_installed:
            rows.append(["Node.js", node_version, "OK"])
            report.add_success(f"Node.js: {node_version}")
        else:
            rows.append(["Node.js", "", "Not found"])
            report.add_warning("Node.js not installed - MCP servers may not work")

        # Check Git Bash on Windows
        if is_windows():
            bash_path = find_git_bash()
            if bash_path:
                rows.append(["Git Bash", bash_path, "OK"])
                report.add_success(f"Git Bash: {bash_path}")
            else:
                rows.append(["Git Bash", "", "Not found"])
                report.add_warning("Git Bash not found")

        # Check Claude Code
        if is_docker():
            rows.append(["Claude Code", "Skipped (Docker)", "OK"])
        else:
            cc_installed, cc_version = check_claude_code_installed()
            if cc_installed:
                rows.append(["Claude Code", cc_version, "OK"])
                report.add_success(f"Claude Code: {cc_version}")
            else:
                rows.append(["Claude Code", "", "Not found"])
                report.add_warning("Claude Code CLI not installed")

        await ctx.output.show_table(
            headers=["Component", "Version", "Status"],
            rows=rows,
            title="Prerequisites",
        )

    async def _show_completion(
        self,
        ctx: CommandContext,
        config: TriagentConfig,
        credentials: TriagentCredentials | None,
        report: InitReport,
    ) -> None:
        """Show setup completion summary."""
        from triagent.skills import get_available_personas
        from triagent.teams.config import get_team_config

        team_config = get_team_config(config.team)
        team_name = team_config.display_name if team_config else config.team

        # Get API provider name
        if credentials:
            provider_name = dict(API_PROVIDERS).get(
                credentials.api_provider, credentials.api_provider
            )
        else:
            provider_name = "Not configured"

        # Get persona display name
        personas = get_available_personas(config.team)
        persona_display = config.persona.title() if config.persona else "Default"
        for p in personas:
            if p.name == config.persona:
                persona_display = p.display_name
                break

        await ctx.output.show_panel(
            f"**Setup Complete!**\n\n"
            f"**Team:** {team_name}\n"
            f"**Persona:** {persona_display}\n"
            f"**ADO Project:** {config.ado_project}\n"
            f"**API Provider:** {provider_name}\n\n"
            f"*Type your message or use /help for commands*",
            title="Success",
            style="success",
        )

        # Show warnings/failures if any
        if report.has_failures():
            failure_list = "\n".join([f"- {f.component}" for f in report.failures])
            await ctx.output.show_panel(
                f"**Some components need attention:**\n\n{failure_list}",
                title="Warnings",
                style="warning",
            )
        elif report.warnings:
            warning_list = "\n".join([f"- {w}" for w in report.warnings])
            await ctx.output.show_panel(
                f"**Warnings:**\n\n{warning_list}",
                title="Warnings",
                style="warning",
            )


# Register the command
from triagent.core.commands import register_command
register_command(InitCommand)
