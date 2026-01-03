"""Confirm command - toggles write operation confirmations."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class ConfirmCommand(Command):
    """Toggle confirmation prompts for write operations."""

    name = "confirm"
    description = "Toggle write confirmation prompts"
    aliases = []

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Toggle the write confirmation setting.

        Note: auto_approve_writes=True means confirmations are DISABLED.
        We toggle this value and show appropriate message.
        """
        config = ctx.config_manager.load_config()

        # Toggle the auto_approve_writes setting
        # auto_approve_writes=True means skip confirmations (confirmations disabled)
        # auto_approve_writes=False means require confirmations (confirmations enabled)
        config.auto_approve_writes = not config.auto_approve_writes
        ctx.config_manager.save_config(config)

        confirmations_enabled = not config.auto_approve_writes

        if confirmations_enabled:
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
            data={"confirmations_enabled": confirmations_enabled},
        )


# Register the command
from triagent.core.commands import register_command
register_command(ConfirmCommand)
