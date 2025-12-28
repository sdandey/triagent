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

## Web Terminal (Docker)

Run triagent in a browser-based terminal - no local Python installation required.

### One-Liner Install (Recommended)

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/sdandey/triagent/main/start-web.ps1 | iex
```

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/start-web.sh | bash
```

This downloads, starts the container, and opens http://localhost:7681 in your browser.

### Manual Setup

```bash
# Build and start (from cloned repo)
docker compose -f docker-compose.web.yml up -d

# Open in browser
open http://localhost:7681

# Stop
docker compose -f docker-compose.web.yml down
```

See [docs/web-terminal.md](docs/web-terminal.md) for more details.

## Setup Wizard

The `/init` command guides you through configuration:

1. **Model Selection** - Choose API provider (Databricks, Azure Foundry, Anthropic)
2. **Team Selection** - Choose team and ADO project
3. **MCP Server Setup** - Configure Azure DevOps MCP server
4. **Azure Authentication** - Browser-based Azure login
5. **Prerequisites Check** - Verify required tools are installed

Note: The wizard displays installation instructions but does not auto-install tools. See [Prerequisites](#prerequisites) for installation instructions.

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

## Prerequisites

### Required

- **Python 3.11+** - Core runtime
- **Azure DevOps account** - For ADO automation

### Recommended

- **Azure CLI** - For Azure authentication and ADO operations
  - macOS: `brew install azure-cli`
  - Windows: Download from https://aka.ms/installazurecliwindows
  - Linux: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`

- **Azure CLI Extensions** - Install after Azure CLI:
  ```bash
  az extension add --name azure-devops --version 1.0.2
  az extension add --name application-insights --version 2.0.0b1 --allow-preview true
  az extension add --name log-analytics --version 1.0.0b1 --allow-preview true
  ```

- **Node.js 18+** - For MCP servers
  - macOS: `brew install node`
  - Windows: Download from https://nodejs.org
  - Linux: See https://deb.nodesource.com

### Optional

- **Claude Code CLI** - For SDK mode (default)
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
  Or use `triagent --legacy` to skip this requirement.

### API Access (choose one)

- Databricks Foundation Model API
- Azure AI Foundry
- Direct Anthropic API

## License

MIT License - see [LICENSE](LICENSE) for details.
