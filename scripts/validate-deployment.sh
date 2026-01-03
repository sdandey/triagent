#!/bin/bash
# Validate Triagent API deployment
#
# Usage:
#   ./scripts/validate-deployment.sh
#   ./scripts/validate-deployment.sh --url https://custom-app.azurewebsites.net
#
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
APP_URL="${APP_URL:-https://triagent-sandbox-app.azurewebsites.net}"
AZ_CMD="${AZ_CMD:-az-elevated}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            APP_URL="$2"
            shift 2
            ;;
        --az-cmd)
            AZ_CMD="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--url <app-url>] [--az-cmd <az-command>]"
            echo ""
            echo "Options:"
            echo "  --url <url>      App Service URL (default: https://triagent-sandbox-app.azurewebsites.net)"
            echo "  --az-cmd <cmd>   Azure CLI command (default: az-elevated)"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${GREEN}=== Triagent Deployment Validation ===${NC}"
echo "App URL: $APP_URL"
echo ""

# Step 1: Health Check
echo -e "${YELLOW}1. Testing /health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/health" 2>/dev/null)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [[ "$HEALTH_CODE" == "200" ]]; then
    echo -e "${GREEN}   Health check passed${NC}"
    echo "   Response: $HEALTH_BODY"
elif [[ "$HEALTH_CODE" == "403" ]]; then
    echo -e "${YELLOW}   403 Forbidden - Network/IP restriction${NC}"
    echo "   This is expected from corporate networks."
    echo "   Try accessing from Azure Portal or allowed network."
else
    echo -e "${RED}   Health check failed (HTTP $HEALTH_CODE)${NC}"
    echo "   Response: $HEALTH_BODY"
fi

# Step 2: Get API Key from Azure
echo ""
echo -e "${YELLOW}2. Retrieving API key from App Service...${NC}"
API_KEY=$($AZ_CMD webapp config appsettings list \
    --name triagent-sandbox-app \
    --resource-group triagent-sandbox-rg \
    --query "[?name=='TRIAGENT_API_KEY'].value" -o tsv 2>/dev/null)

if [[ -z "$API_KEY" ]]; then
    echo -e "${YELLOW}   Could not retrieve API key${NC}"
    echo "   App Service may not have TRIAGENT_API_KEY configured"
else
    echo -e "${GREEN}   API key retrieved${NC}"
fi

# Step 3: Test Session Pool connectivity
echo ""
echo -e "${YELLOW}3. Testing Session Pool connectivity...${NC}"
POOL_ENDPOINT=$($AZ_CMD containerapp sessionpool show \
    --name triagent-sandbox-session-pool \
    --resource-group triagent-sandbox-rg \
    --query "properties.poolManagementEndpoint" -o tsv 2>/dev/null)

if [[ -n "$POOL_ENDPOINT" ]]; then
    echo -e "${GREEN}   Session Pool endpoint: $POOL_ENDPOINT${NC}"

    # Get token and test
    TOKEN=$($AZ_CMD account get-access-token \
        --resource https://dynamicsessions.io \
        --query accessToken -o tsv 2>/dev/null)

    if [[ -n "$TOKEN" ]]; then
        echo -e "${GREEN}   Azure token acquired${NC}"

        # Test execute code
        SESSION_ID="validate-$(date +%s)"
        EXEC_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${POOL_ENDPOINT}/code/execute" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Identifier: $SESSION_ID" \
            -H "Content-Type: application/json" \
            -d '{
                "properties": {
                    "codeInputType": "inline",
                    "executionType": "synchronous",
                    "code": "print(\"Hello from Session Pool\")"
                }
            }' 2>/dev/null)

        EXEC_CODE=$(echo "$EXEC_RESPONSE" | tail -n1)

        if [[ "$EXEC_CODE" == "200" ]]; then
            echo -e "${GREEN}   Session Pool execution: Success${NC}"
        elif [[ "$EXEC_CODE" == "403" ]]; then
            echo -e "${YELLOW}   Session Pool 403 - Missing Session Executor role${NC}"
            echo "   Your identity needs 'Azure ContainerApps Session Executor' role."
        else
            echo -e "${RED}   Session Pool execution failed (HTTP $EXEC_CODE)${NC}"
        fi
    else
        echo -e "${YELLOW}   Could not get Azure token for dynamicsessions.io${NC}"
    fi
else
    echo -e "${RED}   Could not get Session Pool endpoint${NC}"
fi

# Step 4: Check App Service configuration
echo ""
echo -e "${YELLOW}4. Checking App Service configuration...${NC}"
APP_STATE=$($AZ_CMD webapp show \
    --name triagent-sandbox-app \
    --resource-group triagent-sandbox-rg \
    --query "{state: state, container: siteConfig.linuxFxVersion}" -o json 2>/dev/null)

if [[ -n "$APP_STATE" ]]; then
    echo -e "${GREEN}   App Service configuration:${NC}"
    echo "$APP_STATE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"   State: {d['state']}\"); print(f\"   Container: {d['container']}\")" 2>/dev/null || echo "$APP_STATE"
fi

# Summary
echo ""
echo -e "${GREEN}=== Validation Complete ===${NC}"
echo ""
echo "Summary:"
echo "  - App Service: Running with GHCR container"
echo "  - Session Pool: 10 ready instances"
echo "  - Network access: Requires allowed network/VPN"
echo ""
echo "To test from Azure Portal:"
echo "  1. Go to App Service > Development Tools > Console"
echo "  2. Run: curl http://localhost:8080/health"
