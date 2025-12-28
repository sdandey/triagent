"""Environment detection utilities for triagent."""

from __future__ import annotations

import os
from pathlib import Path


def is_docker() -> bool:
    """Detect if running inside a Docker container.

    Detection methods (in order):
    1. Check TRIAGENT_DOCKER environment variable (explicit override)
    2. Check for /.dockerenv file (Docker creates this)
    3. Check for 'docker' in /proc/1/cgroup (Linux containers)

    Returns:
        True if running in Docker container, False otherwise.
    """
    # Explicit environment variable override
    if os.environ.get("TRIAGENT_DOCKER", "").lower() in ("1", "true", "yes"):
        return True

    # Check for /.dockerenv file (Docker creates this)
    if Path("/.dockerenv").exists():
        return True

    # Check cgroup for 'docker' string (Linux containers)
    try:
        with open("/proc/1/cgroup") as f:
            return "docker" in f.read()
    except (FileNotFoundError, PermissionError):
        pass

    return False


def is_ci() -> bool:
    """Detect if running in a CI environment.

    Checks common CI environment variables set by various CI systems.

    Returns:
        True if running in CI (GitHub Actions, Azure Pipelines, etc.)
    """
    ci_vars = [
        "CI",
        "GITHUB_ACTIONS",
        "AZURE_PIPELINES",
        "TF_BUILD",
        "JENKINS_URL",
        "GITLAB_CI",
        "CIRCLECI",
        "TRAVIS",
        "BUILDKITE",
    ]
    return any(os.environ.get(var) for var in ci_vars)


def get_environment_type() -> str:
    """Get a human-readable environment type string.

    Returns:
        One of: 'docker', 'ci', or 'local'
    """
    if is_docker():
        return "docker"
    if is_ci():
        return "ci"
    return "local"
