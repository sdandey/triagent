#!/bin/bash
set -e

echo "=== Triagent Development Environment Setup ==="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required="3.11"
if [ "$(printf '%s\n' "$required" "$python_version" | sort -V | head -n1)" != "$required" ]; then
    echo "ERROR: Python 3.11+ required, found $python_version"
    exit 1
fi
echo "✓ Python $python_version"

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
source .venv/bin/activate
echo "✓ Virtual environment activated"

# Install/upgrade pip and uv
pip install --upgrade pip uv --quiet
echo "✓ Package managers updated"

# Install dependencies
uv pip install -e ".[dev]"
echo "✓ Dependencies installed"

# Check Azure CLI (don't install - let triagent /init handle it)
if command -v az &> /dev/null; then
    az_version=$(az --version 2>&1 | head -1)
    echo "✓ Azure CLI found: $az_version"
else
    echo "⚠ Azure CLI not found (will be installed by 'triagent /init')"
fi

# Check Node.js
if command -v npm &> /dev/null; then
    npm_version=$(npm --version 2>&1)
    echo "✓ Node.js/npm found: v$npm_version"
else
    echo "⚠ Node.js not found. Install for MCP server support:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install node"
    else
        echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -"
        echo "  sudo apt-get install -y nodejs"
    fi
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Activate venv:  source .venv/bin/activate"
echo "  2. Run triagent:   triagent"
echo "  3. Run /init:      The setup wizard will install Azure CLI if needed"
echo ""
echo "Development commands:"
echo "  Run tests:    pytest tests/"
echo "  Run linting:  ruff check src/"
echo "  Type check:   mypy src/triagent"
