"""System prompts for Triagent CLI."""

from __future__ import annotations

from pathlib import Path

from triagent.teams.config import get_team_config

# Base directory for CLAUDE.md files
CLAUDE_MD_DIR = Path(__file__).parent / "claude_md"


BASE_SYSTEM_PROMPT = """You are Triagent, a Claude-powered assistant for Azure DevOps automation.

You have access to Azure CLI commands and Azure DevOps MCP tools to help users:
- Query Azure Kusto for log data
- Create and manage Azure DevOps work items
- Create, review, and manage Pull Requests
- Monitor build and release pipelines

Always be helpful, concise, and professional in your responses."""


def get_claude_md_content(team_name: str) -> str:
    """Load team-specific CLAUDE.md content.

    Args:
        team_name: Team identifier

    Returns:
        CLAUDE.md content for the team
    """
    team_config = get_team_config(team_name)
    if not team_config:
        return ""

    claude_md_path = CLAUDE_MD_DIR / team_config.claude_md
    if not claude_md_path.exists():
        return ""

    return claude_md_path.read_text()


def get_system_prompt(team_name: str) -> str:
    """Get the full system prompt for a team.

    Args:
        team_name: Team identifier

    Returns:
        Complete system prompt including team-specific instructions
    """
    team_config = get_team_config(team_name)

    prompt_parts = [BASE_SYSTEM_PROMPT]

    if team_config:
        prompt_parts.append("\n## Team Context\n")
        prompt_parts.append(f"- Team: {team_config.display_name}")
        prompt_parts.append(f"- ADO Project: {team_config.ado_project}")
        prompt_parts.append(f"- ADO Organization: {team_config.ado_organization}")

    # Add team-specific CLAUDE.md content
    claude_md = get_claude_md_content(team_name)
    if claude_md:
        prompt_parts.append(f"\n## Team Instructions\n{claude_md}")

    return "\n".join(prompt_parts)
