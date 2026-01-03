"""Unit tests for system prompt construction."""

import pytest

from triagent.skills.system import get_system_prompt
from triagent.skills.loader import load_persona


class TestSystemPromptConstruction:
    """Tests for system prompt construction with different personas."""

    def test_developer_persona_includes_core_skills(self) -> None:
        """Test that developer persona system prompt includes all core skills."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify BASE_SYSTEM_PROMPT content
        assert "You are Triagent" in prompt
        assert "Azure DevOps automation" in prompt

        # Verify team context
        assert "Omnia Data" in prompt
        assert "Audit Cortex 2" in prompt

        # Verify active persona
        assert "Active Persona: Developer" in prompt

        # Verify core skills are listed
        assert "Azure DevOps Basics" in prompt
        assert "Telemetry Basics" in prompt
        assert "ADO LSI/Defect Creation" in prompt

        # Verify core skill CONTENT is included (not just names)
        assert "az boards work-item show" in prompt  # From ado_basics.md
        assert "AppExceptions" in prompt  # From telemetry_basics.md
        assert "Service to Team Mapping" in prompt  # From ado_lsi_defect.md

    def test_support_persona_includes_core_skills(self) -> None:
        """Test that support persona system prompt includes all core skills."""
        prompt = get_system_prompt("omnia-data", "support")

        # Verify active persona
        assert "Active Persona: Support" in prompt

        # Verify core skills content
        assert "Azure DevOps Basics" in prompt
        assert "Telemetry Basics" in prompt
        assert "ADO LSI/Defect Creation" in prompt

        # Verify telemetry-specific content is present
        assert "Log Analytics Workspace Reference" in prompt
        assert "Subscription Switching" in prompt

    def test_developer_persona_includes_persona_specific_skills(self) -> None:
        """Test that developer persona includes developer-specific skills."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify developer-specific skills listed
        assert "Developer Skills" in prompt

        # Verify developer skill content included
        # (These may vary based on actual skill files)
        persona = load_persona("omnia-data", "developer")
        for skill_name in persona.definition.skills:
            if skill_name in persona.skills:
                skill = persona.skills[skill_name]
                assert skill.metadata.display_name in prompt

    def test_support_persona_includes_persona_specific_skills(self) -> None:
        """Test that support persona includes support-specific skills."""
        prompt = get_system_prompt("omnia-data", "support")

        # Verify support-specific skills listed
        assert "Support Skills" in prompt

        # Verify support skill content included
        persona = load_persona("omnia-data", "support")
        for skill_name in persona.definition.skills:
            if skill_name in persona.skills:
                skill = persona.skills[skill_name]
                assert skill.metadata.display_name in prompt

    def test_system_prompt_includes_organization_context(self) -> None:
        """Test that system prompt includes correct ADO organization context."""
        prompt = get_system_prompt("omnia-data", "developer")

        assert "symphonyvsts" in prompt
        assert "Audit Cortex 2" in prompt

    def test_ado_basics_content_in_prompt(self) -> None:
        """Test that ado_basics skill content is fully embedded."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify key sections from ado_basics.md
        assert "Organization Context" in prompt
        assert "https://dev.azure.com/symphonyvsts" in prompt
        assert "Work Item Operations" in prompt
        assert "Repository Reference" in prompt
        assert "workpaper-service" in prompt  # From repo table
        assert "REST API (For HTML Content)" in prompt

    def test_telemetry_basics_content_in_prompt(self) -> None:
        """Test that telemetry_basics skill content is fully embedded."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify key sections from telemetry_basics.md
        assert "Log Analytics Workspace Reference" in prompt
        assert "874aa8fb-6d29-4521-920f-63ac7168404e" in prompt  # AME Non-Prod workspace ID
        assert "ed9e6912-0544-405b-921b-f2d6aad2155e" in prompt  # AME Prod workspace ID
        assert "Subscription Switching" in prompt
        assert "az account set" in prompt
        assert "Service AppRoleName Reference" in prompt
        assert "WorkpaperService" in prompt  # From AppRoleName table

    def test_ado_lsi_defect_content_in_prompt(self) -> None:
        """Test that ado_lsi_defect skill content is fully embedded."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify key sections from ado_lsi_defect.md
        assert "Service to Team Mapping" in prompt
        assert "HTML Field Templates" in prompt
        assert "Work Item Creation Workflow" in prompt
        assert "AskUserQuestion" in prompt  # Prompting guidance


class TestCoreSkillsLoading:
    """Tests for core skills loading from team-specific directory."""

    def test_core_skills_loaded_for_developer(self) -> None:
        """Test that all core skills are loaded for developer persona."""
        persona = load_persona("omnia-data", "developer")

        assert persona is not None
        assert "ado_basics" in persona.skills
        assert "telemetry_basics" in persona.skills
        assert "ado_lsi_defect" in persona.skills

    def test_core_skills_loaded_for_support(self) -> None:
        """Test that all core skills are loaded for support persona."""
        persona = load_persona("omnia-data", "support")

        assert persona is not None
        assert "ado_basics" in persona.skills
        assert "telemetry_basics" in persona.skills
        assert "ado_lsi_defect" in persona.skills

    def test_core_skill_content_not_empty(self) -> None:
        """Test that loaded core skills have non-empty content."""
        persona = load_persona("omnia-data", "developer")

        for skill_name in ["ado_basics", "telemetry_basics", "ado_lsi_defect"]:
            assert skill_name in persona.skills
            skill = persona.skills[skill_name]
            assert skill.content, f"{skill_name} has empty content"
            assert len(skill.content) > 100, f"{skill_name} content too short"

    def test_core_skill_metadata_complete(self) -> None:
        """Test that core skills have complete metadata."""
        persona = load_persona("omnia-data", "developer")

        for skill_name in ["ado_basics", "telemetry_basics", "ado_lsi_defect"]:
            skill = persona.skills[skill_name]
            assert skill.metadata.name == skill_name
            assert skill.metadata.display_name, f"{skill_name} missing display_name"
            assert skill.metadata.description, f"{skill_name} missing description"
            assert skill.metadata.version, f"{skill_name} missing version"


class TestTeamSpecificCoreSkills:
    """Tests for team-specific core skill loading (after migration)."""

    def test_omnia_data_core_skills_path(self) -> None:
        """Test that omnia-data core skills are loaded from team directory."""
        from pathlib import Path
        from triagent.skills.loader import SKILLS_DIR

        # After migration, skills should exist in omnia-data/core/
        team_core_dir = SKILLS_DIR / "omnia-data" / "core"

        # These assertions verify the migration was completed
        assert team_core_dir.exists(), "omnia-data/core/ directory should exist"
        assert (team_core_dir / "ado_basics.md").exists(), "ado_basics.md should exist in team core"
        assert (team_core_dir / "telemetry_basics.md").exists(), "telemetry_basics.md should exist in team core"
        assert (team_core_dir / "ado_lsi_defect.md").exists(), "ado_lsi_defect.md should exist in team core"

    def test_persona_loads_team_core_skills(self) -> None:
        """Test that persona correctly loads team-specific core skills."""
        persona = load_persona("omnia-data", "developer")

        # Verify skills are loaded (regardless of source directory)
        assert persona is not None
        assert len(persona.skills) >= 3  # At least core skills

        # Verify content includes team-specific references
        if "ado_basics" in persona.skills:
            skill = persona.skills["ado_basics"]
            # This content is specific to omnia-data team
            assert "symphonyvsts" in skill.content
            assert "Audit Cortex 2" in skill.content

    def test_skill_file_paths_are_team_specific(self) -> None:
        """Test that skill file paths point to team directory."""
        persona = load_persona("omnia-data", "developer")

        for skill_name in ["ado_basics", "telemetry_basics", "ado_lsi_defect"]:
            skill = persona.skills[skill_name]
            # Verify the skill was loaded from omnia-data/core/
            assert "omnia-data" in str(skill.file_path), f"{skill_name} should be loaded from omnia-data directory"
            assert "core" in str(skill.file_path), f"{skill_name} should be loaded from core directory"


class TestTeamContextSkill:
    """Tests for team_context core skill for all teams."""

    def test_omnia_data_team_context_loaded(self) -> None:
        """Test that omnia-data team_context skill is loaded."""
        persona = load_persona("omnia-data", "developer")

        assert persona is not None
        assert "team_context" in persona.skills
        skill = persona.skills["team_context"]
        assert skill.content
        # Verify unique content from omnia_data.md was migrated
        assert "Repository Ownership" in skill.content
        assert "Release Branch Strategy" in skill.content

    def test_omnia_data_team_context_in_prompt(self) -> None:
        """Test that omnia-data team_context content appears in system prompt."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify team context content is embedded
        assert "Team Context" in prompt
        assert "Repository Ownership" in prompt

    def test_levvia_team_persona_loads(self) -> None:
        """Test that levvia team developer persona loads correctly."""
        persona = load_persona("levvia", "developer")

        assert persona is not None
        assert "team_context" in persona.skills
        skill = persona.skills["team_context"]
        assert skill.content
        assert "Levvia" in skill.content

    def test_levvia_system_prompt(self) -> None:
        """Test that levvia team system prompt works."""
        prompt = get_system_prompt("levvia", "developer")

        assert "You are Triagent" in prompt
        assert "Levvia" in prompt
        assert "Project Omnia" in prompt

    def test_omnia_team_persona_loads(self) -> None:
        """Test that omnia team developer persona loads correctly."""
        persona = load_persona("omnia", "developer")

        assert persona is not None
        assert "team_context" in persona.skills
        skill = persona.skills["team_context"]
        assert skill.content
        assert "Omnia" in skill.content

    def test_omnia_system_prompt(self) -> None:
        """Test that omnia team system prompt works."""
        prompt = get_system_prompt("omnia", "developer")

        assert "You are Triagent" in prompt
        assert "Omnia" in prompt
        assert "Project Omnia" in prompt

    def test_all_teams_have_team_context(self) -> None:
        """Test that all configured teams have team_context core skill."""
        from triagent.teams.config import get_team_names

        for team in get_team_names():
            persona = load_persona(team, "developer")
            assert persona is not None, f"{team} should have developer persona"
            assert "team_context" in persona.skills, f"{team} should have team_context skill"
