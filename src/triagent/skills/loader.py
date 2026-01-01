"""Skill and persona loader for the triagent skills system.

This module handles:
- Parsing YAML frontmatter from markdown skill files
- Loading individual skills from .md files
- Loading persona definitions from YAML files
- Composing complete personas with all their skills and subagents
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .models import (
    LoadedPersona,
    PersonaDefinition,
    SkillDefinition,
    SkillMetadata,
    SubagentConfig,
)

# Base directory for skills files
SKILLS_DIR = Path(__file__).parent


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter dict, remaining content)

    Example:
        ```
        ---
        name: my_skill
        description: A skill
        ---

        ## Skill Content
        Instructions here...
        ```
    """
    # Match YAML frontmatter between --- delimiters
    frontmatter_pattern = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n?",
        re.DOTALL | re.MULTILINE,
    )

    match = frontmatter_pattern.match(content)
    if not match:
        return {}, content

    frontmatter_yaml = match.group(1)
    remaining_content = content[match.end():].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_yaml) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, remaining_content


def load_skill(path: Path) -> SkillDefinition | None:
    """Load a single skill from a markdown file.

    Args:
        path: Path to the skill .md file

    Returns:
        SkillDefinition or None if loading fails
    """
    if not path.exists() or not path.suffix == ".md":
        return None

    try:
        content = path.read_text(encoding="utf-8")
        frontmatter, skill_content = parse_frontmatter(content)

        if not frontmatter.get("name"):
            # Use filename as name if not specified
            frontmatter["name"] = path.stem

        metadata = SkillMetadata.from_dict(frontmatter)
        return SkillDefinition(
            metadata=metadata,
            content=skill_content,
            file_path=path,
        )
    except Exception:
        return None


def load_subagent(path: Path) -> SubagentConfig | None:
    """Load a subagent configuration from a Python or YAML file.

    Args:
        path: Path to the subagent config file

    Returns:
        SubagentConfig or None if loading fails
    """
    if not path.exists():
        return None

    try:
        if path.suffix == ".yaml" or path.suffix == ".yml":
            content = yaml.safe_load(path.read_text(encoding="utf-8"))
            return SubagentConfig.from_dict(content)
        elif path.suffix == ".py":
            # Import and get SUBAGENT_CONFIG dict
            # For safety, we parse the file rather than executing it
            content = path.read_text(encoding="utf-8")

            # Simple extraction of SUBAGENT_CONFIG dict
            # This is a simplified approach - in production, use AST parsing
            config_match = re.search(
                r'SUBAGENT_CONFIG\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
                content,
                re.DOTALL,
            )
            if config_match:
                # Parse the dict-like string (simplified)
                config_str = "{" + config_match.group(1) + "}"
                # Convert to valid Python dict
                # This is a simplified approach for demonstration
                try:
                    # Use eval in a restricted context
                    config = eval(config_str, {"__builtins__": {}}, {})  # noqa: S307
                    return SubagentConfig.from_dict(config)
                except Exception:
                    pass
        return None
    except Exception:
        return None


def create_subagent_from_skill(skill: SkillDefinition, subagent_name: str) -> SubagentConfig:
    """Create SubagentConfig from skill content.

    The skill's markdown content becomes the subagent's prompt.
    The skill's description and tools are inherited. This allows subagent
    prompts to be generated dynamically from the skill files without
    requiring separate YAML configuration files.

    Args:
        skill: The skill definition containing metadata and content
        subagent_name: The subagent name from skill.metadata.subagents

    Returns:
        SubagentConfig generated from skill content
    """
    # Build the subagent prompt from skill content
    prompt = f"""You are a {skill.metadata.display_name} specialist.

{skill.content}

When providing feedback:
- Organize by priority (Critical, High, Medium, Low)
- Include specific code examples showing fixes
- Reference the guidelines above"""

    return SubagentConfig(
        name=subagent_name,
        description=skill.metadata.description,
        prompt=prompt,
        tools=skill.metadata.tools,
        model="sonnet",
    )


