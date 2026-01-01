"""Unit tests for system prompt generation with skills.

These tests verify that the system prompt is correctly generated with:
- Skills summary section with "DO NOT use Task tool" instruction
- Core skills listed for all personas
- Persona-specific skills listed correctly
- Full skill content embedded in the prompt
- Team context included
"""

from triagent.prompts.system import get_system_prompt


class TestDeveloperPersonaPrompt:
    """Tests for developer persona prompt generation."""

    def test_developer_prompt_includes_skills_section(self) -> None:
        """Test developer prompt includes Available Skills section."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert "## Available Skills" in prompt
        assert "DO NOT use the Task tool to spawn subagents" in prompt

    def test_developer_prompt_includes_core_skills(self) -> None:
        """Test developer prompt lists core skills."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert "### Core Skills" in prompt
        assert "Azure DevOps Basics" in prompt
        assert "Telemetry Basics" in prompt

    def test_developer_prompt_includes_persona_skills(self) -> None:
        """Test developer prompt lists developer-specific skills."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert "### Developer Skills" in prompt
        assert "Python Code Review" in prompt
        assert "PySpark Code Review" in prompt
        assert ".NET Code Review" in prompt
        assert "ADO PR Review" in prompt
        assert "Release Investigation" in prompt

    def test_developer_prompt_includes_skill_content(self) -> None:
        """Test developer prompt embeds full skill content."""
        prompt = get_system_prompt("omnia-data", "developer")
        # Check for Python code review content
        assert "type hints" in prompt.lower() or "pep" in prompt.lower()
        # Check for PySpark code review content
        assert "spark" in prompt.lower() or "dataframe" in prompt.lower()

    def test_developer_prompt_includes_persona_context(self) -> None:
        """Test developer prompt includes persona context."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert "## Active Persona: Developer" in prompt


class TestSupportPersonaPrompt:
    """Tests for support persona prompt generation."""

    def test_support_prompt_includes_skills_section(self) -> None:
        """Test support prompt includes Available Skills section."""
        prompt = get_system_prompt("omnia-data", "support")
        assert "## Available Skills" in prompt
        assert "DO NOT use the Task tool to spawn subagents" in prompt

    def test_support_prompt_includes_core_skills(self) -> None:
        """Test support prompt lists core skills."""
        prompt = get_system_prompt("omnia-data", "support")
        assert "### Core Skills" in prompt
        assert "Azure DevOps Basics" in prompt
        assert "Telemetry Basics" in prompt

    def test_support_prompt_includes_persona_skills(self) -> None:
        """Test support prompt lists support-specific skills."""
        prompt = get_system_prompt("omnia-data", "support")
        assert "### Support Skills" in prompt
        assert "Telemetry Investigation" in prompt
        assert "Root Cause Analysis" in prompt
        assert "ADO Work Items" in prompt
        assert "LSI Creation" in prompt

    def test_support_prompt_includes_skill_content(self) -> None:
        """Test support prompt embeds full skill content."""
        prompt = get_system_prompt("omnia-data", "support")
        # Check for Telemetry Investigation content
        assert "kusto" in prompt.lower() or "log analytics" in prompt.lower()
        # Check for RCA content
        assert "root cause" in prompt.lower() or "incident" in prompt.lower()

    def test_support_prompt_includes_persona_context(self) -> None:
        """Test support prompt includes persona context."""
        prompt = get_system_prompt("omnia-data", "support")
        assert "## Active Persona: Support" in prompt


class TestTeamContext:
    """Tests for team context in prompts."""

    def test_prompt_includes_team_context(self) -> None:
        """Test prompt includes team configuration."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert "## Team Context" in prompt
        assert "Omnia Data" in prompt
        assert "Audit Cortex 2" in prompt
        assert "symphonyvsts" in prompt

    def test_prompt_includes_how_to_use_skills(self) -> None:
        """Test prompt includes skill usage instructions."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert "### How to Use Skills" in prompt
        assert "Identify the skill" in prompt
        assert "Fetch relevant data" in prompt
        assert "Apply skill guidelines" in prompt


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_nonexistent_team_returns_base_prompt(self) -> None:
        """Test nonexistent team returns base prompt without skills."""
        prompt = get_system_prompt("nonexistent-team", "developer")
        assert "You are Triagent" in prompt
        assert "## Available Skills" not in prompt

    def test_nonexistent_persona_returns_base_prompt(self) -> None:
        """Test nonexistent persona returns base prompt without skills."""
        prompt = get_system_prompt("omnia-data", "nonexistent")
        assert "You are Triagent" in prompt
        assert "## Available Skills" not in prompt

    def test_developer_and_support_have_different_skills(self) -> None:
        """Test developer and support personas have different skills."""
        dev_prompt = get_system_prompt("omnia-data", "developer")
        support_prompt = get_system_prompt("omnia-data", "support")

        # Developer-specific skills
        assert "Python Code Review" in dev_prompt
        assert "Python Code Review" not in support_prompt
        assert "PySpark Code Review" in dev_prompt
        assert "PySpark Code Review" not in support_prompt

        # Support-specific skills
        assert "Telemetry Investigation" in support_prompt
        assert "Telemetry Investigation" not in dev_prompt
        assert "LSI Creation" in support_prompt
        assert "LSI Creation" not in dev_prompt
