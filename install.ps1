#Requires -Version 5.1
<#
.SYNOPSIS
    Triagent CLI Installer for Windows

.DESCRIPTION
    Installs Python (if needed), pipx, and triagent CLI tool.

.PARAMETER Version
    Specific version of triagent to install (default: latest)

.PARAMETER NonInteractive
    Run in non-interactive mode (auto-approve all prompts)

.PARAMETER NoColor
    Disable colored output

.PARAMETER UseTestPyPI
    Install from TestPyPI instead of PyPI (for testing pre-release versions)

.EXAMPLE
    # Interactive installation
    .\install.ps1

.EXAMPLE
    # Install specific version non-interactively
    .\install.ps1 -Version "0.2.0" -NonInteractive

.EXAMPLE
    # Install from TestPyPI (for testing pre-release versions)
    .\install.ps1 -UseTestPyPI -Version "1.2.1.dev1"

.EXAMPLE
    # Piped installation
    irm https://raw.githubusercontent.com/sdandey/triagent/main/install.ps1 | iex

.LINK
    https://github.com/sdandey/triagent
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$Version = "",

    [Parameter()]
    [switch]$NonInteractive,

    [Parameter()]
    [switch]$NoColor,

    [Parameter()]
    [switch]$UseTestPyPI
)

# Configuration
$script:MinPythonVersion = [version]"3.11.0"
$script:PackageName = "triagent"
$script:UseTestPyPI = $UseTestPyPI

# ============================================================================
# Output Functions
# ============================================================================

$script:UseColor = -not $NoColor -and $Host.UI.SupportsVirtualTerminal

function Write-Info {
    param([string]$Message)
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
    if ($script:UseColor) {
        Write-Host "[" -NoNewline
        Write-Host "ERROR" -ForegroundColor Red -NoNewline
        Write-Host "] $Message"
    } else {
        Write-Host "[ERROR] $Message"
    }
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

# ============================================================================
# Python Detection and Installation
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
                if ($version -ge $script:MinPythonVersion) {
                    return @{
                        Command = $candidate.Cmd
                        Args = if ($candidate.Args.Count -gt 1) { $candidate.Args[0..($candidate.Args.Count-2)] } else { @() }
                        Version = $version.ToString()
                    }
                }
            }
        } catch {
            # Command not found, continue
        }
    }

    return $null
}

function Install-Python {
    Write-Info "Python $($script:MinPythonVersion)+ not found. Installing..."

    # Check for winget first
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Info "Installing Python via winget..."

        $result = Start-Process -FilePath "winget" -ArgumentList @(
            "install",
            "-e",
            "--id", "Python.Python.3.12",
            "-h",
            "--force",
            "--accept-source-agreements",
            "--accept-package-agreements"
        ) -Wait -PassThru -NoNewWindow

        if ($result.ExitCode -eq 0) {
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")

            $python = Find-Python
            if ($python) {
                Write-Success "Python $($python.Version) installed"
                return $python
            }
        }
    }

    # Fallback: Download installer directly
    Write-Info "Downloading Python installer..."

    $arch = Get-Architecture
    $pythonVersion = "3.12.0"
    $installerUrl = if ($arch -eq "x64") {
        "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-amd64.exe"
    } else {
        "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion.exe"
    }

    $installerPath = Join-Path $env:TEMP "python-installer.exe"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing

        Write-Info "Running Python installer..."

        # Install with PATH options
        $installArgs = @(
            "/quiet",
            "InstallAllUsers=0",
            "PrependPath=1",
            "Include_pip=1",
            "Include_test=0"
        )

        $result = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru

        if ($result.ExitCode -eq 0) {
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")

            $python = Find-Python
            if ($python) {
                Write-Success "Python $($python.Version) installed"
                return $python
            }
        }
    } finally {
        Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
    }

    throw "Failed to install Python. Please install manually from https://python.org"
}

# ============================================================================
# pipx Detection and Installation
# ============================================================================

