# Triagent Web Terminal

**Last Updated:** 2025-12-27
**Version:** 1.0

Access the triagent CLI through your web browser using a containerized terminal interface.

## Overview

The web terminal provides a browser-based interface to the triagent CLI, running inside a Docker container. This solves Windows compatibility issues and allows easy sharing with teammates.

**Key Features:**
- Full triagent CLI experience in browser
- Persistent configuration across restarts
- No local Python/Node.js installation required
- Works on Windows, macOS, and Linux

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Azure credentials (optional, for Azure DevOps integration)

## Quick Start

### One-Liner Install (Recommended)

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/sdandey/triagent/main/start-web.ps1 | iex
```

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/start-web.sh | bash
```

This downloads the pre-built image, starts the container, and opens http://localhost:7681.

### Manual Build (For Development)

```bash
# Clone the repository
git clone https://github.com/sdandey/triagent.git
cd triagent

# Build and start
docker compose -f docker-compose.web.yml build
docker compose -f docker-compose.web.yml up -d
```

### 2. Start the Web Terminal (Manual)

```bash
# Start in background
docker compose -f docker-compose.web.yml up -d

# Or use the helper script
./scripts/start-web.sh -d
```

### 3. Access the Terminal

Open your browser and navigate to:

```
http://localhost:7681
```

You'll see the triagent CLI prompt in your browser.

### 4. First-Time Setup

In the web terminal, run the setup wizard:

```
/init
```

This will guide you through:
1. Azure CLI installation
2. Azure authentication
3. API provider configuration (Databricks/Azure Foundry/Anthropic)
4. Team selection
5. MCP server setup

## Usage

### Common Commands

```bash
# Start in background
docker compose -f docker-compose.web.yml up -d

# View logs
docker compose -f docker-compose.web.yml logs -f

# Stop the container
docker compose -f docker-compose.web.yml down

# Rebuild after code changes
docker compose -f docker-compose.web.yml up -d --build
```

### Using the Helper Script

```bash
# Start in foreground (see output)
./scripts/start-web.sh

# Start in background
./scripts/start-web.sh -d

# Force rebuild
./scripts/start-web.sh --build

# View logs
./scripts/start-web.sh --logs

# Stop
./scripts/start-web.sh --stop
```

## Configuration

### Environment Variables

Pass API keys via environment variables instead of storing them in credentials.json:

```bash
# Anthropic API (direct)
export ANTHROPIC_API_KEY=your-key

# Azure AI Foundry
export ANTHROPIC_FOUNDRY_API_KEY=your-key
export ANTHROPIC_FOUNDRY_RESOURCE=your-resource

# Databricks
export DATABRICKS_BASE_URL=https://your-workspace.databricks.com
export DATABRICKS_TOKEN=your-token

# Then start the container
docker compose -f docker-compose.web.yml up -d
```

### Persistent Storage

Configuration is stored in a Docker volume called `triagent-config`. This persists:
- `config.json` - Settings
- `credentials.json` - API credentials
- `mcp_servers.json` - MCP server configuration
- `history/` - Conversation history

To reset configuration:

```bash
# Remove the volume
docker volume rm triagent-config
```

### Azure Credentials

Azure CLI credentials are stored in a separate Docker volume (`triagent-azure-config`). This allows:
- Azure DevOps operations after `/init` authentication
- Credentials persist across container restarts
- Isolated from host machine's Azure config

To reset Azure credentials:
```bash
docker volume rm triagent-azure-config
```

## Enabling Authentication

For shared deployments, enable basic authentication:

```bash
# Start with authentication
TTYD_USER=admin TTYD_PASS=your-secret-password \
  docker compose -f docker-compose.web.yml up -d
```

Or edit `docker-compose.web.yml` to use the authenticated service configuration.

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose -f docker-compose.web.yml logs

# Ensure port 7681 is not in use
lsof -i :7681
```

### /init fails

Run commands step by step:
1. Check Azure CLI: `az --version`
2. Check Node.js: `node --version`
3. Check npm: `npm --version`

### Terminal disconnects

- Refresh the browser page
- Check if container is still running: `docker ps`

### Config not persisting

Ensure the volume is created:
```bash
docker volume ls | grep triagent-config
```

## Architecture

```
+--------------------------------------------------+
|              Docker Container                     |
|                                                  |
|  ttyd (port 7681)  -->  triagent CLI             |
|                                                  |
|  Volumes:                                        |
|  - /home/triagent/.triagent (triagent-config)    |
|  - /home/triagent/.azure (triagent-azure-config) |
+--------------------------------------------------+
```

## Advanced Options

### Custom Port

```bash
# Use port 8080 instead
docker run -p 8080:7681 triagent-web
```

### SSL/TLS

For production deployments, put the container behind a reverse proxy (nginx, Traefik) with SSL termination.

### Multiple Sessions

Each browser tab creates a new session. The container supports multiple concurrent connections.

## Related Documentation

- [Triagent CLI Documentation](../README.md)
- [ttyd - Web Terminal Server](https://github.com/tsl0922/ttyd)
- [xterm.js - Terminal Emulator](https://xtermjs.org/)
