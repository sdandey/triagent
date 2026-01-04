"""Windows-specific utilities for triagent.

This module provides functions to detect and configure Git Bash on Windows,
which is required by Claude Code CLI to function properly.

Also provides a workaround for Windows command line length limits when using
the Claude Agent SDK.
"""

import logging
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude_agent_sdk._internal.transport.subprocess_cli import (
        SubprocessCLITransport,
    )

logger = logging.getLogger(__name__)

# Windows command line length limit (8191 chars, use 8000 for safety)
_CMD_LENGTH_LIMIT = 8000

# Track if we've already applied the patch
_sdk_patched = False


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


def patch_sdk_for_windows() -> None:
    """Monkey-patch claude_agent_sdk to handle long command lines on Windows.

    The SDK passes system_prompt directly on the command line, which can exceed
    Windows' ~8000 character limit. This patch writes long prompts to temp
    files and uses the --system-prompt-file argument instead.

    This is a workaround until the SDK natively handles this case.
    See: https://github.com/anthropics/claude-code/issues/XXX
    """
    global _sdk_patched

    if _sdk_patched or not is_windows():
        return

    try:
        from claude_agent_sdk._internal.transport.subprocess_cli import (
            SubprocessCLITransport,
        )
    except ImportError:
        logger.warning("Could not import SDK transport for patching")
        return

    # Save original method
    original_build_command = SubprocessCLITransport._build_command

    def patched_build_command(self: "SubprocessCLITransport") -> list[str]:
        """Patched _build_command that handles long system_prompt on Windows."""
        cmd = original_build_command(self)

        # Check command length
        cmd_str = " ".join(cmd)
        if len(cmd_str) <= _CMD_LENGTH_LIMIT:
            return cmd

        # Handle long --system-prompt argument
        try:
            sp_idx = cmd.index("--system-prompt")
            system_prompt_value = cmd[sp_idx + 1]

            if len(system_prompt_value) > _CMD_LENGTH_LIMIT // 2:
                # Write to temp file (SDK will clean up via self._temp_files)
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False, encoding="utf-8"
                )
                temp_file.write(system_prompt_value)
                temp_file.close()

                # Track for cleanup by the SDK
                self._temp_files.append(temp_file.name)

                # Change --system-prompt to --system-prompt-file with filepath
                # Note: @filepath syntax only works for --agents, not --system-prompt
                cmd[sp_idx] = "--system-prompt-file"
                cmd[sp_idx + 1] = temp_file.name

                logger.debug(
                    f"Using --system-prompt-file for long prompt: {temp_file.name}"
                )
        except (ValueError, IndexError):
            pass

        return cmd

    # Apply patch
    SubprocessCLITransport._build_command = patched_build_command
    _sdk_patched = True
    logger.debug("Applied Windows SDK patch for long command lines")
