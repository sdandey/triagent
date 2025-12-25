@echo off
setlocal enabledelayedexpansion

echo === Triagent Development Environment Setup ===
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+
    echo https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION%

REM Create virtual environment
if not exist ".venv" (
    python -m venv .venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install/upgrade pip and uv
pip install --upgrade pip uv --quiet
echo [OK] Package managers updated

REM Install dependencies
uv pip install -e ".[dev]"
echo [OK] Dependencies installed

REM Check Azure CLI (don't install - let triagent /init handle it)
where az >nul 2>&1
if errorlevel 1 (
    echo [!!] Azure CLI not found (will be installed by 'triagent /init')
) else (
    for /f "tokens=*" %%i in ('az --version 2^>^&1 ^| findstr /i "azure-cli"') do (
        echo [OK] %%i
    )
)

REM Check Node.js
where npm >nul 2>&1
if errorlevel 1 (
    echo [!!] Node.js not found. Install for MCP server support:
    echo     winget install OpenJS.NodeJS.LTS
) else (
    for /f "tokens=*" %%i in ('npm --version 2^>^&1') do (
        echo [OK] Node.js/npm v%%i
    )
)

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo   1. Activate venv:  .venv\Scripts\activate.bat
echo   2. Run triagent:   triagent
echo   3. Run /init:      The setup wizard will install Azure CLI if needed
echo.
echo Development commands:
echo   Run tests:    pytest tests\
echo   Run linting:  ruff check src\
echo   Type check:   mypy src\triagent

endlocal
