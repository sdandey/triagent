#!/bin/bash
# Start both Chainlit UI and internal API

set -e

# Start internal API on port 8081
echo "Starting internal API on port 8081..."
uvicorn triagent.web.container.api:container_app --host 0.0.0.0 --port 8081 &
API_PID=$!

# Wait for internal API to be ready
sleep 2

# Start Chainlit on port 8080
echo "Starting Chainlit UI on port 8080..."
chainlit run /app/src/triagent/web/container/chainlit_app.py --host 0.0.0.0 --port 8080 &
CHAINLIT_PID=$!

echo "Started API (PID: $API_PID) and Chainlit (PID: $CHAINLIT_PID)"

# Wait for either process to exit
wait -n

# Kill both if one exits
echo "A process exited, shutting down..."
kill $API_PID $CHAINLIT_PID 2>/dev/null || true
