# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Triagent is a Claude-powered CLI for Azure DevOps automation. It provides an interactive chat interface that uses Claude AI (via Databricks, Azure AI Foundry, or direct Anthropic API) to automate Azure DevOps operations including work items, pull requests, pipelines, and Kusto queries.

## Build and Development Commands

```bash
# Install with development dependencies (using uv)
uv pip install -e ".[dev]"

# Run the CLI
triagent

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_config.py -v

# Run a single test
pytest tests/test_config.py::TestTriagentConfig::test_default_values -v

# Linting
ruff check src/

# Type checking
mypy src/
```

## Architecture

### Core Components

- **cli.py**: Main entry point. Implements interactive REPL loop with slash commands (`/init`, `/help`, `/config`, `/team`, `/clear`, `/exit`). Uses prompt-toolkit for input and rich for output.

- **agent.py**: Claude integration layer. `AgentSession` manages conversation state and routes to either:
  - `DatabricksClient`: Custom client for Databricks Foundation Model API (OpenAI-compatible format)
  - Anthropic SDK: Direct API or Azure Foundry

- **config.py**: Configuration management via `ConfigManager`. Stores settings in `~/.triagent/`:
  - `config.json`: Team, project, organization settings (`TriagentConfig`)
  - `credentials.json`: API tokens and provider config (`TriagentCredentials`)
  - `mcp_servers.json`: MCP server configuration

- **teams/config.py**: Team definitions (`levvia`, `omnia`, `omnia-data`) with ADO project mappings and team-specific CLAUDE.md files.

- **prompts/system.py**: Builds system prompts by combining base prompt with team context and team-specific CLAUDE.md content from `prompts/claude_md/`.

- **tools/azure_cli.py**: Azure CLI tool for the agent. Defines `AZURE_CLI_TOOL` schema and `execute_azure_cli()` with automatic consent for reads, confirmation for writes.

### API Provider Flow

The agent supports three providers configured via `TriagentCredentials.api_provider`:
1. `databricks` (default): Uses `DatabricksClient` with OAuth token refresh via `databricks auth token`
2. `azure_foundry`: Sets Foundry environment variables, uses Anthropic SDK
3. `anthropic`: Direct Anthropic API

### Tool Execution

`send_message_with_tools()` implements an agentic loop:
1. Send message with tool definitions
2. Check for tool calls in response
3. Execute tools, collect results
4. Append results to conversation, repeat until no more tool calls

## Testing

Tests use pytest with pytest-asyncio. Test files mirror source structure:
- `tests/test_config.py`: Config and credentials serialization
- `tests/test_teams.py`: Team configuration lookups

Configuration tests use `TemporaryDirectory` for isolated file system operations.

## Azure DevOps Repositories (Audit Cortex 2)

### Organization Details
- **Organization**: symphonyvsts
- **Project**: Audit Cortex 2
- **Git SSH Base**: `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/`
- **Local Clone Path**: `~/code/{repo-name}`

### Active Repositories (Monitored Services)

These repositories have active application logs and are prioritized for exception investigation:

| Repository | Branch | AppRoleName | SSH Clone URL |
|------------|--------|-------------|---------------|
| data-exchange-service | master | DataExchangeGateway | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/data-exchange-service` |
| cortex-datamanagement-services | master | AppSupportService, DataPreparationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortex-datamanagement-services` |
| engagement-service | master | EngagementService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/engagement-service` |
| security-service | master | SecurityService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/security-service` |
| data-kitchen-service | master | DataKitchenService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/data-kitchen-service` |
| analytic-template-service | master | AnalyticTemplateService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/analytic-template-service` |
| notification-service | master | NotificationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/notification-service` |
| staging-service | master | StagingService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/staging-service` |
| spark-job-management | master | SparkJobManagementService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/spark-job-management` |
| cortex-ui | master | Cortex-UI | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/cortex-ui` |
| client-service | master | ClientService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/client-service` |
| workpaper-service | master | WorkpaperService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/workpaper-service` |
| async-workflow-framework | master | async-workflow-function | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/async-workflow-framework` |
| sampling-service | master | SamplingService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/sampling-service` |
| localization-service | master | LocalizationService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/localization-service` |
| scheduler-service | master | SchedulerService | `git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/scheduler-service` |

### Git Commands for Investigation

#### Clone a repository
```bash
git clone git@ssh.dev.azure.com:v3/symphonyvsts/Audit%20Cortex%202/{repo-name} ~/code/{repo-name}
```

#### Update existing repository
```bash
cd ~/code/{repo-name}
git fetch origin
git checkout master
git pull origin master
```

#### Checkout release branch
```bash
git fetch --all
git checkout release-{version}
git pull origin release-{version}
```
