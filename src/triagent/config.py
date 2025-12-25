"""Configuration management for Triagent CLI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Default config directory
CONFIG_DIR = Path.home() / ".triagent"
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
MCP_SERVERS_FILE = CONFIG_DIR / "mcp_servers.json"
HISTORY_DIR = CONFIG_DIR / "history"


@dataclass
class TriagentConfig:
    """Triagent configuration settings."""

    team: str = "omnia-data"
    azure_cli_authenticated: bool = False
    ado_organization: str = "symphonyvsts"
    ado_project: str = "Audit Cortex 2"
    verbose: bool = False
    # SSL settings for corporate environments
    disable_ssl_verify: bool = True  # Default ON for corporate proxies
    ssl_cert_file: str | None = None  # Path to CA bundle for NODE_EXTRA_CA_CERTS
    # Write confirmation settings
    auto_approve_writes: bool = False  # If True, skip write operation confirmations
    # Output formatting
    markdown_format: bool = False  # If True, render markdown (buffers); False streams plain text

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "team": self.team,
            "azure_cli_authenticated": self.azure_cli_authenticated,
            "ado_organization": self.ado_organization,
            "ado_project": self.ado_project,
            "verbose": self.verbose,
            "disable_ssl_verify": self.disable_ssl_verify,
            "ssl_cert_file": self.ssl_cert_file,
            "auto_approve_writes": self.auto_approve_writes,
            "markdown_format": self.markdown_format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TriagentConfig:
        """Create config from dictionary."""
        return cls(
            team=data.get("team", "omnia-data"),
            azure_cli_authenticated=data.get("azure_cli_authenticated", False),
            ado_organization=data.get("ado_organization", "symphonyvsts"),
            ado_project=data.get("ado_project", "Audit Cortex 2"),
            verbose=data.get("verbose", False),
            disable_ssl_verify=data.get("disable_ssl_verify", True),
            ssl_cert_file=data.get("ssl_cert_file"),
            auto_approve_writes=data.get("auto_approve_writes", False),
            markdown_format=data.get("markdown_format", False),
        )


@dataclass
class TriagentCredentials:
    """Triagent credentials (stored securely)."""

    # API Provider: "databricks" | "azure_foundry" | "anthropic"
    api_provider: str = "databricks"

    # Databricks credentials
    databricks_auth_token: str = ""
    databricks_base_url: str = "https://adb-270181971930646.6.azuredatabricks.net/serving-endpoints/databricks-claude-sonnet-4-5"
    databricks_model: str = "databricks-claude-sonnet-4-5"

    # Azure Foundry credentials
    anthropic_foundry_api_key: str = ""
    anthropic_foundry_resource: str = ""
    anthropic_foundry_base_url: str = ""
    anthropic_foundry_model: str = "claude-opus-4-5"

    # ADO credentials
    ado_pat: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert credentials to dictionary."""
        return {
            "api_provider": self.api_provider,
            "databricks_auth_token": self.databricks_auth_token,
            "databricks_base_url": self.databricks_base_url,
            "databricks_model": self.databricks_model,
            "anthropic_foundry_api_key": self.anthropic_foundry_api_key,
            "anthropic_foundry_resource": self.anthropic_foundry_resource,
            "anthropic_foundry_base_url": self.anthropic_foundry_base_url,
            "anthropic_foundry_model": self.anthropic_foundry_model,
            "ado_pat": self.ado_pat,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TriagentCredentials:
        """Create credentials from dictionary."""
        return cls(
            api_provider=data.get("api_provider", "databricks"),
            databricks_auth_token=data.get("databricks_auth_token", ""),
            databricks_base_url=data.get(
                "databricks_base_url",
                "https://adb-270181971930646.6.azuredatabricks.net/serving-endpoints/databricks-claude-sonnet-4-5",
            ),
            databricks_model=data.get("databricks_model", "databricks-claude-sonnet-4-5"),
            anthropic_foundry_api_key=data.get("anthropic_foundry_api_key", ""),
            anthropic_foundry_resource=data.get("anthropic_foundry_resource", ""),
            anthropic_foundry_base_url=data.get("anthropic_foundry_base_url", ""),
            anthropic_foundry_model=data.get("anthropic_foundry_model", "claude-opus-4-5"),
            ado_pat=data.get("ado_pat", ""),
        )


class ConfigManager:
    """Manages Triagent configuration and credentials."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize config manager.

        Args:
            config_dir: Custom config directory (defaults to ~/.triagent)
        """
        self.config_dir = config_dir or CONFIG_DIR
        self.config_file = self.config_dir / "config.json"
        self.credentials_file = self.config_dir / "credentials.json"
        self.mcp_servers_file = self.config_dir / "mcp_servers.json"
        self.history_dir = self.config_dir / "history"

        self._config: TriagentConfig | None = None
        self._credentials: TriagentCredentials | None = None

    def ensure_dirs(self) -> None:
        """Ensure all config directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Set permissions to user-only for credentials
        os.chmod(self.config_dir, 0o700)

    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()

    def load_config(self) -> TriagentConfig:
        """Load configuration from file."""
        if self._config is not None:
            return self._config

        if not self.config_file.exists():
            self._config = TriagentConfig()
            return self._config

        with open(self.config_file) as f:
            data = json.load(f)
            self._config = TriagentConfig.from_dict(data)

        return self._config

    def save_config(self, config: TriagentConfig | None = None) -> None:
        """Save configuration to file."""
        if config is not None:
            self._config = config

        if self._config is None:
            self._config = TriagentConfig()

        self.ensure_dirs()
        with open(self.config_file, "w") as f:
            json.dump(self._config.to_dict(), f, indent=2)

    def load_credentials(self) -> TriagentCredentials:
        """Load credentials from file."""
        if self._credentials is not None:
            return self._credentials

        if not self.credentials_file.exists():
            self._credentials = TriagentCredentials()
            return self._credentials

        with open(self.credentials_file) as f:
            data = json.load(f)
            self._credentials = TriagentCredentials.from_dict(data)

        return self._credentials

    def save_credentials(self, credentials: TriagentCredentials | None = None) -> None:
        """Save credentials to file (with restricted permissions)."""
        if credentials is not None:
            self._credentials = credentials

        if self._credentials is None:
            self._credentials = TriagentCredentials()

        self.ensure_dirs()

        with open(self.credentials_file, "w") as f:
            json.dump(self._credentials.to_dict(), f, indent=2)

        # Set file permissions to owner-only
        os.chmod(self.credentials_file, 0o600)

    def get_config_value(self, key: str) -> Any:
        """Get a specific config value."""
        config = self.load_config()
        return getattr(config, key, None)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a specific config value."""
        config = self.load_config()
        if hasattr(config, key):
            setattr(config, key, value)
            self.save_config(config)
        else:
            raise ValueError(f"Unknown config key: {key}")

    def setup_environment(self) -> None:
        """Set up environment variables for Claude Agent SDK."""
        credentials = self.load_credentials()

        if credentials.api_provider == "databricks" and credentials.databricks_auth_token:
            os.environ["ANTHROPIC_BASE_URL"] = credentials.databricks_base_url
            os.environ["ANTHROPIC_AUTH_TOKEN"] = credentials.databricks_auth_token
            os.environ["ANTHROPIC_MODEL"] = credentials.databricks_model
        elif credentials.api_provider == "azure_foundry" and credentials.anthropic_foundry_api_key:
            os.environ["CLAUDE_CODE_USE_FOUNDRY"] = "1"
            os.environ["ANTHROPIC_FOUNDRY_API_KEY"] = credentials.anthropic_foundry_api_key
            os.environ["ANTHROPIC_FOUNDRY_RESOURCE"] = credentials.anthropic_foundry_resource


# Global config manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