function Find-Pipx {
    try {
        $output = & pipx --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    } catch {
        # pipx not found
    }
    return $false
}

function Install-Pipx {
    param([hashtable]$Python)

    Write-Info "Installing pipx..."

    # Build pip command
    $pipArgs = $Python.Args + @("-m", "pip", "install", "--user", "pipx")

    & $Python.Command @pipArgs

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install pipx"
    }

    # Ensure pipx is in PATH
    $ensureArgs = $Python.Args + @("-m", "pipx", "ensurepath")
    & $Python.Command @ensureArgs 2>$null

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Add common pipx locations to current session
    $userScripts = Join-Path $env:APPDATA "Python\Python312\Scripts"
    $localBin = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts"

    foreach ($path in @($userScripts, $localBin)) {
        if ((Test-Path $path) -and ($env:Path -notlike "*$path*")) {
            $env:Path = "$path;$env:Path"
        }
    }

    if (Find-Pipx) {
        Write-Success "pipx installed"
        return
    }

    throw "pipx installation failed"
}

# ============================================================================
# Azure CLI Detection and Installation
# ============================================================================

function Find-AzureCLI {
    try {
        $output = & az --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Extract version from first line (e.g., "azure-cli                         2.64.0")
            if ($output[0] -match "azure-cli\s+(\d+\.\d+\.\d+)") {
                return @{ Found = $true; Version = $Matches[1] }
            }
            return @{ Found = $true; Version = "unknown" }
        }
    } catch {
        # az not found
    }
    return @{ Found = $false; Version = $null }
}

function Install-AzureCLI {
    Write-Info "Installing Azure CLI via MSI..."

    # Download MSI installer directly (no winget dependency)
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
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")

            # Add common Azure CLI paths to current session
            $azureCLIPaths = @(
                "$env:ProgramFiles\Microsoft SDKs\Azure\CLI2\wbin",
                "${env:ProgramFiles(x86)}\Microsoft SDKs\Azure\CLI2\wbin",
                "$env:LOCALAPPDATA\Programs\Azure CLI\wbin"
            )
            foreach ($path in $azureCLIPaths) {
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
            Write-Warn "Azure CLI installation returned exit code $($result.ExitCode)"
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
# Triagent Installation
# ============================================================================

function Install-Triagent {
    param([string]$Version)

    $package = $script:PackageName
    if ($Version -and $Version -ne "latest") {
        $package = "$($script:PackageName)==$Version"
    }

    Write-Info "Installing $($script:PackageName) via pipx..."

    # Check if already installed
    $listOutput = & pipx list 2>&1
    if ($listOutput -match $script:PackageName) {
        Write-Warn "$($script:PackageName) is already installed. Reinstalling..."
        & pipx uninstall $script:PackageName 2>$null
    }

    # Build install command with optional TestPyPI
    if ($script:UseTestPyPI) {
        Write-Info "Using TestPyPI index..."
        & pipx install $package --pip-args "--index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/"
    } else {
        & pipx install $package
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install $($script:PackageName)"
    }

    Write-Success "$($script:PackageName) installed"
}

function Test-Installation {
    Write-Info "Verifying installation..."

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    try {
        $version = & $script:PackageName --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$($script:PackageName) is ready: $version"
            return $true
        }
    } catch {
        # Command not found
    }

    # Check if in pipx but not in PATH
    $listOutput = & pipx list 2>&1
    if ($listOutput -match $script:PackageName) {
        Write-Warn "$($script:PackageName) installed but not in PATH"
        Write-Host ""
        Write-Host "You may need to restart your terminal or add pipx to PATH."
        return $true
    }

    return $false
}

# ============================================================================
# PATH Configuration
# ============================================================================

function Update-UserPath {
    # Common locations to check
    $locations = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\Scripts"),
        (Join-Path $env:APPDATA "Python\Python312\Scripts"),
        (Join-Path $env:APPDATA "Python\Scripts")
    )

    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pathsToAdd = @()

    foreach ($loc in $locations) {
        if ((Test-Path $loc) -and ($userPath -notlike "*$loc*")) {
            $pathsToAdd += $loc
        }
    }

    if ($pathsToAdd.Count -gt 0) {
        $newPath = ($pathsToAdd -join ";") + ";" + $userPath
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = $newPath + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")

        Write-Info "Added to PATH: $($pathsToAdd -join ', ')"
    }
}

