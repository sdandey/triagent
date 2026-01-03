"""Confirm command - toggles write operation confirmations."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class ConfirmCommand(Command):
    """Toggle confirmation prompts for write operations."""

    name = "confirm"
    description = "Toggle write confirmation prompts"
    aliases = []

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Toggle the write confirmation setting."""
        config = ctx.config_manager.load_config()

        # Toggle the setting
        new_value = not config.require_write_confirmation
        config.require_write_confirmation = new_value
        ctx.config_manager.save_config(config)

        if new_value:
            await ctx.output.show_panel(
                "Write confirmations are now **enabled**.\n\n"
                "You will be prompted before any write operations "
                "(creating work items, adding PR comments, etc.).",
                title="Confirmations Enabled",
                style="success",
            )
        else:
            await ctx.output.show_panel(
                "Write confirmations are now **disabled**.\n\n"
                "Write operations will execute without prompting. "
                "Use `/confirm` again to re-enable.",
                title="Confirmations Disabled",
                style="warning",
            )

        return CommandResult(
            success=True,
            data={"require_write_confirmation": new_value},
        )


# Register the command
from triagent.core.commands import register_command
register_command(ConfirmCommand)
