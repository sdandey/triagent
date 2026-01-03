"""Team command - switch between teams."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class TeamCommand(Command):
    """Switch to a different team or show current team."""

    name = "team"
    description = "Switch team or show current team"
    aliases = []

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Switch team or display current team information."""
        from triagent.teams.config import TEAM_CONFIG, get_team_config

        config = ctx.config_manager.load_config()

        # If no argument, show current team and available options
        if not ctx.args:
            current_team = config.team or "not set"
            team_config = get_team_config(config.team) if config.team else None

            await ctx.output.show_panel(
                f"**Current Team:** {current_team}\n"
                f"**ADO Project:** {team_config.ado_project if team_config else 'N/A'}\n"
                f"**Persona:** {config.persona or 'default'}",
                title="Team Configuration",
                style="info",
            )

            # Show available teams
            rows = []
            for name, tc in TEAM_CONFIG.items():
                current = "✓" if name == config.team else ""
                rows.append([current, name, tc.display_name, tc.ado_project])

            await ctx.output.show_table(
                headers=["", "Team", "Display Name", "ADO Project"],
                rows=rows,
                title="Available Teams",
            )

            await ctx.output.write_text(
                "\nUse `/team <name>` to switch teams."
            )
            return CommandResult(success=True)

        # Switch to specified team
        new_team = ctx.args[0].lower()

        if new_team not in TEAM_CONFIG:
            available = ", ".join(TEAM_CONFIG.keys())
            return CommandResult(
                success=False,
                message=f"Unknown team: {new_team}. Available: {available}",
            )

        # Update config
        old_team = config.team
        config.team = new_team
        team_config = TEAM_CONFIG[new_team]
        config.ado_project = team_config.ado_project
        config.ado_organization = team_config.ado_organization

        # Reset persona to default for new team
        config.persona = "developer"

        ctx.config_manager.save_config(config)

        await ctx.output.show_panel(
            f"Switched from **{old_team or 'none'}** to **{new_team}**\n\n"
            f"ADO Project: {team_config.ado_project}\n"
            f"Persona: {config.persona}",
            title="Team Changed",
            style="success",
        )

        return CommandResult(
            success=True,
            requires_restart=True,
            data={"team": new_team, "persona": config.persona},
        )


# Register the command
from triagent.core.commands import register_command
register_command(TeamCommand)
