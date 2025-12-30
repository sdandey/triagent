"""Tests for configuration management."""

from pathlib import Path
from tempfile import TemporaryDirectory

from triagent.config import ConfigManager, TriagentConfig, TriagentCredentials


class TestTriagentConfig:
    """Tests for TriagentConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TriagentConfig()

        assert config.team == "omnia-data"
        assert config.azure_cli_authenticated is False
        assert config.ado_organization == "symphonyvsts"
        assert config.ado_project == "Audit Cortex 2"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        config = TriagentConfig(team="omnia", verbose=True)
        data = config.to_dict()

        assert data["team"] == "omnia"
        assert data["verbose"] is True

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "team": "levvia",
            "azure_cli_authenticated": True,
            "ado_project": "Project Omnia",
        }
        config = TriagentConfig.from_dict(data)

        assert config.team == "levvia"
        assert config.azure_cli_authenticated is True
        assert config.ado_project == "Project Omnia"


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_ensure_dirs(self) -> None:
        """Test directory creation."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".triagent"
            manager = ConfigManager(config_dir=config_dir)
            manager.ensure_dirs()

            assert config_dir.exists()
            assert manager.history_dir.exists()

    def test_save_and_load_config(self) -> None:
        """Test saving and loading configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".triagent"
            manager = ConfigManager(config_dir=config_dir)

            config = TriagentConfig(team="omnia", verbose=True)
            manager.save_config(config)

            # Create new manager to test loading
            manager2 = ConfigManager(config_dir=config_dir)
            loaded = manager2.load_config()

            assert loaded.team == "omnia"
            assert loaded.verbose is True

    def test_config_exists(self) -> None:
        """Test config existence check."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".triagent"
            manager = ConfigManager(config_dir=config_dir)

            assert manager.config_exists() is False

            manager.save_config(TriagentConfig())

            assert manager.config_exists() is True


class TestTriagentCredentials:
    """Tests for TriagentCredentials."""

    def test_default_values(self) -> None:
        """Test default credential values."""
        creds = TriagentCredentials()

        # Default provider is azure_foundry
        assert creds.api_provider == "azure_foundry"
        assert creds.anthropic_foundry_api_key == ""
        assert creds.anthropic_foundry_resource == ""
        assert creds.anthropic_foundry_base_url == ""
        assert creds.anthropic_foundry_model == "claude-opus-4-5"
        assert creds.ado_pat == ""

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        creds = TriagentCredentials(anthropic_foundry_api_key="test-key")
        data = creds.to_dict()

        assert data["anthropic_foundry_api_key"] == "test-key"
        assert data["api_provider"] == "azure_foundry"
        assert "anthropic_foundry_base_url" in data
        assert "anthropic_foundry_model" in data

    def test_from_dict_azure_foundry(self) -> None:
        """Test creation from dictionary with Azure Foundry credentials."""
        data = {
            "api_provider": "azure_foundry",
            "anthropic_foundry_api_key": "foundry-key",
            "anthropic_foundry_resource": "foundry-resource",
        }
        creds = TriagentCredentials.from_dict(data)

        assert creds.api_provider == "azure_foundry"
        assert creds.anthropic_foundry_api_key == "foundry-key"
        assert creds.anthropic_foundry_resource == "foundry-resource"
