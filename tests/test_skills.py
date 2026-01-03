"""Unit tests for the skills and persona system."""

from pathlib import Path

import pytest

from triagent.skills.loader import (
    get_available_personas,
    load_persona,
    load_persona_definition,
    load_skill,
    parse_frontmatter,
)
from triagent.skills.models import (
    PersonaDefinition,
    SkillDefinition,
    SkillMetadata,
)


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self) -> None:
        """Test parsing valid YAML frontmatter."""
        content = """---
name: test_skill
display_name: "Test Skill"
description: "A test skill"
version: "1.0.0"
---

## Skill Content

Instructions here.
"""
        frontmatter, remaining = parse_frontmatter(content)

        assert frontmatter["name"] == "test_skill"
        assert frontmatter["display_name"] == "Test Skill"
        assert frontmatter["description"] == "A test skill"
        assert "## Skill Content" in remaining

    def test_parse_no_frontmatter(self) -> None:
        """Test parsing content without frontmatter."""
        content = """# Just Markdown

No frontmatter here.
"""
        frontmatter, remaining = parse_frontmatter(content)

        assert frontmatter == {}
        assert "# Just Markdown" in remaining

    def test_parse_empty_frontmatter(self) -> None:
        """Test parsing empty frontmatter."""
        content = """---
---

Content here.
"""
        frontmatter, remaining = parse_frontmatter(content)

        assert frontmatter == {}
        assert "Content here." in remaining


class TestSkillMetadata:
    """Tests for SkillMetadata model."""

    def test_from_dict_minimal(self) -> None:
        """Test creating SkillMetadata with minimal fields."""
        data = {"name": "test_skill"}
        metadata = SkillMetadata.from_dict(data)

        assert metadata.name == "test_skill"
        assert metadata.display_name == ""  # Empty when not provided
        assert metadata.description == ""
        assert metadata.version == "1.0.0"
        assert metadata.tags == []
        assert metadata.requires == []
        assert metadata.subagents == []
        assert metadata.tools == []
        assert metadata.triggers == []

    def test_from_dict_full(self) -> None:
        """Test creating SkillMetadata with all fields."""
        data = {
            "name": "full_skill",
            "display_name": "Full Skill",
            "description": "A fully specified skill",
            "version": "2.0.0",
            "tags": ["code-review", "python"],
            "requires": ["ado_basics"],
            "subagents": ["python-code-reviewer"],
            "tools": ["Read", "Grep"],
            "triggers": ["review.*\\.py"],
        }
        metadata = SkillMetadata.from_dict(data)

        assert metadata.name == "full_skill"
        assert metadata.display_name == "Full Skill"
        assert metadata.description == "A fully specified skill"
        assert metadata.version == "2.0.0"
        assert metadata.tags == ["code-review", "python"]
        assert metadata.requires == ["ado_basics"]
        assert metadata.subagents == ["python-code-reviewer"]
        assert metadata.tools == ["Read", "Grep"]
        assert metadata.triggers == ["review.*\\.py"]


class TestPersonaDefinition:
    """Tests for PersonaDefinition model."""

    def test_from_dict(self) -> None:
        """Test creating PersonaDefinition from dict."""
        data = {
            "name": "developer",
            "display_name": "Developer",
            "description": "Developer persona",
            "core_skills": ["ado_basics"],
            "skills": ["dotnet_code_review"],
            "system_prompt_additions": "Additional context",
            "default_model": "sonnet",
        }
        persona = PersonaDefinition.from_dict(data, "omnia-data")

        assert persona.name == "developer"
        assert persona.display_name == "Developer"
        assert persona.team == "omnia-data"
        assert persona.core_skills == ["ado_basics"]
        assert persona.skills == ["dotnet_code_review"]


class TestLoadSkill:
    """Tests for skill loading from files."""

    def test_load_existing_skill(self, tmp_path: Path) -> None:
        """Test loading a skill from a valid markdown file."""
        skill_file = tmp_path / "test_skill.md"
        skill_file.write_text("""---
name: test_skill
display_name: "Test Skill"
description: "A test skill"
---

## Instructions

Do the thing.
""")
        skill = load_skill(skill_file)

        assert skill is not None
        assert skill.metadata.name == "test_skill"
        assert skill.metadata.display_name == "Test Skill"
        assert "Do the thing" in skill.content

    def test_load_nonexistent_skill(self, tmp_path: Path) -> None:
        """Test loading a non-existent skill returns None."""
        skill = load_skill(tmp_path / "nonexistent.md")
        assert skill is None

    def test_load_skill_without_frontmatter(self, tmp_path: Path) -> None:
        """Test loading a skill without frontmatter uses filename."""
        skill_file = tmp_path / "simple_skill.md"
        skill_file.write_text("Just some instructions.")

        skill = load_skill(skill_file)

        assert skill is not None
        assert skill.metadata.name == "simple_skill"


class TestLoadPersonaDefinition:
    """Tests for persona definition loading."""

    def test_load_omnia_data_developer(self) -> None:
        """Test loading the omnia-data developer persona."""
        persona = load_persona_definition("omnia-data", "developer")

        assert persona is not None
        assert persona.name == "developer"
        assert persona.display_name == "Developer"
        assert persona.team == "omnia-data"
        assert "ado_basics" in persona.core_skills

    def test_load_omnia_data_support(self) -> None:
        """Test loading the omnia-data support persona."""
        persona = load_persona_definition("omnia-data", "support")

        assert persona is not None
        assert persona.name == "support"
        assert persona.display_name == "Support"
        assert "telemetry_basics" in persona.core_skills

    def test_load_nonexistent_persona(self) -> None:
        """Test loading a non-existent persona returns None."""
        persona = load_persona_definition("omnia-data", "nonexistent")
        assert persona is None

    def test_load_nonexistent_team(self) -> None:
        """Test loading from a non-existent team returns None."""
        persona = load_persona_definition("nonexistent-team", "developer")
        assert persona is None


class TestGetAvailablePersonas:
    """Tests for listing available personas."""

    def test_get_omnia_data_personas(self) -> None:
        """Test getting personas for omnia-data team."""
        personas = get_available_personas("omnia-data")

        assert len(personas) >= 2
        persona_names = [p.name for p in personas]
        assert "developer" in persona_names
        assert "support" in persona_names

    def test_get_nonexistent_team_personas(self) -> None:
        """Test getting personas for non-existent team returns empty list."""
        personas = get_available_personas("nonexistent-team")
        assert personas == []


class TestLoadPersona:
    """Tests for complete persona loading."""

    def test_load_developer_persona(self) -> None:
        """Test loading complete developer persona with skills."""
        persona = load_persona("omnia-data", "developer")

        assert persona is not None
        assert persona.definition.name == "developer"
        # Should have core skills loaded
        assert "ado_basics" in persona.skills or len(persona.skills) > 0

    def test_load_support_persona(self) -> None:
        """Test loading complete support persona with skills."""
        persona = load_persona("omnia-data", "support")

        assert persona is not None
        assert persona.definition.name == "support"
        assert persona.definition.display_name == "Support"

    def test_load_nonexistent_persona(self) -> None:
        """Test loading non-existent persona returns None."""
        persona = load_persona("omnia-data", "nonexistent")
        assert persona is None
