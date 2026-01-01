"""Skills and personas system for triagent.

This module provides the skills architecture that enables:
- Team-specific personas (Developer, Support)
- Composed skill sets with YAML frontmatter metadata
- Subagent configuration for automatic routing
- Language detection for code review tasks

Usage:
    from triagent.skills import SkillLoader, load_persona

    # Load a persona
    loader = SkillLoader()
    persona = loader.load_persona("omnia-data", "developer")

    # Get subagent definitions for SDK
    agents = persona.get_agent_definitions()

    # Detect code reviewer from PR files
    from triagent.skills import detect_code_reviewer
    reviewer = detect_code_reviewer([".cs", ".csproj"])
"""

from .loader import (
    SkillLoader,
    get_available_personas,
    load_persona,
    load_skill,
    parse_frontmatter,
)
from .models import (
    FILE_EXTENSION_MAP,
    LoadedPersona,
    PersonaDefinition,
    SkillDefinition,
    SkillMetadata,
    SubagentConfig,
    detect_code_reviewer,
)

__all__ = [
    # Models
    "SkillMetadata",
    "SkillDefinition",
    "SubagentConfig",
    "PersonaDefinition",
    "LoadedPersona",
    # Loader
    "SkillLoader",
    "load_skill",
    "load_persona",
    "get_available_personas",
    "parse_frontmatter",
    # Language detection
    "FILE_EXTENSION_MAP",
    "detect_code_reviewer",
]
