"""MCP Server setup for Triagent CLI."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from triagent.config import ConfigManager

# Required Azure CLI extensions for full functionality
REQUIRED_AZURE_EXTENSIONS = [
    "azure-devops",        # ADO operations
    "application-insights",  # App Insights queries
    "log-analytics",       # Log Analytics queries
]

MCP_SERVERS_CONFIG = {
    "azure-devops": {
        "command": "npx",
        "args": ["-y", "@anthropic-ai/mcp-server-azure-devops"],
        "env": {
            "AZURE_DEVOPS_ORG": "",
            "AZURE_DEVOPS_PROJECT": "",
        },
    }
}


def check_npm_installed() -> bool:
    """Check if npm/npx is installed."""
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_nodejs_installed() -> tuple[bool, str]:
    """Check if Node.js is installed.

    Returns:
        Tuple of (is_installed, version_string)
    """
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def install_nodejs() -> tuple[bool, str]:
    """Auto-install Node.js based on detected OS.

    Supports:
    - macOS: Homebrew
    - Windows: winget
    - Linux: NodeSource apt repository (Debian/Ubuntu)

    Returns:
        Tuple of (success, message)
    """
    # Check if already installed
    installed, version = check_nodejs_installed()
    if installed:
        return True, f"Already installed: {version}"

    system = platform.system().lower()

    if system == "darwin":  # macOS
        # Check if brew is available
        if shutil.which("brew"):
            try:
                result = subprocess.run(
                    ["brew", "install", "node"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "Installed via Homebrew"
                return False, f"Homebrew install failed: {result.stderr}"
            except subprocess.TimeoutExpired:
                return False, "Installation timed out"
        return False, "Homebrew not found. Install from: https://brew.sh"

    elif system == "windows":
        # Try winget first
        if shutil.which("winget"):
            try:
                result = subprocess.run(
                    ["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS", "-h"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "Installed via winget"
                # winget may return non-zero even on success, check if node exists
                installed, version = check_nodejs_installed()
                if installed:
                    return True, f"Installed via winget: {version}"
            except subprocess.TimeoutExpired:
                pass  # Fall through to manual instructions

        return False, "winget install failed. Install manually from: https://nodejs.org"

    elif system == "linux":
        # Debian/Ubuntu installation via NodeSource
        try:
            # Run NodeSource setup script
            setup_result = subprocess.run(
                ["bash", "-c", "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if setup_result.returncode != 0:
                return False, f"NodeSource setup failed: {setup_result.stderr}"

            # Install nodejs
            install_result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", "nodejs"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if install_result.returncode == 0:
                return True, "Installed via apt"
            return False, f"apt install failed: {install_result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except FileNotFoundError:
            return False, "curl or apt not found"

    return False, f"Unsupported OS: {system}"


def _find_az_command() -> str | None:
    """Find the az command path.

    Checks both system PATH and common pip install locations (~/.local/bin).

    Returns:
        Path to az command or None if not found
    """
    # Try system PATH first
    if shutil.which("az"):
        return "az"

    # Check common pip install locations
    local_az = Path.home() / ".local" / "bin" / "az"
    if local_az.exists():
        return str(local_az)

    return None


def check_azure_cli_installed() -> tuple[bool, str]:
    """Check if Azure CLI is installed.

    Checks both system PATH and common pip install locations (~/.local/bin).

    Returns:
        Tuple of (is_installed, version_string)
    """
    az_cmd = _find_az_command()
    if not az_cmd:
        return False, ""

    try:
        result = subprocess.run(
            [az_cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split("\n")[0]
            return True, first_line
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_azure_devops_extension() -> bool:
    """Check if Azure DevOps CLI extension is installed."""
    az_cmd = _find_az_command()
    if not az_cmd:
        return False

    try:
        result = subprocess.run(
            [az_cmd, "extension", "show", "--name", "azure-devops"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_azure_devops_extension() -> bool:
    """Install Azure DevOps CLI extension.

    Returns:
        True if installation succeeded
    """
    az_cmd = _find_az_command()
    if not az_cmd:
        return False

    try:
        result = subprocess.run(
            [az_cmd, "extension", "add", "--name", "azure-devops", "-y"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_azure_extension(name: str) -> bool:
    """Check if an Azure CLI extension is installed.

    Args:
        name: Extension name (e.g., 'azure-devops', 'log-analytics')

    Returns:
        True if extension is installed
    """
    az_cmd = _find_az_command()
    if not az_cmd:
        return False

    try:
        result = subprocess.run(
            [az_cmd, "extension", "show", "--name", name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_azure_extension(name: str, version: str | None = None) -> bool:
    """Install an Azure CLI extension with optional version pinning and pip fallback.

    Args:
        name: Extension name to install
        version: Specific version to install (uses pinned version if None)

    Returns:
        True if installation succeeded
    """
    import sys

    from triagent.versions import AZURE_EXTENSION_VERSIONS

    # Use pinned version if not specified
    version = version or AZURE_EXTENSION_VERSIONS.get(name)

    # Find az command (supports pip-installed CLI in ~/.local/bin)
    az_cmd = _find_az_command()

    if az_cmd:
        cmd = [az_cmd, "extension", "add", "--name", name, "-y"]
        if version:
            cmd.extend(["--version", version])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return True
        except subprocess.TimeoutExpired:
            pass  # Fall through to pip

    # Fallback: Try pip install for extension
    # Azure CLI extensions are available as pip packages
    pip_package = f"azure-cli-{name}"
    try:
        pip_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_package],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return pip_result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def _install_azure_cli_pip() -> tuple[bool, str]:
    """Fallback: Install Azure CLI via pip (no sudo required).

    Returns:
        Tuple of (success, message)
    """
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "azure-cli"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for large package
        )
        if result.returncode == 0:
            return True, "Installed via pip"
        return False, f"pip install failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "pip install timed out"


def install_azure_cli() -> tuple[bool, str]:
    """Auto-install Azure CLI based on detected OS with pip fallback.

    Supports:
    - macOS: Homebrew, then pip fallback
    - Windows: winget or MSI installer, then pip fallback
    - Linux: apt (Debian/Ubuntu), then pip fallback

    Returns:
        Tuple of (success, message)
    """
    # Check if already installed
    installed, version = check_azure_cli_installed()
    if installed:
        return True, f"Already installed: {version}"

    system = platform.system().lower()

    if system == "darwin":  # macOS
        # Check if brew is available
        if shutil.which("brew"):
            try:
                result = subprocess.run(
                    ["brew", "install", "azure-cli"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "Installed via Homebrew"
            except subprocess.TimeoutExpired:
                pass  # Fall through to pip

        # Fallback to pip
        return _install_azure_cli_pip()

    elif system == "windows":
        # Try winget first
        if shutil.which("winget"):
            try:
                result = subprocess.run(
                    ["winget", "install", "-e", "--id", "Microsoft.AzureCLI", "-h"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "Installed via winget"
            except subprocess.TimeoutExpired:
                pass  # Fall through to MSI

        # Try PowerShell MSI installer
        ps_script = (
            "Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows "
            "-OutFile $env:TEMP\\AzureCLI.msi; "
            "Start-Process msiexec.exe -Wait -ArgumentList "
            "'/I', \"$env:TEMP\\AzureCLI.msi\", '/quiet'; "
            "Remove-Item $env:TEMP\\AzureCLI.msi"
        )
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                return True, "Installed via MSI"
        except subprocess.TimeoutExpired:
            pass  # Fall through to pip

        # Fallback to pip
        return _install_azure_cli_pip()

    elif system == "linux":
        # Try Debian/Ubuntu installation first
        if shutil.which("curl") and shutil.which("sudo"):
            try:
                result = subprocess.run(
                    ["bash", "-c", "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "Installed via apt"
            except subprocess.TimeoutExpired:
                pass  # Fall through to pip

        # Fallback to pip (works without sudo/curl)
        return _install_azure_cli_pip()

    # Unknown OS - try pip as last resort
    return _install_azure_cli_pip()


def run_azure_login() -> bool:
    """Run Azure CLI login via browser.

    Returns:
        True if login succeeded
    """
    try:
        result = subprocess.run(
            ["az", "login"],
            capture_output=False,  # Let user see the browser prompt
            timeout=300,  # 5 minute timeout for login
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_azure_account() -> dict[str, Any] | None:
    """Get current Azure account info.

    Returns:
        Account info dict or None if not logged in
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def setup_mcp_servers(
    config_manager: ConfigManager,
    ado_org: str,
    ado_project: str,
) -> bool:
    """Set up MCP servers configuration.

    Args:
        config_manager: Config manager instance
        ado_org: Azure DevOps organization
        ado_project: Azure DevOps project

    Returns:
        True if setup succeeded
    """
    mcp_config = MCP_SERVERS_CONFIG.copy()

    # Update Azure DevOps server config
    mcp_config["azure-devops"]["env"]["AZURE_DEVOPS_ORG"] = ado_org
    mcp_config["azure-devops"]["env"]["AZURE_DEVOPS_PROJECT"] = ado_project

    config_manager.ensure_dirs()

    with open(config_manager.mcp_servers_file, "w") as f:
        json.dump({"mcpServers": mcp_config}, f, indent=2)

    return True


