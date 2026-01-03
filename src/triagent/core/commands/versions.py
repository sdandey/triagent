"""Versions command - displays version information for all components."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class VersionsCommand(Command):
    """Display version information for Triagent and its components."""

    name = "versions"
    description = "Show version information"
    aliases = ["version", "v"]

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Display version information."""
        from triagent import __version__
        from triagent.versions import (
            AZURE_EXTENSION_VERSIONS,
            CLAUDE_CODE_VERSION,
            MCP_AZURE_DEVOPS_VERSION,
        )

        await ctx.output.show_panel(
            f"**Triagent** v{__version__}",
            title="Version Information",
            style="info",
        )

        # Core versions
        rows = [
            ["Triagent", __version__],
            ["Claude Code SDK", CLAUDE_CODE_VERSION],
            ["MCP Azure DevOps", MCP_AZURE_DEVOPS_VERSION],
        ]

        # Azure CLI extensions
        for ext_name, ext_version in AZURE_EXTENSION_VERSIONS.items():
            rows.append([f"Azure CLI: {ext_name}", ext_version])

        await ctx.output.show_table(
            headers=["Component", "Version"],
            rows=rows,
            title="Installed Versions",
        )

        return CommandResult(success=True)


# Register the command
from triagent.core.commands import register_command
register_command(VersionsCommand)
