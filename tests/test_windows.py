"""Tests for Windows utility functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from triagent.utils.windows import (
    check_winget_available,
    find_git_bash,
    get_git_bash_env,
    install_git_windows,
    is_windows,
)


class TestIsWindows:
    """Tests for is_windows function."""

    @patch("platform.system")
    def test_is_windows_true(self, mock_system: MagicMock) -> None:
        """Test that is_windows returns True on Windows."""
        mock_system.return_value = "Windows"
        assert is_windows() is True

    @patch("platform.system")
    def test_is_windows_false_darwin(self, mock_system: MagicMock) -> None:
        """Test that is_windows returns False on macOS."""
        mock_system.return_value = "Darwin"
        assert is_windows() is False

    @patch("platform.system")
    def test_is_windows_false_linux(self, mock_system: MagicMock) -> None:
        """Test that is_windows returns False on Linux."""
        mock_system.return_value = "Linux"
        assert is_windows() is False


class TestFindGitBash:
    """Tests for find_git_bash function."""

    @patch.dict("os.environ", {"CLAUDE_CODE_GIT_BASH_PATH": "/custom/bash.exe"})
    @patch("pathlib.Path.exists")
    def test_env_override_exists(self, mock_exists: MagicMock) -> None:
        """Test that env var override is used when path exists."""
        mock_exists.return_value = True
        assert find_git_bash() == "/custom/bash.exe"

    @patch.dict("os.environ", {"CLAUDE_CODE_GIT_BASH_PATH": "/nonexistent/bash.exe"})
    @patch("pathlib.Path.exists")
    @patch("shutil.which")
    def test_env_override_not_exists_fallback(
        self, mock_which: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test fallback when env var path doesn't exist."""
        mock_exists.return_value = False
        mock_which.return_value = None
        assert find_git_bash() is None

    @patch.dict("os.environ", {}, clear=True)
    @patch("shutil.which")
    def test_derive_from_git_path(self, mock_which: MagicMock) -> None:
        """Test deriving bash.exe location from git.exe in PATH."""
        # git.exe is at C:\Program Files\Git\cmd\git.exe
        mock_which.return_value = r"C:\Program Files\Git\cmd\git.exe"

        with patch.object(Path, "exists") as mock_exists:
            # bash.exe should exist at C:\Program Files\Git\bin\bash.exe
            mock_exists.return_value = True
            result = find_git_bash()
            assert result is not None
            assert "bash.exe" in result

    @patch("shutil.which")
    def test_common_paths_fallback(
        self, mock_which: MagicMock, clean_env_preserve_home: None
    ) -> None:
        """Test fallback to common installation paths."""
        mock_which.return_value = None  # git not in PATH

        def mock_exists(path: Path) -> bool:
            # Only the first common path exists
            return str(path) == r"C:\Program Files\Git\bin\bash.exe"

        with patch.object(Path, "exists", mock_exists):
            result = find_git_bash()

        assert result == r"C:\Program Files\Git\bin\bash.exe"

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_bash_in_path(
        self, mock_exists: MagicMock, mock_which: MagicMock, clean_env_preserve_home: None
    ) -> None:
        """Test finding bash directly in PATH."""
        mock_exists.return_value = False  # No common paths exist

        def which_side_effect(cmd: str) -> str | None:
            if cmd == "bash":
                return "/usr/bin/bash"
            return None

        mock_which.side_effect = which_side_effect

        result = find_git_bash()
        assert result == "/usr/bin/bash"

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_not_found(
        self, mock_exists: MagicMock, mock_which: MagicMock, clean_env_preserve_home: None
    ) -> None:
        """Test when git bash is not found anywhere."""
        mock_exists.return_value = False
        mock_which.return_value = None
        assert find_git_bash() is None


class TestGetGitBashEnv:
    """Tests for get_git_bash_env function."""

    @patch("triagent.utils.windows.find_git_bash")
    def test_returns_env_when_found(self, mock_find: MagicMock) -> None:
        """Test that env dict is returned when bash is found."""
        mock_find.return_value = r"C:\Program Files\Git\bin\bash.exe"
        result = get_git_bash_env()
        assert result == {
            "CLAUDE_CODE_GIT_BASH_PATH": r"C:\Program Files\Git\bin\bash.exe"
        }

    @patch("triagent.utils.windows.find_git_bash")
    def test_returns_empty_when_not_found(self, mock_find: MagicMock) -> None:
        """Test that empty dict is returned when bash is not found."""
        mock_find.return_value = None
        result = get_git_bash_env()
        assert result == {}


class TestCheckWingetAvailable:
    """Tests for check_winget_available function."""

    @patch("subprocess.run")
    def test_winget_available(self, mock_run: MagicMock) -> None:
        """Test when winget is available."""
        mock_run.return_value = MagicMock(returncode=0)
        assert check_winget_available() is True

    @patch("subprocess.run")
    def test_winget_not_available(self, mock_run: MagicMock) -> None:
        """Test when winget returns non-zero exit code."""
        mock_run.return_value = MagicMock(returncode=1)
        assert check_winget_available() is False

    @patch("subprocess.run")
    def test_winget_not_found(self, mock_run: MagicMock) -> None:
        """Test when winget executable is not found."""
        mock_run.side_effect = FileNotFoundError()
        assert check_winget_available() is False

    @patch("subprocess.run")
    def test_winget_timeout(self, mock_run: MagicMock) -> None:
        """Test when winget command times out."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="winget", timeout=10)
        assert check_winget_available() is False


class TestInstallGitWindows:
    """Tests for install_git_windows function."""

    @patch("triagent.utils.windows.check_winget_available")
    def test_no_winget(self, mock_check: MagicMock) -> None:
        """Test that install fails when winget is not available."""
        mock_check.return_value = False
        assert install_git_windows() is False

    @patch("triagent.utils.windows.check_winget_available")
    @patch("subprocess.run")
    def test_install_success(
        self, mock_run: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test successful installation."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        assert install_git_windows() is True

    @patch("triagent.utils.windows.check_winget_available")
    @patch("subprocess.run")
    def test_install_failure(
        self, mock_run: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test installation failure."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=1)
        assert install_git_windows() is False

    @patch("triagent.utils.windows.check_winget_available")
    @patch("subprocess.run")
    def test_install_timeout(
        self, mock_run: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test installation timeout."""
        import subprocess

        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="winget", timeout=300)
        assert install_git_windows() is False
