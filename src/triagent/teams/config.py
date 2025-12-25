"""Team configurations for Triagent CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TeamConfig:
    """Configuration for a specific team."""

    name: str
    display_name: str
    ado_project: str
    ado_organization: str
    claude_md: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "ado_project": self.ado_project,
            "ado_organization": self.ado_organization,
            "claude_md": self.claude_md,
            "description": self.description,
        }


# Team configurations
TEAM_CONFIG: dict[str, TeamConfig] = {
    "levvia": TeamConfig(
        name="levvia",
        display_name="Levvia",
        ado_project="Project Omnia",
        ado_organization="symphonyvsts",
        claude_md="levvia.md",
        description="Levvia team configuration",
    ),
    "omnia": TeamConfig(
        name="omnia",
        display_name="Omnia",
        ado_project="Project Omnia",
        ado_organization="symphonyvsts",
        claude_md="omnia.md",
        description="Omnia team configuration",
    ),
    "omnia-data": TeamConfig(
        name="omnia-data",
        display_name="Omnia Data",
        ado_project="Audit Cortex 2",
        ado_organization="symphonyvsts",
        claude_md="omnia_data.md",
        description="Omnia Data team configuration",
    ),
}


def get_team_config(team_name: str) -> TeamConfig | None:
    """Get team configuration by name.

    Args:
        team_name: Team identifier (levvia, omnia, omnia-data)

    Returns:
        TeamConfig if found, None otherwise
    """
    return TEAM_CONFIG.get(team_name.lower())


def get_team_names() -> list[str]:
    """Get list of available team names."""
    return list(TEAM_CONFIG.keys())


def get_team_display_names() -> list[str]:
    """Get list of team display names for UI."""
    return [config.display_name for config in TEAM_CONFIG.values()]
