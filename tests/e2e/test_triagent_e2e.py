"""End-to-end tests for triagent CLI."""

import subprocess

import pytest


class TestTriagentLocalE2E:
    """Local E2E tests for triagent CLI."""

    def test_cli_version(self) -> None:
        """TC1: CLI shows version."""
        result = subprocess.run(
            ["triagent", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    def test_help_no_legacy(self) -> None:
        """TC2: Help shows no --legacy reference."""
        result = subprocess.run(
            ["triagent", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--legacy" not in result.stdout

    def test_no_legacy_imports(self) -> None:
        """Verify no legacy code references remain."""
        result = subprocess.run(
            [
                "grep",
                "-r",
                "AgentSession\\|DatabricksClient",
                "src/triagent/",
                "--include=*.py",
            ],
            capture_output=True,
            text=True,
        )
        assert result.stdout == "", f"Legacy references found: {result.stdout}"


class TestTriagentDockerE2E:
    """Docker E2E tests for triagent CLI."""

    @pytest.fixture(autouse=True)
    def check_docker(self) -> None:
        """Skip if Docker not available."""
        result = subprocess.run(["docker", "--version"], capture_output=True)
        if result.returncode != 0:
            pytest.skip("Docker not available")

    def test_docker_build(self) -> None:
        """TC9: Docker image builds successfully."""
        result = subprocess.run(
            ["docker", "build", "-t", "triagent-e2e-test", "."],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0

    def test_docker_unit_tests(self) -> None:
        """TC10: Unit tests pass in Docker."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "triagent-e2e-test",
                "pytest",
                "tests/",
                "-v",
                "--ignore=tests/e2e",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0

    def test_docker_version(self) -> None:
        """TC11: Version works in Docker."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "triagent-e2e-test",
                "triagent",
                "--version",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_docker_help_no_legacy(self) -> None:
        """TC12: Help in Docker shows no --legacy."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "triagent-e2e-test",
                "triagent",
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--legacy" not in result.stdout
