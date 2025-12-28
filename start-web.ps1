# Triagent Web Terminal - Quick Start (Windows)
#
# One-liner install:
#   irm https://raw.githubusercontent.com/sdandey/triagent/main/start-web.ps1 | iex
#
# This script:
#   1. Checks for Docker
#   2. Downloads docker-compose.yml
#   3. Starts the triagent web terminal
#   4. Opens browser to http://localhost:7681

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Triagent Web Terminal Installer    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking for Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Error: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "  https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check Docker is running
try {
    docker info 2>&1 | Out-Null
} catch {
    Write-Host ""
    Write-Host "Error: Docker is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "Docker found!" -ForegroundColor Green

# Create directory
$dir = "$env:USERPROFILE\.triagent-web"
Write-Host "Setting up in: $dir" -ForegroundColor Yellow

if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Set-Location $dir

# Download compose file
Write-Host "Downloading docker-compose.yml..." -ForegroundColor Yellow
$composeUrl = "https://raw.githubusercontent.com/sdandey/triagent/main/docker-compose.standalone.yml"
try {
    Invoke-WebRequest -Uri $composeUrl -OutFile "docker-compose.yml" -UseBasicParsing
} catch {
    Write-Host "Error: Failed to download docker-compose.yml" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Pull image
Write-Host "Pulling Docker image (this may take a few minutes)..." -ForegroundColor Yellow
docker compose pull

# Start container
Write-Host "Starting triagent web terminal..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Success! Triagent is running.        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Web Terminal: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:7681" -ForegroundColor Cyan
Write-Host ""
Write-Host "  First time? Run " -NoNewline -ForegroundColor White
Write-Host "/init" -NoNewline -ForegroundColor Yellow
Write-Host " in the terminal to configure." -ForegroundColor White
Write-Host ""
Write-Host "  Stop:    " -NoNewline -ForegroundColor White
Write-Host "cd $dir; docker compose down" -ForegroundColor Gray
Write-Host "  Restart: " -NoNewline -ForegroundColor White
Write-Host "cd $dir; docker compose up -d" -ForegroundColor Gray
Write-Host ""

# Try to open browser
Start-Process "http://localhost:7681"
