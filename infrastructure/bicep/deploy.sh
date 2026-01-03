#!/bin/bash
set -e

# =============================================================================
# Triagent Web UI - Azure Infrastructure Deployment Script
# =============================================================================
# This script deploys the Bicep templates to provision Azure infrastructure
# for the Triagent Web UI with Azure Container Apps dynamic sessions.
# =============================================================================

# Configuration (can be overridden with environment variables)
SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-}"
LOCATION="${LOCATION:-eastus}"
NAMING_PREFIX="${NAMING_PREFIX:-triagent-sandbox}"
DEPLOYMENT_NAME="triagent-infra-$(date +%Y%m%d%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "Azure CLI is installed"

    # Check if logged in
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    print_success "Logged in to Azure"

    # Check Bicep
    if ! az bicep version &> /dev/null; then
        print_warning "Bicep CLI not found. Installing..."
        az bicep install
    fi
    print_success "Bicep CLI is available"
}

# Set subscription
set_subscription() {
    if [ -z "$SUBSCRIPTION_ID" ]; then
        echo ""
        echo "Available subscriptions:"
        az account list --query "[].{Name:name, Id:id}" -o table
        echo ""
        read -p "Enter subscription ID (or press Enter to use current): " SUBSCRIPTION_ID
    fi

    if [ -n "$SUBSCRIPTION_ID" ]; then
        az account set --subscription "$SUBSCRIPTION_ID"
        print_success "Using subscription: $(az account show --query name -o tsv)"
    else
        print_success "Using current subscription: $(az account show --query name -o tsv)"
    fi
}

# Validate templates
validate_templates() {
    print_header "Validating Bicep Templates"

    az deployment sub validate \
        --location "$LOCATION" \
        --template-file main.bicep \
        --parameters namingPrefix="$NAMING_PREFIX" location="$LOCATION" \
        --output none

    print_success "Bicep templates are valid"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure"

    echo "Deployment settings:"
    echo "  - Location: $LOCATION"
    echo "  - Naming Prefix: $NAMING_PREFIX"
    echo "  - Deployment Name: $DEPLOYMENT_NAME"
    echo ""

    az deployment sub create \
        --name "$DEPLOYMENT_NAME" \
        --location "$LOCATION" \
        --template-file main.bicep \
        --parameters namingPrefix="$NAMING_PREFIX" location="$LOCATION" \
        --verbose

    print_success "Infrastructure deployed successfully"
}

# Get deployment outputs
get_outputs() {
    print_header "Deployment Outputs"

    RG_NAME=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.resourceGroupName.value' -o tsv)
    ACR_LOGIN_SERVER=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.acrLoginServer.value' -o tsv)
    APP_URL=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.appServiceUrl.value' -o tsv)
    SESSION_POOL_ENDPOINT=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.sessionPoolEndpoint.value' -o tsv)
    REDIS_HOSTNAME=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.redisHostname.value' -o tsv)

    echo ""
    echo "Resource Group:        $RG_NAME"
    echo "ACR Login Server:      $ACR_LOGIN_SERVER"
    echo "App Service URL:       $APP_URL"
    echo "Session Pool Endpoint: $SESSION_POOL_ENDPOINT"
    echo "Redis Hostname:        $REDIS_HOSTNAME"
    echo ""
}

# Print next steps
print_next_steps() {
    print_header "Next Steps"

    ACR_NAME=$(echo "$ACR_LOGIN_SERVER" | cut -d'.' -f1)

    echo "1. Build and push the session container image:"
    echo ""
    echo "   # Login to ACR"
    echo "   az acr login --name $ACR_NAME"
    echo ""
    echo "   # Build and push (from project root)"
    echo "   docker build -f Dockerfile.session -t $ACR_LOGIN_SERVER/triagent-session:latest ."
    echo "   docker push $ACR_LOGIN_SERVER/triagent-session:latest"
    echo ""
    echo "2. Deploy the FastAPI backend to App Service:"
    echo ""
    echo "   # Create deployment package"
    echo "   cd src/triagent/web && zip -r ../../../app.zip ."
    echo ""
    echo "   # Deploy to App Service"
    echo "   az webapp deploy --name ${NAMING_PREFIX}-app \\"
    echo "       --resource-group ${NAMING_PREFIX}-rg \\"
    echo "       --src-path app.zip"
    echo ""
    echo "3. Open the web UI:"
    echo "   $APP_URL"
    echo ""
}

# Main execution
main() {
    print_header "Triagent Web UI - Azure Infrastructure Deployment"

    # Change to script directory
    cd "$(dirname "$0")"

    check_prerequisites
    set_subscription
    validate_templates
    deploy_infrastructure
    get_outputs
    print_next_steps

    print_success "Deployment complete!"
}

# Run main function
main "$@"
