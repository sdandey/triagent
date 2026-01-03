"""Shared test fixtures for isolated testing."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def isolated_config_dir() -> Generator[Path, None, None]:
    """Provide isolated temporary config directory.

    Yields:
        Path to temporary .triagent config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".triagent"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Clean environment without any triagent config.

    Removes sensitive environment variables that might interfere with tests.

    Yields:
        None (context manager)
    """
    # Remove any existing triagent env vars
    env_vars_to_clear = [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_FOUNDRY_API_KEY",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_FOUNDRY_RESOURCE",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_AUTH_TOKEN",
        "ADO_PAT",
        "AZURE_DEVOPS_ORG",
        "AZURE_DEVOPS_PROJECT",
    ]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def mock_azure_cli() -> Generator[MagicMock, None, None]:
    """Mock Azure CLI for testing without real Azure.

    Yields:
        Mock subprocess.run function
    """
    with patch("subprocess.run") as mock_run:
        # Default: Azure CLI installed and authenticated
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"version": "2.60.0"}',
            stderr="",
        )
        yield mock_run


@pytest.fixture
def mock_azure_cli_not_installed() -> Generator[MagicMock, None, None]:
    """Mock Azure CLI as not installed.

    Yields:
        Mock subprocess.run function that simulates missing Azure CLI
    """
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("az not found")
        yield mock_run


@pytest.fixture
def temp_home_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Path, None, None]:
    """Create a temporary home directory for testing.

    This isolates tests from the user's actual home directory.

    Yields:
        Path to temporary home directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.setenv("USERPROFILE", str(home_dir))  # Windows
        yield home_dir


@pytest.fixture
def clean_env_preserve_home(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Clear environment but preserve home directory variables.

    This fixture clears all environment variables except those needed
    for Path.home() to work (HOME on macOS/Linux, USERPROFILE on Windows).

    Yields:
        None (context manager)
    """
    # Save home dir vars before clearing
    home = os.environ.get("HOME")
    userprofile = os.environ.get("USERPROFILE")

    # Clear all env vars
    for key in list(os.environ.keys()):
        monkeypatch.delenv(key, raising=False)

    # Restore home dir vars (cross-platform)
    if home:
        monkeypatch.setenv("HOME", home)
    if userprofile:
        monkeypatch.setenv("USERPROFILE", userprofile)

    yield


@pytest.fixture
def isolated_config_manager(
    isolated_config_dir: Path,
) -> "Generator[ConfigManager, None, None]":
    """Provide an isolated ConfigManager instance.

    Args:
        isolated_config_dir: Temporary config directory fixture

    Yields:
        ConfigManager instance using temporary directory
    """
    from triagent.config import ConfigManager

    manager = ConfigManager(config_dir=isolated_config_dir)
    manager.ensure_dirs()
    yield manager
