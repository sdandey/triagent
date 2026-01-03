#Requires -Version 5.1
<#
.SYNOPSIS
    Windows Prerequisites Installer for Triagent

.DESCRIPTION
    Installs prerequisites for triagent CLI:
    - Python 3.12.8
    - Git for Windows 2.47.1 (includes Git Bash)
    - Azure CLI 2.67.0

    Sets environment variables:
    - CLAUDE_CODE_GIT_BASH_PATH (for Claude Code compatibility)

    This script does NOT install triagent itself.
    After running this script, install triagent via: pip install triagent

.PARAMETER NonInteractive
    Run in non-interactive mode (auto-approve all prompts)

.PARAMETER NoColor
    Disable colored output

.PARAMETER SkipPython
    Skip Python installation

.PARAMETER SkipGit
    Skip Git installation

.PARAMETER SkipAzureCLI
    Skip Azure CLI installation

.EXAMPLE
    # Interactive installation (recommended)
    .\install.ps1

.EXAMPLE
    # Non-interactive installation
    .\install.ps1 -NonInteractive

.EXAMPLE
    # Piped installation
    irm https://raw.githubusercontent.com/sdandey/triagent/main/install.ps1 | iex

.LINK
    https://github.com/sdandey/triagent
#>

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$NonInteractive,

    [Parameter()]
    [switch]$NoColor,

    [Parameter()]
    [switch]$SkipPython,

    [Parameter()]
    [switch]$SkipGit,

    [Parameter()]
    [switch]$SkipAzureCLI
)

# ============================================================================
# Piped Execution Detection (irm | iex support)
# ============================================================================

# Detect if running via irm | iex (piped to Invoke-Expression)
$script:IsPipedExecution = $MyInvocation.CommandOrigin -eq 'Internal' -or
                           [string]::IsNullOrEmpty($MyInvocation.InvocationName) -or
                           $MyInvocation.InvocationName -eq '&'

# When piped, param() switches don't work - initialize script-level equivalents
if ($script:IsPipedExecution) {
    $script:NonInteractiveMode = $false
    $script:NoColorMode = $false
    $script:SkipPythonMode = $false
    $script:SkipGitMode = $false
    $script:SkipAzureCLIMode = $false
} else {
    # Direct execution - copy param values to script variables
    $script:NonInteractiveMode = $NonInteractive.IsPresent
    $script:NoColorMode = $NoColor.IsPresent
    $script:SkipPythonMode = $SkipPython.IsPresent
    $script:SkipGitMode = $SkipGit.IsPresent
    $script:SkipAzureCLIMode = $SkipAzureCLI.IsPresent
}

# ============================================================================
# Configuration - Pinned Versions (sync with src/triagent/versions.py)
# ============================================================================

$script:PythonVersion = "3.12.8"
$script:AzureCLIVersion = "2.67.0"
$script:GitVersion = "2.47.1"

# ============================================================================
# Global Variables
# ============================================================================

$script:UseColor = -not $script:NoColorMode -and $Host.UI.SupportsVirtualTerminal
$script:LogFile = $null
$script:InstallDrive = $null
$script:PythonPath = $null
$script:GitPath = $null
$script:AzureCLIPath = $null

# ============================================================================
# Logging Functions
# ============================================================================

function Initialize-Logging {
    $fileTimestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $script:LogFile = Join-Path $PWD "triagent-install-$fileTimestamp.log"

    # Create log file with header
    $headerTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $header = @"
============================================================
Triagent Prerequisites Installer Log
Started: $headerTimestamp
============================================================

"@
    $header | Out-File -FilePath $script:LogFile -Encoding UTF8
    Write-Info "Log file: $($script:LogFile)"
}

function Write-Log {
    param([string]$Message)
    if ($script:LogFile) {
        "$(Get-Date -Format 'HH:mm:ss') $Message" | Out-File -FilePath $script:LogFile -Append -Encoding UTF8
    }
}

function Write-Info {
    param([string]$Message)
    Write-Log "[INFO] $Message"
    if ($script:UseColor) {
        Write-Host "[" -NoNewline
        Write-Host "INFO" -ForegroundColor Cyan -NoNewline
        Write-Host "] $Message"
    } else {
        Write-Host "[INFO] $Message"
    }
}

function Write-Success {
    param([string]$Message)
    Write-Log "[OK] $Message"
    if ($script:UseColor) {
        Write-Host "[" -NoNewline
        Write-Host "OK" -ForegroundColor Green -NoNewline
        Write-Host "] $Message"
    } else {
        Write-Host "[OK] $Message"
    }
}

