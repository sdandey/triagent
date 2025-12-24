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
