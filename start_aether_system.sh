#!/bin/bash
#
# Start HAL + Aether Access System
#
# This script starts both HAL Core (the panel brain) and Aether Access
# (the management interface) for the Azure Panel.
#
# Architecture:
#   HAL Core (port 8081)     - Standalone panel brain, owns all data
#   Aether Access (port 8080) - Management UI, reads from HAL
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
export HAL_DB_PATH="${HAL_DB_PATH:-$SCRIPT_DIR/hal_core.db}"
export HAL_PORT="${HAL_PORT:-8081}"
export AETHER_PORT="${AETHER_PORT:-8080}"
export HAL_CORE_URL="${HAL_CORE_URL:-http://localhost:$HAL_PORT}"

echo "========================================"
echo "HAL + Aether Access System Startup"
echo "========================================"
echo "HAL Core:      port $HAL_PORT"
echo "Aether Access: port $AETHER_PORT"
echo "Database:      $HAL_DB_PATH"
echo "========================================"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Check for required packages
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn, aiohttp, pydantic" 2>/dev/null || {
    echo "Installing dependencies..."
    pip3 install fastapi uvicorn aiohttp pydantic
}

# Create PID directory
mkdir -p "$SCRIPT_DIR/.pids"

# Start HAL Core
echo ""
echo "Starting HAL Core (the panel brain)..."
cd "$SCRIPT_DIR/api"
nohup python3 hal_core_api.py > "$SCRIPT_DIR/.pids/hal_core.log" 2>&1 &
echo $! > "$SCRIPT_DIR/.pids/hal_core.pid"
echo "HAL Core started (PID: $(cat $SCRIPT_DIR/.pids/hal_core.pid))"

# Wait for HAL to be ready
echo "Waiting for HAL Core to be ready..."
for i in {1..30}; do
    if curl -s "http://localhost:$HAL_PORT/hal/health" > /dev/null 2>&1; then
        echo "HAL Core is ready!"
        break
    fi
    sleep 0.5
done

# Start Aether Access
echo ""
echo "Starting Aether Access (management interface)..."
cd "$SCRIPT_DIR/gui/backend"
nohup python3 api_aether.py > "$SCRIPT_DIR/.pids/aether_access.log" 2>&1 &
echo $! > "$SCRIPT_DIR/.pids/aether_access.pid"
echo "Aether Access started (PID: $(cat $SCRIPT_DIR/.pids/aether_access.pid))"

# Wait for Aether to be ready
echo "Waiting for Aether Access to be ready..."
for i in {1..30}; do
    if curl -s "http://localhost:$AETHER_PORT/api/system/info" > /dev/null 2>&1; then
        echo "Aether Access is ready!"
        break
    fi
    sleep 0.5
done

echo ""
echo "========================================"
echo "System Started Successfully!"
echo "========================================"
echo ""
echo "HAL Core API:      http://localhost:$HAL_PORT"
echo "  - Health:        http://localhost:$HAL_PORT/hal/health"
echo "  - API Docs:      http://localhost:$HAL_PORT/docs"
echo ""
echo "Aether Access API: http://localhost:$AETHER_PORT"
echo "  - Dashboard:     http://localhost:$AETHER_PORT/api/dashboard/stats"
echo "  - API Docs:      http://localhost:$AETHER_PORT/docs"
echo ""
echo "Logs:"
echo "  - HAL Core:      $SCRIPT_DIR/.pids/hal_core.log"
echo "  - Aether Access: $SCRIPT_DIR/.pids/aether_access.log"
echo ""
echo "To stop the system, run: ./stop_aether_system.sh"
echo "========================================"