function Write-Warn {
    param([string]$Message)
    Write-Log "[WARN] $Message"
    if ($script:UseColor) {
        Write-Host "[" -NoNewline
        Write-Host "WARN" -ForegroundColor Yellow -NoNewline
        Write-Host "] $Message"
    } else {
        Write-Host "[WARN] $Message"
    }
}

function Write-Err {
    param([string]$Message)
    Write-Log "[ERROR] $Message"
    if ($script:UseColor) {
        Write-Host "[" -NoNewline
        Write-Host "ERROR" -ForegroundColor Red -NoNewline
        Write-Host "] $Message"
    } else {
        Write-Host "[ERROR] $Message"
    }
}

function Write-Step {
    param([string]$StepNumber, [string]$Message)
    Write-Host ""
    Write-Log "=== Step $StepNumber`: $Message ==="
    if ($script:UseColor) {
        Write-Host "=== Step $StepNumber`: " -NoNewline -ForegroundColor Cyan
        Write-Host "$Message ===" -ForegroundColor White
    } else {
        Write-Host "=== Step $StepNumber`: $Message ==="
    }
}

# ============================================================================
# Admin Check
# ============================================================================

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ============================================================================
# Environment Detection
# ============================================================================

function Test-IsCI {
    return $env:CI -or $env:GITHUB_ACTIONS -or $env:AZURE_PIPELINES -or $env:TF_BUILD -or $env:JENKINS_URL
}

function Get-Architecture {
    if ([Environment]::Is64BitOperatingSystem) {
        return "x64"
    }
    return "x86"
}

function Get-InstallDrive {
    # Detect AWS WorkSpaces (D:) vs laptop (C:)
    if (Test-Path "D:\Users") {
        return "D:"
    }
    return "C:"
}

function Get-InstallationPaths {
    $drive = Get-InstallDrive
    $script:InstallDrive = $drive

    # Determine paths based on drive
    if ($drive -eq "D:") {
        # AWS WorkSpaces typically uses D:\Program Files
        $script:PythonPath = "$drive\Program Files\Python312"
        $script:GitPath = "$drive\Program Files\Git"
        $script:AzureCLIPath = "$drive\Program Files\Microsoft SDKs\Azure\CLI2"
    } else {
        # Standard Windows laptop
        $script:PythonPath = "$env:ProgramFiles\Python312"
        $script:GitPath = "$env:ProgramFiles\Git"
        $script:AzureCLIPath = "$env:ProgramFiles\Microsoft SDKs\Azure\CLI2"
    }

    return @{
        Drive = $drive
        Python = $script:PythonPath
        Git = $script:GitPath
        AzureCLI = $script:AzureCLIPath
    }
}

function Show-InstallationPaths {
    param([hashtable]$Paths)

    Write-Host ""
    Write-Host "Detected Environment:" -ForegroundColor Cyan
    Write-Host "  Drive: $($Paths.Drive)"
    if ($Paths.Drive -eq "D:") {
        Write-Host "  Type:  AWS WorkSpaces" -ForegroundColor Yellow
    } else {
        Write-Host "  Type:  Standard Windows"
    }
    Write-Host ""
    Write-Host "Installation Paths:" -ForegroundColor Cyan
    Write-Host "  Python:    $($Paths.Python)"
    Write-Host "  Git:       $($Paths.Git)"
    Write-Host "  Azure CLI: $($Paths.AzureCLI)"
    Write-Host ""
}

function Confirm-InstallationPaths {
    param([hashtable]$Paths)

    if ($script:NonInteractiveMode -or (Test-IsCI)) {
        return $true
    }

    Show-InstallationPaths -Paths $Paths

    $response = Read-Host "Proceed with these installation paths? [Y/n]"
    return ($response -match "^[Yy]?$")
}

# ============================================================================
# Python Installation
# ============================================================================

function Find-Python {
    $candidates = @(
        @{ Cmd = "python"; Args = @("--version") },
        @{ Cmd = "python3"; Args = @("--version") },
        @{ Cmd = "py"; Args = @("-3", "--version") }
    )

    foreach ($candidate in $candidates) {
        try {
            $output = & $candidate.Cmd $candidate.Args 2>&1
            if ($LASTEXITCODE -eq 0 -and $output -match "Python (\d+\.\d+\.\d+)") {
                $version = [version]$Matches[1]
                $minVersion = [version]"3.11.0"
                if ($version -ge $minVersion) {
                    return @{
                        Command = $candidate.Cmd
                        Version = $version.ToString()
                        Found = $true
                    }
                }
            }
        } catch {
            # Command not found, continue
        }
    }

    return @{ Found = $false }
}

