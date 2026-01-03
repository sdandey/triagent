"""Utility modules for triagent."""

from triagent.utils.environment import (
    get_environment_type,
    is_ci,
    is_docker,
)
from triagent.utils.windows import (
    check_winget_available,
    find_git_bash,
    get_git_bash_env,
    install_git_windows,
    is_windows,
)

__all__ = [
    # Environment detection
    "is_docker",
    "is_ci",
    "get_environment_type",
    # Windows utilities
    "is_windows",
    "find_git_bash",
    "get_git_bash_env",
    "check_winget_available",
    "install_git_windows",
]
