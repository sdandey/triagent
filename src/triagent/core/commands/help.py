"""Help command - displays available commands and their descriptions."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class HelpCommand(Command):
    """Display help information about available commands."""

    name = "help"
    description = "Show available commands"
    aliases = ["h", "?"]

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Display help for all commands or a specific command."""
        from triagent.core.commands import get_all_commands, get_command

        # If argument provided, show help for specific command
        if ctx.args:
            cmd_name = ctx.args[0].lstrip("/")
            cmd_class = get_command(cmd_name)
            if cmd_class:
                await ctx.output.write_markdown(cmd_class().get_help())
                return CommandResult(success=True)
            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command: /{cmd_name}",
                )

        # Show all commands
        await ctx.output.show_panel(
            "**Triagent Commands**\n\nUse `/help <command>` for details.",
            title="Help",
            style="info",
        )

        # Build command list
        commands = get_all_commands()
        rows = []
        for name, cmd_class in sorted(commands.items()):
            if not cmd_class.hidden:
                cmd = cmd_class()
                aliases = ""
                if cmd.aliases:
                    aliases = f" ({', '.join('/' + a for a in cmd.aliases)})"
                rows.append([f"/{name}{aliases}", cmd.description])

        await ctx.output.show_table(
            headers=["Command", "Description"],
            rows=rows,
        )

        # Show environment-specific info
        if ctx.environment == "web":
            await ctx.output.write_text(
                "\n*Type a command in the chat to execute it.*"
            )
        else:
            await ctx.output.write_text(
                "\n*Type a command at the prompt to execute it.*"
            )

        return CommandResult(success=True)


# Register the command
from triagent.core.commands import register_command
register_command(HelpCommand)
