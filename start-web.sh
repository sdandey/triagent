#!/bin/bash
# Triagent Web Terminal - Quick Start (macOS/Linux)
#
# One-liner install:
#   curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/start-web.sh | bash
#
# This script:
#   1. Checks for Docker
#   2. Downloads docker-compose.yml
#   3. Starts the triagent web terminal
#   4. Opens browser to http://localhost:7681

set -e

echo ""
echo "========================================"
echo "    Triagent Web Terminal Installer    "
echo "========================================"
echo ""

# Check Docker
echo "Checking for Docker..."
if ! command -v docker &> /dev/null; then
    echo ""
    echo "Error: Docker is not installed or not in PATH."
    echo ""
    echo "Please install Docker Desktop:"
    echo "  https://www.docker.com/products/docker-desktop"
    echo ""
    exit 1
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo ""
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    echo ""
    exit 1
fi

echo "Docker found!"

# Create directory
DIR="$HOME/.triagent-web"
echo "Setting up in: $DIR"

mkdir -p "$DIR"
cd "$DIR"

# Download compose file
echo "Downloading docker-compose.yml..."
curl -sSL "https://raw.githubusercontent.com/sdandey/triagent/main/docker-compose.standalone.yml" \
    -o docker-compose.yml

# Pull image
echo "Pulling Docker image (this may take a few minutes)..."
docker compose pull

# Start container
echo "Starting triagent web terminal..."
docker compose up -d

echo ""
echo "========================================"
echo "  Success! Triagent is running.        "
echo "========================================"
echo ""
echo "  Web Terminal: http://localhost:7681"
echo ""
echo "  First time? Run /init in the terminal to configure."
echo ""
echo "  Stop:    cd $DIR && docker compose down"
echo "  Restart: cd $DIR && docker compose up -d"
echo ""

# Try to open browser
if command -v open &> /dev/null; then
    open "http://localhost:7681"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:7681"
fi
