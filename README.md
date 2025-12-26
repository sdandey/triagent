# Triagent CLI

Claude-powered CLI for Azure DevOps automation.

## Overview

Triagent is an interactive command-line tool that uses Claude AI (via Azure AI Foundry) to help automate Azure DevOps operations:

- Query Azure Kusto for log data
- Create and manage Azure DevOps work items
- Create, review, and manage Pull Requests
- Monitor build and release pipelines

## Installation

### Quick Install (Recommended)

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/sdandey/triagent/main/install.ps1 | iex
```

### Alternative Methods

```bash
# Using pipx (recommended for CLI tools)
pipx install triagent

# Using uv
uv tool install triagent

# Using pip
pip install triagent
```

### Install Specific Version

```bash
# macOS/Linux
curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash -s -- --version 0.2.0

# Windows
.\install.ps1 -Version "0.2.0"
```

## Quick Start

```bash
# Start interactive chat
triagent

# Run setup wizard
triagent
> /init
```

## Setup Wizard

The `/init` command guides you through:

1. **Azure CLI Installation** - Checks and installs Azure CLI
2. **Azure Authentication** - Browser-based Azure login
3. **Azure Foundry API** - Configure Claude API credentials
4. **Azure DevOps MCP Server** - Set up MCP tools
5. **Team Selection** - Choose your team (Levvia, Omnia, Omnia Data)

## Slash Commands

| Command | Description |
|---------|-------------|
| `/init` | Run setup wizard |
| `/help` | Show available commands |
| `/config` | View current configuration |
| `/config set <key> <value>` | Set a config value |
| `/team` | Show current team |
| `/team <name>` | Switch team |
| `/clear` | Clear conversation history |
| `/exit` | Exit Triagent |

## Configuration

Configuration is stored in `~/.triagent/`:

```
~/.triagent/
├── config.json          # Main configuration
├── credentials.json     # API credentials (secure)
├── mcp_servers.json     # MCP server config
└── history/             # Conversation history
```

## Teams

Triagent supports multiple team configurations:

- **Levvia** - Project Omnia
- **Omnia** - Project Omnia
- **Omnia Data** - Audit Cortex 2

Each team has its own ADO project and custom instructions.

## Development

```bash
# Clone repository
git clone https://github.com/sdandey/triagent.git
cd triagent

# Install with UV
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/
```

## Requirements

- Python 3.11+
- Azure CLI
- Azure DevOps account
- Claude API access (via Azure AI Foundry)

## License

MIT License - see [LICENSE](LICENSE) for details.
