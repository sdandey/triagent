"""Data models for skills and personas.

This module defines the core data structures for the skills system:
- SkillMetadata: Parsed from YAML frontmatter in skill markdown files
- SubagentConfig: Configuration for subagents that execute skills
- PersonaDefinition: Team-specific persona with composed skills
- LoadedPersona: Runtime representation with resolved skills and subagents
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillMetadata:
    """Metadata parsed from skill file YAML frontmatter.

    Example frontmatter:
    ```yaml
    ---
    name: dotnet_code_review
    display_name: ".NET Code Review"
    description: "Review .NET/C# code changes in PRs"
    version: "1.0.0"
    tags: [code-review, dotnet, csharp]
    requires: [ado_basics]
    subagents: [dotnet_analyzer]
    tools: [Read, Glob, Grep, mcp__azure-devops__add_pull_request_comment]
    triggers: ["review.*\\.cs", "review.*dotnet"]
    ---
    ```
    """

    name: str
    display_name: str
    description: str
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)  # Dependency skill names
    subagents: list[str] = field(default_factory=list)  # Subagent names
    tools: list[str] = field(default_factory=list)  # Required tool names
    triggers: list[str] = field(default_factory=list)  # Regex patterns for auto-activation

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillMetadata:
        """Create SkillMetadata from parsed YAML frontmatter."""
        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            requires=data.get("requires", []),
            subagents=data.get("subagents", []),
            tools=data.get("tools", []),
            triggers=data.get("triggers", []),
        )


@dataclass
class SkillDefinition:
    """Complete skill definition including metadata and content."""

    metadata: SkillMetadata
    content: str  # Markdown content after frontmatter
    file_path: Path | None = None  # Source file path

    @property
    def name(self) -> str:
        """Skill name from metadata."""
        return self.metadata.name


@dataclass
class SubagentConfig:
    """Configuration for a subagent that executes skills.

    This maps to Claude Agent SDK's AgentDefinition.
    The description is critical for automatic routing - Claude uses it
    to match user intent to the appropriate subagent.
    """

    name: str
    description: str  # Critical for Task tool routing
    prompt: str  # System prompt for the subagent
    tools: list[str] = field(default_factory=list)
    model: str = "sonnet"  # haiku, sonnet, or opus
    # File extension patterns for language detection
    file_extensions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubagentConfig:
        """Create SubagentConfig from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            prompt=data.get("prompt", ""),
            tools=data.get("tools", []),
            model=data.get("model", "sonnet"),
            file_extensions=data.get("file_extensions", []),
        )

    def to_agent_definition(self) -> dict[str, Any]:
        """Convert to Claude Agent SDK AgentDefinition format.

        Returns dict compatible with ClaudeAgentOptions.agents parameter.
        """
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "tools": self.tools,
            "model": self.model,
        }


@dataclass
class PersonaDefinition:
    """Definition for a team-specific persona (Developer, Support).

    Personas compose multiple skills and provide context for the system prompt.
    """

    name: str  # "developer" or "support"
    display_name: str  # "Developer" or "Support"
    description: str
    team: str  # Team identifier (e.g., "omnia-data")
    core_skills: list[str] = field(default_factory=list)  # Shared skill names
    skills: list[str] = field(default_factory=list)  # Persona-specific skill names
    on_demand_skills: list[str] = field(default_factory=list)  # Skills loaded via MCP tool
    system_prompt_additions: str = ""  # Additional context for system prompt
    default_model: str = "sonnet"

    @classmethod
    def from_dict(cls, data: dict[str, Any], team: str) -> PersonaDefinition:
        """Create PersonaDefinition from parsed YAML."""
        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            team=team,
            core_skills=data.get("core_skills", []),
            skills=data.get("skills", []),
            on_demand_skills=data.get("on_demand_skills", []),
            system_prompt_additions=data.get("system_prompt_additions", ""),
            default_model=data.get("default_model", "sonnet"),
        )


@dataclass
class LoadedPersona:
    """Runtime representation of a fully loaded persona.

    Contains resolved skills and subagents ready for use.
    """

    definition: PersonaDefinition
    skills: dict[str, SkillDefinition] = field(default_factory=dict)
    subagents: dict[str, SubagentConfig] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Persona name."""
        return self.definition.name

    @property
    def display_name(self) -> str:
        """Persona display name."""
        return self.definition.display_name

    @property
    def team(self) -> str:
        """Team identifier."""
        return self.definition.team

    def get_agent_definitions(self) -> dict[str, dict[str, Any]]:
        """Get all subagent definitions for SDK integration.

        Returns dict mapping subagent names to AgentDefinition dicts.
        """
        return {
            name: subagent.to_agent_definition()
            for name, subagent in self.subagents.items()
        }

    def get_system_prompt_additions(self) -> str:
        """Get persona-specific system prompt additions."""
        parts = []

        # Add persona context
        if self.definition.system_prompt_additions:
            parts.append(self.definition.system_prompt_additions)

        # Add skill content
        for skill in self.skills.values():
            if skill.content:
                parts.append(f"\n## {skill.metadata.display_name}\n{skill.content}")

        return "\n".join(parts)

    def get_all_tools(self) -> list[str]:
        """Get all tools required by this persona's skills."""
        tools = set()
        for skill in self.skills.values():
            tools.update(skill.metadata.tools)
        for subagent in self.subagents.values():
            tools.update(subagent.tools)
        return sorted(tools)


# File extension to code reviewer mapping for language detection
FILE_EXTENSION_MAP: dict[str, str] = {
    # C# / .NET
    ".cs": "csharp-code-reviewer",
    ".csproj": "csharp-code-reviewer",
    ".sln": "csharp-code-reviewer",
    # Python
    ".py": "python-code-reviewer",
    ".pyi": "python-code-reviewer",
    ".ipynb": "pyspark-code-reviewer",  # Notebooks -> PySpark
    # TypeScript / JavaScript
    ".ts": "typescript-code-reviewer",
    ".tsx": "typescript-code-reviewer",
    ".js": "typescript-code-reviewer",
    ".jsx": "typescript-code-reviewer",
}


def detect_code_reviewer(changed_files: list[str]) -> str:
    """Detect which code reviewer to use based on file extensions.

    Args:
        changed_files: List of file paths from PR changes

    Returns:
        Subagent name for the appropriate code reviewer
    """
    extension_counts: dict[str, int] = {}

    for file in changed_files:
        ext = Path(file).suffix.lower()
        if ext in FILE_EXTENSION_MAP:
            reviewer = FILE_EXTENSION_MAP[ext]
            extension_counts[reviewer] = extension_counts.get(reviewer, 0) + 1

    if not extension_counts:
        return "default-code-reviewer"

    # Return reviewer with most matching files
    return max(extension_counts, key=extension_counts.get)  # type: ignore[arg-type]
