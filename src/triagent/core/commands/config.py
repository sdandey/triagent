"""Config command - view and modify configuration."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class ConfigCommand(Command):
    """View or modify Triagent configuration."""

    name = "config"
    description = "View or modify configuration"
    aliases = ["cfg"]

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Display or modify configuration."""
        config = ctx.config_manager.load_config()
        credentials = ctx.config_manager.load_credentials()

        # If no arguments, show current config
        if not ctx.args:
            await ctx.output.show_panel(
                "Use `/config <key> <value>` to modify settings.",
                title="Current Configuration",
                style="info",
            )

            # Core settings
            core_items = [
                ("Team", config.team or "not set"),
                ("Persona", config.persona or "developer"),
                ("ADO Organization", config.ado_organization or "not set"),
                ("ADO Project", config.ado_project or "not set"),
            ]
            await ctx.output.show_key_value(core_items, title="Core Settings")

            # API settings
            api_items = [
                ("API Provider", credentials.api_provider or "not set"),
                ("API Key", "***" if credentials.anthropic_foundry_api_key else "not set"),
                ("Base URL", credentials.anthropic_foundry_base_url or "not set"),
            ]
            await ctx.output.show_key_value(api_items, title="API Settings")

            # Preferences
            pref_items = [
                ("Write Confirmations", "disabled" if config.auto_approve_writes else "enabled"),
                ("Markdown Mode", "enabled" if config.markdown_format else "disabled"),
                ("Verbose Mode", "enabled" if config.verbose else "disabled"),
            ]
            await ctx.output.show_key_value(pref_items, title="Preferences")

            return CommandResult(success=True)

        # Handle config modification
        if len(ctx.args) < 2:
            return CommandResult(
                success=False,
                message="Usage: /config <key> <value>",
            )

        key = ctx.args[0].lower()
        value = " ".join(ctx.args[1:])

        # Handle known keys
        if key in ("team", "persona"):
            return CommandResult(
                success=False,
                message=f"Use /{key} command to change {key}.",
            )

        # Boolean settings
        bool_settings = {
            "confirm": "auto_approve_writes",
            "markdown": "markdown_format",
            "verbose": "verbose",
        }

        if key in bool_settings:
            attr_name = bool_settings[key]
            bool_value = value.lower() in ("true", "1", "yes", "on", "enabled")
            setattr(config, attr_name, bool_value)
            ctx.config_manager.save_config(config)

            await ctx.output.show_panel(
                f"**{key}** set to **{'enabled' if bool_value else 'disabled'}**",
                title="Configuration Updated",
                style="success",
            )
            return CommandResult(success=True, data={key: bool_value})

        # Unknown key
        known_keys = list(bool_settings.keys()) + ["team", "persona"]
        return CommandResult(
            success=False,
            message=f"Unknown config key: {key}. Known keys: {', '.join(known_keys)}",
        )


# Register the command
from triagent.core.commands import register_command
register_command(ConfigCommand)
