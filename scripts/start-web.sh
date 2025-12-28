#!/bin/bash
# start-web.sh - Start triagent web terminal
#
# This script builds and runs the triagent web terminal container.
# Access the terminal at http://localhost:7681
#
# Usage:
#   ./scripts/start-web.sh              # Start in foreground
#   ./scripts/start-web.sh -d           # Start in background (detached)
#   ./scripts/start-web.sh --build      # Force rebuild before starting
#   ./scripts/start-web.sh --stop       # Stop the running container
#   ./scripts/start-web.sh --logs       # View container logs

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")/.."

# Default options
DETACH=""
BUILD_FLAG=""
COMPOSE_FILE="docker-compose.web.yml"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detach)
            DETACH="-d"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --stop)
            echo -e "${YELLOW}Stopping triagent web terminal...${NC}"
            docker compose -f "$COMPOSE_FILE" down
            echo -e "${GREEN}Stopped.${NC}"
            exit 0
            ;;
        --logs)
            docker compose -f "$COMPOSE_FILE" logs -f
            exit 0
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --detach    Run in background"
            echo "  --build         Force rebuild before starting"
            echo "  --stop          Stop the running container"
            echo "  --logs          View container logs"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print banner
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Triagent Web Terminal                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Build and start
echo -e "${YELLOW}Starting triagent web terminal...${NC}"
docker compose -f "$COMPOSE_FILE" up $BUILD_FLAG $DETACH

if [ -n "$DETACH" ]; then
    echo ""
    echo -e "${GREEN}Triagent web terminal is running!${NC}"
    echo ""
    echo -e "  ${BLUE}Web Terminal:${NC}  http://localhost:7681"
    echo ""
    echo -e "  ${YELLOW}First time?${NC} Run ${GREEN}/init${NC} in the terminal to configure."
    echo ""
    echo -e "  ${YELLOW}Commands:${NC}"
    echo "    View logs:   ./scripts/start-web.sh --logs"
    echo "    Stop:        ./scripts/start-web.sh --stop"
    echo ""
fi
