"""Tests for team configurations."""


from triagent.teams.config import (
    TEAM_CONFIG,
    TeamConfig,
    get_team_config,
    get_team_display_names,
    get_team_names,
)


class TestTeamConfig:
    """Tests for TeamConfig."""

    def test_team_config_structure(self) -> None:
        """Test team config has required fields."""
        for name, config in TEAM_CONFIG.items():
            assert isinstance(config, TeamConfig)
            assert config.name == name
            assert config.display_name
            assert config.ado_project
            assert config.ado_organization


class TestGetTeamConfig:
    """Tests for get_team_config function."""

    def test_get_existing_team(self) -> None:
        """Test getting an existing team config."""
        config = get_team_config("omnia-data")

        assert config is not None
        assert config.name == "omnia-data"
        assert config.display_name == "Omnia Data"
        assert config.ado_project == "Audit Cortex 2"

    def test_get_nonexistent_team(self) -> None:
        """Test getting a non-existent team returns None."""
        config = get_team_config("nonexistent")

        assert config is None

    def test_case_insensitive(self) -> None:
        """Test team lookup is case insensitive."""
        config = get_team_config("OMNIA-DATA")

        assert config is not None
        assert config.name == "omnia-data"


class TestGetTeamNames:
    """Tests for team name functions."""

    def test_get_team_names(self) -> None:
        """Test getting list of team names."""
        names = get_team_names()

        assert "levvia" in names
        assert "omnia" in names
        assert "omnia-data" in names

    def test_get_team_display_names(self) -> None:
        """Test getting list of display names."""
        names = get_team_display_names()

        assert "Levvia" in names
        assert "Omnia" in names
        assert "Omnia Data" in names
