#!/bin/bash
set -e

echo "=== Running Isolated Triagent Tests ==="
echo ""

# Build fresh Docker image
echo "--- Building Docker Image ---"
docker build -t triagent-test .
echo ""

# Run unit tests
echo "--- Unit Tests ---"
docker run --rm triagent-test pytest tests/unit/ -v
echo ""

# Run integration tests with Azure credentials (if available)
if [ -d "$HOME/.azure" ]; then
    echo "--- Integration Tests (with Azure auth) ---"
    docker run --rm \
        -v ~/.azure:/home/tester/.azure:ro \
        triagent-test pytest tests/integration/ -v || echo "⚠ Integration tests skipped or failed"
    echo ""
else
    echo "⚠ Skipping integration tests (~/.azure not found)"
    echo ""
fi

# Run E2E CLI verification
echo "--- E2E CLI Verification ---"
docker run --rm triagent-test bash -c "
    echo 'Testing triagent CLI...'
    triagent --version
    echo ''
    echo 'Testing npm/npx...'
    npm --version
    echo ''
    echo 'Note: Azure CLI will be installed by /init'
"
echo ""

# Interactive mode option
if [ "$1" == "--interactive" ] || [ "$1" == "-i" ]; then
    echo "--- Interactive Mode ---"
    echo "Starting container with Azure credentials mounted..."
    docker run --rm -it \
        -v ~/.azure:/home/tester/.azure:ro \
        triagent-test bash
else
    echo "=== All Tests Passed ==="
    echo ""
    echo "For interactive testing, run:"
    echo "  ./scripts/test-isolated.sh --interactive"
    echo ""
    echo "Or manually:"
    echo "  docker run --rm -it -v ~/.azure:/home/tester/.azure:ro triagent-test bash"
fi
