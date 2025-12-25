"""End-to-end tests for triagent /init flow."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest


def _triagent_available() -> bool:
    """Check if triagent CLI is available in PATH."""
    try:
        result = subprocess.run(
            ["triagent", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class TestTriagentCLI:
    """Test triagent CLI installation and basic commands."""

    @pytest.mark.skipif(
        not _triagent_available(),
        reason="triagent CLI not installed in PATH",
    )
    def test_triagent_version(self):
        """Verify triagent CLI is installed and accessible."""
        result = subprocess.run(
            ["triagent", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Triagent CLI" in result.stdout

    @pytest.mark.skipif(
        not _triagent_available(),
        reason="triagent CLI not installed in PATH",
    )
    def test_triagent_help(self):
        """Verify triagent --help works."""
        result = subprocess.run(
            ["triagent", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Triagent" in result.stdout


class TestAzureCLIInstall:
    """Test Azure CLI detection and installation."""

    def test_azure_cli_detection(self):
        """Test Azure CLI detection function."""
        from triagent.mcp.setup import check_azure_cli_installed

        installed, version = check_azure_cli_installed()
        # Just verify the function returns correct types
        assert isinstance(installed, bool)
        assert isinstance(version, str)

    def test_install_azure_cli_returns_tuple(self):
        """Test install_azure_cli returns proper tuple."""
        from triagent.mcp.setup import install_azure_cli

        # Note: This doesn't actually install, just tests the function signature
        # when Azure CLI is already installed
        result = install_azure_cli()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    @pytest.mark.skipif(
        subprocess.run(["az", "--version"], capture_output=True).returncode != 0,
        reason="Azure CLI not installed",
    )
    def test_azure_cli_installed(self):
        """Verify Azure CLI is installed (if available)."""
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "azure-cli" in result.stdout


class TestAzureDevOpsExtension:
    """Test Azure DevOps extension detection and installation."""

    def test_extension_detection(self):
        """Test Azure DevOps extension detection function."""
        from triagent.mcp.setup import check_azure_devops_extension

        result = check_azure_devops_extension()
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        subprocess.run(["az", "--version"], capture_output=True).returncode != 0,
        reason="Azure CLI not installed",
    )
    def test_extension_install(self):
        """Test Azure DevOps extension install function."""
        from triagent.mcp.setup import install_azure_devops_extension

        # This may install the extension if not present
        result = install_azure_devops_extension()
        assert isinstance(result, bool)


class TestConfigDirectory:
    """Test configuration directory creation."""

    def test_config_directory_creation(self):
        """Test that config directory is created properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".triagent"

            from triagent.config import ConfigManager

            manager = ConfigManager(config_dir=config_dir)
            manager.ensure_dirs()

            assert config_dir.exists()
            assert (config_dir / "history").exists()

    def test_config_file_creation(self):
        """Test that config files are created properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".triagent"

            from triagent.config import ConfigManager, TriagentConfig

            manager = ConfigManager(config_dir=config_dir)
            config = TriagentConfig(team="omnia-data")
            manager.save_config(config)

            assert manager.config_file.exists()


class TestNodeJS:
    """Test Node.js/npm availability for MCP servers."""

    def test_npm_detection(self):
        """Test npm detection function."""
        from triagent.mcp.setup import check_npm_installed

        result = check_npm_installed()
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        subprocess.run(["npm", "--version"], capture_output=True).returncode != 0,
        reason="npm not installed",
    )
    def test_npm_available(self):
        """Verify npm is available for MCP servers."""
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
