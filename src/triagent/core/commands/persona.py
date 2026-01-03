"""Persona command - switch between personas within a team."""

from __future__ import annotations

from triagent.core.commands.base import Command, CommandContext, CommandResult


class PersonaCommand(Command):
    """Switch to a different persona or show current persona."""

    name = "persona"
    description = "Switch persona or show current persona"
    aliases = ["p"]

    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Switch persona or display current persona information."""
        from triagent.skills import get_available_personas

        config = ctx.config_manager.load_config()

        if not config.team:
            return CommandResult(
                success=False,
                message="No team selected. Use /team to select a team first.",
            )

        # Get available personas for current team
        personas = get_available_personas(config.team)

        if not personas:
            return CommandResult(
                success=False,
                message=f"No personas defined for team: {config.team}",
            )

        # If no argument, show current persona and available options
        if not ctx.args:
            current_persona = config.persona or "developer"

            await ctx.output.show_panel(
                f"**Team:** {config.team}\n"
                f"**Current Persona:** {current_persona}",
                title="Persona Configuration",
                style="info",
            )

            # Show available personas
            rows = []
            for persona in personas:
                current = "✓" if persona.name == current_persona else ""
                rows.append([current, persona.name, persona.display_name, persona.description])

            await ctx.output.show_table(
                headers=["", "Name", "Display Name", "Description"],
                rows=rows,
                title="Available Personas",
            )

            await ctx.output.write_text(
                "\nUse `/persona <name>` to switch personas."
            )
            return CommandResult(success=True)

        # Switch to specified persona
        new_persona = ctx.args[0].lower()

        # Validate persona exists
        persona_names = [p.name for p in personas]
        if new_persona not in persona_names:
            available = ", ".join(persona_names)
            return CommandResult(
                success=False,
                message=f"Unknown persona: {new_persona}. Available: {available}",
            )

        # Update config
        old_persona = config.persona
        config.persona = new_persona
        ctx.config_manager.save_config(config)

        # Find persona details
        persona_info = next((p for p in personas if p.name == new_persona), None)
        display_name = persona_info.display_name if persona_info else new_persona

        await ctx.output.show_panel(
            f"Switched from **{old_persona or 'default'}** to **{new_persona}**\n\n"
            f"Persona: {display_name}\n"
            f"Team: {config.team}",
            title="Persona Changed",
            style="success",
        )

        return CommandResult(
            success=True,
            requires_restart=True,
            data={"persona": new_persona, "team": config.team},
        )


# Register the command
from triagent.core.commands import register_command
register_command(PersonaCommand)
