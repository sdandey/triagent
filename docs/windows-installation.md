# Windows Installation Guide

This guide covers installing triagent prerequisites on Windows, including AWS WorkSpaces environments.

## Important: Claude Code CLI is Bundled

**You do NOT need to install Claude Code CLI separately.** The `claude-agent-sdk` Python package bundles its own Claude Code CLI binary. When you run `pip install triagent`, the CLI is automatically included.

The only prerequisites you need are:
- **Python 3.11+** - Runtime for triagent
- **Git for Windows** - Required by the bundled CLI on Windows
- **Node.js 18+** - Required for MCP servers (Azure DevOps integration)
- **Azure CLI** - Optional, for Azure DevOps operations

## Quick Install

Run the prerequisites installer in PowerShell **as Administrator**:

```powershell
irm https://raw.githubusercontent.com/sdandey/triagent/main/install.ps1 | iex
```

Or download and run manually:

```powershell
# Download
Invoke-WebRequest -Uri https://raw.githubusercontent.com/sdandey/triagent/main/install.ps1 -OutFile install.ps1

# Run as Administrator
.\install.ps1
```

## What Gets Installed

The installer sets up prerequisites for triagent:

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12.8 | Core runtime |
| Git for Windows | 2.47.1 | Version control + Git Bash |
| Azure CLI | 2.67.0 | Azure DevOps integration |

**Environment Variables Set:**

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_GIT_BASH_PATH` | Path to Git Bash for Claude Code compatibility |

## Requirements

- **Windows 10/11** (64-bit)
- **Administrator privileges** (required for installations)
- **Internet connection** (to download installers)

## Installation Steps

The installer performs these steps:

### Step 1: Environment Detection

Automatically detects:
- **AWS WorkSpaces** (uses D: drive)
- **Standard Windows laptop** (uses C: drive)

Shows planned installation paths and asks for confirmation.

### Step 2: Python Installation

- Downloads Python 3.12.8 directly from python.org
- Installs with pip and adds to PATH
- No winget dependency (corporate environment compatible)

### Step 3: Git for Windows Installation

- Downloads Git 2.47.1 from github.com/git-for-windows
- Includes Git Bash (required for triagent)
- Adds to PATH

### Step 4: Azure CLI Installation

- Downloads from aka.ms/installazurecliwindows
- If outdated version exists, offers to upgrade
- Adds to PATH

### Step 5: Environment Variables

Sets `CLAUDE_CODE_GIT_BASH_PATH` to the detected Git Bash location using dynamic detection:

1. Checks if git is in PATH
2. Checks Windows Registry
3. Checks common installation locations

Also ensures `C:\Windows\System32` is in PATH (fixes Claude Code VS Code extension issues).

## After Installation

Once the installer completes:

1. **Close and reopen PowerShell** (to refresh PATH)
2. **Install triagent**:
   ```bash
   pip install triagent
   ```
3. **Run triagent**:
   ```bash
   triagent
   ```
4. **Run the setup wizard** (`/init`) to configure your API provider

## Git Bash Environment Setup (Optional)

If you want to run triagent from Git Bash, you need to configure environment variables in `~/.bashrc` because Windows User environment variables are NOT automatically available in Git Bash.

Add the following to your `~/.bashrc`:

```bash
# ============================================
# Triagent Environment Configuration
# ============================================

# Git Bash path for bundled Claude Code CLI (REQUIRED)
export CLAUDE_CODE_GIT_BASH_PATH="D:\\Program Files\\Git\\bin\\bash.exe"
# Or on AWS WorkSpaces:
# export CLAUDE_CODE_GIT_BASH_PATH="D:\\Users\\$USER\\AppData\\Local\\Programs\\Git\\bin\\bash.exe"