def load_persona_definition(team: str, persona_name: str) -> PersonaDefinition | None:
    """Load a persona definition from YAML file.

    Args:
        team: Team identifier (e.g., "omnia-data")
        persona_name: Persona name ("developer" or "support")

    Returns:
        PersonaDefinition or None if not found
    """
    persona_file = SKILLS_DIR / team / f"_persona_{persona_name}.yaml"

    if not persona_file.exists():
        return None

    try:
        data = yaml.safe_load(persona_file.read_text(encoding="utf-8"))
        data["name"] = persona_name  # Ensure name is set
        return PersonaDefinition.from_dict(data, team)
    except Exception:
        return None


def get_available_personas(team: str) -> list[PersonaDefinition]:
    """Get all available personas for a team.

    Args:
        team: Team identifier

    Returns:
        List of PersonaDefinition objects
    """
    team_dir = SKILLS_DIR / team
    if not team_dir.exists():
        return []

    personas = []
    for persona_file in team_dir.glob("_persona_*.yaml"):
        persona_name = persona_file.stem.replace("_persona_", "")
        persona = load_persona_definition(team, persona_name)
        if persona:
            personas.append(persona)

    return personas


def load_persona(team: str, persona_name: str) -> LoadedPersona | None:
    """Load a complete persona with all skills and subagents.

    Args:
        team: Team identifier (e.g., "omnia-data")
        persona_name: Persona name ("developer" or "support")

    Returns:
        LoadedPersona with all resolved skills and subagents
    """
    # Load persona definition
    definition = load_persona_definition(team, persona_name)
    if not definition:
        return None

    skills: dict[str, SkillDefinition] = {}
    subagents: dict[str, SubagentConfig] = {}

    # Load core skills
    core_dir = SKILLS_DIR / "core"
    for skill_name in definition.core_skills:
        skill_path = core_dir / f"{skill_name}.md"
        skill = load_skill(skill_path)
        if skill:
            skills[skill_name] = skill

    # Load persona-specific skills
    persona_dir = SKILLS_DIR / team / persona_name
    for skill_name in definition.skills:
        skill_path = persona_dir / f"{skill_name}.md"
        skill = load_skill(skill_path)
        if skill:
            skills[skill_name] = skill

    # Load subagents from core
    core_subagents_dir = core_dir / "_subagents"
    if core_subagents_dir.exists():
        for subagent_file in core_subagents_dir.glob("*.yaml"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent
        for subagent_file in core_subagents_dir.glob("*.py"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent

    # Load subagents from team
    team_subagents_dir = SKILLS_DIR / team / "_subagents"
    if team_subagents_dir.exists():
        for subagent_file in team_subagents_dir.glob("*.yaml"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent
        for subagent_file in team_subagents_dir.glob("*.py"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent

    # Generate subagents dynamically from skills that reference them
    # This allows skill markdown content to become the subagent's prompt
    # without requiring separate YAML configuration files
    for _skill_name, skill in skills.items():
        for subagent_name in skill.metadata.subagents:
            if subagent_name not in subagents:
                subagents[subagent_name] = create_subagent_from_skill(skill, subagent_name)

    return LoadedPersona(
        definition=definition,
        skills=skills,
        subagents=subagents,
    )


class SkillLoader:
    """Convenience class for loading skills and personas."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        """Initialize skill loader.

        Args:
            skills_dir: Custom skills directory (defaults to package dir)
        """
        self.skills_dir = skills_dir or SKILLS_DIR

    def get_available_teams(self) -> list[str]:
        """Get list of teams with skills defined."""
        teams = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_") and item.name != "core":
                teams.append(item.name)
        return sorted(teams)

    def get_personas_for_team(self, team: str) -> list[PersonaDefinition]:
        """Get available personas for a team."""
        return get_available_personas(team)

    def load_persona(self, team: str, persona_name: str) -> LoadedPersona | None:
        """Load a complete persona."""
        return load_persona(team, persona_name)

    def load_skill(self, path: Path) -> SkillDefinition | None:
        """Load a single skill from file."""
        return load_skill(path)
