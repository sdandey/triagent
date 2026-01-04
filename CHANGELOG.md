# Changelog

All notable changes to Triagent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2026-01-03

### Added
- **Windows SDK Patch** for long system prompts (`patch_sdk_for_windows()`)
  - Handles Windows ~8191 char command line limit
  - Writes 57K+ system prompt to temp file using `--system-prompt-file`
- **On-Demand Skills Loading** for system prompt optimization:
  - New `get_code_review_guidelines` MCP tool fetches guidelines only when needed
  - Code review skills (python, pyspark, dotnet) no longer loaded at startup
  - Reduces initial system prompt size by ~5000 chars
  - Auto-detects language from file extensions
- **Windows Installer Improvements** (`install.ps1`):
  - Piped execution support (`irm | iex`)
  - `-ConfigureGitBash` flag for Git Bash environment setup
- **Cross-Platform Test Fixtures** (`tests/conftest.py`):
  - `clean_env_preserve_home` fixture preserves HOME/USERPROFILE
- **Issue Creation Workflow** in CLAUDE.md with templates for:
  - Acceptance Criteria from user perspective
  - Testing Guide with test scenarios (unit, integration, E2E)
  - Implementation task comments with code examples
  - PR validation checklist
- **Issue Implementation Workflow** for branch → implement → test → commit → PR cycle
- **Skills & Persona Architecture**:
  - `/persona` command to switch between developer/support modes
  - Skills loader with YAML persona definitions
  - Team-specific skill files for omnia-data team
  - Developer persona skills: code review, PR management, release investigation
  - Support persona skills: ADO work items, telemetry analysis
- **SDK Slash Command Pass-through**:
  - Claude Code SDK command discovery via `get_server_info()`
  - Pass unknown slash commands through to SDK (e.g., `/release-notes`)
  - Display SDK commands in `/help` alongside triagent commands
- **Subagent Visibility** indicators with Nerd Font icons
- **Comprehensive Staging Service API documentation** for Issue #23:
  - File browse, search, upload/download operations
  - Data Kitchen Service file APIs
  - Common user prompts & API mapping
- E2E tests for local and Docker environments (`tests/e2e/`)
- Updated README.md with architecture documentation
- Platform setup instructions for macOS and Windows

### Fixed
- **Git Bash Azure CLI Detection** ([#9](https://github.com/sdandey/triagent/issues/9)):
  - Added `shell=True` fallback to all Azure CLI functions
  - `shutil.which()` doesn't work reliably in MINGW64/Git Bash
- **Azure Extension Detection** in Git Bash:
  - `check_azure_extension()`, `check_azure_devops_extension()`
- **Azure Login** in Git Bash:
  - `run_azure_login()`, `get_azure_account()`

### Changed
- Now uses Claude Agent SDK exclusively for all operations
- Default API provider changed from `databricks` to `azure_foundry`
- Version now read dynamically from package metadata
- Updated Issue #23 with Staging Service and Data Kitchen file operation APIs
- Enhanced acceptance criteria for file browsing and search operations

### Removed
- **BREAKING**: Removed `--legacy` CLI flag and Databricks implementation
- Removed `DatabricksClient`, `AgentSession`, and related legacy code (~1046 lines)
- Removed Databricks as an API provider option
- Claude Code CLI prerequisite check from `/init` (SDK bundles its own CLI binary)

## [1.3.0] - 2025-12-28

### Added
- Docker-based web terminal with ttyd ([`2645131`](https://github.com/sdandey/triagent/commit/2645131))
- Windows init improvements with non-blocking flow ([`64d4d67`](https://github.com/sdandey/triagent/commit/64d4d67))
- Improved Windows installation workflow and `/init` command ([#14](https://github.com/sdandey/triagent/pull/14))

### Fixed
- Restart SDK client after `/init` in async mode ([`406d5c4`](https://github.com/sdandey/triagent/commit/406d5c4))
- Reinitialize agent session after `/init` changes provider ([`e893a5a`](https://github.com/sdandey/triagent/commit/e893a5a))
- Use shared Azure CLI extension directory in Docker ([`d97b1fa`](https://github.com/sdandey/triagent/commit/d97b1fa))

## [1.2.0] - 2025-12-26

### Added
- Curl-based cross-platform installer (`install.sh`) ([`690c7af`](https://github.com/sdandey/triagent/commit/690c7af))
- RC (Release Candidate) workflow for pre-release testing ([`50d40e2`](https://github.com/sdandey/triagent/commit/50d40e2))

### Fixed
- Avoid duplicate GitHub release creation ([`77850f1`](https://github.com/sdandey/triagent/commit/77850f1))
- Add TestPyPI environment to RC workflow ([`35840e5`](https://github.com/sdandey/triagent/commit/35840e5))

## [1.1.0] - 2025-12-25

### Added
- pip fallback for Azure CLI installation ([`079e78b`](https://github.com/sdandey/triagent/commit/079e78b))

## [1.0.0] - 2025-12-25

### Added
- Initial PyPI release
- Claude Agent SDK integration with async patterns
- Azure AI Foundry support for Claude API access
- Azure DevOps MCP server integration (`@anthropic-ai/mcp-server-azure-devops`)
- Interactive CLI with slash commands:
  - `/init` - Setup wizard
  - `/help` - Show available commands
  - `/config` - View/modify configuration
  - `/team` - Show/switch teams
  - `/clear` - Clear conversation history
  - `/exit` - Exit application
- Team configurations (levvia, omnia, omnia-data)
- Security hooks for write operation confirmations
- Kusto query generation MCP tools:
  - `get_team_config`
  - `generate_kusto_query`
  - `list_telemetry_tables`
- Defect investigation workflow
- Docker support with standalone images
- python-semantic-release for auto-versioning ([`58e3055`](https://github.com/sdandey/triagent/commit/58e3055))
- TestPyPI publishing for main branch commits ([`bba5b81`](https://github.com/sdandey/triagent/commit/bba5b81))
- Version pinning, streaming toggle, and cross-platform fixes ([`0d79077`](https://github.com/sdandey/triagent/commit/0d79077))
- Pulsing animation to CLI status indicators ([`eed8bd1`](https://github.com/sdandey/triagent/commit/eed8bd1))
- Log Analytics Workspace Customer IDs to telemetry config ([`8e74082`](https://github.com/sdandey/triagent/commit/8e74082))
- Node.js auto-installation and subscription info for log analysis ([`a0b309a`](https://github.com/sdandey/triagent/commit/a0b309a))
- Azure DevOps repository information for 16+ services ([`18b09d8`](https://github.com/sdandey/triagent/commit/18b09d8))

### Changed
- Make mypy non-blocking in CI ([`c73e3a3`](https://github.com/sdandey/triagent/commit/c73e3a3))

### Fixed
- Ruff linting errors for CI ([`aca5f7b`](https://github.com/sdandey/triagent/commit/aca5f7b))

## [0.0.0] - 2025-12-23

### Added
- Initial commit: Triagent CLI for Azure DevOps automation ([`e9750c7`](https://github.com/sdandey/triagent/commit/e9750c7))
- Core CLI structure with Typer
- Rich terminal output
- Configuration management (`~/.triagent/`)
- DatabricksClient for legacy Foundation Model API
- AgentSession for conversation management
- Basic Azure CLI tool integration
