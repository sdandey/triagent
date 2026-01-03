#!/bin/bash
# =============================================================================
# Triagent Web UI - Infrastructure Deployment Script
# =============================================================================
# This script is designed to be used in Azure DevOps pipelines.
# It follows ADO pipeline best practices for logging and error handling.
#
# Usage:
#   ./scripts/deploy-infrastructure.sh
#
# Environment Variables (set by ADO pipeline or manually):
#   AZURE_SUBSCRIPTION_ID  - Target Azure subscription ID
#   LOCATION               - Azure region (default: eastus)
#   NAMING_PREFIX          - Resource naming prefix (default: triagent-sandbox)
#   BICEP_PATH             - Path to Bicep CLI (optional)
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_DIR="$(dirname "$SCRIPT_DIR")"
LOCATION="${LOCATION:-eastus}"
NAMING_PREFIX="${NAMING_PREFIX:-triagent-sandbox}"
DEPLOYMENT_NAME="triagent-infra-$(date +%Y%m%d%H%M%S)"
BICEP_PATH="${BICEP_PATH:-$HOME/.azure/bin/bicep}"

# =============================================================================
# Logging Functions (ADO Pipeline Compatible)
# =============================================================================
log_section() {
    echo ""
    echo "##[section]$1"
    echo "=============================================================================="
}

log_info() {
    echo "##[command]$1"
}

log_success() {
    echo "##[section]SUCCESS: $1"
}

log_warning() {
    echo "##[warning]$1"
}

log_error() {
    echo "##[error]$1"
}

log_debug() {
    echo "##[debug]$1"
}

# Set ADO pipeline variable
set_variable() {
    local name=$1
    local value=$2
    echo "##vso[task.setvariable variable=$name;isOutput=true]$value"
    echo "  $name = $value"
}

# =============================================================================
# Step 1: Validate Prerequisites
# =============================================================================
validate_prerequisites() {
    log_section "Step 1: Validating Prerequisites"

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed"
        exit 1
    fi
    log_info "Azure CLI version: $(az version --query '"azure-cli"' -o tsv)"

    # Check Bicep CLI
    if [[ -f "$BICEP_PATH" ]]; then
        log_info "Bicep CLI version: $($BICEP_PATH --version)"
    else
        log_warning "Bicep CLI not found at $BICEP_PATH, will use az bicep"
    fi

    # Check Azure login
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Run 'az login' first."
        exit 1
    fi

    local current_user=$(az account show --query user.name -o tsv)
    local current_sub=$(az account show --query name -o tsv)
    log_info "Logged in as: $current_user"
    log_info "Current subscription: $current_sub"

    log_success "Prerequisites validated"
}

# =============================================================================
# Step 2: Set Azure Subscription
# =============================================================================
set_subscription() {
    log_section "Step 2: Setting Azure Subscription"

    if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
        log_info "Setting subscription to: $AZURE_SUBSCRIPTION_ID"
        az account set --subscription "$AZURE_SUBSCRIPTION_ID"
    fi

    local sub_id=$(az account show --query id -o tsv)
    local sub_name=$(az account show --query name -o tsv)

    log_info "Using subscription: $sub_name ($sub_id)"
    log_success "Subscription configured"
}

# =============================================================================
# Step 3: Build Bicep Templates
# =============================================================================
build_templates() {
    log_section "Step 3: Building Bicep Templates"

    cd "$BICEP_DIR"
    log_info "Working directory: $(pwd)"

    # Build Bicep to ARM JSON
    log_info "Compiling main.bicep to ARM template..."

    if [[ -f "$BICEP_PATH" ]]; then
        $BICEP_PATH build main.bicep --outfile main.json 2>&1 | while read line; do
            if [[ "$line" == *"Warning"* ]]; then
                log_warning "$line"
            else
                echo "  $line"
            fi
        done
    else
        az bicep build --file main.bicep --outfile main.json 2>&1
    fi

    if [[ -f "main.json" ]]; then
        log_info "ARM template generated: main.json ($(wc -c < main.json) bytes)"
        log_success "Bicep templates compiled successfully"
    else
        log_error "Failed to generate ARM template"
        exit 1
    fi
}

# =============================================================================
# Step 4: Validate Deployment
# =============================================================================
validate_deployment() {
    log_section "Step 4: Validating Deployment"

    log_info "Running deployment validation..."
    log_info "  Location: $LOCATION"
    log_info "  Naming Prefix: $NAMING_PREFIX"

    az deployment sub validate \
        --location "$LOCATION" \
        --template-file main.json \
        --parameters namingPrefix="$NAMING_PREFIX" location="$LOCATION" \
        --output none

    log_success "Deployment validation passed"
}

