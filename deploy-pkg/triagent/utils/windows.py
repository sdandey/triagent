"""Windows-specific utilities for triagent.

This module provides functions to detect and configure Git Bash on Windows,
which is required by Claude Code CLI to function properly.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if the current platform is Windows, False otherwise.
    """
    return platform.system() == "Windows"


def find_git_bash() -> str | None:
    """Find git bash.exe on Windows.

    Searches in the following order:
    1. CLAUDE_CODE_GIT_BASH_PATH environment variable (user override)
    2. Derive from git.exe location in PATH
    3. Common Git for Windows installation paths
    4. bash in PATH directly

    Returns:
        Path to bash.exe if found, None otherwise.
    """
    # Check user override first
    if env_path := os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"):
        if Path(env_path).exists():
            return env_path

    # Derive from git.exe in PATH
    # If git.exe is at C:\Program Files\Git\cmd\git.exe
    # Then bash.exe is at C:\Program Files\Git\bin\bash.exe
    if git_path := shutil.which("git"):
        git_dir = Path(git_path).parent.parent  # Go up from cmd/ to Git/
        bash_candidate = git_dir / "bin" / "bash.exe"
        if bash_candidate.exists():
            return str(bash_candidate)

    # Fallback: Common Git for Windows locations
    common_paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        Path.home() / "AppData" / "Local" / "Programs" / "Git" / "bin" / "bash.exe",
    ]

    for path in common_paths:
        if Path(path).exists():
            return str(path)

    # Try PATH directly
    if bash_path := shutil.which("bash"):
        return bash_path

    return None


def get_git_bash_env() -> dict[str, str]:
    """Get environment dict with CLAUDE_CODE_GIT_BASH_PATH if found.

    Returns:
        Dictionary with CLAUDE_CODE_GIT_BASH_PATH set if bash.exe was found,
        empty dictionary otherwise.
    """
    if bash_path := find_git_bash():
        return {"CLAUDE_CODE_GIT_BASH_PATH": bash_path}
    return {}


def check_winget_available() -> bool:
    """Check if winget is available on Windows.

    Returns:
        True if winget is available and working, False otherwise.
    """
    try:
        result = subprocess.run(
            ["winget", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_git_windows() -> bool:
    """Auto-install Git for Windows using winget.

    Installs Git for Windows in non-interactive mode using the Windows
    Package Manager (winget).

    Returns:
        True if installation succeeded, False otherwise.
    """
    if not check_winget_available():
        return False

    try:
        # Install Git using winget (non-interactive)
        result = subprocess.run(
            [
                "winget",
                "install",
                "--id",
                "Git.Git",
                "-e",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