# ============================================================================
# Main Execution
# ============================================================================

function Main {
    $ErrorActionPreference = "Stop"

    # Auto-enable non-interactive in CI
    if (Test-IsCI) {
        $script:NonInteractive = $true
    }

    Write-Host ""
    if ($script:UseColor) {
        Write-Host "Triagent CLI Installer" -ForegroundColor Cyan
        Write-Host "======================" -ForegroundColor Cyan
    } else {
        Write-Host "Triagent CLI Installer"
        Write-Host "======================"
    }
    Write-Host ""

    $arch = Get-Architecture
    Write-Info "Detected: Windows ($arch)"

    # Step 1: Python
    $python = Find-Python
    if ($python) {
        Write-Success "Python $($python.Version) found"
    } else {
        if ($NonInteractive -or (Test-IsCI)) {
            $python = Install-Python
        } else {
            Write-Warn "Python $($script:MinPythonVersion)+ not found"
            $response = Read-Host "Install Python automatically? [Y/n]"
            if ($response -match "^[Yy]?$") {
                $python = Install-Python
            } else {
                throw "Python $($script:MinPythonVersion)+ required. Install from https://python.org"
            }
        }
    }

    # Step 2: pipx
    if (Find-Pipx) {
        Write-Success "pipx found"
    } else {
        if ($NonInteractive -or (Test-IsCI)) {
            Install-Pipx -Python $python
        } else {
            Write-Warn "pipx not found"
            $response = Read-Host "Install pipx automatically? [Y/n]"
            if ($response -match "^[Yy]?$") {
                Install-Pipx -Python $python
            } else {
                throw "pipx required. Install from https://pipx.pypa.io"
            }
        }
    }

    # Step 3: Configure PATH
    Update-UserPath

    # Step 4: Install triagent
    Install-Triagent -Version $Version

    # Step 5: Azure CLI
    $az = Find-AzureCLI
    if ($az.Found) {
        Write-Success "Azure CLI $($az.Version) found"
    } else {
        if ($NonInteractive -or (Test-IsCI)) {
            Install-AzureCLI
        } else {
            Write-Warn "Azure CLI not found"
            $response = Read-Host "Install Azure CLI? [Y/n]"
            if ($response -match "^[Yy]?$") {
                Install-AzureCLI
            } else {
                Write-Info "Skipping Azure CLI. Install from: https://aka.ms/installazurecliwindows"
            }
        }
    }

    # Step 6: Verify
    if (-not (Test-Installation)) {
        Write-Warn "Installation complete but verification failed"
    }

    Write-Host ""
    if ($script:UseColor) {
        Write-Host "Installation Complete!" -ForegroundColor Green
    } else {
        Write-Host "Installation Complete!"
    }
    Write-Host ""
    Write-Host "Get started:"
    if ($script:UseColor) {
        Write-Host "  $($script:PackageName)" -ForegroundColor Cyan -NoNewline
        Write-Host "        # Start interactive chat"
        Write-Host "  $($script:PackageName) /init" -ForegroundColor Cyan -NoNewline
        Write-Host "  # Run setup wizard"
    } else {
        Write-Host "  $($script:PackageName)        # Start interactive chat"
        Write-Host "  $($script:PackageName) /init  # Run setup wizard"
    }
    Write-Host ""

    if (-not (Test-IsCI)) {
        if ($script:UseColor) {
            Write-Host "Note: You may need to restart your terminal for PATH changes." -ForegroundColor Yellow
        } else {
            Write-Host "Note: You may need to restart your terminal for PATH changes."
        }
        Write-Host ""
    }
}

# Entry point
try {
    Main
} catch {
    Write-Err $_.Exception.Message
    exit 1
}