# =============================================================================
# Step 5: Deploy Infrastructure
# =============================================================================
deploy_infrastructure() {
    log_section "Step 5: Deploying Infrastructure"

    log_info "Deployment Name: $DEPLOYMENT_NAME"
    log_info "Location: $LOCATION"
    log_info "Naming Prefix: $NAMING_PREFIX"

    # Run what-if first to show changes
    log_info "Running what-if analysis..."
    az deployment sub what-if \
        --location "$LOCATION" \
        --template-file main.json \
        --parameters namingPrefix="$NAMING_PREFIX" location="$LOCATION" \
        --result-format ResourceIdOnly 2>&1 || true

    echo ""
    log_info "Starting deployment..."

    az deployment sub create \
        --name "$DEPLOYMENT_NAME" \
        --location "$LOCATION" \
        --template-file main.json \
        --parameters namingPrefix="$NAMING_PREFIX" location="$LOCATION" \
        --output json > deployment_output.json

    log_success "Infrastructure deployment completed"
}

# =============================================================================
# Step 6: Extract and Export Outputs
# =============================================================================
export_outputs() {
    log_section "Step 6: Extracting Deployment Outputs"

    # Extract outputs from deployment
    local rg_name=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.resourceGroupName.value' -o tsv)
    local acr_server=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.acrLoginServer.value' -o tsv)
    local app_url=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.appServiceUrl.value' -o tsv)
    local session_pool=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.sessionPoolEndpoint.value' -o tsv)
    local redis_host=$(az deployment sub show --name "$DEPLOYMENT_NAME" --query 'properties.outputs.redisHostname.value' -o tsv)

    echo ""
    echo "Deployment Outputs:"
    echo "-------------------"
    set_variable "RESOURCE_GROUP" "$rg_name"
    set_variable "ACR_LOGIN_SERVER" "$acr_server"
    set_variable "APP_SERVICE_URL" "$app_url"
    set_variable "SESSION_POOL_ENDPOINT" "$session_pool"
    set_variable "REDIS_HOSTNAME" "$redis_host"
    set_variable "DEPLOYMENT_NAME" "$DEPLOYMENT_NAME"

    log_success "Outputs exported as pipeline variables"
}

# =============================================================================
# Step 7: Verify Resources
# =============================================================================
verify_resources() {
    log_section "Step 7: Verifying Deployed Resources"

    local rg_name="${NAMING_PREFIX}-rg"

    log_info "Listing resources in $rg_name..."

    az resource list \
        --resource-group "$rg_name" \
        --query "[].{Name:name, Type:type, Location:location}" \
        --output table

    log_success "Resource verification completed"
}

# =============================================================================
# Step 8: Print Summary
# =============================================================================
print_summary() {
    log_section "Deployment Summary"

    local rg_name="${NAMING_PREFIX}-rg"
    local acr_name="${NAMING_PREFIX//-/}acr"

    echo ""
    echo "Infrastructure deployed successfully!"
    echo ""
    echo "Resources Created:"
    echo "  - Resource Group:        $rg_name"
    echo "  - Container Registry:    ${acr_name}.azurecr.io"
    echo "  - Log Analytics:         ${NAMING_PREFIX}-law"
    echo "  - Container Apps Env:    ${NAMING_PREFIX}-cae"
    echo "  - Session Pool:          ${NAMING_PREFIX}-session-pool"
    echo "  - App Service:           ${NAMING_PREFIX}-app"
    echo "  - Redis Cache:           ${NAMING_PREFIX}-redis"
    echo ""
    echo "Next Steps:"
    echo "  1. Build and push container image:"
    echo "     az acr login --name $acr_name"
    echo "     docker build -f Dockerfile.session -t ${acr_name}.azurecr.io/triagent-session:latest ."
    echo "     docker push ${acr_name}.azurecr.io/triagent-session:latest"
    echo ""
    echo "  2. Deploy FastAPI app to App Service"
    echo ""

    log_success "Deployment script completed"
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    log_section "Triagent Web UI - Infrastructure Deployment"
    echo "Started at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

    validate_prerequisites
    set_subscription
    build_templates
    validate_deployment
    deploy_infrastructure
    export_outputs
    verify_resources
    print_summary

    echo ""
    echo "Completed at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
}

# Run main
main "$@"