function Install-Python {
    Write-Info "Installing Python $($script:PythonVersion)..."

    $arch = Get-Architecture
    $installerUrl = if ($arch -eq "x64") {
        "https://www.python.org/ftp/python/$($script:PythonVersion)/python-$($script:PythonVersion)-amd64.exe"
    } else {
        "https://www.python.org/ftp/python/$($script:PythonVersion)/python-$($script:PythonVersion).exe"
    }

    $installerPath = Join-Path $env:TEMP "python-$($script:PythonVersion)-installer.exe"

    try {
        Write-Info "Downloading Python installer..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing

        Write-Info "Running Python installer (this may take a few minutes)..."

        # Determine install directory based on environment
        $targetDir = $script:PythonPath

        $installArgs = @(
            "/quiet",
            "InstallAllUsers=1",
            "PrependPath=1",
            "Include_pip=1",
            "Include_test=0",
            "TargetDir=$targetDir"
        )

        $result = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru

        if ($result.ExitCode -eq 0) {
            # Refresh PATH
            Update-EnvironmentPath

            $python = Find-Python
            if ($python.Found) {
                Write-Success "Python $($python.Version) installed"
                return $true
            } else {
                Write-Warn "Python installed but may need terminal restart"
                return $true
            }
        } else {
            Write-Err "Python installer returned exit code $($result.ExitCode)"
            return $false
        }
    } catch {
        Write-Err "Failed to install Python: $($_.Exception.Message)"
        return $false
    } finally {
        Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# Git Installation
# ============================================================================

function Find-Git {
    try {
        $output = & git --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $output -match "git version (\d+\.\d+\.\d+)") {
            return @{
                Version = $Matches[1]
                Found = $true
            }
        }
    } catch {
        # git not found
    }
    return @{ Found = $false }
}

function Install-Git {
    Write-Info "Installing Git for Windows $($script:GitVersion)..."

    # Git for Windows uses a different version format in the URL
    $gitVersionUrl = $script:GitVersion -replace '\.', '.'
    $installerUrl = "https://github.com/git-for-windows/git/releases/download/v$($script:GitVersion).windows.1/Git-$($script:GitVersion)-64-bit.exe"

    $installerPath = Join-Path $env:TEMP "Git-$($script:GitVersion)-installer.exe"

    try {
        Write-Info "Downloading Git installer..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing

        Write-Info "Running Git installer (this may take a few minutes)..."

        # Git for Windows uses Inno Setup
        # /DIR specifies install directory
        # /VERYSILENT runs without UI
        # /NORESTART prevents restart prompt
        # /COMPONENTS adds components
        $installArgs = @(
            "/VERYSILENT",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            "/DIR=`"$($script:GitPath)`"",
            "/COMPONENTS=`"icons,ext\reg\shellhere,assoc,assoc_sh`""
        )

        $result = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru

        if ($result.ExitCode -eq 0) {
            # Add Git to PATH
            $gitCmdPath = Join-Path $script:GitPath "cmd"
            Add-ToSystemPath -Path $gitCmdPath

            # Refresh PATH
            Update-EnvironmentPath

            $git = Find-Git
            if ($git.Found) {
                Write-Success "Git $($git.Version) installed"
                return $true
            } else {
                Write-Warn "Git installed but may need terminal restart"
                return $true
            }
        } else {
            Write-Err "Git installer returned exit code $($result.ExitCode)"
            return $false
        }
    } catch {
        Write-Err "Failed to install Git: $($_.Exception.Message)"
        return $false
    } finally {
        Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# Azure CLI Installation
# ============================================================================

function Find-AzureCLI {
    try {
        $output = & az --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($output[0] -match "azure-cli\s+(\d+\.\d+\.\d+)") {
                return @{
                    Version = $Matches[1]
                    Found = $true
                }
            }
            return @{ Version = "unknown"; Found = $true }
        }
    } catch {
        # az not found
    }
    return @{ Found = $false }
}

function Test-AzureCLIVersionOutdated {
    param([string]$CurrentVersion)

    try {
        $current = [version]$CurrentVersion
        $required = [version]$script:AzureCLIVersion
        return $current -lt $required
    } catch {
        return $false
    }
}

function Uninstall-AzureCLI {
    Write-Info "Uninstalling outdated Azure CLI..."

    try {
        # Find Azure CLI in installed programs
        $uninstallKey = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like "*Azure CLI*" }

        if ($uninstallKey) {
            $uninstallString = $uninstallKey.UninstallString
            if ($uninstallString -match "msiexec") {
                # MSI uninstall
                $productCode = $uninstallKey.PSChildName
                $result = Start-Process -FilePath "msiexec.exe" -ArgumentList "/x", $productCode, "/quiet", "/norestart" -Wait -PassThru
                return ($result.ExitCode -eq 0)
            }
        }

        Write-Warn "Could not find Azure CLI uninstaller"
        return $false
    } catch {
        Write-Err "Failed to uninstall Azure CLI: $($_.Exception.Message)"
        return $false
    }
}

function Install-AzureCLI {
    param([bool]$Upgrade = $false)

    if ($Upgrade) {
        Write-Info "Upgrading Azure CLI to $($script:AzureCLIVersion)..."
    } else {
        Write-Info "Installing Azure CLI $($script:AzureCLIVersion)..."
    }

    $installerUrl = "https://aka.ms/installazurecliwindows"
    $installerPath = Join-Path $env:TEMP "AzureCLI.msi"

    try {
        Write-Info "Downloading Azure CLI installer..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing

        Write-Info "Running Azure CLI installer (this may take a few minutes)..."

        $installArgs = @(
            "/i",
            $installerPath,
            "/quiet",
            "/norestart"
        )

        $result = Start-Process -FilePath "msiexec.exe" -ArgumentList $installArgs -Wait -PassThru

        if ($result.ExitCode -eq 0) {
            # Refresh PATH
            Update-EnvironmentPath

            # Add Azure CLI path to current session
            $programFilesX86 = [Environment]::GetFolderPath('ProgramFilesX86')
            $azPaths = @(
                "$env:ProgramFiles\Microsoft SDKs\Azure\CLI2\wbin",
                "$programFilesX86\Microsoft SDKs\Azure\CLI2\wbin"
            )
            foreach ($path in $azPaths) {
                if ((Test-Path $path) -and ($env:Path -notlike "*$path*")) {
                    $env:Path = "$path;$env:Path"
                }
            }

            $az = Find-AzureCLI
            if ($az.Found) {
                Write-Success "Azure CLI $($az.Version) installed"
                return $true
            } else {
                Write-Warn "Azure CLI installed but may need terminal restart"
                return $true
            }
        } else {
            Write-Err "Azure CLI installer returned exit code $($result.ExitCode)"
            return $false
        }
    } catch {
        Write-Err "Failed to install Azure CLI: $($_.Exception.Message)"
        return $false
    } finally {
        Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# Environment Variables
# ============================================================================

function Find-GitBashPath {
    # Method 1: Check if git is in PATH and find its installation
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        # git.exe is typically in Git\cmd, bash.exe is in Git\bin
        $gitDir = Split-Path (Split-Path $gitCmd.Source -Parent) -Parent
        $bashPath = Join-Path $gitDir "bin\bash.exe"
        if (Test-Path $bashPath) {
            return $bashPath
        }
    }

    # Method 2: Check registry for Git installation path
    $regPaths = @(
        "HKLM:\SOFTWARE\GitForWindows",
        "HKCU:\SOFTWARE\GitForWindows",
        "HKLM:\SOFTWARE\WOW6432Node\GitForWindows"
    )
    foreach ($regPath in $regPaths) {
        try {
            $installPath = (Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue).InstallPath
            if ($installPath) {
                $bashPath = Join-Path $installPath "bin\bash.exe"
                if (Test-Path $bashPath) {
                    return $bashPath
                }
            }
        } catch { }
    }

    # Method 3: Check common installation locations
    $programFilesX86 = [Environment]::GetFolderPath('ProgramFilesX86')
    $commonPaths = @(
        "$env:ProgramFiles\Git\bin\bash.exe",
        "$programFilesX86\Git\bin\bash.exe",
        "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe",
        "D:\Program Files\Git\bin\bash.exe"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    # Method 4: Check the path we just installed to
    if ($script:GitPath) {
        $bashPath = Join-Path $script:GitPath "bin\bash.exe"
        if (Test-Path $bashPath) {
            return $bashPath
        }
    }

    return $null
}

function Set-ClaudeCodeEnvironment {
    Write-Info "Setting Claude Code environment variables..."

    # Find Git Bash path
    $bashPath = Find-GitBashPath

    if (-not $bashPath) {
        Write-Warn "Could not find Git Bash. CLAUDE_CODE_GIT_BASH_PATH not set."
        Write-Warn "You may need to set this manually after Git is installed."
        return $false
    }

    try {
        # Set CLAUDE_CODE_GIT_BASH_PATH as Machine (System) environment variable
        [System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", $bashPath, "Machine")

        # Also set in current session
        $env:CLAUDE_CODE_GIT_BASH_PATH = $bashPath

        Write-Success "CLAUDE_CODE_GIT_BASH_PATH = $bashPath"
        return $true
    } catch {
        Write-Err "Failed to set environment variable: $($_.Exception.Message)"
        return $false
    }
}

function Ensure-System32InPath {
    # Fix for Claude Code VS Code extension Git Bash detection issue
    # See: https://github.com/anthropics/claude-code/issues/12022

    $system32 = "$env:SystemRoot\System32"
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")

    if ($machinePath -notlike "*$system32*") {
        Write-Info "Adding System32 to PATH (Claude Code VS Code fix)..."
        try {
            $newPath = "$system32;$machinePath"
            [System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
            $env:Path = "$system32;$env:Path"
            Write-Success "Added $system32 to PATH"
            return $true
        } catch {
            Write-Warn "Could not add System32 to PATH: $($_.Exception.Message)"
            return $false
        }
    }

    return $true
}

# ============================================================================
# PATH Management
# ============================================================================

function Update-EnvironmentPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Add-ToSystemPath {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $false
    }

    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($machinePath -notlike "*$Path*") {
        try {
            $newPath = "$machinePath;$Path"
            [System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
            Write-Info "Added to PATH: $Path"
            return $true
        } catch {
            Write-Warn "Could not add to PATH: $Path"
            return $false
        }
    }
    return $true
}

# ============================================================================
# Summary
# ============================================================================

function Show-Summary {
    $python = Find-Python
    $git = Find-Git
    $az = Find-AzureCLI

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Environment Variables Set:" -ForegroundColor Cyan
    $gitBashPath = $env:CLAUDE_CODE_GIT_BASH_PATH
    if ($gitBashPath) {
        Write-Host "  CLAUDE_CODE_GIT_BASH_PATH = $gitBashPath"
    } else {
        Write-Host "  CLAUDE_CODE_GIT_BASH_PATH = (not set)" -ForegroundColor Yellow
    }
    Write-Host ""

    Write-Host "Installed Versions:" -ForegroundColor Cyan
    if ($python.Found) {
        Write-Host "  Python:    $($python.Version)"
    } else {
        Write-Host "  Python:    (not detected)" -ForegroundColor Yellow
    }
    if ($git.Found) {
        Write-Host "  Git:       $($git.Version)"
    } else {
        Write-Host "  Git:       (not detected)" -ForegroundColor Yellow
    }
    if ($az.Found) {
        Write-Host "  Azure CLI: $($az.Version)"
    } else {
        Write-Host "  Azure CLI: (not detected)" -ForegroundColor Yellow
    }
    Write-Host ""

    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Close and reopen PowerShell (to refresh PATH)"
    Write-Host "  2. Open Git Bash (recommended for triagent)"
    Write-Host "  3. Install triagent: pip install triagent"
    Write-Host "  4. Run: triagent"
    Write-Host ""

    if ($script:LogFile) {
        Write-Host "Log file: $($script:LogFile)" -ForegroundColor Gray
    }
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# Main Execution
# ============================================================================

function Main {
    # Banner
    Write-Host ""
    if ($script:UseColor) {
        Write-Host "Triagent Prerequisites Installer" -ForegroundColor Cyan
        Write-Host "=================================" -ForegroundColor Cyan
    } else {
        Write-Host "Triagent Prerequisites Installer"
        Write-Host "================================="
    }
    Write-Host ""

    # Step 0: Admin Check
    if (-not (Test-Administrator)) {
        Write-Host ""
        Write-Err "This script requires Administrator privileges."
        Write-Host ""
        Write-Host "Please:" -ForegroundColor Yellow
        Write-Host "  1. Close this PowerShell window"
        Write-Host "  2. Right-click PowerShell and select 'Run as Administrator'"
        Write-Host "  3. Run this script again"
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }

    # Step 1: Initialize Logging
    Initialize-Logging

    Write-Info "Running as Administrator"
    Write-Info "Architecture: $(Get-Architecture)"

    # Auto-enable non-interactive in CI
    if (Test-IsCI) {
        $script:NonInteractiveMode = $true
        Write-Info "CI environment detected - running non-interactively"
    }

    # Step 2: Detect Environment & Installation Paths
    Write-Step "1" "Detecting Environment"

    $paths = Get-InstallationPaths

    if (-not (Confirm-InstallationPaths -Paths $paths)) {
        Write-Warn "Installation cancelled by user"
        return
    }

    # Step 3: Python Installation
    if (-not $script:SkipPythonMode) {
        Write-Step "2" "Python Installation"

        $python = Find-Python
        if ($python.Found) {
            Write-Success "Python $($python.Version) already installed"
        } else {
            if ($script:NonInteractiveMode -or (Test-IsCI)) {
                $installed = Install-Python
            } else {
                $response = Read-Host "Python 3.11+ not found. Install Python $($script:PythonVersion)? [Y/n]"
                if ($response -match "^[Yy]?$") {
                    $installed = Install-Python
                } else {
                    Write-Warn "Skipping Python installation"
                }
            }
        }
    } else {
        Write-Info "Skipping Python installation (--SkipPython)"
    }

    # Step 4: Git Installation
    if (-not $script:SkipGitMode) {
        Write-Step "3" "Git for Windows Installation"

        $git = Find-Git
        if ($git.Found) {
            Write-Success "Git $($git.Version) already installed"
        } else {
            if ($script:NonInteractiveMode -or (Test-IsCI)) {
                $installed = Install-Git
            } else {
                $response = Read-Host "Git not found. Install Git for Windows $($script:GitVersion)? [Y/n]"
                if ($response -match "^[Yy]?$") {
                    $installed = Install-Git
                } else {
                    Write-Warn "Skipping Git installation"
                }
            }
        }
    } else {
        Write-Info "Skipping Git installation (--SkipGit)"
    }

    # Step 5: Azure CLI Installation
    if (-not $script:SkipAzureCLIMode) {
        Write-Step "4" "Azure CLI Installation"

        $az = Find-AzureCLI
        if ($az.Found) {
            if (Test-AzureCLIVersionOutdated -CurrentVersion $az.Version) {
                Write-Warn "Azure CLI $($az.Version) is outdated (required: $($script:AzureCLIVersion))"

                if ($script:NonInteractiveMode -or (Test-IsCI)) {
                    Uninstall-AzureCLI
                    Install-AzureCLI -Upgrade $true
                } else {
                    $response = Read-Host "Upgrade Azure CLI to $($script:AzureCLIVersion)? [Y/n]"
                    if ($response -match "^[Yy]?$") {
                        Uninstall-AzureCLI
                        Install-AzureCLI -Upgrade $true
                    } else {
                        Write-Warn "Keeping current Azure CLI version"
                    }
                }
            } else {
                Write-Success "Azure CLI $($az.Version) already installed"
            }
        } else {
            if ($script:NonInteractiveMode -or (Test-IsCI)) {
                Install-AzureCLI
            } else {
                $response = Read-Host "Azure CLI not found. Install Azure CLI $($script:AzureCLIVersion)? [Y/n]"
                if ($response -match "^[Yy]?$") {
                    Install-AzureCLI
                } else {
                    Write-Warn "Skipping Azure CLI installation"
                }
            }
        }
    } else {
        Write-Info "Skipping Azure CLI installation (--SkipAzureCLI)"
    }

    # Step 6: Set Environment Variables
    Write-Step "5" "Environment Variables"

    Set-ClaudeCodeEnvironment
    Ensure-System32InPath

    # Step 7: Show Summary
    Show-Summary

    # Keep terminal open on completion
    if (-not (Test-IsCI) -and -not $script:NonInteractiveMode) {
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

# ============================================================================
# Entry Point
# ============================================================================

try {
    Main
} catch {
    Write-Host ""
    Write-Err "An unexpected error occurred:"
    Write-Err $_.Exception.Message
    Write-Host ""
    Write-Host "Stack trace:" -ForegroundColor Gray
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    Write-Host ""

    if ($script:LogFile) {
        Write-Host "See log file for details: $($script:LogFile)" -ForegroundColor Yellow
        $_.Exception.Message | Out-File -FilePath $script:LogFile -Append -Encoding UTF8
        $_.ScriptStackTrace | Out-File -FilePath $script:LogFile -Append -Encoding UTF8
    }

    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