def check_databricks_cli_installed() -> tuple[bool, str]:
    """Check if Databricks CLI is installed.

    Returns:
        Tuple of (is_installed, version_string)
    """
    try:
        result = subprocess.run(
            ["databricks", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def get_databricks_token_from_cli() -> str | None:
    """Get Databricks token from CLI authentication.

    Returns:
        Token string or None if not available
    """
    try:
        result = subprocess.run(
            ["databricks", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_databricks_token_from_config() -> str | None:
    """Get Databricks token from ~/.databrickscfg file.

    Returns:
        Token string or None if not found
    """
    config_file = Path.home() / ".databrickscfg"
    if not config_file.exists():
        return None

    try:
        import configparser

        config = configparser.ConfigParser()
        config.read(config_file)

        # Check DEFAULT section first, then any other section
        for section in ["DEFAULT"] + config.sections():
            if config.has_option(section, "token"):
                return config.get(section, "token")

        return None
    except Exception:
        return None


def get_databricks_token() -> str | None:
    """Get Databricks token from CLI or config file.

    Returns:
        Token string or None if not available
    """
    # Try CLI first (more reliable for current auth)
    token = get_databricks_token_from_cli()
    if token:
        return token

    # Fall back to config file
    return get_databricks_token_from_config()


def check_claude_code_installed() -> tuple[bool, str]:
    """Check if claude-code CLI is installed using npm root (cross-platform).

    This method is reliable across all platforms because it:
    1. Uses npm's own configuration to find global modules
    2. Doesn't rely on PATH or shell hash cache
    3. Works on Windows, macOS, Linux, and Docker

    Returns:
        Tuple of (is_installed, version_string)
    """
    import json
    import re

    # Method 1: Check npm global modules directory (most reliable)
    try:
        result = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            npm_root = result.stdout.strip()
            package_dir = Path(npm_root) / "@anthropic-ai" / "claude-code"
            package_json = package_dir / "package.json"

            if package_json.exists():
                # Read version from package.json
                with open(package_json) as f:
                    pkg = json.load(f)
                    version = pkg.get("version", "unknown")
                    return True, version
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Method 2: Fallback - try npm list (slower but also reliable)
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "@anthropic-ai/claude-code", "--depth=0"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and "@anthropic-ai/claude-code" in result.stdout:
            # Parse version from output like "@anthropic-ai/claude-code@2.0.76"
            match = re.search(r"@anthropic-ai/claude-code@([\d.]+)", result.stdout)
            if match:
                return True, match.group(1)
            return True, "installed"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Method 3: Last resort - try command directly (may fail due to hash cache)
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return True, version
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return False, ""


def install_claude_code() -> tuple[bool, str]:
    """Install claude-code CLI globally via npm with pinned version.

    Returns:
        Tuple of (success, message)
    """
    from triagent.versions import CLAUDE_CODE_VERSION

    # Check if npm is available
    if not check_npm_installed():
        return False, "npm/Node.js not installed. Install from: https://nodejs.org"

    # Check if already installed
    installed, version = check_claude_code_installed()
    if installed:
        return True, f"Already installed: {version}"

    # Install globally with pinned version
    package = f"@anthropic-ai/claude-code@{CLAUDE_CODE_VERSION}"
    try:
        result = subprocess.run(
            ["npm", "install", "-g", package],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for npm install
        )
        if result.returncode == 0:
            # Verify installation
            installed, version = check_claude_code_installed()
            if installed:
                return True, f"Installed: {version}"
            return True, f"Installed v{CLAUDE_CODE_VERSION} (restart terminal to use 'claude' command)"
        return False, f"Installation failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Installation timed out"
    except FileNotFoundError:
        return False, "npm not found"
