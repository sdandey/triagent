#!/bin/bash
# Shell wrapper for Azure Container Apps Dynamic Sessions API testing
#
# Usage:
#   ./scripts/test-session-api.sh
#
# This script:
#   1. Checks Azure authentication
#   2. Sets the correct subscription
#   3. Gets the Session Pool endpoint
#   4. Launches the interactive Python script
#
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Azure Container Apps Dynamic Sessions API Testing ===${NC}"
echo ""

# Use az-elevated by default, can override with AZ_CMD environment variable
AZ_CMD="${AZ_CMD:-az-elevated}"

# Step 1: Check Azure authentication
echo -e "${YELLOW}Step 1: Checking Azure authentication...${NC}"
if ! $AZ_CMD account show &>/dev/null; then
    echo -e "${RED}Not logged into Azure. Running '$AZ_CMD login'...${NC}"
    $AZ_CMD login
fi

# Step 2: Set correct subscription
echo -e "${YELLOW}Step 2: Setting subscription...${NC}"
$AZ_CMD account set --subscription "US-AZSUB-AME-AA-ODATAOPENAI-SBX"

SUBSCRIPTION=$($AZ_CMD account show --query name -o tsv)
echo -e "${GREEN}✓ Using subscription: $SUBSCRIPTION${NC}"

# Step 3: Get Session Pool endpoint
echo -e "${YELLOW}Step 3: Getting Session Pool endpoint...${NC}"
POOL_ENDPOINT=$($AZ_CMD containerapp sessionpool show \
    --name triagent-sandbox-session-pool \
    --resource-group triagent-sandbox-rg \
    --query "properties.poolManagementEndpoint" -o tsv 2>/dev/null)

if [ -z "$POOL_ENDPOINT" ]; then
    echo -e "${RED}Failed to get Session Pool endpoint.${NC}"
    echo ""
    echo "Ensure triagent-sandbox-session-pool exists in triagent-sandbox-rg."
    echo ""
    echo "To create it, run:"
    echo "  az-elevated containerapp sessionpool create \\"
    echo "    --name triagent-sandbox-session-pool \\"
    echo "    --resource-group triagent-sandbox-rg \\"
    echo "    --environment triagent-sandbox-cae \\"
    echo "    --location eastus \\"
    echo "    --container-type PythonLTS \\"
    echo "    --ready-session-instances 10"
    exit 1
fi

echo -e "${GREEN}✓ Session Pool: $POOL_ENDPOINT${NC}"

# Step 4: Show current configuration
echo ""
echo -e "${YELLOW}Step 4: Getting Session Pool configuration...${NC}"
$AZ_CMD containerapp sessionpool show \
    --name triagent-sandbox-session-pool \
    --resource-group triagent-sandbox-rg \
    --query "{
        name: name,
        maxSessions: properties.scaleConfiguration.maxConcurrentSessions,
        readyInstances: properties.scaleConfiguration.readySessionInstances,
        cooldownPeriod: properties.dynamicPoolConfiguration.lifecycleConfiguration.cooldownPeriodInSeconds,
        maxAlivePeriod: properties.dynamicPoolConfiguration.lifecycleConfiguration.maxAlivePeriodInSeconds
    }" -o table

echo ""

# Export environment variables for Python script
export TRIAGENT_SESSION_POOL_ENDPOINT="$POOL_ENDPOINT"
export AZ_CMD="$AZ_CMD"

# Step 5: Run Python script
echo -e "${YELLOW}Step 5: Starting interactive session...${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run Python script
python "$SCRIPT_DIR/test-session-api.py"
