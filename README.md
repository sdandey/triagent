# Triagent CLI

Claude-powered CLI for Azure DevOps automation.

## Overview

Triagent is an interactive command-line tool that uses Claude AI (via Azure AI Foundry) to help automate Azure DevOps operations.

### Capabilities

- **Azure DevOps Automation**
  - Create, update, and query work items
  - Create, review, and manage Pull Requests
  - Monitor build and release pipelines
  - Add PR comments and set votes

- **Kusto Log Analysis**
  - Generate Kusto queries for Application Insights
  - Query AppExceptions, AppRequests, AppDependencies, AppTraces
  - Support for multiple Log Analytics workspaces (DEV/QAS/PRD)

- **Defect Investigation**
  - Automatic investigation workflow for defects/incidents
  - Service-to-AppRoleName mapping
  - Telemetry correlation across tables

- **Security Controls**
  - Pre-tool execution validation (blocks dangerous commands)
  - Write operation confirmations (configurable)
  - Azure CLI and Git operation guards

## Architecture

Triagent uses the Claude Agent SDK to provide an AI-powered interactive CLI:

```
┌─────────────────────────────────────────────────────────┐
│                    Triagent CLI                         │
├─────────────────────────────────────────────────────────┤
│  Interactive REPL │ Slash Commands │ Activity Tracker   │
├─────────────────────────────────────────────────────────┤
│                 Claude Agent SDK                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ SDK Client  │  │  Security   │  │  System Prompt  │  │
│  │   Options   │  │   Hooks     │  │   + Team CLAUDE │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   MCP Servers                           │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │  triagent (local)   │  │  azure-devops (npx)     │   │
│  │  - get_team_config  │  │  - work items           │   │
│  │  - generate_kusto   │  │  - pull requests        │   │
│  │  - list_tables      │  │  - pipelines            │   │
│  └─────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Components

- **TriagentSDKClient**: Builds `ClaudeAgentOptions` with hooks, MCP servers, and team-specific prompts
- **Security Hooks**: Pre/post-tool execution validation (blocks dangerous commands, confirms writes)
- **MCP Tools**: In-process triagent tools + external Azure DevOps MCP server
- **Team Configurations**: Custom CLAUDE.md files per team with ADO context

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

1. **Model Selection** - Choose API provider (Azure Foundry, Anthropic)
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

## MCP Tools

Triagent provides custom MCP tools for team-specific operations:

| Tool | Description |
|------|-------------|
| `get_team_config` | Returns team configuration for Kusto queries and ADO context |
| `generate_kusto_query` | Generates Kusto query templates for Application Insights |
| `list_telemetry_tables` | Lists available telemetry tables with field descriptions |

External MCP server for Azure DevOps operations:
- `@anthropic-ai/mcp-server-azure-devops@0.1.1`

## Security

Triagent implements security hooks to protect against dangerous operations:

### Blocked Commands
- Destructive bash patterns (`rm -rf /`, `DROP TABLE`, fork bombs)
- Direct file system attacks (`> /dev/`, `chmod 777`)

### Confirmed Operations
- Azure DevOps writes (work items, PRs, comments)
- Azure CLI writes (pipelines, repos, policies)
- Git operations (commit, push, merge)

Toggle confirmations: `/confirm off` (use with caution)

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

Triagent supports multiple team configurations with custom CLAUDE.md files:

| Team | Display Name | ADO Project | Features |
|------|--------------|-------------|----------|
| `levvia` | Levvia | Project Omnia | Custom prompts |
| `omnia` | Omnia | Project Omnia | Custom prompts |
| `omnia-data` | Omnia Data | Audit Cortex 2 | 18 repos, service mappings, telemetry config |

Switch teams: `/team <name>`

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
- **Node.js 18+** - For Claude Code CLI and MCP servers
- **Claude Code CLI** - Powers the AI agent
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- **Azure DevOps account** - For ADO automation

### Recommended

- **Azure CLI** - For Azure authentication and ADO operations
  - macOS: `brew install azure-cli`
  - Windows: Download from https://aka.ms/installazurecliwindows
  - Linux: `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`

- **Azure CLI Extensions** - Install after Azure CLI:
  ```bash
  az extension add --name azure-devops
  az extension add --name application-insights --allow-preview true
  az extension add --name log-analytics --allow-preview true
  ```

### API Access (choose one)

- Azure AI Foundry
- Direct Anthropic API

## Platform Setup

### macOS

1. **Install Homebrew** (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.11+**:
   ```bash
   brew install python@3.11
   ```

3. **Install Node.js 18+**:
   ```bash
   brew install node
   ```

4. **Install Azure CLI**:
   ```bash
   brew install azure-cli
   ```

5. **Install Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

6. **Install Triagent**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash
   ```

7. **Configure Azure CLI extensions**:
   ```bash
   az extension add --name azure-devops
   az extension add --name application-insights --allow-preview true
   az extension add --name log-analytics --allow-preview true
   ```

8. **Login to Azure**:
   ```bash
   az login
   ```

### Windows

1. **Install via PowerShell** (Run as Administrator):
   ```powershell
   irm https://raw.githubusercontent.com/sdandey/triagent/main/install.ps1 | iex
   ```
   This installs Python, Node.js, Git, Azure CLI, and triagent automatically.

2. **Or manual installation**:

   a. **Install Python 3.11+**: Download from https://www.python.org/downloads/
      - Check "Add Python to PATH" during installation

   b. **Install Node.js 18+**: Download from https://nodejs.org/
      - Use LTS version

   c. **Install Git for Windows**: Download from https://git-scm.com/download/win
      - Required for Claude Code CLI bash execution

   d. **Install Azure CLI**: Download from https://aka.ms/installazurecliwindows

   e. **Install Claude Code CLI**:
      ```powershell
      npm install -g @anthropic-ai/claude-code
      ```

   f. **Install Triagent**:
      ```powershell
      pip install triagent
      ```

3. **Configure Azure CLI extensions** (PowerShell):
   ```powershell
   az extension add --name azure-devops
   az extension add --name application-insights --allow-preview true
   az extension add --name log-analytics --allow-preview true
   ```

4. **Login to Azure**:
   ```powershell
   az login
   ```

### Verify Installation

Run these commands to verify your setup:

```bash
# Check versions
triagent --version
claude --version
az --version
node --version
python --version

# Start triagent and run setup wizard
triagent
> /init
```

## License

MIT License - see [LICENSE](LICENSE) for details.
