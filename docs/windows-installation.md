# Windows Installation Guide

This guide covers installing triagent prerequisites on Windows, including AWS WorkSpaces environments.

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
2. **Open Git Bash** (recommended for running triagent)
3. **Install triagent**:
   ```bash
   pip install triagent
   ```
4. **Run triagent**:
   ```bash
   triagent
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
