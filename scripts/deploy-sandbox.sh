#!/bin/bash
# Deploy to Azure sandbox environment for integration testing
#
# Usage:
#   ./scripts/deploy-sandbox.sh           # Deploy to production slot
#   ./scripts/deploy-sandbox.sh --slot staging  # Deploy to staging slot
#
# Environment:
#   RESOURCE_GROUP    - Azure resource group (default: triagent-sandbox-rg)
#   APP_NAME          - Azure App Service name (default: triagent-sandbox-app)

set -e

# Default values
RESOURCE_GROUP="${RESOURCE_GROUP:-triagent-sandbox-rg}"
APP_NAME="${APP_NAME:-triagent-sandbox-app}"
SLOT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --slot)
            SLOT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--slot <slot-name>]"
            echo ""
            echo "Options:"
            echo "  --slot <name>  Deploy to a specific deployment slot"
            echo "  -h, --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Deploying to Azure Sandbox ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
if [[ -n "$SLOT" ]]; then
    echo "Deployment Slot: $SLOT"
fi
echo ""

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. Verify Azure CLI is logged in
echo "Checking Azure CLI authentication..."
if ! az account show > /dev/null 2>&1; then
    echo "Error: Not logged in to Azure CLI. Run 'az login' first."
    exit 1
fi

# 2. Build the application package
echo "Building application package..."
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv
fi
uv pip install --system -e ".[web]" || true

# 3. Create deployment package
echo "Creating deployment package..."
rm -rf deploy-pkg app.zip 2>/dev/null || true
mkdir -p deploy-pkg

# Copy source files
cp -r src/triagent deploy-pkg/
cp pyproject.toml README.md deploy-pkg/

# Create startup command file
cat > deploy-pkg/startup.txt << 'EOF'
gunicorn triagent.web.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
EOF

# Create zip
cd deploy-pkg
zip -r ../app.zip . -x "*.pyc" -x "__pycache__/*" -x "*.git*"
cd ..

# 4. Deploy to App Service
echo "Deploying to App Service..."
DEPLOY_CMD="az webapp deploy --name $APP_NAME --resource-group $RESOURCE_GROUP --src-path app.zip --type zip"
if [[ -n "$SLOT" ]]; then
    DEPLOY_CMD="$DEPLOY_CMD --slot $SLOT"
fi
eval "$DEPLOY_CMD"

# 5. Wait for deployment to complete
echo "Waiting for deployment..."
sleep 30

# 6. Verify health endpoint
echo "Verifying deployment..."
if [[ -n "$SLOT" ]]; then
    HEALTH_URL="https://${APP_NAME}-${SLOT}.azurewebsites.net/health"
else
    HEALTH_URL="https://${APP_NAME}.azurewebsites.net/health"
fi

echo "Checking: $HEALTH_URL"
if curl -s --fail "$HEALTH_URL" | jq .; then
    echo ""
    echo "=== Deployment Complete ==="
    if [[ -n "$SLOT" ]]; then
        echo "App URL: https://${APP_NAME}-${SLOT}.azurewebsites.net"
        echo "Swagger: https://${APP_NAME}-${SLOT}.azurewebsites.net/docs"
    else
        echo "App URL: https://${APP_NAME}.azurewebsites.net"
        echo "Swagger: https://${APP_NAME}.azurewebsites.net/docs"
    fi
else
    echo "Warning: Health check failed. Check Azure Portal for deployment status."
    exit 1
fi

# Cleanup
rm -rf deploy-pkg app.zip
