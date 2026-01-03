"""Clear command - clears conversation history."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class ClearCommand(Command):
    """Clear the conversation history."""

    name = "clear"
    description = "Clear conversation history"
    aliases = ["cls"]

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Clear the conversation history."""
        await ctx.output.write_text("Conversation history cleared.")
        return CommandResult(
            success=True,
            should_clear=True,
            message="Conversation cleared",
        )


# Register the command
from triagent.core.commands import register_command
register_command(ClearCommand)