# Azure AI Foundry settings (configure with your values)
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_FOUNDRY_API_KEY="your-api-key"
export ANTHROPIC_FOUNDRY_RESOURCE="your-resource-name"
export ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-4-5"
export CLAUDE_CODE_USE_FOUNDRY="1"
```

Then reload your shell:
```bash
source ~/.bashrc
```

### Why Is This Needed?

Git Bash (MSYS2/MinGW) initializes its environment independently of Windows. Environment variables set in Windows Control Panel or via PowerShell are not automatically inherited. You must explicitly export them in `~/.bashrc`.

## Azure AI Foundry Configuration

If using Azure AI Foundry as your API provider, you need these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Azure AI Foundry API key |
| `ANTHROPIC_FOUNDRY_API_KEY` | Yes | Same as above (for compatibility) |
| `ANTHROPIC_FOUNDRY_RESOURCE` | Yes | Your Azure resource name (e.g., `usa-s-mgyg1ysp-eastus2`) |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | No | Model deployment name (default: `claude-opus-4-5`) |
| `CLAUDE_CODE_USE_FOUNDRY` | Yes | Set to `1` to enable Foundry mode |
| `CLAUDE_CODE_GIT_BASH_PATH` | Yes (Windows) | Path to Git Bash executable |

You can set these in:
- **Windows**: System Properties > Environment Variables (for PowerShell/CMD)
- **Git Bash**: `~/.bashrc` file (must be set separately)

## Verification

### PowerShell/CMD
```powershell
# Check Python
python --version   # Should show Python 3.11+

# Check triagent
triagent --version

# Check environment
$env:CLAUDE_CODE_GIT_BASH_PATH
```

### Git Bash
```bash
# Check Python
python --version

# Check triagent
triagent --version

# Check environment
echo $CLAUDE_CODE_GIT_BASH_PATH
echo $ANTHROPIC_API_KEY
```

## Command-Line Options

```powershell
.\install.ps1 [-NonInteractive] [-NoColor] [-SkipPython] [-SkipGit] [-SkipAzureCLI]
```

| Option | Description |
|--------|-------------|
| `-NonInteractive` | Auto-approve all prompts |
| `-NoColor` | Disable colored output |
| `-SkipPython` | Skip Python installation |
| `-SkipGit` | Skip Git installation |
| `-SkipAzureCLI` | Skip Azure CLI installation |

## Logging

All output is logged to a file in the current directory:

```
triagent-install-YYYYMMDD-HHMMSS.log
```

## Troubleshooting

### "This script requires Administrator privileges"

Right-click PowerShell and select "Run as Administrator".

### Python/Git/Azure CLI not detected after installation

Close and reopen PowerShell to refresh the PATH environment variable.

### Claude Code still requires git-bash

Verify `CLAUDE_CODE_GIT_BASH_PATH` is set:

```powershell
$env:CLAUDE_CODE_GIT_BASH_PATH
```

If not set, run the installer again or set manually:

```powershell
[Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", "C:\Program Files\Git\bin\bash.exe", "Machine")
```

### AWS WorkSpaces specific issues

The installer automatically detects AWS WorkSpaces (D: drive) and adjusts paths accordingly. If you need to override:

1. Run installer non-interactively: `.\install.ps1 -NonInteractive`
2. Or set paths manually after declining the default paths

### Corporate environment blocks downloads

The installer uses direct download URLs from:
- python.org
- github.com/git-for-windows
- aka.ms/installazurecliwindows

If these are blocked, download the installers manually and run them:

- Python: https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
- Git: https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe
- Azure CLI: https://aka.ms/installazurecliwindows

## Pinned Versions

Versions are pinned in `src/triagent/versions.py`:

```python
PYTHON_VERSION = "3.12.8"
AZURE_CLI_VERSION = "2.67.0"
GIT_FOR_WINDOWS_VERSION = "2.47.1"
```

To update versions, modify these constants and update `install.ps1` accordingly.

## Why Git Bash?

Triagent uses `prompt_toolkit` for its interactive UI, which has known compatibility issues with Windows PowerShell. Git Bash provides a Unix-like terminal that works correctly.

Additionally, Claude Code requires Git Bash on Windows for its shell operations. The `CLAUDE_CODE_GIT_BASH_PATH` environment variable tells Claude Code where to find it.

## Related Documentation

- [Main README](../README.md)
- [Claude Code Windows Issues](https://github.com/anthropics/claude-code/issues/12022)
- [Git for Windows](https://gitforwindows.org/)
